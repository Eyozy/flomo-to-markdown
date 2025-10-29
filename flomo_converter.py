import sys
import argparse
import glob
from datetime import datetime
from bs4 import BeautifulSoup

# 从项目核心模块导入功能
from converter import ExportMode, convert_notes, get_available_years

# CLI 增强模块导入
try:
    from cli_utils import success, warning, error, info, highlight, print_header, print_section, print_section_end, print_info_line
    from config_manager import load_config
    CLI_ENHANCED = True
except ImportError:
    # 向后兼容：如果新模块不可用，使用基础功能
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

# --- 配置项 (Configuration) ---
def load_application_config():
    """加载应用配置，支持配置文件和默认值"""
    if CLI_ENHANCED:
        config = load_config()
        return config['source_dir'], config['output_dir']
    else:
        # 向后兼容：使用原有默认配置
        return 'flomo', 'converted_notes'

# 动态加载配置
SOURCE_DIR, OUTPUT_DIR = load_application_config()

# HTML 解析规则，仅用于 print_file_info 函数
HTML_CONFIG = {
    'note_container': 'div.memo',
    'date_element': 'div.time',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

def check_python_version():
    """检查 Python 版本是否为 3.6 或更高。"""
    if sys.version_info < (3, 6):
        error("错误：此脚本需要 Python 3.6 或更高版本。")
        info(f"您当前的 Python 版本是 {sys.version.split(' ')[0]}。")
        sys.exit(1)

def print_file_info(source_dir):
    """打印文件详细信息（CLI 功能）"""
    import os
    if not os.path.isdir(source_dir):
        error(f"源文件夹 '{source_dir}' 不存在。")
        return

    html_files = glob.glob(os.path.join(source_dir, '*.html')) + glob.glob(os.path.join(source_dir, '*.htm'))
    if not html_files:
        error(f"在源文件夹 '{source_dir}' 中未找到任何 .html 或 .htm 文件。")
        return

    print_info_line("源目录", source_dir)
    print_info_line("HTML 文件数量", len(html_files))

    all_years = get_available_years(source_dir)
    if all_years:
        print_info_line("包含年份", ", ".join(map(str, all_years)))
        print_info_line("年份范围", f"{all_years[0]} - {all_years[-1]}")
        
        print("\n📋 各年份笔记统计：")
        for year in all_years:
            year_notes = 0
            for file_path in html_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f, 'lxml')
                    note_containers = soup.select(HTML_CONFIG['note_container'])
                    for note_container in note_containers:
                        date_element = note_container.select_one(HTML_CONFIG['date_element'])
                        date_str = date_element.get_text(strip=True) if date_element else ''
                        try:
                            if datetime.strptime(date_str, HTML_CONFIG['date_format']).year == year:
                                year_notes += 1
                        except (ValueError, TypeError):
                            continue
                except Exception:
                    continue
            info(f"   {year}年：{year_notes} 条笔记")
    else:
        warning("未检测到有效的年份信息")

def interactive_year_selection(source_dir):
    """交互式年份选择（CLI 功能）"""
    all_years = get_available_years(source_dir)
    if not all_years:
        error("未找到任何有效的年份信息")
        return None
    
    info("\n📅 检测到以下年份：")
    for i, year in enumerate(all_years, 1):
        print(f"   {i}. {year}")
    print(f"   {len(all_years) + 1}. 全部年份")
    
    while True:
        try:
            choice = input(f"\n请选择要转换的年份（1-{len(all_years) + 1}）：").strip()
            if not choice:
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(all_years):
                selected_year = all_years[choice_num - 1]
                success(f"已选择：{selected_year}年")
                return selected_year
            elif choice_num == len(all_years) + 1:
                success("已选择：全部年份")
                return None
            else:
                warning(f"请输入 1-{len(all_years) + 1} 之间的数字")
        except ValueError:
            warning("请输入有效的数字")

def main():
    """主函数，协调整个转换流程。"""
    check_python_version()

    if CLI_ENHANCED:
        print_header("flomo to Markdown")
    else:
        print("--- flomo HTML to Markdown Converter ---")

    parser = argparse.ArgumentParser(
        prog='flomo_converter.py',
        description='flomo HTML to Markdown CLI - 智能笔记归档工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📚 使用示例：
  python flomo_converter.py                          # 转换所有年份
  python flomo_converter.py --year 2025              # 转换 2025 年
  python flomo_converter.py --list-years             # 列出可用年份
  python flomo_converter.py --info                   # 详细统计信息
  python flomo_converter.py --interactive            # 交互式选择
  python flomo_converter.py --export-mode single_memos --year 2023
  python flomo_converter.py --source ./data --output ./result
        """
    )
    parser.add_argument('--source', type=str, default=SOURCE_DIR, help=f'📁 源文件夹路径 (默认：{SOURCE_DIR})')
    parser.add_argument('--output', type=str, default=OUTPUT_DIR, help=f'💾 输出文件夹路径 (默认：{OUTPUT_DIR})')
    parser.add_argument('--year', type=int, metavar='YEAR', help='📅 只转换指定年份的笔记 (例：--year 2025)')
    parser.add_argument('--list-years', action='store_true', help='📋 列出源文件中包含的所有年份')
    parser.add_argument('--info', action='store_true', help='📊 显示源文件的详细信息和统计数据')
    parser.add_argument('--interactive', action='store_true', help='🎮 使用交互式模式选择年份')
    parser.add_argument('--export-mode', type=str, choices=[e.value for e in ExportMode], default=ExportMode.SINGLE_FILE.value, help='🎨 选择导出模式')
    
    args = parser.parse_args()

    # 处理信息查询类参数
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
            warning("未找到任何有效的年份信息")
        print_section_end()
        return

    year_filter = args.year
    if args.interactive:
        print_section("🎯 交互式年份选择")
        year_filter = interactive_year_selection(args.source)
        print_section_end()

    # 显示导出模式信息
    print_section("🚀 开始转换")
    print_info_line("导出模式", args.export_mode, 'info')
    print_info_line("源目录", args.source, 'info')
    print_info_line("输出目录", args.output, 'info')
    if year_filter:
        print_info_line("年份过滤", str(year_filter), 'info')

    # 调用统一的转换函数
    result_dir = convert_notes(
        source_dir=args.source,
        output_dir=args.output,
        year_filter=year_filter,
        export_mode=ExportMode(args.export_mode)
    )

    print_section("✅ 转换结果")
    if result_dir:
        import os
        success("转换成功！")
        print_info_line("输出目录", result_dir, 'success')
        try:
            output_content = os.listdir(result_dir)
            if output_content:
                print_info_line("生成内容", [f"📁 {item}" if os.path.isdir(os.path.join(result_dir, item)) else f"📄 {item}" for item in output_content], 'success')
        except FileNotFoundError:
            warning("无法读取输出目录内容。")
    else:
        error("转换失败。请检查源目录或文件内容。")
    print_section_end()

if __name__ == '__main__':
    main()

