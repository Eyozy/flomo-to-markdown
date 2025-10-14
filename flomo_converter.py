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

# --- 配置项 (Configuration) ---
# --- 请根据您的需求修改以下路径 ---

# 1. 源文件夹：存放您从 flomo 导出的 HTML 文件和 file 图片文件夹的地方。
#    脚本会在此文件夹内查找 .html 文件进行转换。
SOURCE_DIR = 'flomo'

# 2. 输出文件夹：所有转换结果的存放位置。
#    如果此文件夹不存在，脚本会自动创建。
OUTPUT_DIR = 'converted_notes'

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
        print(f"✅ 输出目录 '{output_dir}' 和图片目录 '{image_path}' 已准备就绪。")
        return image_path
    except OSError as e:
        print(f"❌ 错误：创建输出目录失败：{e}")
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
            print(f"   - 警告：图片文件未找到 '{source_image_path}'，跳过。")
            continue
        
        original_filename = os.path.basename(source_image_path)
        date_prefix = note_date_str.replace(':', '-').replace(' ', '_')
        new_unique_filename = f"{date_prefix}_{original_filename}"
        dest_image_path = os.path.join(image_output_path, new_unique_filename)

        try:
            shutil.copy2(source_image_path, dest_image_path)
            new_src = f"{image_subdir_name}/{new_unique_filename}"
            img['src'] = new_src
            print(f"   - 图片已处理：{original_filename} -> {new_unique_filename}")
        except Exception as e:
            print(f"   - 错误：处理图片 '{original_filename}' 时失败：{e}")
            
    return note_container

def parse_html_file(file_path, image_output_path, image_subdir_name, year_filter=None):
    """解析单个 HTML 文件，返回包含笔记信息的列表。"""
    print(f"\n📄 正在解析文件：{file_path}...")
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

    parser = argparse.ArgumentParser(
        description="Flomo HTML to Markdown Converter CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  # 转换所有年份的笔记
  python3 flomo_converter.py
  
  # 转换特定年份的笔记
  python3 flomo_converter.py --year 2023
  
  # 查看可用年份
  python3 flomo_converter.py --list-years
  
  # 查看文件详细信息
  python3 flomo_converter.py --info
  
  # 交互式选择年份
  python3 flomo_converter.py --interactive
  
  # 指定源目录和输出目录
  python3 flomo_converter.py --source ./flomo-export --output ./output --year 2022
        """
    )
    
    parser.add_argument('--source', type=str, default=SOURCE_DIR,
                        help=f"源文件夹：存放 flomo 导出的 HTML 文件和图片文件夹 (默认：{SOURCE_DIR})")
    parser.add_argument('--output', type=str, default=OUTPUT_DIR,
                        help=f"输出文件夹：所有转换结果的存放位置 (默认：{OUTPUT_DIR})")
    parser.add_argument('--year', type=int,
                        help="可选：只转换指定年份的笔记。例如：--year 2023")
    parser.add_argument('--list-years', action='store_true',
                        help="列出源文件中包含的所有年份")
    parser.add_argument('--info', action='store_true',
                        help="显示源文件的详细信息")
    parser.add_argument('--interactive', action='store_true',
                        help="使用交互式模式选择年份")
    
    args = parser.parse_args()

    source_dir = args.source
    output_dir = args.output
    year_filter = args.year

    # 处理信息查询类参数
    if args.info:
        print("--- flomo HTML to Markdown Converter ---")
        print("📋 文件信息查询模式")
        print_file_info(source_dir)
        return

    if args.list_years:
        print("--- flomo HTML to Markdown Converter ---")
        print("📅 年份列表查询模式")
        all_years = get_available_years(source_dir)
        if all_years:
            print(f"✅ 找到以下年份：{', '.join(map(str, all_years))}")
        else:
            print("❌ 未找到任何有效的年份信息")
        return

    if args.interactive:
        print("--- flomo HTML to Markdown Converter ---")
        print("🎯 交互式模式")
        year_filter = interactive_year_selection(source_dir)
        if year_filter is None:
            print("✨ 正在转换所有年份的笔记...")
        else:
            print(f"✨ 正在转换 {year_filter} 年的笔记...")
    else:
        print("--- flomo HTML to Markdown Converter ---")
        if year_filter:
            print(f"✨ 正在转换 {year_filter} 年的笔记...")
        else:
            print("✨ 正在转换所有年份的笔记...")

    if not os.path.isdir(source_dir):
        print(f"❌ 错误：源文件夹 '{source_dir}' 不存在。请检查配置项并确保文件夹位置正确。")
        return

    # 根据年份过滤调整文件和文件夹命名
    if year_filter is not None:
        markdown_filename = f"{year_filter}-flomo-output.md"
        image_subdir_name = f"{year_filter}-flomo-images"
    else:
        # 获取所有年份用于命名
        all_years_for_naming = get_available_years(source_dir)
        if len(all_years_for_naming) > 1:
            markdown_filename = f'{all_years_for_naming[0]}-{all_years_for_naming[-1]}-flomo-output.md'
            image_subdir_name = f'{all_years_for_naming[0]}-{all_years_for_naming[-1]}-flomo-images'
        elif all_years_for_naming:
            markdown_filename = f'{all_years_for_naming[0]}-flomo-output.md'
            image_subdir_name = f'{all_years_for_naming[0]}-flomo-images'
        else:
            markdown_filename = 'flomo-output.md'
            image_subdir_name = 'flomo-images'

    image_output_path = create_output_directories(output_dir, image_subdir_name)
    all_notes = []
    html_files = glob.glob(os.path.join(source_dir, '*.html')) + glob.glob(os.path.join(source_dir, '*.htm'))
    
    if not html_files:
        print(f"❌ 错误：在源文件夹 '{source_dir}' 中未找到任何 .html 或 .htm 文件。")
        return

    for file_path in html_files:
        notes_from_file = parse_html_file(file_path, image_output_path, image_subdir_name, year_filter)
        all_notes.extend(notes_from_file)

    if not all_notes:
        print("\n🤔 未提取到任何有效笔记，程序结束。")
        
        # 增强错误提示：如果指定了年份但未找到笔记，显示可用年份
        if year_filter is not None:
            all_years = get_available_years(source_dir)
            if all_years:
                print(f"\n💡 提示：该文件包含以下年份：{', '.join(map(str, all_years))}")
                print(f"💡 请使用 --year 参数指定存在的年份，或使用 --list-years 查看所有年份")
            else:
                print(f"💡 提示：未检测到任何有效的年份信息，请检查文件格式是否正确")
        
        # 如果没有笔记，且创建了空的图片目录，则删除
        if os.path.exists(image_output_path) and not os.listdir(image_output_path):
            shutil.rmtree(image_output_path)
            print(f"已删除空的图片目录：{image_output_path}")
        return
    
    all_notes.sort(key=lambda x: x['date_obj'], reverse=True)

    output_md_path = os.path.join(output_dir, markdown_filename)
    if generate_markdown(all_notes, output_md_path):
        print(f"\n🎉 成功！所有笔记已合并到：{output_md_path}")
        
        # 如果没有图片且是特定年份，删除空的图片文件夹
        has_images = contains_images(all_notes)
        if not has_images and year_filter is not None:
            if os.path.exists(image_output_path) and not os.listdir(image_output_path):
                shutil.rmtree(image_output_path)
                print(f"已删除空的图片目录：{image_output_path}")
    else:
        print(f"\n❌ 错误：生成 Markdown 文件失败。")
        # 如果生成失败，清理可能创建的目录
        shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == '__main__':
    main()
