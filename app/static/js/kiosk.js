/**
 * Kiosk Mode JavaScript
 * Visitor Management System
 */

document.addEventListener('DOMContentLoaded', function() {
    /**
     * Kiosk Fullscreen Mode
     */
    function toggleFullScreen() {
        if (!document.fullscreenElement &&
            !document.mozFullScreenElement &&
            !document.webkitFullscreenElement &&
            !document.msFullscreenElement) {
            
            // Enter fullscreen
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen();
            } else if (document.documentElement.msRequestFullscreen) {
                document.documentElement.msRequestFullscreen();
            } else if (document.documentElement.mozRequestFullScreen) {
                document.documentElement.mozRequestFullScreen();
            } else if (document.documentElement.webkitRequestFullscreen) {
                document.documentElement.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
            }
        } else {
            // Exit fullscreen
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            }
        }
    }

    // Add event listener to fullscreen button if it exists
    const fullscreenBtn = document.getElementById('enter-fullscreen');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', toggleFullScreen);
    }

    /**
     * Kiosk Clock
     */
    function updateClock() {
        const clockElement = document.getElementById('kiosk-clock');
        if (!clockElement) return;

        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const seconds = now.getSeconds().toString().padStart(2, '0');
        
        clockElement.textContent = `${hours}:${minutes}:${seconds}`;
    }

    // Initialize and update clock every second if it exists
    const clockElement = document.getElementById('kiosk-clock');
    if (clockElement) {
        updateClock();
        setInterval(updateClock, 1000);
    }

    /**
     * Form Validation Enhancements
     */
    const forms = document.querySelectorAll('.kiosk-form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
    
    /**
     * Auto-Focus First Form Field
     */
    const firstInput = document.querySelector('.kiosk-form input:not([type="hidden"]):first-of-type');
    if (firstInput) {
        firstInput.focus();
    }
    
    /**
     * Exit Kiosk Form Handling
     */
    const exitKioskForm = document.getElementById('exit-kiosk-form');
    if (exitKioskForm) {
        exitKioskForm.addEventListener('submit', function(event) {
            // Form submission is handled by the backend
            // This just ensures the form is properly validated client-side
            if (!exitKioskForm.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                exitKioskForm.classList.add('was-validated');
            }
        });
    }
    
    /**
     * Screen Timeout Detection & Reset
     * - Reset timeout on user interaction
     * - Redirect to main kiosk page after inactivity
     */
    let inactivityTimeout;
    const TIMEOUT_DURATION = 120000; // 2 minutes in milliseconds
    
    function resetInactivityTimer() {
        clearTimeout(inactivityTimeout);
        inactivityTimeout = setTimeout(redirectToHome, TIMEOUT_DURATION);
    }
    
    function redirectToHome() {
        // Only redirect if we're not already on the main page and we're in kiosk mode
        if (window.location.pathname.includes('/kiosk') && 
            !window.location.pathname.endsWith('/kiosk/') && 
            !window.location.pathname.endsWith('/kiosk')) {
            
            // Get org_id from URL if available
            const orgIdMatch = window.location.pathname.match(/\/org\/(\d+)/);
            const orgId = orgIdMatch ? orgIdMatch[1] : null;
            
            if (orgId) {
                window.location.href = `/kiosk/org/${orgId}`;
            } else {
                window.location.href = '/kiosk/';
            }
        }
    }
    
    // Set up initial timeout
    resetInactivityTimer();
    
    // Reset timer on user interaction
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, resetInactivityTimer, true);
    });
});