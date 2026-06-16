import colorama
from colorama import Fore, Style

colorama.init()

COLORS = {
    'success': Fore.GREEN,
    'warning': Fore.YELLOW,
    'error': Fore.RED,
    'info': Fore.CYAN,
    'highlight': Fore.MAGENTA,
}

def _colored(message, color='info'):
    if color in COLORS:
        print(f"{COLORS[color]}{message}{Style.RESET_ALL}")
    else:
        print(message)

def success(message):
    _colored(f"✅ {message}", 'success')

def warning(message):
    _colored(f"⚠️  {message}", 'warning')

def error(message):
    _colored(f"❌ {message}", 'error')

def info(message):
    _colored(f"ℹ️  {message}", 'info')

def print_info_line(label, value, color='info'):
    if isinstance(value, (list, tuple)):
        if value:
            print(f"│  {label}:")
            for item in value:
                print(f"│  • {item}")
        else:
            print(f"│  {label}: 无")
    else:
        _colored(f"│  {label}: {value}", color)
