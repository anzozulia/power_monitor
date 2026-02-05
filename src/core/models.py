"""
Power Outage Monitor - Database Models

Entities:
- Location: Monitored property with configuration
- Heartbeat: Individual heartbeat signal from device
- PowerEvent: Power status change record
- DiagramMessage: Telegram message tracking for diagrams
"""

import secrets
import uuid

from django.db import models
from django.utils import timezone


class PowerStatus(models.TextChoices):
    """Power status enumeration."""
    UNKNOWN = 'unknown', 'Unknown'
    ON = 'on', 'Power On'
    OFF = 'off', 'Power Off'


class EventType(models.TextChoices):
    """Power event type enumeration."""
    POWER_ON = 'power_on', 'Power On'
    POWER_OFF = 'power_off', 'Power Off'


class AlertLanguage(models.TextChoices):
    """Language selection for alerting and diagrams."""
    EN = 'en', 'English'
    RU = 'ru', 'Русский'
    UK = 'uk', 'Українська'


class Location(models.Model):
    """
    Represents a monitored property/house with its configuration.
    
    Each location has its own Telegram bot settings and device API key.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    
    # Heartbeat configuration
    heartbeat_period_seconds = models.PositiveIntegerField(
        default=60,
        help_text="Expected interval between heartbeats in seconds (minimum 10)"
    )
    grace_period_seconds = models.PositiveIntegerField(
        default=30,
        help_text="Extra time before marking as offline in seconds (minimum 10)"
    )
    
    # Telegram configuration
    telegram_bot_token = models.CharField(max_length=100)
    telegram_chat_id = models.CharField(max_length=50)
    alert_language = models.CharField(
        max_length=2,
        choices=AlertLanguage.choices,
        default=AlertLanguage.EN,
    )
    
    # Device authentication
    api_key = models.CharField(max_length=64, unique=True, editable=False)
    
    # Power status tracking
    current_power_status = models.CharField(
        max_length=10,
        choices=PowerStatus.choices,
        default=PowerStatus.UNKNOWN
    )
    monitoring_started_at = models.DateTimeField(null=True, blank=True)
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    last_status_change_at = models.DateTimeField(null=True, blank=True)
    
    # Alerting status
    alerting_enabled = models.BooleanField(default=True)
    alerting_failed = models.BooleanField(default=False)

    # Maintenance controls
    is_offline_detection_disabled = models.BooleanField(
        default=False,
        help_text="Disable auto power-off when heartbeat timeout exceeds grace period.",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Auto-generate API key on first save
        if not self.api_key:
            self.api_key = self._generate_api_key()
        super().save(*args, **kwargs)
    
    @staticmethod
    def _generate_api_key() -> str:
        """Generate a secure 64-character API key."""
        return secrets.token_hex(32)
    
    def clean(self):
        """Validate model fields."""
        from django.core.exceptions import ValidationError
        
        if self.heartbeat_period_seconds < 10:
            raise ValidationError({
                'heartbeat_period_seconds': 'Heartbeat period must be at least 10 seconds.'
            })
        
        if self.grace_period_seconds < 10:
            raise ValidationError({
                'grace_period_seconds': 'Grace period must be at least 10 seconds.'
            })
    
    @property
    def is_monitoring_active(self) -> bool:
        """Check if monitoring has started for this location."""
        return self.monitoring_started_at is not None
    
    @property
    def timeout_seconds(self) -> int:
        """Total seconds before marking as offline."""
        return self.heartbeat_period_seconds + self.grace_period_seconds
    
    @property
    def power_status_display(self) -> str:
        """Human-readable power status."""
        if not self.is_monitoring_active:
            return "Not Started"
        return self.get_current_power_status_display()


class Heartbeat(models.Model):
    """
    Records each heartbeat signal received from devices.
    
    High-volume table - each device sends a heartbeat every N seconds.
    """
    id = models.BigAutoField(primary_key=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='heartbeats'
    )
    received_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        ordering = ['-received_at']
        verbose_name = 'Heartbeat'
        verbose_name_plural = 'Heartbeats'
        indexes = [
            models.Index(fields=['location', '-received_at']),
        ]
    
    def __str__(self):
        return f"{self.location.name} @ {self.received_at}"


class PowerEvent(models.Model):
    """
    Records power status changes for historical tracking and analytics.
    
    Used for:
    - Generating weekly diagrams
    - Calculating outage durations
    - Historical analytics
    """
    id = models.BigAutoField(primary_key=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='power_events'
    )
    event_type = models.CharField(max_length=10, choices=EventType.choices)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    previous_state_duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duration of the previous power state in seconds"
    )
    
    # Alert tracking
    alert_sent = models.BooleanField(default=False)
    alert_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-occurred_at']
        verbose_name = 'Power Event'
        verbose_name_plural = 'Power Events'
        indexes = [
            models.Index(fields=['location', 'occurred_at']),
        ]
    
    def __str__(self):
        return f"{self.location.name}: {self.get_event_type_display()} @ {self.occurred_at}"
    
    @property
    def duration_display(self) -> str:
        """Human-readable duration of previous state."""
        if self.previous_state_duration_seconds is None:
            return "N/A"
        
        seconds = self.previous_state_duration_seconds
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"


class DiagramMessage(models.Model):
    """
    Tracks Telegram messages containing weekly diagrams.
    
    Used for:
    - Pin/unpin management
    - Hourly message updates
    - Message history
    """
    id = models.BigAutoField(primary_key=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='diagram_messages'
    )
    telegram_message_id = models.BigIntegerField()
    diagram_date = models.DateField(db_index=True)
    is_pinned = models.BooleanField(default=False)
    last_updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-diagram_date']
        verbose_name = 'Diagram Message'
        verbose_name_plural = 'Diagram Messages'
        unique_together = ['location', 'diagram_date']
        indexes = [
            models.Index(fields=['location', 'diagram_date']),
        ]
    
    def __str__(self):
        return f"{self.location.name} diagram for {self.diagram_date}"
