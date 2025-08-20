// Application page functionality with WebSocket for real-time updates

// Use config if available, otherwise fallback to localhost
const BACKEND_URL = window.BACKEND_URL || 'http://localhost:8000';
let websocket = null;
let sessionId = null;
let jobId = null;

// Initialize application page
async function initializeApplication() {
    // Get job info from session storage
    jobId = sessionStorage.getItem('selectedJobId');
    const jobTitle = sessionStorage.getItem('selectedJobTitle');
    
    if (!jobId) {
        // If no job selected, redirect to home
        window.location.href = 'index.html';
        return;
    }
    
    // Update page title
    document.getElementById('jobTitle').textContent = `Applying for: ${jobTitle}`;
    
    // Create application session
    await createApplicationSession();
    
    // Connect WebSocket for real-time updates
    connectWebSocket();
    
    // Setup form submission
    setupFormSubmission();
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
        
        // Store session ID for Elevenlabs widget
        window.APPLICATION_SESSION_ID = sessionId;
        window.MCP_SERVER_URL = data.mcp_server_url;
        
        console.log('Application session created:', sessionId);
        
    } catch (error) {
        console.error('Error creating session:', error);
        showError('Failed to initialize application. Please try again.');
    }
}

// Connect WebSocket for real-time form updates
function connectWebSocket() {
    if (!sessionId) return;
    
    const wsUrl = BACKEND_URL.replace('http://', 'ws://').replace('https://', 'wss://');
    websocket = new WebSocket(`${wsUrl}/ws/${sessionId}`);
    
    websocket.onopen = () => {
        console.log('WebSocket connected');
        updateStatus('connected', 'Ready to start voice interview');
    };
    
    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleRealtimeUpdate(data);
    };
    
    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('error', 'Connection error');
    };
    
    websocket.onclose = () => {
        console.log('WebSocket disconnected');
        updateStatus('disconnected', 'Connection lost');
        
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
        // Update form field
        updateFormField(data.field_name, data.value);
        
        // Add to transcript
        addToTranscript('system', `Updated ${data.field_name}: ${data.value}`);
        
        // Update progress
        updateProgress();
        
    } else if (data.type === 'application_submitted') {
        // Application was submitted
        handleApplicationSubmitted(data);
    }
}

// Update a form field with animation
function updateFormField(fieldName, value) {
    const field = document.getElementById(fieldName);
    const statusElement = document.getElementById(`${fieldName}-status`);
    
    if (field) {
        // Add highlighting effect
        field.classList.add('field-updating');
        
        // Update value
        field.value = value;
        
        // Show checkmark
        if (statusElement) {
            statusElement.innerHTML = '✓';
            statusElement.className = 'field-status success';
        }
        
        // Remove highlighting after animation
        setTimeout(() => {
            field.classList.remove('field-updating');
        }, 1000);
    }
}

// Update progress bar
function updateProgress() {
    const requiredFields = ['name', 'email', 'phone'];
    const allFields = ['name', 'email', 'phone', 'years_experience', 'skills', 'cover_letter'];
    
    let filledRequired = 0;
    let filledTotal = 0;
    
    requiredFields.forEach(field => {
        if (document.getElementById(field).value) {
            filledRequired++;
        }
    });
    
    allFields.forEach(field => {
        if (document.getElementById(field).value) {
            filledTotal++;
        }
    });
    
    const percentage = Math.round((filledTotal / allFields.length) * 100);
    
    // Update progress bar
    document.getElementById('progressFill').style.width = `${percentage}%`;
    document.getElementById('progressText').textContent = `${percentage}% Complete`;
    
    // Enable submit button if all required fields are filled
    const submitBtn = document.getElementById('submitBtn');
    if (filledRequired === requiredFields.length) {
        submitBtn.disabled = false;
        submitBtn.classList.add('ready');
    }
}

// Update voice assistant status
function updateStatus(status, text) {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
    statusIndicator.className = `status-indicator ${status}`;
    statusText.textContent = text;
}

// Add message to transcript
function addToTranscript(type, message) {
    const transcriptContent = document.getElementById('transcriptContent');
    
    const entry = document.createElement('div');
    entry.className = `transcript-entry ${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    entry.innerHTML = `
        <span class="transcript-time">${timestamp}</span>
        <span class="transcript-message">${message}</span>
    `;
    
    transcriptContent.appendChild(entry);
    
    // Scroll to bottom
    transcriptContent.scrollTop = transcriptContent.scrollHeight;
}

// Setup form submission
function setupFormSubmission() {
    const submitBtn = document.getElementById('submitBtn');
    
    submitBtn.addEventListener('click', async () => {
        if (!sessionId) {
            showError('Session not initialized');
            return;
        }
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
        
        try {
            const response = await fetch(`${BACKEND_URL}/api/applications/submit?session_id=${sessionId}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Failed to submit application');
            }
            
            const result = await response.json();
            
            if (result.success) {
                handleApplicationSubmitted(result);
            } else {
                throw new Error(result.message || 'Submission failed');
            }
            
        } catch (error) {
            console.error('Error submitting application:', error);
            showError('Failed to submit application. Please try again.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Application';
        }
    });
}

// Handle successful application submission
function handleApplicationSubmitted(data) {
    // Show success message
    const formSection = document.querySelector('.form-section');
    
    formSection.innerHTML = `
        <div class="success-message">
            <h2>✅ Application Submitted Successfully!</h2>
            <p>Thank you for applying. We've received your application and will review it shortly.</p>
            <p class="application-id">Application ID: ${data.application_id || sessionId}</p>
            <div class="success-actions">
                <a href="index.html" class="btn">Browse More Jobs</a>
            </div>
        </div>
    `;
    
    // Update status
    updateStatus('success', 'Application submitted!');
    
    // Add to transcript
    addToTranscript('system', 'Application submitted successfully!');
    
    // Close WebSocket
    if (websocket) {
        websocket.close();
    }
}

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-notification';
    errorDiv.textContent = message;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeApplication();
});