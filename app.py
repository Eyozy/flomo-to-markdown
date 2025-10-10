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
from converter import convert_notes, IMAGE_SUBDIR_NAME, MARKDOWN_FILENAME, get_available_years, contains_images

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

@app.route('/parse-years', methods=['POST'])
@limiter.limit("10 per minute")
def parse_years():
    """解析上传文件中的年份信息"""
    try:
        if 'file' not in request.files:
            return {'error': 'No file selected.'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'error': 'No file selected.'}, 400
        
        if not (file and allowed_file(file.filename)):
            return {'error': 'File type not allowed.'}, 400
        
        filename = secure_filename(file.filename)
        is_html = filename.lower().endswith(('.html', '.htm'))
        
        # Create temp dir for source
        source_dir = tempfile.mkdtemp(prefix='flomo_parse_')
        
        try:
            if is_html:
                # Single HTML file
                html_path = os.path.join(source_dir, filename)
                file.save(html_path)
            elif filename.lower().endswith('.zip'):
                # ZIP file
                zip_path = os.path.join(source_dir, filename)
                file.save(zip_path)
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(source_dir)
                    logger.info('ZIP extracted successfully')
                except zipfile.BadZipFile:
                    logger.error('Invalid ZIP file')
                    shutil.rmtree(source_dir)
                    return {'error': '无效 ZIP 文件。'}, 400
                except Exception as e:
                    logger.error(f'ZIP extraction failed: {e}')
                    shutil.rmtree(source_dir)
                    return {'error': 'ZIP 解压失败。'}, 400
                # Remove the zip file itself
                os.remove(zip_path)
            
            # Get available years
            years = get_available_years(source_dir)
            
            # Clean up
            shutil.rmtree(source_dir)
            
            if years:
                return {'years': years, 'success': True}
            else:
                return {'error': '未找到任何有效的笔记数据。'}, 400
                
        except Exception as e:
            logger.error(f'Parse years failed: {e}')
            shutil.rmtree(source_dir, ignore_errors=True)
            return {'error': '解析文件时发生错误。'}, 500
            
    except BadRequest:
        return {'error': '文件过大（最大 50MB）。'}, 400

@app.route('/', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def index():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected.')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash('No file selected.')
                return redirect(request.url)
            
            # Get year filter from form
            year_filter = request.form.get('year_filter')
            if year_filter and year_filter != 'all':
                try:
                    year_filter = int(year_filter)
                except ValueError:
                    year_filter = None
            else:
                year_filter = None
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                is_html = filename.lower().endswith(('.html', '.htm'))
                # Create temp dir for source
                source_dir = tempfile.mkdtemp(prefix='flomo_source_')
                if is_html:
                    # Single HTML file
                    html_path = os.path.join(source_dir, filename)
                    file.save(html_path)
                    output_dir = convert_notes(source_dir, year_filter=year_filter)
                elif filename.lower().endswith('.zip'):
                    # ZIP file
                    zip_path = os.path.join(source_dir, filename)
                    file.save(zip_path)
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(source_dir)
                        logger.info('ZIP extracted successfully')
                    except zipfile.BadZipFile:
                        logger.error('Invalid ZIP file')
                        shutil.rmtree(source_dir)
                        flash('无效 ZIP 文件。')
                        return redirect(request.url)
                    except Exception as e:
                        logger.error(f'ZIP extraction failed: {e}')
                        shutil.rmtree(source_dir)
                        flash('ZIP 解压失败。')
                        return redirect(request.url)
                    # Remove the zip file itself
                    os.remove(zip_path)
                    output_dir = convert_notes(source_dir, year_filter=year_filter)
                else:
                    shutil.rmtree(source_dir)
                    flash('Invalid file type.')
                    return redirect(request.url)
                
                if output_dir:
                    # 检查输出目录中是否包含图片
                    has_images = False
                    if year_filter:
                        image_path = os.path.join(output_dir, f"{year_filter}-flomo-images")
                        has_images = os.path.exists(image_path) and os.listdir(image_path)
                    else:
                        image_path = os.path.join(output_dir, IMAGE_SUBDIR_NAME)
                        has_images = os.path.exists(image_path) and os.listdir(image_path)
                    
                    # Get all years for range filename BEFORE source_dir is cleaned up
                    all_years_for_naming = get_available_years(source_dir)

                    # Generate filename based on year filter
                    if year_filter:
                        download_name = f'{year_filter}-flomo-output.md'
                        if has_images:
                            zip_download_name = f'{year_filter}-flomo-output.zip'
                    else:
                        if len(all_years_for_naming) > 1:
                            download_name = f'{all_years_for_naming[0]}-{all_years_for_naming[-1]}-flomo-output.md'
                            zip_download_name = f'{all_years_for_naming[0]}-{all_years_for_naming[-1]}-flomo-output.zip'
                        elif all_years_for_naming:
                            download_name = f'{all_years_for_naming[0]}-flomo-output.md'
                            zip_download_name = f'{all_years_for_naming[0]}-flomo-output.zip'
                        else:
                            download_name = 'flomo-output.md'
                            zip_download_name = 'flomo-output.zip'
                    
                    # 根据是否有图片和年份过滤决定输出格式
                    if year_filter and not has_images:
                        # 特定年份且无图片，返回单个 MD 文件
                        md_path = os.path.join(output_dir, f"{year_filter}-flomo-output.md")
                        temp_md_path = tempfile.mktemp(suffix='.md')
                        shutil.copy(md_path, temp_md_path)
                        shutil.rmtree(source_dir)
                        shutil.rmtree(output_dir)
                        return send_file(temp_md_path, as_attachment=True, download_name=download_name)
                    elif is_html and not has_images: # 确保单个 HTML 文件且无图片时返回 MD
                        # 单个 HTML 文件，返回 MD 文件
                        md_path = os.path.join(output_dir, MARKDOWN_FILENAME)
                        temp_md_path = tempfile.mktemp(suffix='.md')
                        shutil.copy(md_path, temp_md_path)
                        shutil.rmtree(source_dir)
                        shutil.rmtree(output_dir)
                        return send_file(temp_md_path, as_attachment=True, download_name=download_name)
                    else:
                        # ZIP 文件或包含图片的情况，返回 ZIP 压缩包
                        output_zip = shutil.make_archive(os.path.join(tempfile.gettempdir(), 'flomo_output'), 'zip', output_dir)
                        shutil.rmtree(source_dir)
                        shutil.rmtree(output_dir)
                        return send_file(output_zip, as_attachment=True, download_name=zip_download_name)
                else:
                    shutil.rmtree(source_dir)
                    flash('Conversion failed. No valid notes found.')
                    return redirect(request.url)
            else:
                flash('File type not allowed.')
                return redirect(request.url)
        except BadRequest:
            flash('文件过大（最大 50MB）。')
            return redirect(request.url)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='127.0.0.1')
