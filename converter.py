import os
import shutil
import tempfile
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import glob
from enum import Enum

logger = logging.getLogger(__name__)

# 导出模式枚举
class ExportMode(Enum):
    SINGLE_FILE = "single_file"        # 单一合并文件（默认）
    SINGLE_MEMOS = "single_memos"      # 单条 memo 导出
    YEARLY_ARCHIVES = "yearly_archives"    # 按年归档

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

def find_image_file(original_src, html_file_directory, note_date_str):
    """查找图片文件的完整路径"""
    # 首先尝试直接路径
    source_image_path = os.path.normpath(os.path.join(html_file_directory, original_src))
    if os.path.exists(source_image_path):
        return source_image_path

    # 如果直接路径找不到，尝试在 file 目录下按日期查找
    try:
        note_date = datetime.strptime(note_date_str, HTML_CONFIG['date_format'])
        date_folder = note_date.strftime('%Y-%m-%d')
        file_dir = os.path.join(html_file_directory, 'file')

        if os.path.exists(file_dir):
            date_file_path = os.path.join(file_dir, date_folder)
            if os.path.exists(date_file_path):
                for root, dirs, files in os.walk(date_file_path):
                    if os.path.basename(original_src) in files:
                        found_path = os.path.join(root, os.path.basename(original_src))
                        if os.path.exists(found_path):
                            return found_path
    except Exception as e:
        logger.debug(f"按日期查找图片失败：{e}")

    return None

def process_single_image(img, note_date_str, source_html_path, image_output_path, image_subdir_name):
    """处理单个图片"""
    original_src = img.get('src')
    if not original_src or original_src.startswith(('http://', 'https://')):
        return False

    html_file_directory = os.path.dirname(os.path.abspath(source_html_path))
    source_image_path = find_image_file(original_src, html_file_directory, note_date_str)

    if not source_image_path:
        logger.warning(f"图片文件未找到 '{original_src}'，跳过。")
        return False

    if not image_output_path:
        logger.info(f"跳过图片复制：{os.path.basename(source_image_path)}")
        return False

    # 确保图片输出目录存在
    if not os.path.exists(image_output_path):
        os.makedirs(image_output_path, exist_ok=True)

    original_filename = os.path.basename(source_image_path)
    date_prefix = note_date_str.replace(':', '-').replace(' ', '_')
    new_unique_filename = f"{date_prefix}_{original_filename}"
    dest_image_path = os.path.join(image_output_path, new_unique_filename)

    try:
        shutil.copy2(source_image_path, dest_image_path)
        new_src = f"{image_subdir_name}/{new_unique_filename}"
        img['src'] = new_src
        logger.info(f"图片已处理：{original_filename} -> {new_unique_filename}")
        return True
    except Exception as e:
        logger.error(f"处理图片 '{original_filename}' 时失败：{e}")
        return False

def process_and_update_images_in_note(note_container, note_date_str, source_html_path, image_output_path, image_subdir_name=IMAGE_SUBDIR_NAME):
    """在笔记中查找、复制并重命名图片，然后更新其路径。"""
    images = note_container.find_all('img')
    if not images:
        return note_container

    processed_count = 0
    for img in images:
        if process_single_image(img, note_date_str, source_html_path, image_output_path, image_subdir_name):
            processed_count += 1

    if processed_count > 0:
        logger.info(f"已处理 {processed_count} 张图片")

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

            # 处理图片
            image_subdir_name = os.path.basename(image_output_path)
            processed_container = process_and_update_images_in_note(
                note_container, date_str, file_path, image_output_path, image_subdir_name
            )

            content_element = processed_container.select_one(HTML_CONFIG['content_element'])
            markdown_content = md(str(content_element), heading_style='ATX').strip() if content_element else ""

            # 查找图片（无论是否处理图片路径，都要检测图片存在）
            images_in_note = processed_container.find_all('img')

            # 在非单一文件模式下，需要保留原始图片路径信息
            if image_output_path is None:
                # 非单一文件模式，保留原始图片路径
                for img in images_in_note:
                    new_src = img.get('src')
                    alt_text = img.get('alt', '')
                    markdown_content += f"\n\n![{alt_text}]({new_src})"
            else:
                # 单一文件模式，图片路径已经处理过
                for img in images_in_note:
                    new_src = img.get('src')
                    alt_text = img.get('alt', '')
                    markdown_content += f"\n\n![{alt_text}]({new_src})"
            
            if markdown_content.strip():
                parsed_notes.append({
                    'date_obj': date_obj,
                    'date_str': date_str,
                    'content': markdown_content.strip(),
                    'has_images': len(images_in_note) > 0
                })
        
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

def convert_notes(source_dir, output_dir=None, markdown_filename=MARKDOWN_FILENAME, image_subdir_name=IMAGE_SUBDIR_NAME, year_filter=None, export_mode=ExportMode.SINGLE_FILE):
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

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 为所有导出模式创建图片文件夹（如果有图片的话）
    # 这里先不创建，让各个导出函数根据实际需要创建
    image_output_path = os.path.join(output_dir, image_subdir_name)
    logger.info(f"输出目录 '{output_dir}' 已准备就绪。")

    all_notes = []

    if not html_files:
        logger.error(f"在源文件夹 '{source_dir}' 中未找到任何 .html 或 .htm 文件。")
        return None

    # 创建临时图片处理目录，用于在转换过程中存储图片
    temp_image_path = os.path.join(output_dir, image_subdir_name)

    for file_path in html_files:
        # 所有模式都处理图片，让各个导出函数决定如何组织
        notes_from_file = parse_html_file(file_path, temp_image_path, year_filter)
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

    # 根据导出模式执行不同的生成逻辑
    success = False

    if export_mode == ExportMode.SINGLE_FILE:
        # 原有的单一文件模式
        output_md_path = os.path.join(output_dir, markdown_filename)
        success = generate_markdown(all_notes, output_md_path)
        if success:
            logger.info(f"成功！所有笔记已合并到：{output_md_path}")

    elif export_mode == ExportMode.SINGLE_MEMOS:
        # 单条 memo 导出模式
        success = generate_individual_memos(all_notes, output_dir, image_subdir_name)
        if success:
            logger.info(f"成功！已生成 {len(all_notes)} 个单条 memo 文件")

    elif export_mode == ExportMode.YEARLY_ARCHIVES:
        # 按年归档模式
        selected_years = [year_filter] if year_filter else None
        success = generate_yearly_archives(all_notes, output_dir, selected_years)
        if success:
            logger.info(f"成功！已创建按年归档文件夹")

    if success:
        # 清理临时图片目录（如果存在且不同于最终图片目录）
        if temp_image_path != image_output_path and os.path.exists(temp_image_path):
            shutil.rmtree(temp_image_path)
            logger.info(f"已清理临时图片目录：{temp_image_path}")

        # 如果没有图片，删除空的图片文件夹（适用于所有模式）
        if not has_images and image_output_path is not None:
            if os.path.exists(image_output_path) and not os.listdir(image_output_path):
                shutil.rmtree(image_output_path)
                logger.info(f"已删除空的图片目录：{image_output_path}")

        return output_dir
    else:
        shutil.rmtree(output_dir, ignore_errors=True)
        return None

def generate_individual_memos(all_notes, output_dir, image_subdir_name=IMAGE_SUBDIR_NAME):
    """生成单条 memo 文件：每个 memo 一个 md 文件"""
    logger.info(f"开始生成单条 memo 文件，共 {len(all_notes)} 条笔记")

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 检查是否有图片并收集图片路径
    has_images = any(note.get('has_images', False) for note in all_notes)
    images_to_copy = set()

    for note in all_notes:
        if note.get('has_images', False):
            images_to_copy.update(extract_image_paths_from_content(note['content']))

    logger.info(f"检测到 {len(images_to_copy)} 个图片文件需要处理")

    # 只有在有图片时才创建图片文件夹
    image_output_path = None
    if has_images and images_to_copy:
        image_output_path = os.path.join(output_dir, image_subdir_name)
        os.makedirs(image_output_path, exist_ok=True)
        logger.info(f"创建图片文件夹：{image_output_path}")

        # 复制图片文件
        temp_image_dir = os.path.join(output_dir, IMAGE_SUBDIR_NAME)
        if not os.path.exists(temp_image_dir):
            temp_image_dir = os.path.join(output_dir, image_subdir_name)

        copy_images_to_directory(images_to_copy, temp_image_dir, image_output_path)
    else:
        logger.info("没有图片，跳过创建图片文件夹")

    # 生成文件
    generated_files = []
    for i, note in enumerate(all_notes, 1):
        date_str = note['date_obj'].strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"{date_str}.md"
        file_path = os.path.join(output_dir, filename)

        # 更新图片路径
        content = update_image_paths_in_content(note['content'], 'flomo-images/', f'{image_subdir_name}/')

        # 生成 markdown 内容
        markdown_content = f"# {note['date_str']}\n\n{content}\n"

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            generated_files.append(file_path)
            logger.debug(f"已生成文件 {i}/{len(all_notes)}: {filename}")
        except Exception as e:
            logger.error(f"生成文件 {filename} 失败：{e}")

    logger.info(f"成功生成 {len(generated_files)} 个单条 memo 文件")
    return len(generated_files) > 0

def generate_yearly_archives(all_notes, output_dir, selected_years=None):
    """生成按年归档文件：每年一个文件夹"""
    if not selected_years:
        # 提取所有年份
        selected_years = sorted(set(note['date_obj'].year for note in all_notes))

    logger.info(f"开始生成按年归档，年份：{selected_years}")

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    created_archives = []

    # 判断是否为全部年份模式（根据用户选择而非数据内容）
    is_all_years = len(selected_years) > 1

    # 检查是否有图片
    has_images = any(note.get('has_images', False) for note in all_notes)

    # 用于收集需要复制的图片文件
    images_to_copy = set()

    # 收集所有需要复制的图片文件路径
    for note in all_notes:
        if note.get('has_images', False):
            images_to_copy.update(extract_image_paths_from_content(note['content']))

    logger.info(f"检测到 {len(images_to_copy)} 个图片文件需要处理")

    if is_all_years and has_images and images_to_copy:
        # 全部年份模式且有图片：在根目录创建统一的图片文件夹
        unified_image_dir = os.path.join(output_dir, "flomo-images")
        os.makedirs(unified_image_dir, exist_ok=True)
        logger.info(f"创建统一图片文件夹：{unified_image_dir}")

        # 复制图片到统一文件夹
        temp_image_dir = os.path.join(output_dir, IMAGE_SUBDIR_NAME)
        if not os.path.exists(temp_image_dir):
            temp_image_dir = os.path.join(output_dir, "flomo-images")

        copy_images_to_directory(images_to_copy, temp_image_dir, unified_image_dir)

    elif not is_all_years and has_images and images_to_copy:
        # 单一年份模式且有图片：在根目录创建年份特定的图片文件夹
        year_image_dir = os.path.join(output_dir, f"{selected_years[0]}-flomo-images")
        os.makedirs(year_image_dir, exist_ok=True)
        logger.info(f"创建根级年份图片文件夹：{year_image_dir}")

        # 复制图片到年份文件夹
        temp_image_dir = os.path.join(output_dir, IMAGE_SUBDIR_NAME)
        if not os.path.exists(temp_image_dir):
            temp_image_dir = os.path.join(output_dir, "flomo-images")

        copy_images_to_directory(images_to_copy, temp_image_dir, year_image_dir)

    for year in selected_years:
        # 过滤该年份的笔记
        year_notes = [note for note in all_notes if note['date_obj'].year == year]

        if not year_notes:
            logger.warning(f"年份 {year} 没有找到任何笔记，跳过")
            continue

        # 创建年份归档文件夹
        archive_dir = os.path.join(output_dir, f"{year}-archive")
        os.makedirs(archive_dir, exist_ok=True)

        # 处理该年份的每条笔记
        year_files = []
        for note in year_notes:
            # 生成文件名：YYYY-MM-DD_HH-MM-SS.md
            date_str = note['date_obj'].strftime('%Y-%m-%d_%H-%M-%S')
            filename = f"{date_str}.md"
            file_path = os.path.join(archive_dir, filename)

            # 更新图片路径
            content = note['content']
            if 'flomo-images' in content and has_images:
                if is_all_years:
                    # 全部年份模式：使用统一图片文件夹
                    content = update_image_paths_in_content(content, 'flomo-images/', '../flomo-images/')
                else:
                    # 单一年份模式：使用根级年份特定的图片文件夹
                    content = update_image_paths_in_content(content, 'flomo-images/', f'../{year}-flomo-images/')

            # 生成单个 memo 的 markdown 内容
            markdown_content = f"# {note['date_str']}\n\n{content}\n"

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                year_files.append(file_path)
            except Exception as e:
                logger.error(f"生成年份 {year} 的文件 {filename} 失败：{e}")

        if year_files:
            created_archives.append(archive_dir)
            logger.info(f"已创建 {year} 年归档，包含 {len(year_files)} 个文件")

    logger.info(f"成功创建 {len(created_archives)} 个年份归档")
    return len(created_archives) > 0

# ========== 辅助函数 ==========

def extract_image_paths_from_content(content):
    """从内容中提取图片路径"""
    import re
    img_pattern = r'!\[.*?\]\(([^)]+)\)'
    matches = re.findall(img_pattern, content)
    return {match for match in matches if match.startswith('flomo-images/')}

def update_image_paths_in_content(content, old_prefix, new_prefix):
    """更新内容中的图片路径前缀"""
    if old_prefix in content:
        return content.replace(old_prefix, new_prefix)
    return content

def copy_images_to_directory(images_to_copy, source_image_dir, target_image_dir):
    """复制图片文件到目标目录"""
    if not images_to_copy or not os.path.exists(source_image_dir):
        return 0

    if not os.path.exists(target_image_dir):
        os.makedirs(target_image_dir, exist_ok=True)

    copied_count = 0
    for img_rel_path in images_to_copy:
        if img_rel_path.startswith('flomo-images/'):
            img_filename = img_rel_path.replace('flomo-images/', '')
            source_path = os.path.join(source_image_dir, img_filename)
            dest_path = os.path.join(target_image_dir, img_filename)
            if os.path.exists(source_path):
                try:
                    shutil.copy2(source_path, dest_path)
                    copied_count += 1
                    logger.debug(f"复制图片：{img_filename}")
                except Exception as e:
                    logger.error(f"复制图片失败 {img_filename}: {e}")

    if copied_count > 0:
        logger.info(f"成功复制 {copied_count} 张图片到 {target_image_dir}")

    return copied_count
