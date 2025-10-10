document.getElementById('file').addEventListener('change', function(e) {
    const fileName = e.target.files[0]?.name || '';
    const fileNameDiv = document.getElementById('file-name');
    const yearSelection = document.getElementById('year-selection');
    const convertBtn = document.getElementById('convert-btn');
    
    if (fileName) {
        fileNameDiv.textContent = `已选择：${fileName}`;
        fileNameDiv.style.display = 'block';
        
        // 解析文件中的年份信息
        parseYearsFromFile(e.target.files[0]);
    } else {
        fileNameDiv.style.display = 'none';
        yearSelection.style.display = 'none';
        convertBtn.disabled = true;
    }
});

async function parseYearsFromFile(file) {
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');
    const yearSelection = document.getElementById('year-selection');
    const yearFilter = document.getElementById('year-filter');
    const convertBtn = document.getElementById('convert-btn');
    const errorText = document.getElementById('error-text');
    
    // 隐藏所有消息和年份选择
    hideAllMessages();
    yearSelection.style.display = 'none';
    
    // 显示加载动画
    loadingIndicator.style.display = 'flex';
    convertBtn.disabled = true;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/parse-years', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        // 隐藏加载动画
        loadingIndicator.style.display = 'none';
        
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
            convertBtn.disabled = false;
            
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
            convertBtn.disabled = false;
            
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
        
        // 隐藏加载动画
        loadingIndicator.style.display = 'none';
        
        // 显示网络错误
        errorText.textContent = '网络错误，请重试';
        errorMessage.style.display = 'flex';
        convertBtn.disabled = false;
        
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
