# -*- coding: utf-8 -*-
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from detection import views as detection_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', detection_views.login_view, name='home'),
    path('home/', detection_views.home_view, name='detection_home'),
    path('login/', detection_views.login_view, name='login'),
    path('register/', detection_views.register_view, name='register'),
    path('logout/', detection_views.logout_view, name='logout'),
    path('home/', detection_views.home_view, name='detection_home'),
    path('detect/', detection_views.detect_view, name='detection_detect'),
    path('history/', detection_views.history_view, name='detection_history'),
    path('profile/', detection_views.profile_view, name='detection_profile'),
    path('xiaoyu/', detection_views.xiaoyu_chat_view, name='xiaoyu_chat'),
    path('chat-history/', detection_views.chat_history_view, name='chat_history'),
    path('api/login/', detection_views.api_login, name='api_login'),
    path('api/detect/', detection_views.api_detect_image, name='api_detect_image'),
    path('api/delete/<int:record_id>/', detection_views.api_delete_record, name='api_delete_record'),
    path('api/avatar/', detection_views.api_upload_avatar, name='api_upload_avatar'),
    path('api/chat/', detection_views.api_chat, name='api_chat'),
    path('api/chat/records/', detection_views.api_chat_records, name='api_chat_records'),
    path('api/chat/record/<int:record_id>/', detection_views.api_chat_record_detail, name='api_chat_record_detail'),
    path('api/chat/save/', detection_views.api_save_chat_record, name='api_save_chat_record'),
    path('api/chat/delete/<int:record_id>/', detection_views.api_delete_chat_record, name='api_delete_chat_record'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
