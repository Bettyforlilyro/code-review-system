import os
import yaml


def load_config_from_yaml(config_yaml_path):
    """从YAML文件加载配置"""

    # 规范化路径
    config_yaml_path = os.path.abspath(config_yaml_path)

    # 检查配置文件是否存在
    if not os.path.exists(config_yaml_path):
        raise FileNotFoundError(f"{config_yaml_path} 配置文件不存在")

    # 读取并解析YAML配置
    with open(config_yaml_path, 'r', encoding='utf-8') as f:
        yaml_config = yaml.safe_load(f)

    # 将YAML中的配置转换为Celery所需的格式
    loaded_config = {}
    for key, value in yaml_config.items():
        loaded_config[key] = value

    return loaded_config
