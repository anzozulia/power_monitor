"""
Admin Panel URL Configuration
"""

from django.urls import path

from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard redirect
    path('', views.dashboard_redirect, name='dashboard'),
    path('admin/', views.dashboard_redirect, name='admin_dashboard'),
    
    # Location CRUD
    path('admin/locations/', views.location_list, name='location_list'),
    path('admin/locations/new/', views.location_create, name='location_create'),
    path('admin/locations/<uuid:pk>/', views.location_detail, name='location_detail'),
    path('admin/locations/<uuid:pk>/edit/', views.location_edit, name='location_edit'),
    path('admin/locations/<uuid:pk>/delete/', views.location_delete, name='location_delete'),
    path('admin/locations/<uuid:pk>/reset/', views.location_reset, name='location_reset'),
    path(
        'admin/locations/<uuid:pk>/test-telegram/',
        views.location_test_telegram,
        name='location_test_telegram',
    ),
    path(
        'admin/locations/<uuid:pk>/events/<int:event_id>/delete/',
        views.power_event_delete,
        name='power_event_delete',
    ),
    path(
        'admin/locations/<uuid:pk>/toggle-offline-detection/',
        views.location_toggle_offline_detection,
        name='location_toggle_offline_detection',
    ),
]
