# -*- coding: utf-8 -*-
"""
配置加载器 - 从XML读取配置
"""
import xmltodict
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.xml')

def load_config():
    """加载XML配置"""
    if not os.path.exists(CONFIG_PATH):
        return get_default_config()

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
        # 移除注释
        import re
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        return xmltodict.parse(content)

def get_default_config():
    """默认配置"""
    return {
        'configuration': {
            'app_settings': {
                'app_name': '航拍目标检测系统',
                'version': '1.0.0',
            },
            'database': {
                'type': 'sqlite',
                'name': 'db.sqlite3',
            },
            'detection': {
                'default_confidence': '0.25',
                'default_iou': '0.45',
                'model_path': 'models/v8-best.pt',
                'device': 'cpu',
            },
            'classes': {
                'class': [
                    {'@id': '0', '@name': 'car', '@chinese': '小汽车', '@color': '#E53935'},
                    {'@id': '1', '@name': 'motor', '@chinese': '摩托车', '@color': '#8E24AA'},
                    {'@id': '2', '@name': 'people', '@chinese': '人群', '@color': '#43A047'},
                    {'@id': '3', '@name': 'pedestrian', '@chinese': '行人', '@color': '#00ACC1'},
                    {'@id': '4', '@name': 'awning-tricycle', '@chinese': '带篷三轮车', '@color': '#FB8C00'},
                    {'@id': '5', '@name': 'tricycle', '@chinese': '三轮车', '@color': '#F4511E'},
                    {'@id': '6', '@name': 'bicycle', '@chinese': '自行车', '@color': '#6D4C41'},
                    {'@id': '7', '@name': 'truck', '@chinese': '卡车', '@color': '#3949AB'},
                    {'@id': '8', '@name': 'van', '@chinese': '面包车', '@color': '#D81B60'},
                    {'@id': '9', '@name': 'bus', '@chinese': '公交车', '@color': '#00897B'},
                ]
            },
            'ui': {
                'theme': 'blue',
                'page_size': 'large',
            }
        }
    }

# 全局配置实例
CONFIG = load_config()

def get_app_config():
    return CONFIG['configuration']['app_settings']

def get_detection_config():
    return CONFIG['configuration']['detection']

def get_classes():
    classes = CONFIG['configuration']['classes']['class']
    result = {}
    for cls in classes:
        result[int(cls['@id'])] = {
            'name': cls['@name'],
            'chinese': cls['@chinese'],
            'color': cls['@color']
        }
    return result

def get_ui_config():
    return CONFIG['configuration']['ui']

def get_minimax_config():
    return CONFIG['configuration'].get('minimax', {})
