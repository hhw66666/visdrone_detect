# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
import json

class UserProfile(models.Model):
    """用户扩展信息"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

class DetectionRecord(models.Model):
    """检测记录"""
    TYPE_CHOICES = [
        ('image', '图片检测'),
        ('video', '视频检测'),
        ('batch', '批量检测'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='detections')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    file_path = models.ImageField(upload_to='uploads/', null=True, blank=True)
    result_image = models.ImageField(upload_to='results/', null=True, blank=True)
    result_json = models.TextField(blank=True)
    total_detections = models.IntegerField(default=0)
    confidence_threshold = models.FloatField(default=0.25)
    iou_threshold = models.FloatField(default=0.45)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.file_name} - {self.created_at}"

    def get_detections_list(self):
        if self.result_json:
            return json.loads(self.result_json)
        return []

class DetectionHistory(models.Model):
    """检测历史详情"""
    record = models.ForeignKey(DetectionRecord, on_delete=models.CASCADE, related_name='details')
    class_name = models.CharField(max_length=50)
    class_id = models.IntegerField()
    confidence = models.FloatField()
    bbox_x1 = models.IntegerField()
    bbox_y1 = models.IntegerField()
    bbox_x2 = models.IntegerField()
    bbox_y2 = models.IntegerField()

    def __str__(self):
        return f"{self.class_name} - {self.confidence:.2f}"

class FavoriteRecord(models.Model):
    """收藏记录"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    record = models.ForeignKey(DetectionRecord, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'record']

class ChatRecord(models.Model):
    """聊天记录"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_records')
    title = models.CharField(max_length=100, blank=True, help_text="聊天标题（取自第一条消息）")
    messages_json = models.TextField(help_text="聊天消息 JSON")
    message_count = models.IntegerField(default=0, help_text="消息条数")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "聊天记录"
        verbose_name_plural = "聊天记录"

    def __str__(self):
        return f"{self.user.username} - {self.title[:20]} - {self.created_at}"

    def get_messages(self):
        if self.messages_json:
            return json.loads(self.messages_json)
        return []

    def set_messages(self, messages):
        self.messages_json = json.dumps(messages, ensure_ascii=False)
