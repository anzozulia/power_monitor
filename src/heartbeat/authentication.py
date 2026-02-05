"""
Heartbeat API Authentication

API key authentication for ESP32 devices.
"""

from typing import Optional

from core.models import Location


def authenticate_api_key(request) -> Optional[Location]:
    """
    Authenticate request using query param or X-API-Key header.
    
    Returns the Location if authentication succeeds, None otherwise.
    """
    api_key = request.GET.get('api_key') or request.headers.get('X-API-Key')

    if not api_key:
        return None

    try:
        location = Location.objects.get(api_key=api_key)
        return location
    except Location.DoesNotExist:
        return None
