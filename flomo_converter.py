import os
import shutil
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import os
import shutil
import sys
import argparse # 导入 argparse
from datetime import datetime
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import glob
from converter import ExportMode, convert_notes

# CLI 增强模块导入
try:
    from cli_utils import success, warning, error, info, highlight, show_progress, print_header, print_section, print_section_end, print_info_line, print_separator
    from config_manager import load_config, get_config_value
    CLI_ENHANCED = True
except ImportError:
    # 向后兼容：如果新模块不可用，使用基础功能
    CLI_ENHANCED = False
    def success(msg): print(f"✅ {msg}")
    def warning(msg): print(f"⚠️  {msg}")
    def error(msg): print(f"❌ {msg}")
    def info(msg): print(f"ℹ️  {msg}")
    def highlight(msg): print(msg); return msg
    def show_progress(items, desc="处理中"): return items
    def print_header(title): print("=" * 50); print(title); print("=" * 50)
    def print_section(title): print(f"\n--- {title} ---")
    def print_section_end(): print()
    def print_info_line(label, value, color='info'): print(f"{label}: {value}")
    def print_separator(char="─", length=60): print(char * length)

# --- 配置项 (Configuration) ---
# --- 支持配置文件，保持向后兼容 ---

def load_application_config():
    """加载应用配置，支持配置文件和默认值"""
    if CLI_ENHANCED:
        config = load_config()
        return config['source_dir'], config['output_dir'], config['image_subdir_name']
    else:
        # 向后兼容：使用原有默认配置
        return 'flomo', 'converted_notes', 'flomo-images'

# 动态加载配置
SOURCE_DIR, OUTPUT_DIR, IMAGE_SUBDIR_NAME = load_application_config()

# --- HTML 解析规则 (Advanced Configuration) ---
# --- 一般无需修改，除非 flomo 的导出结构发生变化 ---
HTML_CONFIG = {
    'note_container': 'div.memo',
    'date_element': 'div.time',
    'content_element': 'div.content',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

def check_python_version():
    """检查 Python 版本是否为 3.6 或更高。"""
    if sys.version_info < (3, 6):
        print("错误：此脚本需要 Python 3.6 或更高版本。")
        print(f"您当前的 Python 版本是 {sys.version.split(' ')[0]}。")
        sys.exit(1)

def create_output_directories(output_dir, image_subdir_name):
    """创建输出文件夹和图片子文件夹。"""
    try:
        image_path = os.path.join(output_dir, image_subdir_name)
        os.makedirs(image_path, exist_ok=True)
        success(f"输出目录 '{output_dir}' 和图片目录 '{image_path}' 已准备就绪。")
        return image_path
    except OSError as e:
        error(f"创建输出目录失败：{e}")
        sys.exit(1)

def process_and_update_images_in_note(note_container, note_date_str, source_html_path, image_output_path, image_subdir_name):
    """在笔记中查找、复制并重命名图片，然后更新其路径。"""
    images = note_container.find_all('img')
    if not images:
        return note_container

    for img in images:
        original_src = img.get('src')
        if not original_src or original_src.startswith(('http://', 'https://')):
            continue

        html_file_directory = os.path.dirname(os.path.abspath(source_html_path))
        source_image_path = os.path.normpath(os.path.join(html_file_directory, original_src))

        if not os.path.exists(source_image_path):
            warning(f"图片文件未找到 '{source_image_path}'，跳过。")
            continue

        original_filename = os.path.basename(source_image_path)
        date_prefix = note_date_str.replace(':', '-').replace(' ', '_')
        new_unique_filename = f"{date_prefix}_{original_filename}"
        dest_image_path = os.path.join(image_output_path, new_unique_filename)

        try:
            shutil.copy2(source_image_path, dest_image_path)
            new_src = f"{image_subdir_name}/{new_unique_filename}"
            img['src'] = new_src
            print(f"│  图片已处理：{original_filename} -> {new_unique_filename}")
        except Exception as e:
            error(f"处理图片 '{original_filename}' 时失败：{e}")
            
    return note_container

def parse_html_file(file_path, image_output_path, image_subdir_name, year_filter=None):
    """解析单个 HTML 文件，返回包含笔记信息的列表。"""
    print(f"│  正在解析文件：{os.path.basename(file_path)}")
    parsed_notes = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')

        note_containers = soup.select(HTML_CONFIG['note_container'])
        for note_container in note_containers:
            date_element = note_container.select_one(HTML_CONFIG['date_element'])
            date_str = date_element.get_text(strip=True) if date_element else ''
            try:
                date_obj = datetime.strptime(date_str, HTML_CONFIG['date_format'])
            except (ValueError, TypeError):
                continue

            # 如果有年份过滤，跳过不符合年份的笔记
            if year_filter is not None and date_obj.year != year_filter:
                continue

            processed_container = process_and_update_images_in_note(
                note_container, date_str, file_path, image_output_path, image_subdir_name
            )

            content_element = processed_container.select_one(HTML_CONFIG['content_element'])
            markdown_content = md(str(content_element), heading_style='ATX').strip() if content_element else ""

            images_in_note = processed_container.find_all('img')
            for img in images_in_note:
                new_src = img.get('src')
                alt_text = img.get('alt', '')
                markdown_content += f"\n\n![{alt_text}]({new_src})"
            
            if markdown_content.strip():
                parsed_notes.append({'date_obj': date_obj, 'content': markdown_content.strip()})
        
        print(f"   - 提取到 {len(parsed_notes)} 条笔记。")
        return parsed_notes
    except Exception as e:
        print(f"❌ 错误：解析 HTML 文件 '{file_path}' 时失败：{e}")
        return []

def generate_markdown(all_notes, output_md_path):
    """生成 Markdown 文件从笔记列表。"""
    if not all_notes:
        return False
    
    all_notes.sort(key=lambda x: x['date_obj'], reverse=True)

    try:
        with open(output_md_path, 'w', encoding='utf-8') as f:
            current_date_header = None
            for note in all_notes:
                note_date = note['date_obj'].date()
                note_time_str = note['date_obj'].strftime('%H:%M:%S')

                if note_date != current_date_header:
                    f.write(f"# {note_date.strftime('%Y-%m-%d')}\n\n")
                    current_date_header = note_date
                
                f.write(f"**{note_time_str}**\n")
                f.write(note['content'])
                f.write('\n\n---\n\n')
        return True
    except IOError as e:
        print(f"❌ 错误：写入 Markdown 文件失败：{e}")
        return False

def contains_images(notes):
    """检查笔记列表中是否包含图片"""
    for note in notes:
        if '![image]' in note['content'] or '<img' in note['content']: # 简单的图片检测
            return True
    return False

def count_images_in_notes(notes):
    """统计笔记中的图片数量"""
    image_count = 0
    for note in notes:
        # 统计 markdown 格式的图片
        image_count += note['content'].count('![')
        # 统计 HTML 格式的图片
        image_count += note['content'].count('<img')
    return image_count

def parse_html_file_for_years(file_path):
    """解析 HTML 文件，只提取年份信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')

        note_containers = soup.select(HTML_CONFIG['note_container'])
        years = set()
        
        for note_container in note_containers:
            date_element = note_container.select_one(HTML_CONFIG['date_element'])
            date_str = date_element.get_text(strip=True) if date_element else ''
            try:
                date_obj = datetime.strptime(date_str, HTML_CONFIG['date_format'])
                years.add(date_obj.year)
            except (ValueError, TypeError):
                continue
        
        return sorted(list(years))
    except Exception as e:
        print(f"❌ 错误：解析 HTML 文件 '{file_path}' 年份信息时失败：{e}")
        return []

def get_available_years(source_dir):
    """获取源目录中所有 HTML 文件的年份信息"""
    if not os.path.isdir(source_dir):
        return []
    
    html_files = glob.glob(os.path.join(source_dir, '*.html')) + glob.glob(os.path.join(source_dir, '*.htm'))
    if not html_files:
        return []
    
    all_years = set()
    for file_path in html_files:
        years = parse_html_file_for_years(file_path)
        all_years.update(years)
    
    return sorted(list(all_years))

def print_file_info(source_dir):
    """打印文件详细信息"""
    if not os.path.isdir(source_dir):
        print(f"❌ 错误：源文件夹 '{source_dir}' 不存在。")
        return False
    
    html_files = glob.glob(os.path.join(source_dir, '*.html')) + glob.glob(os.path.join(source_dir, '*.htm'))
    if not html_files:
        print(f"❌ 错误：在源文件夹 '{source_dir}' 中未找到任何 .html 或 .htm 文件。")
        return False
    
    print(f"📁 源目录：{source_dir}")
    print(f"📄 HTML 文件数量：{len(html_files)}")
    
    # 获取年份信息
    all_years = get_available_years(source_dir)
    if all_years:
        print(f"📅 包含年份：{', '.join(map(str, all_years))}")
        print(f"📊 年份范围：{all_years[0]} - {all_years[-1]}")
        
        # 统计每个年份的笔记数量
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
                            date_obj = datetime.strptime(date_str, HTML_CONFIG['date_format'])
                            if date_obj.year == year:
                                year_notes += 1
                        except (ValueError, TypeError):
                            continue
                except Exception as e:
                    continue
            print(f"   {year}年：{year_notes} 条笔记")
    else:
        print("⚠️  未检测到有效的年份信息")
    
    return True

def interactive_year_selection(source_dir):
    """交互式年份选择"""
    all_years = get_available_years(source_dir)
    if not all_years:
        print("❌ 错误：未找到任何有效的年份信息")
        return None
    
    print("\n📅 检测到以下年份：")
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
                print(f"✅ 已选择：{selected_year}年")
                return selected_year
            elif choice_num == len(all_years) + 1:
                print("✅ 已选择：全部年份")
                return None
            else:
                print(f"❌ 请输入 1-{len(all_years) + 1} 之间的数字")
        except ValueError:
            print("❌ 请输入有效的数字")

def main():
    """主函数，协调整个转换流程。"""
    check_python_version()

    # 显示应用头部信息
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

🔰 基础转换：
  python flomo_converter.py                          # 转换所有年份
  python flomo_converter.py --year 2025              # 转换 2025 年

📊 信息查询：
  python flomo_converter.py --list-years             # 列出可用年份
  python flomo_converter.py --info                    # 详细统计信息

🎮 交互模式：
  python flomo_converter.py --interactive            # 交互式选择

🎨 导出模式：
  python flomo_converter.py --export-mode single_memos --year 2023
  python flomo_converter.py --export-mode yearly_archives

📁 自定义路径：
  python flomo_converter.py --source ./data --output ./result

💡 完整文档请查看 README.md

注意：--export-mode single_file 为默认模式，等同于直接运行 python flomo_converter.py
        """
    )

    # 基本参数
    parser.add_argument('--source', type=str, default=SOURCE_DIR,
                        help=f'📁 源文件夹路径 (默认：{SOURCE_DIR})')
    parser.add_argument('--output', type=str, default=OUTPUT_DIR,
                        help=f'💾 输出文件夹路径 (默认：{OUTPUT_DIR})')

    # 年份过滤参数
    parser.add_argument('--year', type=int, metavar='YEAR',
                        help='📅 只转换指定年份的笔记 (例：--year 2025)')

    # 信息查询参数
    parser.add_argument('--list-years', action='store_true',
                        help='📋 列出源文件中包含的所有年份')
    parser.add_argument('--info', action='store_true',
                        help='📊 显示源文件的详细信息和统计数据')
    parser.add_argument('--interactive', action='store_true',
                        help='🎮 使用交互式模式选择年份')

    # 导出模式参数
    parser.add_argument('--export-mode', type=str,
                        choices=['single_file', 'single_memos', 'yearly_archives'],
                        default='single_file',
                        help='🎨 选择导出模式 (默认：single_file)\n'
                             '  single_file     - 单一合并文件（默认模式）\n'
                             '  single_memos    - 单条 memo 文件\n'
                             '  yearly_archives - 按年归档')
    
    args = parser.parse_args()

    source_dir = args.source
    output_dir = args.output
    year_filter = args.year

    # 处理导出模式参数
    export_mode_map = {
        'single_file': ExportMode.SINGLE_FILE,
        'single_memos': ExportMode.SINGLE_MEMOS,
        'yearly_archives': ExportMode.YEARLY_ARCHIVES
    }
    export_mode = export_mode_map[args.export_mode]

    # 处理信息查询类参数
    if args.info:
        print_section("📋 文件信息查询")
        print_file_info(source_dir)
        print_section_end()
        return

    if args.list_years:
        print_section("📅 年份列表查询")
        all_years = get_available_years(source_dir)
        if all_years:
            print_info_line("可用年份", ", ".join(map(str, all_years)), 'success')
        else:
            print_info_line("结果", "未找到任何有效的年份信息", 'warning')
        print_section_end()
        return

    if args.interactive:
        print_section("🎯 交互式年份选择")
        year_filter = interactive_year_selection(source_dir)
        if year_filter is None:
            print_info_line("选择", "转换所有年份的笔记", 'info')
        else:
            print_info_line("选择", f"转换 {year_filter} 年的笔记", 'info')
        print_section_end()
    else:
        if year_filter:
            print_info_line("模式", f"转换 {year_filter} 年的笔记", 'info')
        else:
            print_info_line("模式", "转换所有年份的笔记", 'info')

    # 显示导出模式信息
    print_section(f"🚀 开始转换")
    print_info_line("导出模式", args.export_mode, 'info')
    print_info_line("源目录", source_dir, 'info')
    print_info_line("输出目录", output_dir, 'info')
    if year_filter:
        print_info_line("年份过滤", str(year_filter), 'info')

    # 调用统一的转换函数
    result_dir = convert_notes(
        source_dir=source_dir,
        output_dir=output_dir,
        year_filter=year_filter,
        export_mode=export_mode
    )

    print_section("✅ 转换结果")

    if result_dir:
        print_info_line("结果", "转换成功", 'success')
        print_info_line("输出目录", result_dir, 'success')

        # 显示输出目录内容
        output_files = []
        for item in os.listdir(result_dir):
            item_path = os.path.join(result_dir, item)
            if os.path.isfile(item_path):
                output_files.append(f"📄 {item}")
            elif os.path.isdir(item_path):
                # 统计文件夹内容
                sub_items = os.listdir(item_path)
                if sub_items:
                    output_files.append(f"📁 {item}/ ({len(sub_items)} 个项目)")
                else:
                    output_files.append(f"📁 {item}/ (空)")

        if output_files:
            print_info_line("生成内容", output_files, 'success')
        else:
            print_info_line("生成内容", "无", 'warning')
    else:
        print_info_line("结果", "转换失败", 'error')

    print_section_end()


if __name__ == '__main__':
    main()
