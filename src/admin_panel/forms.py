"""
Admin Panel Forms

Forms for location management.
"""

from django import forms

from core.models import Location


class LocationForm(forms.ModelForm):
    """Form for creating and editing locations."""
    
    class Meta:
        model = Location
        fields = [
            'name',
            'heartbeat_period_seconds',
            'grace_period_seconds',
            'telegram_bot_token',
            'telegram_chat_id',
            'alert_language',
            'alerting_enabled',
            'is_offline_detection_disabled',
            'is_router_reconnect_window_enabled',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 px-3',
                'placeholder': 'e.g., Home Kyiv',
            }),
            'heartbeat_period_seconds': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 px-3',
                'min': 10,
            }),
            'grace_period_seconds': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 px-3',
                'min': 10,
            }),
            'telegram_bot_token': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 px-3',
                'placeholder': '123456789:ABCdefGHIjklMNOpqrsTUVwxyz',
            }),
            'telegram_chat_id': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 px-3',
                'placeholder': '-1001234567890',
            }),
            'alert_language': forms.Select(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 px-3',
            }),
            'alerting_enabled': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600',
            }),
            'is_offline_detection_disabled': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600',
            }),
            'is_router_reconnect_window_enabled': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600',
            }),
        }
        help_texts = {
            'heartbeat_period_seconds': 'How often the device will send heartbeats (in seconds). Minimum: 10',
            'grace_period_seconds': 'Extra time to wait before marking as offline (in seconds). Minimum: 10',
            'telegram_bot_token': 'Bot token from @BotFather',
            'telegram_chat_id': 'Chat or channel ID for alerts (negative for groups)',
            'alert_language': 'Language used for Telegram alerts and diagram text.',
            'is_offline_detection_disabled': 'Temporarily disable auto power-off when heartbeats time out.',
            'is_router_reconnect_window_enabled': (
                'Enable a router reconnect window after power-on '
                '(5 minutes window + 3 minutes extra grace).'
            ),
        }
    
    def clean_heartbeat_period_seconds(self):
        value = self.cleaned_data['heartbeat_period_seconds']
        if value < 10:
            raise forms.ValidationError('Heartbeat period must be at least 10 seconds.')
        return value
    
    def clean_grace_period_seconds(self):
        value = self.cleaned_data['grace_period_seconds']
        if value < 10:
            raise forms.ValidationError('Grace period must be at least 10 seconds.')
        return value
