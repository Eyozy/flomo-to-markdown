import sys
import os
import json
import argparse
import glob
import unicodedata
from datetime import datetime
from bs4 import BeautifulSoup

from converter import ExportMode, convert_notes, get_available_years

# CLI 增强模块导入
try:
    from cli_utils import success, warning, error, info, highlight, print_header, print_section, print_section_end, print_info_line
    CLI_ENHANCED = True
except ImportError:
    CLI_ENHANCED = False
    def success(msg): print(f"✅ {msg}")
    def warning(msg): print(f"⚠️  {msg}")
    def error(msg): print(f"❌ {msg}")
    def info(msg): print(f"ℹ️  {msg}")
    def highlight(msg): print(msg); return msg
    def print_header(title): print("=" * 50); print(title); print("=" * 50)
    def print_section(title): print(f"\n--- {title} ---")
    def print_section_end(): print()
    def print_info_line(label, value, color='info'): print(f"{label}: {value}")

try:
    from simple_term_menu import TerminalMenu
    HAS_TUI = True
except ImportError:
    HAS_TUI = False

# --- 配置项 ---
CONFIG_PATH = os.path.expanduser("~/.flomo-converter.json")
DEFAULT_CONFIG = {
    "source_dir": "flomo",
    "output_dir": "converted_notes",
    "enable_colors": True,
    "show_progress": True,
    "image_subdir_name": "flomo-images",
}

def _load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG.copy()

def load_application_config():
    config = _load_config()
    return config['source_dir'], config['output_dir']

SOURCE_DIR, OUTPUT_DIR = load_application_config()

HTML_CONFIG = {
    'note_container': 'div.memo',
    'date_element': 'div.time',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

# ========== 常量 ==========

BACK = 'BACK'
QUIT = 'QUIT'
CONFIRM = 'CONFIRM'

# 统一的图标风格 —— 纯血原生 SMP Emoji，解决底层字符长度不一导致的排版错位问题
ICO_CONVERT  = "🚀"
ICO_INFO     = "📊"
ICO_YEARS    = "📅"
ICO_QUIT     = "🛑"
ICO_BACK     = "🔙"
ICO_DIR      = "📁"
ICO_INPUT    = "🔤"
ICO_ALL      = "🌐"
ICO_SINGLE   = "📄"
ICO_MEMO     = "📝"
ICO_ARCHIVE  = "📦"

# ========== 工具函数 ==========

def _has_flomo_html(directory):
    htmls = glob.glob(os.path.join(directory, '*.html')) + glob.glob(os.path.join(directory, '*.htm'))
    if not htmls:
        return False
    try:
        with open(htmls[0], 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
        return bool(soup.select(HTML_CONFIG['note_container']))
    except Exception:
        return False

def _scan_flomo_dirs():
    candidates = []
    search_roots = [os.getcwd(), os.path.expanduser('~/Downloads'), os.path.expanduser('~/Documents')]
    for root in search_roots:
        if not os.path.isdir(root):
            continue
        if _has_flomo_html(root):
            candidates.append(root)
        try:
            for entry in os.scandir(root):
                if entry.is_dir() and _has_flomo_html(entry.path):
                    candidates.append(entry.path)
        except (PermissionError, OSError):
            continue
    return sorted(set(candidates))

def _display_width(text):
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width

def _pad_string(text, target_width):
    current_width = _display_width(text)
    if current_width < target_width:
        return text + " " * (target_width - current_width)
    return text

def _build_title(main, *sub):
    """构建完美对齐的多行带框标题"""
    content_lines = [f" {main} "]
    for s in sub:
        content_lines.append(f" {s} ")
        
    max_width = max(_display_width(line) for line in content_lines)
    max_width = max(max_width, 30)
    
    lines = []
    top_border = "─" * max_width
    lines.append(f"┌{top_border}┐")
    
    for line in content_lines:
        lines.append(f"│{_pad_string(line, max_width)}│")
        
    bottom_border = "─" * max_width
    lines.append(f"└{bottom_border}┘")
    
    return "\n".join(lines)

def _menu(entries, title="", default=0):
    """统一的菜单创建"""
    return TerminalMenu(
        entries,
        title=title,
        cursor_index=default,
        menu_cursor=" ❯ ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black", "bold"),
        cycle_cursor=True,
        clear_screen=True,
    )

def _classify(idx, entries, has_back=True):
    """分类菜单选择结果：正常选项索引 / BACK / QUIT
    entries 末尾固定是 [返回, 退出] 或 [退出]（无 back）
    """
    nav_count = 1 + (1 if has_back else 0)
    nav_start = len(entries) - nav_count

    if idx is None:
        return QUIT
    if idx >= nav_start:
        if has_back and idx == nav_start:
            return BACK
        return QUIT
    return idx

def _nav(has_back=True):
    """生成导航条目，图标与其他选项统一"""
    items = [f"{ICO_BACK}  返回上一步"] if has_back else []
    items.append(f"{ICO_QUIT}  退出")
    return items

# ========== 文件信息展示 ==========

def _get_year_stats(source_dir):
    """计算年份统计数据"""
    html_files = glob.glob(os.path.join(source_dir, '*.html')) + glob.glob(os.path.join(source_dir, '*.htm'))
    all_years = get_available_years(source_dir)
    year_counts = {}
    total = 0
    for y in all_years:
        count = 0
        for fp in html_files:
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f, 'lxml')
                for nc in soup.select(HTML_CONFIG['note_container']):
                    de = nc.select_one(HTML_CONFIG['date_element'])
                    ds = de.get_text(strip=True) if de else ''
                    try:
                        if datetime.strptime(ds, HTML_CONFIG['date_format']).year == y:
                            count += 1
                    except (ValueError, TypeError):
                        continue
            except Exception:
                continue
        year_counts[y] = count
        total += count
    return html_files, all_years, year_counts, total

def tui_empty_state():
    title = _build_title(
        "flomo to Markdown",
        "",
        "⚠️  未检测到 flomo 导出文件",
        "请在网页端导出并解压到当前目录",
        ""
    )
    entries = [
        f"{ICO_INPUT}  手动输入源路径",
        f"{ICO_QUIT}  退出程序"
    ]
    menu = _menu(entries, title=title)
    idx = menu.show()
    if idx == 0:
        return _manual_input()
    return QUIT

def _manual_input():
    while True:
        try:
            path = input(f"请输入源目录路径（输入 q 退出，回车默认 '{SOURCE_DIR}'）：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return QUIT
        if path.lower() == 'q':
            return QUIT
        if not path:
            path = SOURCE_DIR
            
        if not os.path.isdir(path):
            error(f"目录不存在: {path}")
            continue
            
        try:
            # 权限嗅探：测试系统是否拦截了读取权限（触发 macOS 沙盒拦截）
            list(os.scandir(path))
        except PermissionError:
            error("权限拒绝：系统拦截了对该目录的读取权限（常见于 macOS 下载/文档目录）。")
            info("解决方案：请将 flomo 文件夹整体移动到当前程序所在的目录下再试。")
            continue
        except Exception as e:
            error(f"无法读取目录: {e}")
            continue
            
        success(f"已选择: {path}")
        return path

def tui_dashboard(source_dir):
    html_files, all_years, year_counts, total = _get_year_stats(source_dir)
    
    if not all_years:
        title = _build_title(
            "⚠️ 目录无效",
            f"📁 目标: {source_dir}",
            "❌ 该目录未包含有效的 flomo 导出数据"
        )
        entries = [
            f"{ICO_DIR}  更换源目录",
            f"{ICO_QUIT}  退出程序"
        ]
        menu = _menu(entries, title=title, default=0)
        idx = menu.show()
        if idx is None or idx == 1:
            return QUIT
        return BACK
    
    year_range = f"{all_years[0]} ~ {all_years[-1]} 年" if len(all_years) > 1 else f"{all_years[0]} 年"
    title = _build_title(
        "📦 数据已就绪",
        f"📁 源目录: {source_dir}",
        f"📄 笔记数: {total} 条",
        f"📅 年份跨度: {year_range}"
    )
    
    entries = [
        f"{ICO_CONVERT}  开始转换 (默认输出至 {OUTPUT_DIR})",
        f"{ICO_DIR}  更换源目录",
        f"{ICO_QUIT}  退出程序"
    ]
    menu = _menu(entries, title=title, default=0)
    idx = menu.show()
    
    if idx is None or idx == 2:
        return QUIT
    if idx == 1:
        return BACK
    return CONFIRM

def tui_select_source(current_dirs):
    entries = [f"{ICO_DIR}  {os.path.basename(d)} ({d})" for d in current_dirs]
    entries.append(f"{ICO_INPUT}  手动输入路径")
    entries.append(f"{ICO_BACK}  返回上一步")

    title = _build_title("选择源目录", f"已检测到 {len(current_dirs)} 个 flomo 目录")
    menu = _menu(entries, title=title)
    idx = menu.show()

    if idx is None:
        return QUIT
    if idx == len(entries) - 1:
        return BACK
    if idx == len(entries) - 2:
        return _manual_input()
    return current_dirs[idx]

def tui_select_year(source_dir):
    _, all_years, year_counts, _ = _get_year_stats(source_dir)
    if not all_years:
        return BACK
        
    year_range = f"{all_years[0]}-{all_years[-1]}" if len(all_years) > 1 else f"{all_years[0]}"
    display_years = sorted(all_years, reverse=True)
    
    entries = [f"{ICO_ALL}  全部年份 ({year_range})"]
    for y in display_years:
        entries.append(f"{ICO_YEARS}  {y} 年 ({year_counts[y]} 条)")
    entries.append(f"{ICO_BACK}  返回上一步")
    
    title = _build_title("选择时间范围", "请选择你需要导出的数据范围")
    menu = _menu(entries, title=title, default=0)
    idx = menu.show()
    
    if idx is None:
        return QUIT
    if idx == len(entries) - 1:
        return BACK
    if idx == 0:
        return None
    return display_years[idx - 1]

def tui_select_export_mode(year):
    mode_info = [
        (ExportMode.SINGLE_FILE,   ICO_SINGLE,   "单一文件", "所有笔记合成 1 个 .md"),
        (ExportMode.SINGLE_MEMOS,  ICO_MEMO,     "单条导出", "每条笔记生成独立 .md"),
    ]
    if year is None:
        mode_info.append((ExportMode.YEARLY_ARCHIVES, ICO_ARCHIVE, "按年归档", "每年生成 1 个文件夹"))

    entries = [f"{ico}  {label} ({desc})" for _, ico, label, desc in mode_info]
    entries.append(f"{ICO_BACK}  返回上一步")

    title = _build_title("选择输出模式", "决定 Markdown 文件在硬盘上的结构")
    menu = _menu(entries, title=title)
    idx = menu.show()

    if idx is None:
        return QUIT
    if idx == len(entries) - 1:
        return BACK
    return mode_info[idx][0]

def run_tui_flow():
    if not HAS_TUI:
        warning("未安装 simple-term-menu")
        info("安装: pip install simple-term-menu")
        return run_fallback_flow()

    dirs = _scan_flomo_dirs()
    source = dirs[0] if dirs else None
    state = 'DASHBOARD' if source else 'EMPTY'
    year = None
    mode = None

    while True:
        if state == 'EMPTY':
            res = tui_empty_state()
            if res == QUIT:
                return
            source = res
            state = 'DASHBOARD'

        elif state == 'DASHBOARD':
            res = tui_dashboard(source)
            if res == QUIT:
                return
            if res == BACK:
                state = 'SELECT_SOURCE'
            elif res == CONFIRM:
                state = 'YEAR'

        elif state == 'SELECT_SOURCE':
            current_dirs = _scan_flomo_dirs()
            if not current_dirs:
                res = _manual_input()
            else:
                res = tui_select_source(current_dirs)
            
            if res == QUIT:
                return
            if res == BACK:
                state = 'DASHBOARD'
            else:
                source = res
                state = 'DASHBOARD'

        elif state == 'YEAR':
            res = tui_select_year(source)
            if res == QUIT:
                return
            if res == BACK:
                state = 'DASHBOARD'
            else:
                year = res
                state = 'MODE'

        elif state == 'MODE':
            res = tui_select_export_mode(year)
            if res == QUIT:
                return
            if res == BACK:
                state = 'YEAR'
            else:
                mode = res
                result_dir = convert_notes(
                    source_dir=source,
                    output_dir=OUTPUT_DIR,
                    year_filter=year,
                    export_mode=mode,
                )
                print()
                if result_dir:
                    success("转换成功！")
                    print_info_line("输出目录", result_dir, 'success')
                else:
                    error("转换失败，请检查源目录或文件内容")
                print()
                input("按回车返回主界面...")
                state = 'DASHBOARD'

def run_fallback_flow():
    source = input(f"源目录路径（回车默认 '{SOURCE_DIR}'）：").strip() or SOURCE_DIR
    if not os.path.isdir(source):
        error(f"目录不存在: {source}")
        return

    years = get_available_years(source)
    if years:
        info(f"检测到年份: {', '.join(map(str, years))}")
        year_input = input("选择年份（回车=全部）：").strip()
        try:
            year = int(year_input) if year_input else None
        except ValueError:
            warning("无效年份，将导出全部")
            year = None
    else:
        warning("未检测到年份信息")
        year = None

    mode_names = {1: ExportMode.SINGLE_FILE, 2: ExportMode.SINGLE_MEMOS, 3: ExportMode.YEARLY_ARCHIVES}
    print("导出模式：1=单一文件 2=单条导出 3=按年归档")
    mode_input = input("选择导出模式（回车=单一文件）：").strip()
    try:
        mode = mode_names.get(int(mode_input), ExportMode.SINGLE_FILE) if mode_input else ExportMode.SINGLE_FILE
    except ValueError:
        warning("无效选项，使用单一文件模式")
        mode = ExportMode.SINGLE_FILE

    result_dir = convert_notes(source_dir=source, output_dir=OUTPUT_DIR, year_filter=year, export_mode=mode)
    if result_dir:
        success("转换成功！")
        print_info_line("输出目录", result_dir, 'success')
    else:
        error("转换失败。")

# ========== argparse 流程 ==========

def check_python_version():
    if sys.version_info < (3, 6):
        error("此脚本需要 Python 3.6+")
        info(f"当前版本: {sys.version.split(' ')[0]}")
        sys.exit(1)

def print_file_info(source_dir):
    if not os.path.isdir(source_dir):
        error(f"源文件夹不存在: {source_dir}")
        return

    html_files, all_years, year_counts, total = _get_year_stats(source_dir)
    if not html_files:
        error("未找到 HTML 文件")
        return

    print_info_line("源目录", source_dir)
    print_info_line("HTML 文件数量", len(html_files))

    if all_years:
        print_info_line("包含年份", ", ".join(map(str, all_years)))
        print_info_line("年份范围", f"{all_years[0]} - {all_years[-1]}")
        print("\n📋 各年份笔记统计：")
        for y in all_years:
            info(f"   {y}年：{year_counts[y]} 条笔记")
    else:
        warning("未检测到有效的年份信息")

def run_argparse_flow(args):
    if args.info:
        print_section("📋 文件信息查询")
        print_file_info(args.source)
        print_section_end()
        return

    if args.list_years:
        print_section("📅 年份列表查询")
        all_years = get_available_years(args.source)
        if all_years:
            print_info_line("可用年份", ", ".join(map(str, all_years)), 'success')
        else:
            warning("未找到年份信息")
        print_section_end()
        return

    year_filter = args.year
    print_section("🚀 开始转换")
    print_info_line("导出模式", args.export_mode, 'info')
    print_info_line("源目录", args.source, 'info')
    print_info_line("输出目录", args.output, 'info')
    if year_filter:
        print_info_line("年份过滤", str(year_filter), 'info')

    result_dir = convert_notes(
        source_dir=args.source,
        output_dir=args.output,
        year_filter=year_filter,
        export_mode=ExportMode(args.export_mode),
    )

    print_section("✅ 转换结果")
    if result_dir:
        success("转换成功！")
        print_info_line("输出目录", result_dir, 'success')
        try:
            output_content = os.listdir(result_dir)
            if output_content:
                print_info_line("生成内容", [f"📁 {item}" if os.path.isdir(os.path.join(result_dir, item)) else f"📄 {item}" for item in output_content], 'success')
        except FileNotFoundError:
            warning("无法读取输出目录")
    else:
        error("转换失败")
    print_section_end()

def main():
    check_python_version()

    parser = argparse.ArgumentParser(
        prog='flomo_converter.py',
        description='flomo HTML to Markdown CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  python flomo_converter.py                          # 交互式模式
  python flomo_converter.py --year 2025              # 转换 2025 年
  python flomo_converter.py --list-years             # 列出可用年份
  python flomo_converter.py --info                   # 详细统计
  python flomo_converter.py --export-mode single_memos --year 2023
  python flomo_converter.py --source ./data --output ./result
        """
    )
    parser.add_argument('--source', type=str, default=SOURCE_DIR, help=f'源文件夹 (默认: {SOURCE_DIR})')
    parser.add_argument('--output', type=str, default=OUTPUT_DIR, help=f'输出文件夹 (默认: {OUTPUT_DIR})')
    parser.add_argument('--year', type=int, metavar='YEAR', help='只转换指定年份')
    parser.add_argument('--list-years', action='store_true', help='列出所有年份')
    parser.add_argument('--info', action='store_true', help='显示详细统计')
    parser.add_argument('--export-mode', type=str, choices=[e.value for e in ExportMode], default=ExportMode.SINGLE_FILE.value, help='导出模式')

    args = parser.parse_args()

    has_explicit_args = bool(
        args.year or args.list_years or args.info
        or args.source != SOURCE_DIR
        or args.output != OUTPUT_DIR
        or args.export_mode != ExportMode.SINGLE_FILE.value
    )

    if has_explicit_args:
        run_argparse_flow(args)
    else:
        run_tui_flow()

if __name__ == '__main__':
    main()
