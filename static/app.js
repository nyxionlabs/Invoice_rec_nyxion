document.getElementById('uploadForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const resultDiv = document.getElementById('result');
    const file = fileInput.files[0];

    if (!file) {
        showResult('Please select a file', false);
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    // Show loading
    showResult('Processing invoice...', true, true);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showResult(`Successfully processed invoice! 
                Vendor: ${data.data.vendor_name || 'N/A'} 
                Amount: $${data.data.total_amount || 0} 
                Confidence: ${Math.round((data.data.confidence_score || 0) * 100)}%`, true);

            // Reload page after 2 seconds to show new invoice in table
            setTimeout(() => location.reload(), 2000);
        } else {
            showResult(`Error: ${data.error}`, false);
        }
    })
    .catch(error => {
        showResult(`Error: ${error.message}`, false);
    });
});

function showResult(message, success, loading = false) {
    const resultDiv = document.getElementById('result');
    resultDiv.style.display = 'block';
    resultDiv.textContent = message;
    resultDiv.className = loading ? '' : (success ? 'success' : 'error');
}