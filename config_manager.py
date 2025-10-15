import json
import os
from cli_utils import info, warning

# 默认配置
DEFAULT_CONFIG = {
    "source_dir": "flomo",
    "output_dir": "converted_notes",
    "enable_colors": True,
    "show_progress": True,
    "image_subdir_name": "flomo-images"
}

CONFIG_PATH = os.path.expanduser("~/.flomo-converter.json")

def load_config():
    """
    加载配置文件，保持向后兼容

    Returns:
        dict: 配置字典
    """
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 合并用户配置和默认配置
                config = {**DEFAULT_CONFIG, **user_config}
                info(f"已加载配置文件：{CONFIG_PATH}")
                return config
        except (json.JSONDecodeError, IOError) as e:
            warning(f"配置文件读取失败，使用默认配置：{e}")

    return DEFAULT_CONFIG.copy()

def save_config(config):
    """
    保存配置文件

    Args:
        config (dict): 配置字典
    """
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        info(f"配置已保存至：{CONFIG_PATH}")
    except IOError as e:
        error(f"配置文件保存失败：{e}")

def get_config_value(key, default=None):
    """
    获取配置值

    Args:
        key (str): 配置键
        default: 默认值

    Returns:
        配置值
    """
    config = load_config()
    return config.get(key, default)

def update_config_value(key, value):
    """
    更新配置值

    Args:
        key (str): 配置键
        value: 配置值
    """
    config = load_config()
    config[key] = value
    save_config(config)

def create_default_config():
    """创建默认配置文件"""
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return True
    return False