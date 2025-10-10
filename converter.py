import os
import shutil
import tempfile
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import glob

logger = logging.getLogger(__name__)

# --- HTML 解析规则 (Advanced Configuration) ---
# --- 一般无需修改，除非 flomo 的导出结构发生变化 ---
HTML_CONFIG = {
    'note_container': 'div.memo',
    'date_element': 'div.time',
    'content_element': 'div.content',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

IMAGE_SUBDIR_NAME = 'flomo-images'
MARKDOWN_FILENAME = 'flomo-output.md'

def process_and_update_images_in_note(note_container, note_date_str, source_html_path, image_output_path, image_subdir_name=IMAGE_SUBDIR_NAME):
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
            logger.warning(f"图片文件未找到 '{source_image_path}'，跳过。")
            continue
        
        original_filename = os.path.basename(source_image_path)
        date_prefix = note_date_str.replace(':', '-').replace(' ', '_')
        new_unique_filename = f"{date_prefix}_{original_filename}"
        dest_image_path = os.path.join(image_output_path, new_unique_filename)

        try:
            shutil.copy2(source_image_path, dest_image_path)
            new_src = f"{image_subdir_name}/{new_unique_filename}"
            img['src'] = new_src
            logger.info(f"图片已处理：{original_filename} -> {new_unique_filename}")
        except Exception as e:
            logger.error(f"处理图片 '{original_filename}' 时失败：{e}")
            
    return note_container

def parse_html_file(file_path, image_output_path, year_filter=None):
    """解析单个 HTML 文件，返回包含笔记信息的列表。"""
    logger.info(f"正在解析文件：{file_path}")
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

            # 只有在符合年份过滤条件时才处理图片，传递正确的 image_subdir_name
            image_subdir_name = os.path.basename(image_output_path)
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
        
        logger.info(f"提取到 {len(parsed_notes)} 条笔记。")
        return parsed_notes
    except Exception as e:
        logger.error(f"解析 HTML 文件 '{file_path}' 时失败：{e}")
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
        logger.error(f"写入 Markdown 文件失败：{e}")
        return False

def contains_images(notes):
    """检查笔记列表中是否包含图片"""
    for note in notes:
        if '![image]' in note['content'] or '<img' in note['content']: # 简单的图片检测
            return True
    return False

def extract_years_from_notes(notes):
    """从笔记列表中提取所有年份"""
    years = set()
    for note in notes:
        years.add(note['date_obj'].year)
    return sorted(list(years))

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
        logger.error(f"解析 HTML 文件 '{file_path}' 年份信息时失败：{e}")
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

def convert_notes(source_dir, output_dir=None, markdown_filename=MARKDOWN_FILENAME, image_subdir_name=IMAGE_SUBDIR_NAME, year_filter=None):
    """主转换函数：处理 source_dir 中的 HTML 文件，输出到 output_dir。返回 output_dir 如果成功，否则 None。"""
    logger.info("--- Flomo HTML to Markdown Converter ---")

    if not os.path.isdir(source_dir):
        logger.error(f"源文件夹 '{source_dir}' 不存在。")
        return None

    # Basic validation: Check for Flomo structure in first HTML file
    html_files = glob.glob(os.path.join(source_dir, '*.html')) + glob.glob(os.path.join(source_dir, '*.htm'))
    if html_files:
        try:
            with open(html_files[0], 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'lxml')
            if not soup.select(HTML_CONFIG['note_container']):
                logger.warning(f"源目录 '{source_dir}' 可能不是有效的 Flomo 导出（无笔记容器）。")
        except Exception as e:
            logger.warning(f"验证 Flomo 结构时出错：{e}")

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix='flomo_convert_')

    # 根据年份过滤调整文件和文件夹命名
    if year_filter is not None:
        markdown_filename = f"{year_filter}-flomo-output.md"
        image_subdir_name = f"{year_filter}-flomo-images"

    image_output_path = os.path.join(output_dir, image_subdir_name)
    os.makedirs(image_output_path, exist_ok=True)
    logger.info(f"输出目录 '{output_dir}' 和图片目录 '{image_output_path}' 已准备就绪。")

    all_notes = []
    
    if not html_files:
        logger.error(f"在源文件夹 '{source_dir}' 中未找到任何 .html 或 .htm 文件。")
        return None

    for file_path in html_files:
        notes_from_file = parse_html_file(file_path, image_output_path, year_filter)
        all_notes.extend(notes_from_file)

    if not all_notes:
        logger.warning("未提取到任何有效笔记。")
        return None
    
    # 应用年份过滤（如果还没有在 parse_html_file 中过滤）
    if year_filter is not None:
        filtered_notes = [note for note in all_notes if note['date_obj'].year == year_filter]
        logger.info(f"年份过滤：从 {len(all_notes)} 条笔记中筛选出 {len(filtered_notes)} 条 {year_filter} 年的笔记")
        all_notes = filtered_notes
    
    # 检查过滤后的笔记是否包含图片
    has_images = contains_images(all_notes)
    logger.info(f"图片检测：{year_filter or '全部'} 年份的笔记 {'包含' if has_images else '不包含'}图片")
    
    output_md_path = os.path.join(output_dir, markdown_filename)
    if generate_markdown(all_notes, output_md_path):
        logger.info(f"成功！所有笔记已合并到：{output_md_path}")
        
        # 如果没有图片且是特定年份，删除空的图片文件夹
        if not has_images and year_filter is not None:
            if os.path.exists(image_output_path) and not os.listdir(image_output_path):
                shutil.rmtree(image_output_path)
                logger.info(f"已删除空的图片目录：{image_output_path}")
        
        return output_dir
    else:
        shutil.rmtree(output_dir, ignore_errors=True)
        return None
