"""
URL configuration for Power Outage Monitor project.
"""

from django.urls import path, include

urlpatterns = [
    # Admin Panel (custom, not Django admin)
    path('', include('admin_panel.urls')),
    
    # Heartbeat API
    path('api/', include('heartbeat.urls')),
]
