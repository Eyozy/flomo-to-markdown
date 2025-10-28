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
    const yearSelection = document.getElementById('year-selection');
    const yearFilter = document.getElementById('year-filter');
    const convertBtn = document.getElementById('convert-btn');

    // 隐藏年份选择
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
            // 显示成功 toast 消息
            showToast(`文件解析成功！发现 ${result.years.length} 个年份的笔记`, 'success', 4000);

            // 显示导出模式选择器
            document.getElementById('export-mode-selection').style.display = 'block';

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
        } else {
            // 显示错误 toast 消息
            showToast(result.error || '解析文件时发生错误', 'error', 5000);

            // 重置转换按钮状态
            convertBtn.disabled = false;
            convertBtn.textContent = '转换并下载';

            // 5 秒后重置文件选择
            setTimeout(() => {
                resetFileSelection();
            }, 5000);
        }
    } catch (error) {
        console.error('解析年份时发生错误：', error);

        // 隐藏加载动画和进度条
        loadingIndicator.style.display = 'none';
        progressContainer.style.display = 'none';
        updateProgress(0, '');

        // 显示网络错误 toast 消息
        showToast('网络错误，请重试', 'error', 5000);

        // 重置转换按钮状态
        convertBtn.disabled = false;
        convertBtn.textContent = '转换并下载';

        // 5 秒后重置文件选择
        setTimeout(() => {
            resetFileSelection();
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

function resetFileSelection() {
    const fileInput = document.getElementById('file');
    const fileNameDiv = document.getElementById('file-name');
    const yearSelection = document.getElementById('year-selection');
    const exportModeSelection = document.getElementById('export-mode-selection');
    const convertBtn = document.getElementById('convert-btn');

    // 重置文件输入
    fileInput.value = '';
    fileNameDiv.style.display = 'none';
    yearSelection.style.display = 'none';
    exportModeSelection.style.display = 'none';
    convertBtn.disabled = true;
    convertBtn.textContent = '转换并下载';

    // 隐藏加载指示器
    document.getElementById('loading-indicator').style.display = 'none';
}

// 页面加载时检查是否有 Flash 消息
document.addEventListener('DOMContentLoaded', function() {
    const alertDiv = document.querySelector('.alert');
    if (alertDiv) {
        const message = alertDiv.textContent.trim();
        // 隐藏 Flash 消息，用 toast 代替
        alertDiv.style.display = 'none';
        showToast(message, 'error', 5000);
    }
});

// 表单提交前的额外验证
document.getElementById('convert-form').addEventListener('submit', function(e) {
    const fileInput = document.getElementById('file');
    const yearSelection = document.getElementById('year-selection');

    // 如果没有选择文件，阻止提交
    if (!fileInput.files[0]) {
        e.preventDefault();
        showToast('请先选择文件', 'error');
        return;
    }

    // 如果显示了年份选择但没有选择年份，提示用户
    if (yearSelection.style.display === 'block' && !document.getElementById('year-filter').value) {
        e.preventDefault();
        showToast('请选择年份', 'error');
        return;
    }
});

// ========== Toast 消息系统 ==========

/**
 * 显示 Toast 消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型：'success', 'error', 'info'
 * @param {number} duration - 显示时长（毫秒），默认 5000ms
 * @returns {Object} Toast 对象，包含手动关闭的方法
 */
function showToast(message, type = 'info', duration = 5000) {
    // 创建 toast 元素
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    // 设置图标
    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️'
    };

    // 创建 toast 内容
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-message">${message}</div>
        <button class="toast-close" aria-label="关闭">×</button>
        <div class="toast-progress"></div>
    `;

    // 添加到容器
    const container = document.getElementById('toast-container');
    container.appendChild(toast);

    // 显示动画
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    // 设置进度条动画
    const progressBar = toast.querySelector('.toast-progress');
    if (progressBar && duration > 0) {
        progressBar.style.transition = `width ${duration}ms linear`;
        requestAnimationFrame(() => {
            progressBar.style.width = '0%';
        });
    }

    // 关闭按钮事件
    const closeBtn = toast.querySelector('.toast-close');
    const closeToast = () => {
        hideToast(toast);
    };

    closeBtn.addEventListener('click', closeToast);

    // 自动关闭
    let timeoutId;
    if (duration > 0) {
        timeoutId = setTimeout(() => {
            hideToast(toast);
        }, duration);
    }

    // 返回 toast 对象，包含手动关闭方法
    return {
        element: toast,
        close: closeToast,
        updateMessage: (newMessage) => {
            const messageEl = toast.querySelector('.toast-message');
            if (messageEl) {
                messageEl.textContent = newMessage;
            }
        },
        updateType: (newType) => {
            toast.className = `toast ${newType}`;
            const iconEl = toast.querySelector('.toast-icon');
            if (iconEl) {
                iconEl.textContent = icons[newType] || icons.info;
            }
        }
    };
}

/**
 * 隐藏 Toast 消息
 * @param {HTMLElement} toast - Toast 元素
 */
function hideToast(toast) {
    if (!toast || !toast.parentNode) return;

    toast.classList.add('hide');

    // 动画结束后移除元素
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

/**
 * 清除所有 Toast 消息
 */
function clearAllToasts() {
    const container = document.getElementById('toast-container');
    const toasts = container.querySelectorAll('.toast');
    toasts.forEach(toast => hideToast(toast));
}

/**
 * 更新现有的 showError 函数以使用 Toast
 */
function showErrorWithToast(message) {
    showToast(message, 'error', 5000);
}

/**
 * 更新现有的 showSuccess 函数以使用 Toast
 */
function showSuccessWithToast(message) {
    showToast(message, 'success', 3000);
}

/**
 * 显示信息消息
 */
function showInfoWithToast(message) {
    showToast(message, 'info', 4000);
}
