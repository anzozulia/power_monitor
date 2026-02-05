"""
Admin Panel Views

Handles authentication and location CRUD operations.
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

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
            return redirect('admin_panel:location_config', pk=location.pk)
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
    
    return render(request, 'admin_panel/locations/detail.html', {
        'location': location,
        'recent_events': recent_events,
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
def location_config(request, pk):
    """Display ESP32 configuration for a location."""
    location = get_object_or_404(Location, pk=pk)
    
    # Build the heartbeat endpoint URL
    host = request.get_host()
    endpoint_url = f"http://{host}/api/heartbeat/"
    endpoint_url_with_key = f"{endpoint_url}?api_key={location.api_key}"
    
    return render(request, 'admin_panel/locations/config.html', {
        'location': location,
        'endpoint_url': endpoint_url,
        'endpoint_url_with_key': endpoint_url_with_key,
    })
