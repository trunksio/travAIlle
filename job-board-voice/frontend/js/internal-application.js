// Internal Application Page with AI Assistant Integration

const BACKEND_URL = window.BACKEND_URL || 'http://localhost:5010';
let websocket = null;
let sessionId = null;
let jobId = null;

// Initialize application page
async function initializeApplication() {
    // Get job info from session storage
    jobId = sessionStorage.getItem('selectedJobId');
    const jobTitle = sessionStorage.getItem('selectedJobTitle');
    const department = sessionStorage.getItem('selectedDepartment');
    
    if (!jobId) {
        // If no job selected, redirect to home
        window.location.href = 'index.html';
        return;
    }
    
    // Update page with job info
    document.getElementById('jobTitle').textContent = jobTitle;
    document.getElementById('jobDepartment').textContent = department;
    
    // Create application session
    await createApplicationSession();
    
    // Connect WebSocket for real-time updates
    connectWebSocket();
    
    // Setup form submission
    setupFormSubmission();
    
    // Monitor AI-assisted fields
    monitorProgress();
}

// Create a new application session
async function createApplicationSession() {
    try {
        const response = await fetch(`${BACKEND_URL}/api/sessions/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                job_id: jobId,
                user_agent: navigator.userAgent
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to create session');
        }
        
        const data = await response.json();
        sessionId = data.session_id;
        
        // Store session ID for the AI assistant
        document.getElementById('sessionId').value = sessionId;
        window.APPLICATION_SESSION_ID = sessionId;
        window.SELECTED_JOB_ID = jobId;
        
        console.log('Application session created:', sessionId);
        
    } catch (error) {
        console.error('Error creating session:', error);
        showNotification('Failed to initialize application. Please refresh and try again.', 'error');
    }
}

// Connect WebSocket for real-time form updates
function connectWebSocket() {
    if (!sessionId) return;
    
    const wsUrl = BACKEND_URL.replace('http://', 'ws://').replace('https://', 'wss://');
    websocket = new WebSocket(`${wsUrl}/ws/${sessionId}`);
    
    websocket.onopen = () => {
        console.log('WebSocket connected for real-time updates');
    };
    
    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleRealtimeUpdate(data);
    };
    
    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    websocket.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
            if (sessionId) {
                connectWebSocket();
            }
        }, 3000);
    };
}

// Handle real-time updates from MCP via WebSocket
function handleRealtimeUpdate(data) {
    console.log('Received update:', data);
    
    if (data.type === 'field_update') {
        // Update the appropriate field
        if (data.field_name === 'key_skills' || data.field_name === 'personal_statement') {
            updateAIField(data.field_name, data.value);
        }
    }
}

// Update AI-assisted field with animation
function updateAIField(fieldName, value) {
    const field = document.getElementById(fieldName);
    const statusElement = document.getElementById(`${fieldName}_status`);
    
    if (field) {
        // Add animation
        field.classList.add('field-updating');
        
        // Update value
        field.value = value;
        
        // Show checkmark
        if (statusElement) {
            statusElement.innerHTML = '✓';
            statusElement.classList.add('active');
        }
        
        // Remove animation
        setTimeout(() => {
            field.classList.remove('field-updating');
        }, 1000);
        
        // Update progress
        updateProgress();
    }
}

// Monitor and update progress
function monitorProgress() {
    const fields = ['key_skills', 'personal_statement'];
    
    fields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('input', updateProgress);
        }
    });
}

// Update progress indicator
function updateProgress() {
    const keySkills = document.getElementById('key_skills').value;
    const personalStatement = document.getElementById('personal_statement').value;
    
    let progress = 0;
    let statusText = 'Ready to begin';
    
    if (keySkills && personalStatement) {
        progress = 100;
        statusText = 'AI assistance complete - Ready to submit!';
    } else if (keySkills || personalStatement) {
        progress = 50;
        statusText = 'Great progress - Keep going!';
    }
    
    // Update progress bar
    document.getElementById('progressFill').style.width = `${progress}%`;
    document.getElementById('progressText').textContent = statusText;
    
    // Enable submit button if all required fields are filled
    checkSubmitButton();
}

// Check if submit button should be enabled
function checkSubmitButton() {
    const name = document.getElementById('name').value;
    const employeeId = document.getElementById('employee_id').value;
    const currentDept = document.getElementById('current_department').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const keySkills = document.getElementById('key_skills').value;
    const personalStatement = document.getElementById('personal_statement').value;
    
    const submitBtn = document.getElementById('submitBtn');
    
    if (name && employeeId && currentDept && email && phone && keySkills && personalStatement) {
        submitBtn.disabled = false;
    } else {
        submitBtn.disabled = true;
    }
}

// Setup form submission
function setupFormSubmission() {
    // Monitor manual fields
    const manualFields = ['name', 'employee_id', 'current_department', 'email', 'phone'];
    manualFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('input', checkSubmitButton);
        }
    });
    
    // Handle submit button
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.addEventListener('click', async () => {
        await submitApplication();
    });
}

// Submit the application
async function submitApplication() {
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    
    // Gather all form data
    const applicationData = {
        session_id: sessionId,
        job_id: jobId,
        name: document.getElementById('name').value,
        employee_id: document.getElementById('employee_id').value,
        current_department: document.getElementById('current_department').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        key_skills: document.getElementById('key_skills').value,
        personal_statement: document.getElementById('personal_statement').value,
        submitted_at: new Date().toISOString()
    };
    
    try {
        // In a real implementation, this would submit to the backend
        console.log('Submitting application:', applicationData);
        
        // Simulate submission success
        setTimeout(() => {
            showSuccessMessage();
        }, 1000);
        
    } catch (error) {
        console.error('Error submitting application:', error);
        showNotification('Failed to submit application. Please try again.', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Application';
    }
}

// Show success message
function showSuccessMessage() {
    // Hide form sections
    document.querySelector('.application-container').style.display = 'none';
    document.querySelector('.submit-section').style.display = 'none';
    
    // Show success message
    document.getElementById('successMessage').style.display = 'block';
    
    // Close WebSocket
    if (websocket) {
        websocket.close();
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Simple console log for now
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeApplication();
    
    // Add event listener for Elevenlabs widget when it loads
    setTimeout(() => {
        const widget = document.querySelector('elevenlabs-convai');
        if (widget) {
            console.log('Elevenlabs widget found, session ID:', sessionId);
            // The widget should have access to window.APPLICATION_SESSION_ID
        }
    }, 2000);
});