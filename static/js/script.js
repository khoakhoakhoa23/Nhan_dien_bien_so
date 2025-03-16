document.getElementById('capture-entry').addEventListener('click', () => {
    fetch('/capture_entry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        const resultElement = document.getElementById('entry-result');
        if (data.status === 'success') {
            resultElement.textContent = `Xe vào: ${data.license_plate} - Lưu thành công!`;
            resultElement.style.color = 'green';
            // Tải lại trang để cập nhật danh sách xe
            setTimeout(() => location.reload(), 1000);
        } else {
            resultElement.textContent = data.message;
            resultElement.style.color = 'red';
        }
    })
    .catch(error => {
        document.getElementById('entry-result').textContent = 'Lỗi: ' + error;
    });
});

document.getElementById('capture-exit').addEventListener('click', () => {
    fetch('/capture_exit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        const resultElement = document.getElementById('exit-result');
        if (data.status === 'success') {
            resultElement.textContent = `Xe ra: ${data.license_plate} - Thời gian gửi: ${data.duration}`;
            resultElement.style.color = 'green';
            setTimeout(() => location.reload(), 1000);
        } else {
            resultElement.textContent = data.message;
            resultElement.style.color = 'red';
        }
    })
    .catch(error => {
        document.getElementById('exit-result').textContent = 'Lỗi: ' + error;
    });
});