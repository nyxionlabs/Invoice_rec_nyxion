document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const uploadResult = document.getElementById('uploadResult');

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const file = fileInput.files[0];
            if (!file) {
                showResult('Please select a file', false);
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            showResult('Processing invoice with AI...', true, true);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const result = data.data;
                    showResult(`
                        <strong>✅ Processing Complete!</strong><br>
                        <strong>Vendor:</strong> ${result.vendor_name}<br>
                        <strong>Amount:</strong> $${result.total_amount.toFixed(2)}<br>
                        <strong>Confidence:</strong> ${(result.confidence_score * 100).toFixed(1)}%<br>
                        <strong>Processing Time:</strong> ${result.processing_time}s
                    `, true);

                    // Reload page after 3 seconds to show new invoice in table
                    setTimeout(() => {
                        location.reload();
                    }, 3000);
                } else {
                    showResult(`❌ Error: ${data.error}`, false);
                }
            })
            .catch(error => {
                showResult(`❌ Network Error: ${error.message}`, false);
            });
        });
    }

    function showResult(message, success, loading = false) {
        if (uploadResult) {
            uploadResult.style.display = 'block';
            uploadResult.innerHTML = message;
            uploadResult.className = loading ? '' : (success ? 'success' : 'error');
        }
    }

    // File input change handler
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const uploadArea = document.querySelector('.upload-area .upload-content');
                if (uploadArea) {
                    uploadArea.innerHTML = `
                        <p><strong>File Selected:</strong> ${file.name}</p>
                        <p>Ready to process!</p>
                    `;
                }
            }
        });
    }
});