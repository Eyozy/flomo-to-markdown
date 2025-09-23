document.getElementById('file').addEventListener('change', function(e) {
    const fileName = e.target.files[0]?.name || '';
    const fileNameDiv = document.getElementById('file-name');
    if (fileName) {
        fileNameDiv.textContent = `已选择：${fileName}`;
        fileNameDiv.style.display = 'block';
    } else {
        fileNameDiv.style.display = 'none';
    }
});
