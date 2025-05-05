document.addEventListener('DOMContentLoaded', function() {
    // Timer to return to home screen after inactivity
    let inactivityTimer;
    const inactivityTimeout = 180000; // 3 minutes of inactivity
    
    // Start inactivity timer
    function startInactivityTimer() {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(returnToHome, inactivityTimeout);
    }
    
    // Return to kiosk home screen
    function returnToHome() {
        window.location.href = '/kiosk';
    }
    
    // Reset timer on user interaction
    function resetTimer() {
        startInactivityTimer();
    }
    
    // Add event listeners for user interaction
    document.addEventListener('touchstart', resetTimer);
    document.addEventListener('mousemove', resetTimer);
    document.addEventListener('mousedown', resetTimer);
    document.addEventListener('keypress', resetTimer);
    document.addEventListener('click', resetTimer);
    
    // Start the timer initially
    startInactivityTimer();
    
    // Exit passcode functionality
    const exitButton = document.getElementById('exit-kiosk-btn');
    const exitModal = document.getElementById('exitKioskModal');
    const passcodeInput = document.getElementById('kiosk-passcode');
    const exitForm = document.getElementById('exit-kiosk-form');
    
    if (exitButton && exitModal) {
        exitButton.addEventListener('click', function() {
            const modal = new bootstrap.Modal(exitModal);
            modal.show();
            
            if (passcodeInput) {
                passcodeInput.value = '';
                setTimeout(() => passcodeInput.focus(), 500);
            }
        });
    }
    
    // Set up fullscreen mode
    const enterFullscreenBtn = document.getElementById('enter-fullscreen');
    if (enterFullscreenBtn) {
        enterFullscreenBtn.addEventListener('click', function() {
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen();
            } else if (document.documentElement.mozRequestFullScreen) { // Firefox
                document.documentElement.mozRequestFullScreen();
            } else if (document.documentElement.webkitRequestFullscreen) { // Chrome, Safari & Opera
                document.documentElement.webkitRequestFullscreen();
            } else if (document.documentElement.msRequestFullscreen) { // IE/Edge
                document.documentElement.msRequestFullscreen();
            }
        });
    }
    
    // Clock update
    const clockElement = document.getElementById('kiosk-clock');
    if (clockElement) {
        function updateClock() {
            const now = new Date();
            const hours = now.getHours().toString().padStart(2, '0');
            const minutes = now.getMinutes().toString().padStart(2, '0');
            const seconds = now.getSeconds().toString().padStart(2, '0');
            const dateString = now.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            
            clockElement.innerHTML = `
                <div class="time">${hours}:${minutes}:${seconds}</div>
                <div class="date">${dateString}</div>
            `;
        }
        
        // Update clock immediately and then every second
        updateClock();
        setInterval(updateClock, 1000);
    }
    
    // Staff selection cards
    const staffCards = document.querySelectorAll('.staff-card');
    const staffIdInput = document.getElementById('staff_id');
    
    if (staffCards.length > 0 && staffIdInput) {
        staffCards.forEach(function(card) {
            card.addEventListener('click', function() {
                // Remove selected class from all cards
                staffCards.forEach(c => c.classList.remove('selected'));
                // Add selected class to clicked card
                this.classList.add('selected');
                // Update hidden input value
                staffIdInput.value = this.getAttribute('data-staff-id');
            });
        });
    }
    
    // Virtual keyboard for touch screens
    const useVirtualKeyboard = false; // Set to true to enable
    
    if (useVirtualKeyboard) {
        const textInputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"]');
        textInputs.forEach(function(input) {
            input.addEventListener('focus', function() {
                // Show virtual keyboard
                showVirtualKeyboard(this);
            });
        });
    }
    
    function showVirtualKeyboard(inputElement) {
        // This is a placeholder for a virtual keyboard implementation
        // You would typically use a library like simple-keyboard for this
        console.log('Virtual keyboard for:', inputElement.id);
    }
    
    // Setup webcam if on check-in page
    if (document.getElementById('webcam')) {
        setupWebcam();
    }
});
