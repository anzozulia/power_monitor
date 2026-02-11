"""
Admin Panel Views

Handles authentication and location CRUD operations.
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from telegram.error import TelegramError

from core.models import DiagramMessage, Heartbeat, Location, PowerEvent, PowerStatus

from .forms import LocationForm


# =============================================================================
# Authentication Views
# =============================================================================

def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('admin_panel:location_list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'admin_panel:location_list')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'admin_panel/login.html')


def logout_view(request):
    """Handle user logout."""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out.')
    return redirect('admin_panel:login')


def dashboard_redirect(request):
    """Redirect to location list."""
    return redirect('admin_panel:location_list')


# =============================================================================
# Location Views
# =============================================================================

@login_required
def location_list(request):
    """Display all locations with their current status."""
    locations = Location.objects.all()
    return render(request, 'admin_panel/locations/list.html', {
        'locations': locations,
    })


@login_required
def location_create(request):
    """Create a new location."""
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, f'Location "{location.name}" created successfully.')
            return redirect('admin_panel:location_detail', pk=location.pk)
    else:
        form = LocationForm()
    
    return render(request, 'admin_panel/locations/form.html', {
        'form': form,
        'title': 'Add Location',
        'submit_text': 'Create Location',
    })


@login_required
def location_detail(request, pk):
    """View location details and recent events."""
    location = get_object_or_404(Location, pk=pk)
    recent_events = location.power_events.all()[:10]
    host = request.get_host()
    endpoint_url = f"http://{host}/api/heartbeat/"
    endpoint_url_with_key = f"{endpoint_url}?api_key={location.api_key}"
    
    return render(request, 'admin_panel/locations/detail.html', {
        'location': location,
        'recent_events': recent_events,
        'endpoint_url': endpoint_url,
        'endpoint_url_with_key': endpoint_url_with_key,
    })


@login_required
def location_edit(request, pk):
    """Edit an existing location."""
    location = get_object_or_404(Location, pk=pk)
    
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, f'Location "{location.name}" updated successfully.')
            return redirect('admin_panel:location_list')
    else:
        form = LocationForm(instance=location)
    
    return render(request, 'admin_panel/locations/form.html', {
        'form': form,
        'location': location,
        'title': f'Edit {location.name}',
        'submit_text': 'Save Changes',
    })


@login_required
def location_delete(request, pk):
    """Delete a location."""
    location = get_object_or_404(Location, pk=pk)
    
    if request.method == 'POST':
        name = location.name
        location.delete()
        messages.success(request, f'Location "{name}" deleted successfully.')
        return redirect('admin_panel:location_list')
    
    return render(request, 'admin_panel/locations/detail.html', {
        'location': location,
        'confirm_delete': True,
    })


@login_required
def location_reset(request, pk):
    """Reset monitoring data for a location (keep configuration)."""
    location = get_object_or_404(Location, pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            Heartbeat.objects.filter(location=location).delete()
            PowerEvent.objects.filter(location=location).delete()
            DiagramMessage.objects.filter(location=location).delete()

            location.monitoring_started_at = None
            location.last_heartbeat_at = None
            location.last_status_change_at = None
            location.current_power_status = PowerStatus.UNKNOWN
            location.save(update_fields=[
                'monitoring_started_at',
                'last_heartbeat_at',
                'last_status_change_at',
                'current_power_status',
                'updated_at',
            ])

        messages.success(request, f'Location "{location.name}" data reset successfully.')
        return redirect('admin_panel:location_detail', pk=location.pk)

    recent_events = location.power_events.all()[:10]
    return render(request, 'admin_panel/locations/detail.html', {
        'location': location,
        'recent_events': recent_events,
        'confirm_reset': True,
    })


@login_required
def location_toggle_offline_detection(request, pk):
    """Toggle offline detection for maintenance."""
    location = get_object_or_404(Location, pk=pk)

    if request.method == 'POST':
        location.is_offline_detection_disabled = not location.is_offline_detection_disabled
        location.save(update_fields=['is_offline_detection_disabled', 'updated_at'])
        return JsonResponse({
            'maintenance_mode': location.is_offline_detection_disabled,
        })

    return JsonResponse({'detail': 'Method not allowed.'}, status=405)


@login_required
def location_test_telegram(request, pk):
    """Send and delete a test Telegram message for a location."""
    location = get_object_or_404(Location, pk=pk)

    if request.method == 'POST':
        if not location.telegram_bot_token or not location.telegram_chat_id:
            messages.error(request, 'Telegram bot token or chat ID is missing.')
            return redirect('admin_panel:location_detail', pk=pk)

        try:
            from telegram_client.client import TelegramClient

            client = TelegramClient(location.telegram_bot_token)
            message_id = client.send_message(
                location.telegram_chat_id,
                'Power Monitor test message.',
                disable_notification=True,
            )
            client.delete_message(location.telegram_chat_id, message_id)
            messages.success(request, 'Test message sent and deleted successfully.')
        except TelegramError as e:
            messages.error(request, f'Telegram error: {e}')
        except Exception as e:
            messages.error(request, f'Unexpected error: {e}')

    return redirect('admin_panel:location_detail', pk=pk)


@login_required
def power_event_delete(request, pk, event_id):
    """Delete a power event for a location."""
    event = get_object_or_404(PowerEvent, id=event_id, location_id=pk)

    if request.method == 'POST':
        with transaction.atomic():
            location = event.location
            previous_event = (
                PowerEvent.objects.filter(
                    location_id=pk,
                    occurred_at__lt=event.occurred_at,
                )
                .order_by('-occurred_at')
                .first()
            )
            next_event = (
                PowerEvent.objects.filter(
                    location_id=pk,
                    occurred_at__gt=event.occurred_at,
                )
                .order_by('occurred_at')
                .first()
            )

            _adjust_heartbeats_for_deleted_event(
                location=location,
                event=event,
                previous_event=previous_event,
                next_event=next_event,
            )
            event.delete()

            if next_event:
                if previous_event:
                    duration = next_event.occurred_at - previous_event.occurred_at
                    next_event.previous_state_duration_seconds = int(
                        duration.total_seconds()
                    )
                else:
                    next_event.previous_state_duration_seconds = None
                next_event.save(update_fields=[
                    'previous_state_duration_seconds',
                    'updated_at',
                ])

            _recalculate_location_heartbeat_state(location)

        messages.success(request, 'Power event deleted and durations recalculated.')
    return redirect('admin_panel:location_detail', pk=pk)


def _adjust_heartbeats_for_deleted_event(
    location: Location,
    event: PowerEvent,
    previous_event: PowerEvent | None,
    next_event: PowerEvent | None,
) -> None:
    """Adjust heartbeats so power events reflect heartbeat-derived truth."""
    if event.event_type == 'power_off':
        prev_heartbeat = (
            Heartbeat.objects.filter(
                location=location,
                received_at__lt=event.occurred_at,
            )
            .order_by('-received_at')
            .first()
        )
        next_heartbeat = (
            Heartbeat.objects.filter(
                location=location,
                received_at__gt=event.occurred_at,
            )
            .order_by('received_at')
            .first()
        )
        if not prev_heartbeat or not next_heartbeat:
            return

        has_bridge = Heartbeat.objects.filter(
            location=location,
            received_at__gt=prev_heartbeat.received_at,
            received_at__lt=next_heartbeat.received_at,
        ).exists()
        if has_bridge:
            return

        period_seconds = max(location.heartbeat_period_seconds, 1)
        heartbeats = []
        next_time = prev_heartbeat.received_at + timedelta(seconds=period_seconds)
        while next_time < next_heartbeat.received_at:
            heartbeats.append(Heartbeat(location=location, received_at=next_time))
            next_time += timedelta(seconds=period_seconds)

        if heartbeats:
            Heartbeat.objects.bulk_create(heartbeats)
        return

    if event.event_type == 'power_on':
        end_time = next_event.occurred_at if next_event else timezone.now()
        Heartbeat.objects.filter(
            location=location,
            received_at__gte=event.occurred_at,
            received_at__lt=end_time,
        ).delete()


def _recalculate_location_heartbeat_state(location: Location) -> None:
    last_heartbeat = (
        Heartbeat.objects.filter(location=location)
        .order_by('-received_at')
        .first()
    )
    if last_heartbeat:
        location.last_heartbeat_at = last_heartbeat.received_at
        now = timezone.now()
        from monitoring.services import _is_location_timed_out
        is_timed_out = _is_location_timed_out(location, now)
        if location.is_monitoring_active:
            location.current_power_status = (
                PowerStatus.OFF if is_timed_out else PowerStatus.ON
            )
    else:
        location.last_heartbeat_at = None
        location.current_power_status = PowerStatus.UNKNOWN

    location.save(update_fields=[
        'last_heartbeat_at',
        'current_power_status',
        'updated_at',
    ])
