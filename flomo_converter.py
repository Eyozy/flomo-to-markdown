import os
import shutil
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import glob

# --- 配置项 (Configuration) ---
# --- 请根据您的需求修改以下路径 ---

# 1. 源文件夹：存放您从 Flomo 导出的 HTML 文件和 file 图片文件夹的地方。
#    脚本会在此文件夹内查找 .html 文件进行转换。
SOURCE_DIR = 'flomo'

# 2. 输出文件夹：所有转换结果的存放位置。
#    如果此文件夹不存在，脚本会自动创建。
OUTPUT_DIR = 'converted_notes'

# 3. 输出文件名：最终生成的 Markdown 文件的名字。
MARKDOWN_FILENAME = 'flomo-output.md'

# 4. 图片子文件夹：在输出文件夹内，用于存放所有图片的子文件夹的名字。
IMAGE_SUBDIR_NAME = 'flomo-images'


# --- HTML 解析规则 (Advanced Configuration) ---
# --- 一般无需修改，除非 Flomo 的导出结构发生变化 ---
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

def create_output_directories():
    """创建输出文件夹和图片子文件夹。"""
    try:
        image_path = os.path.join(OUTPUT_DIR, IMAGE_SUBDIR_NAME)
        os.makedirs(image_path, exist_ok=True)
        print(f"✅ 输出目录 '{OUTPUT_DIR}' 和图片目录 '{image_path}' 已准备就绪。")
        return image_path
    except OSError as e:
        print(f"❌ 错误：创建输出目录失败：{e}")
        sys.exit(1)

def process_and_update_images_in_note(note_container, note_date_str, source_html_path, image_output_path):
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
            new_src = f"{IMAGE_SUBDIR_NAME}/{new_unique_filename}"
            img['src'] = new_src
            print(f"   - 图片已处理：{original_filename} -> {new_unique_filename}")
        except Exception as e:
            print(f"   - 错误：处理图片 '{original_filename}' 时失败：{e}")
            
    return note_container

def parse_html_file(file_path, image_output_path):
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

            processed_container = process_and_update_images_in_note(
                note_container, date_str, file_path, image_output_path
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

def main():
    """主函数，协调整个转换流程。"""
    print("--- Flomo HTML to Markdown Converter ---")
    check_python_version()

    if not os.path.isdir(SOURCE_DIR):
        print(f"❌ 错误：源文件夹 '{SOURCE_DIR}' 不存在。请检查配置项并确保文件夹位置正确。")
        return

    image_output_path = create_output_directories()
    all_notes = []
    html_files = glob.glob(os.path.join(SOURCE_DIR, '*.html')) + glob.glob(os.path.join(SOURCE_DIR, '*.htm'))
    
    if not html_files:
        print(f"❌ 错误：在源文件夹 '{SOURCE_DIR}' 中未找到任何 .html 或 .htm 文件。")
        return

    for file_path in html_files:
        notes_from_file = parse_html_file(file_path, image_output_path)
        all_notes.extend(notes_from_file)

    if not all_notes:
        print("\n🤔 未提取到任何有效笔记，程序结束。")
        return
    
    all_notes.sort(key=lambda x: x['date_obj'], reverse=True)

    output_md_path = os.path.join(OUTPUT_DIR, MARKDOWN_FILENAME)
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
        
        print(f"\n🎉 成功！所有笔记已合并到：{output_md_path}")

    except IOError as e:
        print(f"❌ 错误：写入 Markdown 文件失败：{e}")

if __name__ == '__main__':
    main()