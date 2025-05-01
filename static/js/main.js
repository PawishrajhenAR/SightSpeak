document.addEventListener('DOMContentLoaded', () => {
    // Mode switching
    const modeBtns = document.querySelectorAll('.mode-btn');
    const modeSections = document.querySelectorAll('.mode-section');
    let currentVideoStream = null;

    modeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            // Update active button
            modeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            // Show corresponding section
            modeSections.forEach(section => {
                if (section.id === mode + 'Mode') {
                    section.classList.remove('hidden');
                } else {
                    section.classList.add('hidden');
                }
            });
            // Stop any active video stream when switching modes
            stopVideoStream();
        });
    });

    // Image Mode
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const previewImage = document.getElementById('previewImage');
    const detectButton = document.getElementById('detectButton');
    const confidenceThreshold = document.getElementById('confidenceThreshold');
    const confidenceValue = document.getElementById('confidenceValue');
    const resultsSection = document.querySelector('.results-section');
    const resultImage = document.getElementById('resultImage');
    const detectionsList = document.getElementById('detectionsList');
    const loadingOverlay = document.querySelector('.loading-overlay');
    
    let currentImage = null;

    // Handle drag and drop events for image
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('active');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('active');
        });
    });

    // Handle file drop for image
    dropZone.addEventListener('drop', (e) => {
        const file = e.dataTransfer.files[0];
        handleImageFile(file);
    });

    // Handle file selection for image
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleImageFile(file);
    });

    // Handle confidence threshold changes
    confidenceThreshold.addEventListener('input', (e) => {
        const value = e.target.value / 100;
        confidenceValue.textContent = value.toFixed(2);
    });

    // Handle image file
    function handleImageFile(file) {
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                currentImage = e.target.result;
                previewImage.src = currentImage;
                previewImage.style.width = 'auto';
                previewImage.style.height = 'auto';
                previewImage.style.maxHeight = '300px';
                detectButton.disabled = false;
            };
            
            reader.readAsDataURL(file);
        }
    }

    // Image detection
    detectButton.addEventListener('click', async () => {
        if (!currentImage) return;

        try {
            loadingOverlay.style.display = 'flex';
            
            const response = await fetch('/detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image: currentImage,
                    confidence: parseFloat(confidenceValue.textContent)
                })
            });

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            displayResults(data);
        } catch (error) {
            alert('Error processing image: ' + error.message);
        } finally {
            loadingOverlay.style.display = 'none';
        }
    });

    // Display detection results
    function displayResults(data) {
        resultImage.src = data.annotated_image;
        
        // Group detections by class
        const groupedDetections = data.detections.reduce((acc, det) => {
            if (!acc[det.class]) {
                acc[det.class] = 0;
            }
            acc[det.class]++;
            return acc;
        }, {});

        // Clear previous results
        detectionsList.innerHTML = '';
        
        // Create detection items
        Object.entries(groupedDetections).forEach(([className, count]) => {
            const detectionItem = document.createElement('div');
            detectionItem.className = 'detection-item';
            detectionItem.innerHTML = `
                <strong>${className}</strong>: ${count}
            `;
            detectionsList.appendChild(detectionItem);
        });

        resultsSection.style.display = 'block';
    }

    // Video Mode
    const videoDropZone = document.getElementById('videoDropZone');
    const videoInput = document.getElementById('videoInput');
    const startVideoButton = document.getElementById('startVideoButton');
    const stopVideoButton = document.getElementById('stopVideoButton');
    const videoConfidenceThreshold = document.getElementById('videoConfidenceThreshold');
    const videoConfidenceValue = document.getElementById('videoConfidenceValue');
    let currentVideoFile = null;
    let currentVideoURL = null;

    // Handle drag and drop events for video
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        videoDropZone.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        videoDropZone.addEventListener(eventName, () => {
            videoDropZone.classList.add('active');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        videoDropZone.addEventListener(eventName, () => {
            videoDropZone.classList.remove('active');
        });
    });

    // Handle file drop for video
    videoDropZone.addEventListener('drop', (e) => {
        const file = e.dataTransfer.files[0];
        handleVideoFile(file);
    });

    // Handle file selection for video
    videoDropZone.addEventListener('click', () => {
        videoInput.click();
    });

    videoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleVideoFile(file);
    });

    videoConfidenceThreshold.addEventListener('input', (e) => {
        const value = e.target.value / 100;
        videoConfidenceValue.textContent = value.toFixed(2);
    });

    // Handle video file
    function handleVideoFile(file) {
        if (file && file.type.startsWith('video/')) {
            // Revoke previous URL if it exists
            if (currentVideoURL) {
                URL.revokeObjectURL(currentVideoURL);
            }
            currentVideoFile = file;
            currentVideoURL = URL.createObjectURL(file);
            startVideoButton.disabled = false;
            stopVideoButton.disabled = true;

            // Show preview of video in dropzone
            const previewVideo = document.createElement('video');
            previewVideo.src = currentVideoURL;
            previewVideo.style.maxHeight = '200px';
            previewVideo.style.maxWidth = '100%';
            previewVideo.controls = true;
            
            const dropZoneContent = videoDropZone.querySelector('.drop-zone-content');
            dropZoneContent.innerHTML = '';
            dropZoneContent.appendChild(previewVideo);
        }
    }

    // Video controls
    startVideoButton.addEventListener('click', async () => {
        if (!currentVideoFile) return;
        
        try {
            const formData = new FormData();
            formData.append('video', currentVideoFile);
            
            // First upload the video file
            const uploadResponse = await fetch('/upload_video', {
                method: 'POST',
                body: formData
            });
            
            const uploadResult = await uploadResponse.json();
            if (uploadResult.error) throw new Error(uploadResult.error);
            
            // Start video processing
            const response = await fetch('/start_video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    source: uploadResult.filename,
                    confidence: parseFloat(videoConfidenceValue.textContent)
                })
            });
            
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            
            currentVideoStream = data.stream_id;
            resultImage.src = `/video_feed/${data.stream_id}`;
            resultsSection.style.display = 'block';
            startVideoButton.disabled = true;
            stopVideoButton.disabled = false;
            
        } catch (error) {
            alert('Error starting video detection: ' + error.message);
        }
    });

    // Webcam Mode
    const startWebcamButton = document.getElementById('startWebcamButton');
    const stopWebcamButton = document.getElementById('stopWebcamButton');
    const webcamFeed = document.getElementById('webcamFeed');
    const webcamConfidenceThreshold = document.getElementById('webcamConfidenceThreshold');
    const webcamConfidenceValue = document.getElementById('webcamConfidenceValue');

    webcamConfidenceThreshold.addEventListener('input', (e) => {
        const value = e.target.value / 100;
        webcamConfidenceValue.textContent = value.toFixed(2);
    });

    // Webcam controls
    startWebcamButton.addEventListener('click', async () => {
        try {
            const response = await fetch('/start_video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    source: '0',
                    confidence: parseFloat(webcamConfidenceValue.textContent)
                })
            });

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            currentVideoStream = data.stream_id;
            webcamFeed.src = `/video_feed/${data.stream_id}`;
            webcamFeed.style.display = 'block';
            startWebcamButton.disabled = true;
            stopWebcamButton.disabled = false;

        } catch (error) {
            alert('Error starting webcam: ' + error.message);
        }
    });

    function stopVideoStream() {
        if (currentVideoStream) {
            fetch('/stop_video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    stream_id: currentVideoStream
                })
            }).catch(error => console.error('Error stopping video stream:', error));

            currentVideoStream = null;
            webcamFeed.style.display = 'none';
            startVideoButton.disabled = false;
            stopVideoButton.disabled = true;
            startWebcamButton.disabled = false;
            stopWebcamButton.disabled = true;
            resultsSection.style.display = 'none';
        }
    }

    stopVideoButton.addEventListener('click', stopVideoStream);
    stopWebcamButton.addEventListener('click', stopVideoStream);
});