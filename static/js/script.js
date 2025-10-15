// 拖拽上传功能
const uploadArea = document.querySelector('.upload-area');
const fileInput = document.getElementById('file');

// 防止浏览器默认拖拽行为
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    uploadArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, unhighlight, false);
});

function highlight() {
    uploadArea.classList.add('dragover');
}

function unhighlight() {
    uploadArea.classList.remove('dragover');
}

// 处理拖拽文件
uploadArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length > 0) {
        fileInput.files = files;
        handleFileSelection(files[0]);
    }
}

// 点击上传区域也可以触发文件选择
uploadArea.addEventListener('click', (e) => {
    // 确保不是点击在文件输入本身上
    if (e.target !== fileInput) {
        fileInput.click();
    }
});

// 文件选择变化事件
fileInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        handleFileSelection(file);
    }
});

function handleFileSelection(file) {
    const fileName = file.name;
    const fileNameDiv = document.getElementById('file-name');
    const yearSelection = document.getElementById('year-selection');
    const convertBtn = document.getElementById('convert-btn');

    // 检查文件类型
    const allowedTypes = ['.html', '.htm', '.zip'];
    const fileExtension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'));

    if (!allowedTypes.includes(fileExtension)) {
        showError(`不支持的文件类型：${fileExtension}。请上传 .html, .htm 或 .zip 文件。`);
        resetFileSelection();
        return;
    }

    // 检查文件大小 (50MB)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
        showError(`文件太大：${(file.size / 1024 / 1024).toFixed(2)}MB。最大支持 50MB。`);
        resetFileSelection();
        return;
    }

    fileNameDiv.textContent = `已选择：${fileName}`;
    fileNameDiv.style.display = 'block';

    // 禁用转换按钮，等待文件解析完成
    convertBtn.disabled = true;
    convertBtn.textContent = '解析中...';

    // 解析文件中的年份信息
    parseYearsFromFile(file);
}

async function parseYearsFromFile(file) {
    const loadingIndicator = document.getElementById('loading-indicator');
    const loadingText = document.getElementById('loading-text');
    const progressContainer = document.querySelector('.progress-bar-container');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');
    const yearSelection = document.getElementById('year-selection');
    const yearFilter = document.getElementById('year-filter');
    const convertBtn = document.getElementById('convert-btn');
    const errorText = document.getElementById('error-text');

    // 隐藏所有消息和年份选择
    hideAllMessages();
    yearSelection.style.display = 'none';

    // 显示加载动画和进度条
    loadingIndicator.style.display = 'flex';
    progressContainer.style.display = 'block';
    convertBtn.disabled = true;

    // 模拟进度更新
    updateProgress(0, '正在准备上传...');

    const formData = new FormData();
    formData.append('file', file);

    try {
        updateProgress(20, '正在上传文件...');

        const response = await fetch('/parse-years', {
            method: 'POST',
            body: formData
        });

        updateProgress(60, '正在解析文件内容...');

        const result = await response.json();

        updateProgress(90, '正在生成年份选项...');

        // 隐藏加载动画和进度条
        setTimeout(() => {
            loadingIndicator.style.display = 'none';
            progressContainer.style.display = 'none';
            updateProgress(0, '');
        }, 500);

        if (result.success && result.years) {
            // 显示成功消息
            successMessage.style.display = 'flex';

            // 生成年份选项
            let options = '<option value="all">全部</option>';
            result.years.forEach(year => {
                options += `<option value="${year}">${year}</option>`;
            });
            yearFilter.innerHTML = options;
            yearSelection.style.display = 'block';

            // 启用转换按钮
            convertBtn.disabled = false;
            convertBtn.textContent = '转换并下载';

            // 3 秒后隐藏成功消息
            setTimeout(() => {
                successMessage.classList.add('fade-out');
                setTimeout(() => {
                    successMessage.style.display = 'none';
                    successMessage.classList.remove('fade-out');
                }, 300);
            }, 3000);
        } else {
            // 显示错误消息
            errorText.textContent = result.error || '解析文件时发生错误';
            errorMessage.style.display = 'flex';

            // 重置转换按钮状态
            convertBtn.disabled = false;
            convertBtn.textContent = '转换并下载';

            // 5 秒后隐藏错误消息并重置文件选择
            setTimeout(() => {
                errorMessage.classList.add('fade-out');
                setTimeout(() => {
                    errorMessage.style.display = 'none';
                    errorMessage.classList.remove('fade-out');
                    resetFileSelection();
                }, 300);
            }, 5000);
        }
    } catch (error) {
        console.error('解析年份时发生错误：', error);

        // 隐藏加载动画和进度条
        loadingIndicator.style.display = 'none';
        progressContainer.style.display = 'none';
        updateProgress(0, '');

        // 显示网络错误
        errorText.textContent = '网络错误，请重试';
        errorMessage.style.display = 'flex';

        // 重置转换按钮状态
        convertBtn.disabled = false;
        convertBtn.textContent = '转换并下载';

        // 5 秒后隐藏错误消息并重置文件选择
        setTimeout(() => {
            errorMessage.classList.add('fade-out');
            setTimeout(() => {
                errorMessage.style.display = 'none';
                errorMessage.classList.remove('fade-out');
                resetFileSelection();
            }, 300);
        }, 5000);
    }
}

function updateProgress(percent, text) {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const loadingText = document.getElementById('loading-text');

    if (progressFill) {
        progressFill.style.width = percent + '%';
    }

    if (progressText) {
        progressText.textContent = percent + '%';
    }

    if (loadingText && text) {
        loadingText.textContent = text;
    }
}

function hideAllMessages() {
    document.getElementById('loading-indicator').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';
    document.getElementById('success-message').style.display = 'none';
}

function resetFileSelection() {
    const fileInput = document.getElementById('file');
    const fileNameDiv = document.getElementById('file-name');
    const yearSelection = document.getElementById('year-selection');
    const convertBtn = document.getElementById('convert-btn');

    // 重置文件输入
    fileInput.value = '';
    fileNameDiv.style.display = 'none';
    yearSelection.style.display = 'none';
    convertBtn.disabled = true;
    convertBtn.textContent = '转换并下载';

    // 隐藏所有消息
    hideAllMessages();
}

function showError(message) {
    hideAllMessages();
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');

    errorText.textContent = message;
    errorMessage.style.display = 'flex';

    // 5 秒后自动隐藏
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

// 页面加载时检查是否有Flash消息
document.addEventListener('DOMContentLoaded', function() {
    const alertDiv = document.querySelector('.alert');
    if (alertDiv) {
        const message = alertDiv.textContent.trim();
        // 隐藏Flash消息，用我们的错误显示代替
        alertDiv.style.display = 'none';
        showError(message);
    }
});

// 表单提交前的额外验证
document.getElementById('convert-form').addEventListener('submit', function(e) {
    const fileInput = document.getElementById('file');
    const yearSelection = document.getElementById('year-selection');

    // 如果没有选择文件，阻止提交
    if (!fileInput.files[0]) {
        e.preventDefault();
        showError('请先选择文件');
        return;
    }

    // 如果显示了年份选择但没有选择年份，提示用户
    if (yearSelection.style.display === 'block' && !document.getElementById('year-filter').value) {
        e.preventDefault();
        showError('请选择年份');
        return;
    }
});
