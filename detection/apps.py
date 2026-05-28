from django.apps import AppConfig


class DetectionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'detection'

    def ready(self):
        """Django 应用启动时初始化"""
        # 初始化 ModelScope MCP 客户端
        try:
            from ai_services.mcp.modelscope_client import init_modelscope_client
            init_modelscope_client()
        except Exception:
            pass

        # 注册工具
        try:
            from ai_services.tools.setup import setup_tools
            setup_tools()
        except Exception:
            pass
