import os
import zipfile
import tempfile
import shutil
import logging
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from converter import convert_notes, IMAGE_SUBDIR_NAME, MARKDOWN_FILENAME, get_available_years, contains_images, ExportMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'flomo_web_dev_key')  # Use env var in production
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
ALLOWED_EXTENSIONS = {'html', 'htm', 'zip'}

# Rate limiting (5 requests per minute per IP)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["5 per minute"],
    storage_uri="memory://"
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file_upload(file, source_dir):
    """处理文件上传（HTML 或 ZIP），返回成功状态和错误信息"""
    if not file or file.filename == '':
        return False, 'No file selected.'

    if not allowed_file(file.filename):
        return False, 'File type not allowed.'

    filename = secure_filename(file.filename)
    is_html = filename.lower().endswith(('.html', '.htm'))

    try:
        if is_html:
            # Single HTML file
            html_path = os.path.join(source_dir, filename)
            file.save(html_path)
            return True, None
        elif filename.lower().endswith('.zip'):
            # ZIP file
            zip_path = os.path.join(source_dir, filename)
            file.save(zip_path)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(source_dir)
                logger.info('ZIP extracted successfully')
                # Remove the zip file itself
                os.remove(zip_path)
                return True, None
            except zipfile.BadZipFile:
                logger.error('Invalid ZIP file')
                return False, '无效 ZIP 文件。'
            except Exception as e:
                logger.error(f'ZIP extraction failed: {e}')
                return False, 'ZIP 解压失败。'
        else:
            return False, 'Invalid file type.'
    except Exception as e:
        logger.error(f'File upload failed: {e}')
        return False, '文件上传失败。'

def cleanup_temp_dir(temp_dir):
    """清理临时目录"""
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.route('/parse-years', methods=['POST'])
@limiter.limit("10 per minute")
def parse_years():
    """解析上传文件中的年份信息"""
    try:
        if 'file' not in request.files:
            return {'error': 'No file selected.'}, 400

        file = request.files['file']
        source_dir = tempfile.mkdtemp(prefix='flomo_parse_')

        try:
            success, error_msg = handle_file_upload(file, source_dir)
            if not success:
                return {'error': error_msg}, 400

            # Get available years
            years = get_available_years(source_dir)

            if years:
                return {'years': years, 'success': True}
            else:
                return {'error': '未找到任何有效的笔记数据。'}, 400

        except Exception as e:
            logger.error(f'Parse years failed: {e}')
            return {'error': '解析文件时发生错误。'}, 500
        finally:
            cleanup_temp_dir(source_dir)

    except BadRequest:
        return {'error': '文件过大（最大 50MB）。'}, 400

def parse_form_parameters():
    """解析表单参数"""
    year_filter = request.form.get('year_filter')
    if year_filter and year_filter != 'all':
        try:
            year_filter = int(year_filter)
        except ValueError:
            year_filter = None

    export_mode_str = request.form.get('export_mode', 'single_file')
    export_mode_map = {
        'single_file': ExportMode.SINGLE_FILE,
        'single_memos': ExportMode.SINGLE_MEMOS,
        'yearly_archives': ExportMode.YEARLY_ARCHIVES
    }
    export_mode = export_mode_map.get(export_mode_str, ExportMode.SINGLE_FILE)

    return year_filter, export_mode

def generate_download_names(year_filter, all_years, export_mode):
    """生成下载文件名"""
    if export_mode == ExportMode.SINGLE_FILE:
        if year_filter:
            download_name = f'{year_filter}-flomo-output.md'
            zip_download_name = f'{year_filter}-flomo-output.zip'
        else:
            if len(all_years) > 1:
                download_name = f'{all_years[0]}-{all_years[-1]}-flomo-output.md'
                zip_download_name = f'{all_years[0]}-{all_years[-1]}-flomo-output.zip'
            elif all_years:
                download_name = f'{all_years[0]}-flomo-output.md'
                zip_download_name = f'{all_years[0]}-flomo-output.zip'
            else:
                download_name = 'flomo-output.md'
                zip_download_name = 'flomo-output.zip'
        return download_name, zip_download_name
    elif export_mode == ExportMode.SINGLE_MEMOS:
        zip_download_name = 'flomo-memos.zip'
        if year_filter:
            zip_download_name = f'{year_filter}-flomo-memos.zip'
        return None, zip_download_name
    else:  # YEARLY_ARCHIVES
        zip_download_name = 'flomo-yearly-archives.zip'
        if year_filter:
            zip_download_name = f'{year_filter}-flomo-archive.zip'
        return None, zip_download_name

def check_has_images(output_dir, year_filter):
    """检查输出目录是否包含图片"""
    if year_filter:
        image_path = os.path.join(output_dir, f"{year_filter}-flomo-images")
    else:
        image_path = os.path.join(output_dir, IMAGE_SUBDIR_NAME)
    return os.path.exists(image_path) and os.listdir(image_path)

def create_and_send_response(output_dir, export_mode, year_filter, has_images, download_names):
    """创建并发送响应文件"""
    download_name, zip_download_name = download_names

    if export_mode == ExportMode.SINGLE_FILE:
        if has_images:
            # 有图片时返回 ZIP 压缩包
            output_zip = shutil.make_archive(os.path.join(tempfile.gettempdir(), 'flomo_output'), 'zip', output_dir)
            return send_file(output_zip, as_attachment=True, download_name=zip_download_name)
        else:
            # 无图片时直接返回 MD 文件
            md_path = os.path.join(output_dir, f"{year_filter}-flomo-output.md" if year_filter else MARKDOWN_FILENAME)
            temp_md_path = tempfile.mktemp(suffix='.md')
            shutil.copy(md_path, temp_md_path)
            return send_file(temp_md_path, as_attachment=True, download_name=download_name)
    else:
        # 其他模式总是返回 ZIP 压缩包
        zip_prefix = 'flomo_memos' if export_mode == ExportMode.SINGLE_MEMOS else 'flomo_archives'
        output_zip = shutil.make_archive(os.path.join(tempfile.gettempdir(), zip_prefix), 'zip', output_dir)
        return send_file(output_zip, as_attachment=True, download_name=zip_download_name)

@app.route('/', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def index():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected.')
                return redirect(request.url)

            file = request.files['file']
            source_dir = tempfile.mkdtemp(prefix='flomo_source_')

            try:
                # 处理文件上传
                success, error_msg = handle_file_upload(file, source_dir)
                if not success:
                    flash(error_msg)
                    return redirect(request.url)

                # 解析表单参数
                year_filter, export_mode = parse_form_parameters()

                # 执行转换
                output_dir = convert_notes(source_dir, year_filter=year_filter, export_mode=export_mode)

                if not output_dir:
                    flash('Conversion failed. No valid notes found.')
                    return redirect(request.url)

                # 获取所有年份信息（用于文件命名）
                all_years_for_naming = get_available_years(source_dir)

                # 检查是否有图片
                has_images = check_has_images(output_dir, year_filter)

                # 生成下载文件名
                download_names = generate_download_names(year_filter, all_years_for_naming, export_mode)

                # 创建并发送响应
                return create_and_send_response(output_dir, export_mode, year_filter, has_images, download_names)

            except Exception as e:
                logger.error(f'Conversion failed: {e}')
                flash('转换过程中发生错误。')
                return redirect(request.url)
            finally:
                cleanup_temp_dir(source_dir)

        except BadRequest:
            flash('文件过大（最大 50MB）。')
            return redirect(request.url)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='127.0.0.1')
