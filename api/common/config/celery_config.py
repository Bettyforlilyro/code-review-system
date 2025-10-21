import os
from api.common.config.load_config_from_yaml import load_config_from_yaml

# 加载配置
try:
    celery_config_file_path = os.path.join(os.path.dirname(__file__), '..', 'settings', 'celery-config.yaml')
    celery_config = load_config_from_yaml(celery_config_file_path)
except FileNotFoundError:
    # 如果找不到YAML配置文件，则使用默认配置
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    celery_config = {
        "broker_url": REDIS_URL,
        "result_backend": REDIS_URL,
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "timezone": "Asia/Shanghai",
        "enable_utc": False,
        "result_expires": 3600,
    }
