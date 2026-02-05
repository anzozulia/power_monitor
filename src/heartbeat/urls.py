"""
Heartbeat API URL Configuration
"""

from django.urls import path

from . import views

app_name = 'heartbeat'

urlpatterns = [
    path('heartbeat/', views.heartbeat_view, name='heartbeat'),
]
