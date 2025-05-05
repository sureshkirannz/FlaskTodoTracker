/**
 * Main JavaScript for Visitor Management System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Webcam functionality for visitor check-in (if enabled)
    initWebcam();
    
    // Dashboard charts (if on dashboard page)
    initDashboardCharts();
    
    // Staff dropdown in visitor check-in form
    initStaffDropdown();
});

/**
 * Initialize webcam capture for visitor photos
 */
function initWebcam() {
    const webcamElement = document.getElementById('webcam');
    const canvasElement = document.getElementById('canvas');
    const captureButton = document.getElementById('capture-photo');
    const retakeButton = document.getElementById('retake-photo');
    const photoInput = document.getElementById('photo-data');
    
    if (!webcamElement || !canvasElement) {
        return;
    }
    
    let webcam = null;
    
    // Initialize the webcam
    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        .then(function(stream) {
            webcamElement.srcObject = stream;
            webcam = stream;
            
            // Show webcam container
            document.querySelector('.webcam-container').classList.remove('d-none');
        })
        .catch(function(err) {
            console.error("Error accessing webcam:", err);
            document.querySelector('.webcam-error').classList.remove('d-none');
        });
    
    // Capture photo
    if (captureButton) {
        captureButton.addEventListener('click', function() {
            // Draw the video frame to the canvas
            const context = canvasElement.getContext('2d');
            context.drawImage(webcamElement, 0, 0, canvasElement.width, canvasElement.height);
            
            // Convert canvas to data URL and store in hidden input
            const dataUrl = canvasElement.toDataURL('image/png');
            photoInput.value = dataUrl;
            
            // Show captured photo and retake button
            webcamElement.classList.add('d-none');
            canvasElement.classList.remove('d-none');
            captureButton.classList.add('d-none');
            retakeButton.classList.remove('d-none');
        });
    }
    
    // Retake photo
    if (retakeButton) {
        retakeButton.addEventListener('click', function() {
            // Clear canvas and photo input
            const context = canvasElement.getContext('2d');
            context.clearRect(0, 0, canvasElement.width, canvasElement.height);
            photoInput.value = '';
            
            // Show webcam and capture button again
            webcamElement.classList.remove('d-none');
            canvasElement.classList.add('d-none');
            captureButton.classList.remove('d-none');
            retakeButton.classList.add('d-none');
        });
    }
}

/**
 * Initialize dashboard charts
 */
function initDashboardCharts() {
    const visitorsChartElement = document.getElementById('visitorsChart');
    const purposeChartElement = document.getElementById('purposeChart');
    const staffChartElement = document.getElementById('staffChart');
    
    if (!visitorsChartElement) {
        return;
    }
    
    // Load chart data from API
    fetch('/reports/visitor-stats?days=30')
        .then(response => response.json())
        .then(data => {
            // Visitors chart (line chart)
            createVisitorsChart(visitorsChartElement, data.daily);
            
            // Purpose chart (doughnut chart)
            if (purposeChartElement && data.purposes.length > 0) {
                createPurposeChart(purposeChartElement, data.purposes);
            }
            
            // Staff chart (bar chart)
            if (staffChartElement && data.staff.length > 0) {
                createStaffChart(staffChartElement, data.staff);
            }
        })
        .catch(error => console.error('Error loading chart data:', error));
}

/**
 * Create visitors line chart
 */
function createVisitorsChart(element, data) {
    const labels = data.map(item => item.date);
    const counts = data.map(item => item.count);
    
    new Chart(element, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Visitors',
                data: counts,
                borderColor: 'rgba(13, 110, 253, 1)',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Visitor Check-ins (Last 30 Days)'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

/**
 * Create purpose doughnut chart
 */
function createPurposeChart(element, data) {
    const labels = data.map(item => item.purpose);
    const counts = data.map(item => item.count);
    
    new Chart(element, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                label: 'Visitors',
                data: counts,
                backgroundColor: [
                    'rgba(13, 110, 253, 0.8)',
                    'rgba(220, 53, 69, 0.8)',
                    'rgba(25, 135, 84, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(108, 117, 125, 0.8)'
                ],
                borderColor: 'rgba(33, 37, 41, 0.2)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                title: {
                    display: true,
                    text: 'Visit Purposes'
                }
            }
        }
    });
}

/**
 * Create staff bar chart
 */
function createStaffChart(element, data) {
    const labels = data.map(item => item.name);
    const counts = data.map(item => item.count);
    
    new Chart(element, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Visitors',
                data: counts,
                backgroundColor: 'rgba(13, 110, 253, 0.8)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Most Visited Staff'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

/**
 * Initialize staff dropdown with additional information
 */
function initStaffDropdown() {
    const staffSelect = document.getElementById('staff_id');
    const staffInfoContainer = document.getElementById('staff-info');
    
    if (!staffSelect || !staffInfoContainer) {
        return;
    }
    
    // Update staff info when selection changes
    staffSelect.addEventListener('change', function() {
        const staffId = this.value;
        if (!staffId) {
            staffInfoContainer.classList.add('d-none');
            return;
        }
        
        const orgId = document.querySelector('meta[name="organization-id"]').getAttribute('content');
        
        // Fetch staff details
        fetch(`/kiosk/${orgId}/staff/${staffId}`)
            .then(response => response.json())
            .then(staff => {
                // Update staff info display
                let infoHtml = `
                    <div class="card mt-3">
                        <div class="card-body d-flex">
                `;
                
                if (staff.photo) {
                    infoHtml += `
                        <div class="me-3">
                            <img src="data:image/png;base64,${staff.photo}" alt="${staff.first_name} ${staff.last_name}" 
                                class="staff-photo" style="width: 64px; height: 64px; border-radius: 50%;">
                        </div>
                    `;
                }
                
                infoHtml += `
                        <div>
                            <h5 class="card-title">${staff.first_name} ${staff.last_name}</h5>
                            <p class="card-text mb-0">${staff.position || 'Staff'}</p>
                            <p class="card-text text-muted">${staff.department || ''}</p>
                        </div>
                        </div>
                    </div>
                `;
                
                staffInfoContainer.innerHTML = infoHtml;
                staffInfoContainer.classList.remove('d-none');
            })
            .catch(error => {
                console.error('Error fetching staff details:', error);
                staffInfoContainer.classList.add('d-none');
            });
    });
}