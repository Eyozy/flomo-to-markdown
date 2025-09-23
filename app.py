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
from converter import convert_notes, IMAGE_SUBDIR_NAME, MARKDOWN_FILENAME

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
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                is_html = filename.lower().endswith(('.html', '.htm'))
                # Create temp dir for source
                source_dir = tempfile.mkdtemp(prefix='flomo_source_')
                if is_html:
                    # Single HTML file
                    html_path = os.path.join(source_dir, filename)
                    file.save(html_path)
                    output_dir = convert_notes(source_dir)
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
                    output_dir = convert_notes(source_dir)
                else:
                    shutil.rmtree(source_dir)
                    flash('Invalid file type.')
                    return redirect(request.url)
                
                if output_dir:
                    image_path = os.path.join(output_dir, IMAGE_SUBDIR_NAME)
                    if is_html and os.path.exists(image_path) and not os.listdir(image_path):
                        shutil.rmtree(image_path)
                    if is_html:
                        md_path = os.path.join(output_dir, MARKDOWN_FILENAME)
                        temp_md_path = tempfile.mktemp(suffix='.md')
                        shutil.copy(md_path, temp_md_path)
                        shutil.rmtree(source_dir)
                        shutil.rmtree(output_dir)
                        return send_file(temp_md_path, as_attachment=True, download_name='flomo-output.md')
                    else:
                        output_zip = shutil.make_archive(os.path.join(tempfile.gettempdir(), 'flomo_output'), 'zip', output_dir)
                        shutil.rmtree(source_dir)
                        shutil.rmtree(output_dir)
                        return send_file(output_zip, as_attachment=True, download_name='flomo-converted.zip')
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
