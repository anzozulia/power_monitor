"""
Heartbeat API Views

Handles heartbeat reception from devices.
"""

import logging

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from core.models import Location

from .authentication import authenticate_api_key

logger = logging.getLogger('monitoring')


@csrf_exempt
@require_GET
def heartbeat_view(request):
    """
    Receive heartbeat from a device.
    
    Expects api_key query param or X-API-Key header.
    Returns JSON response with status.
    """
    # Authenticate the request
    location = authenticate_api_key(request)
    
    if location is None:
        return JsonResponse({'error': 'invalid_api_key'}, status=401)
    
    # Check for duplicate heartbeat (within 5 seconds)
    now = timezone.now()
    if location.last_heartbeat_at:
        time_since_last = (now - location.last_heartbeat_at).total_seconds()
        if time_since_last < 5:
            logger.debug(f"Duplicate heartbeat ignored for {location.name}")
            return JsonResponse({
                'status': 'duplicate_ignored',
                'received_at': location.last_heartbeat_at.isoformat(),
            })
    
    # Process the heartbeat
    from monitoring.services import process_heartbeat
    process_heartbeat(location, now)
    
    logger.info(f"Heartbeat received for {location.name}")
    
    return JsonResponse({
        'status': 'ok',
        'received_at': now.isoformat(),
    })
