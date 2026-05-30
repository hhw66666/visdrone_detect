# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='detection_home'),
    path('detect/', views.detect_view, name='detection_detect'),
    path('history/', views.history_view, name='detection_history'),
    path('profile/', views.profile_view, name='detection_profile'),
    path('api/detect/', views.api_detect_image, name='api_detect_image'),
    path('api/delete/<int:record_id>/', views.api_delete_record, name='api_delete_record'),
    path('api/avatar/', views.api_upload_avatar, name='api_upload_avatar'),
    path('api/leaderboard/', views.api_leaderboard, name='api_leaderboard'),
]
