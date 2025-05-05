// Webcam integration for visitor photo capture

let webcamElement = null;
let canvasElement = null;
let webcam = null;
let photoData = null;

function setupWebcam() {
    // Set up elements
    webcamElement = document.getElementById('webcam');
    canvasElement = document.getElementById('canvas');
    photoDataInput = document.getElementById('photo_data');
    capturedPhoto = document.getElementById('captured-photo');
    
    if (!webcamElement || !canvasElement) return;
    
    // Initialize webcam
    webcam = new Webcam(webcamElement, 'user', canvasElement);
    
    // Start webcam
    webcam.start()
        .then(result => {
            console.log("Webcam started");
        })
        .catch(err => {
            console.error("Error starting webcam:", err);
            displayWebcamError();
        });
        
    // Setup capture button
    const captureBtn = document.getElementById('capture-btn');
    const retakeBtn = document.getElementById('retake-btn');
    
    if (captureBtn) {
        captureBtn.addEventListener('click', function() {
            photoData = webcam.snap();
            displayCapturedPhoto(photoData);
            
            // Store in hidden input for form submission
            if (photoDataInput) {
                photoDataInput.value = photoData;
            }
        });
    }
    
    if (retakeBtn) {
        retakeBtn.addEventListener('click', function() {
            // Clear captured photo and show webcam again
            if (capturedPhoto) {
                capturedPhoto.style.display = 'none';
            }
            if (webcamElement) {
                webcamElement.style.display = 'block';
            }
            if (captureBtn) {
                captureBtn.style.display = 'inline-block';
            }
            this.style.display = 'none';
            
            // Clear photo data
            photoData = null;
            if (photoDataInput) {
                photoDataInput.value = '';
            }
        });
    }
}

function displayCapturedPhoto(photoData) {
    if (!capturedPhoto) return;
    
    // Display captured photo
    capturedPhoto.src = photoData;
    capturedPhoto.style.display = 'block';
    
    // Hide webcam
    if (webcamElement) {
        webcamElement.style.display = 'none';
    }
    
    // Toggle buttons
    const captureBtn = document.getElementById('capture-btn');
    const retakeBtn = document.getElementById('retake-btn');
    
    if (captureBtn) {
        captureBtn.style.display = 'none';
    }
    if (retakeBtn) {
        retakeBtn.style.display = 'inline-block';
    }
}

function displayWebcamError() {
    const webcamContainer = document.querySelector('.webcam-container');
    if (webcamContainer) {
        webcamContainer.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> Unable to access the webcam. Please make sure your camera is connected and you have granted permission.
            </div>
        `;
    }
}

function stopWebcam() {
    if (webcam) {
        webcam.stop();
    }
}

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only set up webcam if elements exist
    if (document.getElementById('webcam') && document.getElementById('canvas')) {
        setupWebcam();
    }
    
    // Clean up when leaving page
    window.addEventListener('beforeunload', function() {
        stopWebcam();
    });
});

// Webcam library - simplified version for this application
class Webcam {
    constructor(webcamElement, facingMode = 'user', canvasElement = null) {
        this._webcamElement = webcamElement;
        this._facingMode = facingMode;
        this._canvasElement = canvasElement;
    }

    start() {
        return new Promise((resolve, reject) => {
            this.stop();
            
            const constraints = {
                video: {
                    width: { ideal: 320 },
                    height: { ideal: 240 },
                    facingMode: this._facingMode
                }
            };
            
            navigator.mediaDevices.getUserMedia(constraints)
                .then(stream => {
                    this._webcamElement.srcObject = stream;
                    this._webcamElement.play();
                    resolve(this._webcamElement);
                })
                .catch(err => {
                    reject(err);
                });
        });
    }

    stop() {
        if (this._webcamElement && this._webcamElement.srcObject) {
            const tracks = this._webcamElement.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            this._webcamElement.srcObject = null;
        }
    }

    snap() {
        if (!this._canvasElement) {
            this._canvasElement = document.createElement('canvas');
        }
        
        // Set canvas dimensions to match webcam
        const width = this._webcamElement.videoWidth;
        const height = this._webcamElement.videoHeight;
        
        this._canvasElement.width = width;
        this._canvasElement.height = height;
        
        // Draw current frame to canvas
        const context = this._canvasElement.getContext('2d');
        context.drawImage(this._webcamElement, 0, 0, width, height);
        
        // Return data URL of the snapshot
        return this._canvasElement.toDataURL('image/png');
    }
}
