"""
Weekly Power Diagram Generator

Creates a clean, minimal weekly diagram (PNG) using SVG + CairoSVG.
"""

import logging
from datetime import date, datetime, timedelta
from io import BytesIO
from typing import List, Tuple

import cairosvg
import svgwrite
from django.utils import timezone

from core.i18n import get_diagram_strings
from core.models import Heartbeat, Location
from monitoring.services import (
    ROUTER_RECONNECT_GRACE_SECONDS,
    ROUTER_RECONNECT_WINDOW_SECONDS,
)

logger = logging.getLogger('analytics')

# Colors
COLOR_ON = '#4ade80'  # Green
COLOR_OFF = '#f87171'  # Red
COLOR_NO_DATA = '#d1d5db'  # Gray
COLOR_DIMMED_ON = '#86efac'
COLOR_DIMMED_OFF = '#fca5a5'
COLOR_DIMMED_NO_DATA = '#d1d5db'
COLOR_TEXT = '#6b7280'
COLOR_TEXT_DIM = '#9ca3af'
COLOR_TICK = '#6b7280'

class DiagramGenerator:
    """
    Generates weekly power status diagrams.
    """

    def __init__(self, location: Location):
        self.location = location

    def generate(self, target_date: date = None) -> BytesIO:
        if target_date is None:
            target_date = timezone.localdate()

        days = self._get_week_days(target_date)
        strings = get_diagram_strings(self.location.alert_language)
        weekdays = strings["weekdays"]

        day_data = []
        for day_date, is_current_week in days:
            status_data = self._get_day_power_status(day_date)
            day_data.append((day_date, is_current_week, status_data))

        # Layout
        width = 1400
        height = 1040
        top_margin = 135
        left_margin = 270
        right_margin = 80
        row_height = 125
        bar_height = 32
        bar_width = width - left_margin - right_margin

        # Fonts
        title_size = 60
        label_size = 32
        tick_size = 28
        font_family = "Liberation Sans, DejaVu Sans, Arial, sans-serif"
        label_font_family = "DejaVu Sans Mono, Liberation Mono, monospace"

        dwg = svgwrite.Drawing(size=(width, height), profile='full')
        dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill='white'))

        shown_dates = [day_date for day_date, _, _ in day_data]
        week_start = min(shown_dates)
        week_end = max(shown_dates)
        title = f"{strings['title']} {week_start.strftime('%d.%m')} – {week_end.strftime('%d.%m')}"
        dwg.add(
            dwg.text(
                title,
                insert=(width / 2, 90),
                text_anchor="middle",
                font_size=title_size,
                font_family=font_family,
                font_weight="600",
                fill=COLOR_TEXT_DIM,
            )
        )

        for i, (day_date, is_current_week, status_data) in enumerate(day_data):
            row_y = top_margin + i * row_height
            bar_y = row_y + 12

            # Day label
            day_label = f"{weekdays[day_date.weekday()]}({day_date.strftime('%d.%m')})"
            is_today = day_date == target_date
            label_color = COLOR_TEXT if is_current_week else COLOR_TEXT_DIM
            dwg.add(
                dwg.text(
                    day_label,
                    insert=(36, bar_y + bar_height + 8),
                    font_size=label_size,
                    font_family=label_font_family,
                    font_weight="600" if is_today else "400",
                    fill=label_color,
                )
            )
            if is_today:
                underline_y = bar_y + bar_height + 16
                dwg.add(
                    dwg.line(
                        start=(38, underline_y),
                        end=(45 + (len(day_label) * (label_size * 0.55)), underline_y),
                        stroke=COLOR_TEXT,
                        stroke_width=3,
                    )
                )

            # Base bar
            base_color = COLOR_NO_DATA if is_current_week else COLOR_DIMMED_NO_DATA
            dwg.add(
                dwg.rect(
                    insert=(left_margin, bar_y),
                    size=(bar_width, bar_height),
                    rx=6,
                    ry=6,
                    fill=base_color,
                )
            )

            # Status segments
            for start_hour, end_hour, status in status_data:
                if end_hour <= start_hour:
                    continue
                color = self._get_color(status, is_current_week)
                x0 = left_margin + (start_hour / 24.0) * bar_width
                x1 = left_margin + (end_hour / 24.0) * bar_width
                segment_width = max(0.5, x1 - x0)
                round_left = start_hour <= 0.0
                round_right = end_hour >= 24.0
                dwg.add(
                    self._segment_path(
                        dwg=dwg,
                        x=x0,
                        y=bar_y,
                        width=segment_width,
                        height=bar_height,
                        radius=6,
                        round_left=round_left,
                        round_right=round_right,
                        fill=color,
                    )
                )

            # Dots on bar for hours 1-23 (helps align with ticks)
            dot_y = bar_y + (bar_height / 2)
            for hour in range(1, 24):
                x = left_margin + (hour / 24.0) * bar_width
                dwg.add(
                    dwg.circle(
                        center=(x, dot_y),
                        r=2 if hour % 4 != 0 else 3,
                        fill=COLOR_TICK,
                        opacity=0.6 if hour % 4 != 0 else 0.8,
                    )
                )

            # Ticks and labels
            tick_y = bar_y + bar_height + 3
            for hour in range(0, 25):
                x = left_margin + (hour / 24.0) * bar_width
                is_major = hour % 4 == 0
                tick_len = 18 if is_major else 12
                dwg.add(
                    dwg.line(
                        start=(x, tick_y),
                        end=(x, tick_y + tick_len),
                        stroke=COLOR_TICK,
                        stroke_width=3 if is_major else 2,
                    )
                )

                if is_major:
                    dwg.add(
                        dwg.text(
                            f"{hour}:00",
                            insert=(x, tick_y + tick_len + 26),
                            text_anchor="middle",
                            font_size=tick_size,
                            font_family=font_family,
                            font_weight="500",
                            fill=COLOR_TEXT_DIM,
                        )
                    )

        svg_bytes = dwg.tostring().encode('utf-8')
        png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=width, output_height=height)
        buffer = BytesIO()
        buffer.write(png_bytes)
        buffer.seek(0)
        return buffer
    
    def _get_week_days(self, target_date: date) -> List[Tuple[date, bool]]:
        """
        Get the 7 days to display in the diagram.
        
        Returns list of (date, is_current_week) tuples.
        Monday at index 0, Sunday at index 6.
        """
        # Find Monday of current week
        monday = target_date - timedelta(days=target_date.weekday())
        
        days = []
        for i in range(7):
            day_date = monday + timedelta(days=i)
            # Days after today are from last week (dimmed)
            is_current_week = day_date <= target_date
            
            if not is_current_week:
                # Show last week's data for future days
                day_date = day_date - timedelta(days=7)
            
            days.append((day_date, is_current_week))
        
        return days
    
    def _get_day_power_status(self, day_date: date) -> List[Tuple[float, float, str]]:
        """
        Get power status segments for a specific day.
        
        Returns list of (start_hour, end_hour, status) tuples.
        """
        # Check if monitoring was active on this day
        if not self.location.monitoring_started_at:
            return [(0, 24, 'no_data')]
        
        monitoring_start = timezone.localtime(self.location.monitoring_started_at).date()
        if day_date < monitoring_start:
            return [(0, 24, 'no_data')]
        
        # Get heartbeats for this day
        day_start = timezone.make_aware(datetime.combine(day_date, datetime.min.time()))
        day_end = day_start + timedelta(days=1)
        
        heartbeats = list(
            Heartbeat.objects.filter(
                location=self.location,
                received_at__gte=day_start,
                received_at__lt=day_end,
            )
            .order_by('received_at')
            .values_list('received_at', flat=True)
        )
        prev_heartbeat = (
            Heartbeat.objects.filter(
                location=self.location,
                received_at__lt=day_start,
            )
            .order_by('-received_at')
            .values_list('received_at', flat=True)
            .first()
        )
        next_heartbeat = (
            Heartbeat.objects.filter(
                location=self.location,
                received_at__gte=day_end,
            )
            .order_by('received_at')
            .values_list('received_at', flat=True)
            .first()
        )

        timeline = []
        if prev_heartbeat:
            timeline.append(prev_heartbeat)
        timeline.extend(heartbeats)
        if next_heartbeat:
            timeline.append(next_heartbeat)

        # Build intervals from heartbeats
        intervals = []
        timeout_seconds = self.location.timeout_seconds
        if timeline:
            on_started_at = timeline[0]
            for idx in range(len(timeline) - 1):
                start = timeline[idx]
                end = timeline[idx + 1]
                effective_timeout = timeout_seconds
                if self._use_router_reconnect_grace(start, on_started_at):
                    effective_timeout += ROUTER_RECONNECT_GRACE_SECONDS
                status = (
                    'on'
                    if (end - start).total_seconds() <= effective_timeout
                    else 'off'
                )
                intervals.append((start, end, status))
                if status == 'off':
                    on_started_at = end

            end_limit = day_end
            today = timezone.localdate()
            if day_date == today:
                now = timezone.localtime()
                if now < day_end:
                    end_limit = now

            last_time = timeline[-1]
            if last_time < end_limit:
                effective_timeout = timeout_seconds
                if self._use_router_reconnect_grace(last_time, on_started_at):
                    effective_timeout += ROUTER_RECONNECT_GRACE_SECONDS
                status = (
                    'on'
                    if (end_limit - last_time).total_seconds() <= effective_timeout
                    else 'off'
                )
                intervals.append((last_time, end_limit, status))
            elif not intervals and timeline:
                # Single heartbeat in view: infer state to end_limit.
                effective_timeout = timeout_seconds
                if self._use_router_reconnect_grace(timeline[0], on_started_at):
                    effective_timeout += ROUTER_RECONNECT_GRACE_SECONDS
                status = (
                    'on'
                    if (end_limit - timeline[0]).total_seconds() <= effective_timeout
                    else 'off'
                )
                if timeline[0] < end_limit:
                    intervals.append((timeline[0], end_limit, status))
        else:
            end_limit = day_end
            if day_date == timezone.localdate():
                now = timezone.localtime()
                if now < day_end:
                    end_limit = now

        # Build segments for the day
        segments = []
        cursor = day_start

        def add_segment(start_dt: datetime, end_dt: datetime, status: str) -> None:
            start_hour = self._to_day_hour(start_dt)
            end_hour = self._to_day_hour(end_dt)
            if end_hour <= start_hour:
                return
            if segments and segments[-1][2] == status and abs(segments[-1][1] - start_hour) < 0.0001:
                segments[-1] = (segments[-1][0], end_hour, status)
                return
            segments.append((start_hour, end_hour, status))

        for start, end, status in intervals:
            if end <= day_start:
                continue
            if start >= end_limit:
                break
            seg_start = max(start, day_start)
            seg_end = min(end, end_limit)
            if seg_start > cursor:
                add_segment(cursor, seg_start, 'no_data')
            add_segment(seg_start, seg_end, status)
            cursor = max(cursor, seg_end)

        if cursor < end_limit:
            add_segment(cursor, end_limit, 'no_data')

        if day_date == timezone.localdate() and end_limit < day_end:
            add_segment(end_limit, day_end, 'no_data')

        return segments if segments else [(0, 24, 'no_data')]

    @staticmethod
    def _to_day_hour(timestamp: datetime) -> float:
        local_time = timezone.localtime(timestamp)
        return (
            local_time.hour
            + local_time.minute / 60.0
            + local_time.second / 3600.0
        )

    def _use_router_reconnect_grace(
        self,
        heartbeat_time: datetime,
        on_started_at: datetime,
    ) -> bool:
        if not self.location.is_router_reconnect_window_enabled:
            return False
        elapsed = (heartbeat_time - on_started_at).total_seconds()
        return elapsed <= ROUTER_RECONNECT_WINDOW_SECONDS

    def _get_color(self, status: str, is_current_week: bool) -> str:
        """Get the color for a status, with dimming for previous week."""
        if is_current_week:
            if status == 'on':
                return COLOR_ON
            elif status == 'off':
                return COLOR_OFF
            else:
                return COLOR_NO_DATA
        else:
            # Dimmed colors for previous week
            if status == 'on':
                return COLOR_DIMMED_ON
            elif status == 'off':
                return COLOR_DIMMED_OFF
            else:
                return COLOR_DIMMED_NO_DATA

    def _segment_path(
        self,
        dwg: svgwrite.Drawing,
        x: float,
        y: float,
        width: float,
        height: float,
        radius: float,
        round_left: bool,
        round_right: bool,
        fill: str,
    ):
        """Create a path with optional rounded left/right corners."""
        r = min(radius, height / 2, width / 2)
        path = dwg.path(fill=fill, stroke='none')

        # Start at top-left
        if round_left:
            path.push(f"M {x + r},{y}")
        else:
            path.push(f"M {x},{y}")

        # Top edge
        if round_right:
            path.push(f"H {x + width - r}")
            path.push(f"A {r},{r} 0 0 1 {x + width},{y + r}")
        else:
            path.push(f"H {x + width}")

        # Right edge
        if round_right:
            path.push(f"V {y + height - r}")
            path.push(f"A {r},{r} 0 0 1 {x + width - r},{y + height}")
        else:
            path.push(f"V {y + height}")

        # Bottom edge
        if round_left:
            path.push(f"H {x + r}")
            path.push(f"A {r},{r} 0 0 1 {x},{y + height - r}")
        else:
            path.push(f"H {x}")

        # Left edge
        if round_left:
            path.push(f"V {y + r}")
            path.push(f"A {r},{r} 0 0 1 {x + r},{y}")
        else:
            path.push(f"V {y}")

        path.push("Z")
        return path

def generate_diagram_for_location(location: Location, target_date: date | None = None) -> BytesIO:
    """
    Generate a weekly diagram for a location.
    
    Args:
        location: The location to generate diagram for
        target_date: Date to anchor the weekly view (defaults to today)
    
    Returns:
        BytesIO containing the PNG image
    """
    generator = DiagramGenerator(location)
    return generator.generate(target_date=target_date)
