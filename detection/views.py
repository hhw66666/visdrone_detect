# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.paginator import Paginator
import os
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch
from ultralytics import YOLO
import time

# 导入配置
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detect_system.config_loader import get_detection_config, get_classes, get_app_config

# 导入 AI 服务模块
from ai_services.agents.xiaoyu import XiaoyuAgent, get_xiaoyu_agent

# 全局模型
_model = None

def get_model():
    global _model
    if _model is None:
        config = get_detection_config()
        model_path = config['model_path']
        device = config.get('device', 'cpu')
        _model = YOLO(model_path, task='detect')
    return _model

def draw_detections(image, results, classes_config):
    """绘制检测结果"""
    img = np.array(image).copy()
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

    boxes = results.boxes
    detections = []

    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])

        cls_info = classes_config.get(cls_id, {})
        cls_name = cls_info.get('chinese', cls_info.get('name', 'Unknown'))
        color_hex = cls_info.get('color', '#E53935')
        color = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        color_bgr = (color[2], color[1], color[0])
        color_rgb = color  # PIL uses RGB

        # 绘制框
        cv2.rectangle(img, (x1, y1), (x2, y2), color_bgr, 2)

        # 准备标签
        label = f"{cls_name} {conf:.2f}"

        # 使用 PIL 绘制中文文本
        font_size = max(12, int(img.shape[0] * 0.02))
        try:
            font = ImageFont.truetype("msyh.ttc", font_size)
        except:
            try:
                font = ImageFont.truetype("simhei.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("simsun.ttc", font_size)
                except:
                    font = ImageFont.load_default()

        # 转换为 PIL Image
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        draw = ImageDraw.Draw(img_pil)

        # 获取文本尺寸
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 绘制标签背景
        draw.rectangle([x1, y1 - text_height - 4, x1 + text_width, y1], fill=color_rgb)
        # 绘制文本
        draw.text((x1, y1 - text_height - 2), label, fill=(255, 255, 255), font=font)

        # 转换回 OpenCV 格式
        img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

        detections.append({
            'class': cls_name,
            'class_id': cls_id,
            'confidence': conf,
            'bbox': [x1, y1, x2, y2]
        })

    return img, detections

# ==================== 认证视图 ====================

def login_view(request):
    """登录页面"""
    if request.user.is_authenticated:
        return redirect('detection_home')

    app_config = get_app_config()

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('detection_home')
        else:
            return render(request, 'detection/login.html', {
                'error': '用户名或密码错误',
                'app_name': app_config.get('app_name', '检测系统')
            })

    return render(request, 'detection/login.html', {
        'app_name': app_config.get('app_name', '检测系统')
    })

@csrf_exempt
def api_login(request):
    """AJAX登录API"""
    if request.method == 'POST':
        if request.user.is_authenticated:
            return JsonResponse({'success': True, 'redirect': '/home/'})

        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'success': True, 'redirect': '/home/'})
        else:
            return JsonResponse({'success': False, 'error': '用户名或密码错误'})

    return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

def register_view(request):
    """注册页面"""
    if request.user.is_authenticated:
        return redirect('detection_home')

    app_config = get_app_config()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            return render(request, 'detection/register.html', {
                'error': '两次密码不一致',
                'app_name': app_config.get('app_name', '检测系统')
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'detection/register.html', {
                'error': '用户名已存在',
                'app_name': app_config.get('app_name', '检测系统')
            })

        user = User.objects.create_user(username=username, email=email, password=password)
        # 创建用户Profile
        from detection.models import UserProfile
        UserProfile.objects.create(user=user)

        login(request, user)
        return redirect('detection_home')

    return render(request, 'detection/register.html', {
        'app_name': app_config.get('app_name', '检测系统')
    })

def logout_view(request):
    """退出登录"""
    logout(request)
    return redirect('login')

# ==================== 检测视图 ====================

def home_view(request):
    """首页"""
    app_config = get_app_config()
    classes = get_classes()

    # 获取用户的检测记录（如果已登录）
    records = []
    total_detections = 0
    username = None
    if request.user.is_authenticated:
        records = request.user.detections.all()[:10]
        total_detections = request.user.detections.count()
        username = request.user.username

    context = {
        'app_name': app_config.get('app_name', '检测系统'),
        'username': username,
        'classes': classes,
        'records': records,
        'total_detections': total_detections,
    }
    return render(request, 'detection/home.html', context)

@login_required
def detect_view(request):
    """检测页面"""
    app_config = get_app_config()
    classes = get_classes()

    context = {
        'app_name': app_config.get('app_name', '检测系统'),
        'username': request.user.username,
        'classes': classes,
    }
    return render(request, 'detection/detect.html', context)

@login_required
def history_view(request):
    """历史记录"""
    app_config = get_app_config()
    records = request.user.detections.all()

    paginator = Paginator(records, 12)
    page = request.GET.get('page')
    records_page = paginator.get_page(page)

    context = {
        'app_name': app_config.get('app_name', '检测系统'),
        'records': records_page,
        'total': records.count(),
    }
    return render(request, 'detection/history.html', context)

@login_required
def profile_view(request):
    """个人资料"""
    app_config = get_app_config()
    from detection.models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    context = {
        'app_name': app_config.get('app_name', '检测系统'),
        'user': request.user,
        'avatar_url': profile.avatar.url if profile.avatar else None,
    }
    return render(request, 'detection/profile.html', context)

@login_required
def xiaoyu_chat_view(request):
    """小科客服聊天页面"""
    from detection.models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    avatar_url = profile.avatar.url if profile.avatar else None
    return render(request, 'detection/xiaoyu.html', {
        'user_avatar': avatar_url
    })

# ==================== API视图 ====================

@login_required
@csrf_exempt
def api_detect_image(request):
    """图片检测API"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)

    if 'file' not in request.FILES:
        return JsonResponse({'error': '未上传文件'}, status=400)

    file = request.FILES['file']
    conf = float(request.POST.get('conf', 0.25))
    iou = float(request.POST.get('iou', 0.45))

    try:
        image = Image.open(file).convert('RGB')
        model = get_model()

        results = model(image, conf=conf, iou=iou)
        classes_config = get_classes()
        result_img, detections = draw_detections(image, results[0], classes_config)

        # 保存结果图片
        from django.conf import settings
        timestamp = int(time.time())
        filename = f"{request.user.username}_{timestamp}.jpg"
        result_path = os.path.join(settings.MEDIA_ROOT, 'results', filename)
        os.makedirs(os.path.dirname(result_path), exist_ok=True)
        result_img_rgb = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
        cv2.imwrite(result_path, result_img_rgb)

        # 保存检测记录
        from detection.models import DetectionRecord
        record = DetectionRecord.objects.create(
            user=request.user,
            file_name=file.name,
            file_type='image',
            result_image=f'results/{filename}',
            result_json=json.dumps(detections),
            total_detections=len(detections),
            confidence_threshold=conf,
            iou_threshold=iou,
        )

        return JsonResponse({
            'success': True,
            'detections': detections,
            'total': len(detections),
            'result_image': settings.MEDIA_URL + f'results/{filename}',
            'record_id': record.id,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_delete_record(request, record_id):
    """删除记录"""
    try:
        record = request.user.detections.get(id=record_id)
        record.delete()
        return JsonResponse({'success': True})
    except:
        return JsonResponse({'error': '记录不存在'}, status=404)

@login_required
def api_upload_avatar(request):
    """上传头像"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    if 'avatar' not in request.FILES:
        return JsonResponse({'error': '未选择图片'}, status=400)

    avatar_file = request.FILES['avatar']

    # 验证文件类型
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if avatar_file.content_type not in allowed_types:
        return JsonResponse({'error': '仅支持 JPG、PNG、GIF 格式'}, status=400)

    # 验证文件大小 (最大 5MB)
    if avatar_file.size > 5 * 1024 * 1024:
        return JsonResponse({'error': '图片大小不能超过 5MB'}, status=400)

    try:
        from detection.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.avatar = avatar_file
        profile.save()
        return JsonResponse({
            'success': True,
            'avatar_url': profile.avatar.url
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
def api_chat(request):
    """小科客服聊天 API

    使用 ai_services 模块中的 XiaoyuAgent
    """
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        if not message:
            return JsonResponse({'error': '消息不能为空'}, status=400)
    except:
        return JsonResponse({'error': '无效的请求格式'}, status=400)

    try:
        # 获取用户位置（优先使用浏览器 GPS 坐标）
        user_location = data.get('user_location')
        user_ip = None

        if user_location and isinstance(user_location, dict):
            # 使用浏览器 GPS 坐标
            lat = user_location.get('latitude')
            lon = user_location.get('longitude')
            import sys
            sys.stderr.write(f"[DEBUG] 使用浏览器GPS位置: {lat}, {lon}\n")
            sys.stderr.flush()
        else:
            # 回退到 IP 定位
            def get_client_ip():
                x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded:
                    return x_forwarded.split(',')[0].strip()
                return request.META.get('REMOTE_ADDR', '127.0.0.1')

            user_ip = get_client_ip()
            # 调试：如果是 localhost，尝试使用 X-Forwarded-For
            if user_ip == '127.0.0.1':
                import sys
                sys.stderr.write(f"[DEBUG] 检测到 localhost，尝试 X-Forwarded-For\n")
                sys.stderr.flush()
                x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded:
                    user_ip = x_forwarded.split(',')[0].strip()
                    sys.stderr.write(f"[DEBUG] 使用 X-Forwarded-For IP: {user_ip}\n")
                    sys.stderr.flush()
            import sys
            sys.stderr.write(f"[DEBUG] 用户IP: {user_ip}\n")
            sys.stderr.flush()

        # 使用 XiaoyuAgent 处理消息
        agent = get_xiaoyu_agent()
        reply = agent.chat(message, user_ip=user_ip, user_location=user_location)

        return JsonResponse({
            'success': True,
            'reply': reply
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ==================== 聊天记录 API ====================

@login_required
def api_chat_records(request):
    """获取聊天记录列表"""
    if request.method != 'GET':
        return JsonResponse({'error': '仅支持 GET 请求'}, status=405)

    records = request.user.chat_records.all()[:50]  # 最近50条
    data = []
    for r in records:
        data.append({
            'id': r.id,
            'title': r.title or '未命名对话',
            'message_count': r.message_count,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': r.updated_at.strftime('%Y-%m-%d %H:%M'),
        })
    return JsonResponse({'success': True, 'records': data})

@login_required
def api_chat_record_detail(request, record_id):
    """获取聊天记录详情"""
    if request.method != 'GET':
        return JsonResponse({'error': '仅支持 GET 请求'}, status=405)

    try:
        record = request.user.chat_records.get(id=record_id)
        return JsonResponse({
            'success': True,
            'record': {
                'id': record.id,
                'title': record.title or '未命名对话',
                'messages': record.get_messages(),
                'message_count': record.message_count,
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': record.updated_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
    except:
        return JsonResponse({'error': '记录不存在'}, status=404)

@login_required
@csrf_exempt
def api_save_chat_record(request):
    """保存聊天记录"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    try:
        data = json.loads(request.body)
        record_id = data.get('record_id')
        messages = data.get('messages', [])

        if not messages:
            return JsonResponse({'error': '消息不能为空'}, status=400)

        # 取第一条用户消息作为标题
        title = ""
        for msg in messages:
            if msg.get('role') == 'user':
                content = msg.get('content', '')[:50]
                title = content[:30] + ('...' if len(content) > 30 else '')
                break

        from detection.models import ChatRecord

        if record_id:
            # 更新已有记录
            record = request.user.chat_records.get(id=record_id)
            record.title = title
            record.set_messages(messages)
            record.message_count = len(messages)
            record.save()
        else:
            # 创建新记录
            record = ChatRecord.objects.create(
                user=request.user,
                title=title,
                messages_json=json.dumps(messages, ensure_ascii=False),
                message_count=len(messages),
            )

        return JsonResponse({
            'success': True,
            'record_id': record.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
def api_delete_chat_record(request, record_id):
    """删除聊天记录"""
    if request.method != 'POST' and request.method != 'DELETE':
        return JsonResponse({'error': '仅支持 POST/DELETE 请求'}, status=405)

    try:
        from detection.models import ChatRecord
        record = request.user.chat_records.get(id=record_id)
        record.delete()
        return JsonResponse({'success': True})
    except:
        return JsonResponse({'error': '记录不存在'}, status=404)

@login_required
def chat_history_view(request):
    """聊天记录管理页面"""
    return render(request, 'detection/chat_history.html')
