import colorama
from colorama import Fore, Style
from tqdm import tqdm
import sys

colorama.init()

COLORS = {
    'success': Fore.GREEN,
    'warning': Fore.YELLOW,
    'error': Fore.RED,
    'info': Fore.CYAN,
    'highlight': Fore.MAGENTA,
    'dim': Fore.LIGHTBLACK_EX
}

def colored_print(message, color='info'):
    if color in COLORS:
        print(f"{COLORS[color]}{message}{Style.RESET_ALL}")
    else:
        print(message)

def success(message):
    colored_print(f"✅ {message}", 'success')

def warning(message):
    colored_print(f"⚠️  {message}", 'warning')

def error(message):
    colored_print(f"❌ {message}", 'error')

def info(message):
    colored_print(f"ℹ️  {message}", 'info')

def highlight(message):
    colored_print(message, 'highlight')
    return message

def show_progress(items, description="处理中"):
    return tqdm(items, desc=description,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                ncols=80,
                leave=True)

def print_header(title):
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * ((58 - len(title)) // 2) + title + " " * ((59 - len(title)) // 2) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

def print_section(title):
    print()
    print("┌─ " + highlight(title))
    print("│")

def print_section_end():
    print("└─ " + "─" * 55)
    print()

def print_info_line(label, value, color='info'):
    if isinstance(value, (list, tuple)):
        if value:
            print(f"│  {label}:")
            for item in value:
                print(f"│  • {item}")
        else:
            print(f"│  {label}: 无")
    else:
        colored_print(f"│  {label}: {value}", color)

def print_separator(char="─", length=60):
    print(char * length)
