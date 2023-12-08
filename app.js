function previewImage() {
    const imageInput = document.getElementById('imageInput');
    const imagePreview = document.getElementById('imagePreview');
    if (imageInput.files && imageInput.files[0]) {
        let reader = new FileReader();
        reader.onload = function (e) {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';
        };
        reader.readAsDataURL(imageInput.files[0]);
    }
}

async function sendImage() {
    const imageInput = document.getElementById('imageInput');
    if (imageInput.files.length === 0) {
        alert('Please select an image.');
        return;
    }

    const formData = new FormData();
    formData.append('file', imageInput.files[0]);

    try {
        const response = await axios.post('http://localhost:8000/recognize-face', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        document.getElementById('result').textContent = JSON.stringify(response.data);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('result').textContent = 'Error: ' + error.message;
    }
}
