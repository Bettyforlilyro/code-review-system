import os
from api.common.config.load_config_from_yaml import load_config_from_yaml

# 加载配置
try:
    system_config_file = os.path.join(os.path.dirname(__file__), '..', 'settings', 'code-review-config.yaml')
    code_review_config = load_config_from_yaml(system_config_file)['code_review_system']
    relation_db_config = load_config_from_yaml(system_config_file)['relation_db']
    vector_db_config = load_config_from_yaml(system_config_file)['vector_db']

except FileNotFoundError:
    # 如果找不到YAML配置文件，则使用默认配置
    code_review_config = {
        "logging": {
            "level": "DEBUG",
        },
        "cache": {
            "file_cache": {
                "enabled": True,
                "timeout": 86400,
            },
            "mem_cache": {
                "enabled": True,
                "timeout": 3600,
            }
        },
    }
    relation_db_config = {
        "db_type": "postgresql",
        "db_host": "localhost",
        "db_port": "5432",
        "db_name": "code_review_db",
        "db_user": "postgres",
        "db_password": "admin",
    }
    vector_db_config = {
        "db_type": "chroma",
        "db_path": "/home/zhy/workspace/code-review-system/data/chroma",
        "db_host": "localhost",
        "db_port": "8000",
    }