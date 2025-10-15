import colorama
from colorama import Fore, Style
from tqdm import tqdm
import sys

# 初始化 colorama
colorama.init()

# 简单的颜色主题
COLORS = {
    'success': Fore.GREEN,
    'warning': Fore.YELLOW,
    'error': Fore.RED,
    'info': Fore.CYAN,
    'highlight': Fore.MAGENTA,
    'dim': Fore.LIGHTBLACK_EX
}

def colored_print(message, color='info'):
    """
    彩色打印函数，向后兼容

    Args:
        message (str): 要打印的消息
        color (str): 颜色类型，支持 'success', 'warning', 'error', 'info', 'highlight', 'dim'
    """
    if color in COLORS:
        print(f"{COLORS[color]}{message}{Style.RESET_ALL}")
    else:
        print(message)  # 向后兼容：如果颜色不支持，使用普通打印

def success(message):
    """成功消息"""
    colored_print(f"✅ {message}", 'success')

def warning(message):
    """警告消息"""
    colored_print(f"⚠️  {message}", 'warning')

def error(message):
    """错误消息"""
    colored_print(f"❌ {message}", 'error')

def info(message):
    """信息消息"""
    colored_print(f"ℹ️  {message}", 'info')

def highlight(message):
    """高亮消息"""
    colored_print(message, 'highlight')
    return message

def show_progress(items, description="处理中"):
    """
    显示进度条，支持列表和迭代器

    Args:
        items: 要迭代的项
        description (str): 进度条描述

    Returns:
        带进度条的迭代器
    """
    return tqdm(items, desc=description,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                ncols=80,
                leave=True)

def print_separator(char="─", length=60):
    """打印分隔线"""
    print(char * length)

def print_header(title):
    """打印标题头部"""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * ((58 - len(title)) // 2) + title + " " * ((59 - len(title)) // 2) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

def print_section(title):
    """打印节标题"""
    print()
    print("┌─ " + highlight(title))
    print("│")

def print_section_end():
    """打印节结束"""
    print("└─ " + "─" * 55)
    print()

def print_info_line(label, value, color='info'):
    """打印信息行"""
    if isinstance(value, (list, tuple)):
        if value:
            print(f"│  {label}:")
            for item in value:
                print(f"│  • {item}")
        else:
            print(f"│  {label}: 无")
    else:
        colored_print(f"│  {label}: {value}", color)

def print_step(step, total, description):
    """打印步骤信息"""
    progress = f"[{step}/{total}]"
    colored_print(f"│  {progress} {description}", 'info')

def print_separator(char="─", length=60):
    """打印分隔线"""
    print(char * length)