// Chat Interface for Claude-powered career coaching

let conversationHistory = [];
let isProcessing = false;

// Initialize chat interface
function initializeChat() {
    const sendButton = document.getElementById('sendButton');
    const chatInput = document.getElementById('chatInput');
    
    if (!sendButton || !chatInput) return;
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Initial greeting
    setTimeout(() => {
        const jobTitle = sessionStorage.getItem('selectedJobTitle') || '';
        const greeting = window.i18n ? window.i18n.t('chatGreeting', jobTitle) : 
            `Hello! I'm here to help you with your application for the ${jobTitle} position. 

You can start by telling me about your current role and experience, or you can paste your CV text here. I'll help you craft compelling responses for your application.

What would you like to share first?`;
        addChatMessage('assistant', greeting);
    }, 500);
}

// Send message to Claude
async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const message = chatInput.value.trim();
    
    if (!message || isProcessing) return;
    
    // Disable input while processing
    isProcessing = true;
    chatInput.disabled = true;
    sendButton.disabled = true;
    
    // Add user message to chat
    addChatMessage('user', message);
    
    // Clear input
    chatInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Prepare request data
        const requestData = {
            session_id: window.APPLICATION_SESSION_ID || sessionStorage.getItem('sessionId'),
            message: message,
            job_id: window.SELECTED_JOB_ID || sessionStorage.getItem('selectedJobId'),
            job_title: sessionStorage.getItem('selectedJobTitle'),
            department: sessionStorage.getItem('selectedDepartment'),
            language: window.i18n ? window.i18n.getCurrentLanguage() : 'en',
            conversation_history: conversationHistory
        };
        
        // Send to backend
        const response = await fetch(`${BACKEND_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to get response from Claude');
        }
        
        const data = await response.json();
        
        // Remove typing indicator
        hideTypingIndicator();
        
        // Add Claude's response to chat
        addChatMessage('assistant', data.response);
        
        // Handle any field updates
        if (data.field_updates && Object.keys(data.field_updates).length > 0) {
            handleFieldUpdates(data.field_updates);
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addChatMessage('assistant', 'I apologize, but I encountered an error. Please try again or refresh the page if the problem persists.');
    } finally {
        // Re-enable input
        isProcessing = false;
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

// Add message to chat display
function addChatMessage(role, content) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    // Add to conversation history
    conversationHistory.push({ role, content });
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = content;
    
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show typing indicator
function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'chat-message assistant';
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Hide typing indicator
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Handle field updates from Claude's response
function handleFieldUpdates(updates) {
    for (const [field, value] of Object.entries(updates)) {
        // Update the form field
        const fieldElement = document.getElementById(field);
        if (fieldElement) {
            // Animate the update
            fieldElement.style.transition = 'background-color 0.5s';
            fieldElement.style.backgroundColor = '#e0f2fe';
            fieldElement.value = value;
            
            // Update status indicator
            const statusElement = document.getElementById(`${field}_status`);
            if (statusElement) {
                statusElement.textContent = '✓ AI Generated';
                statusElement.style.color = '#10b981';
            }
            
            // Reset background after animation
            setTimeout(() => {
                fieldElement.style.backgroundColor = '';
            }, 2000);
            
            // Update progress
            updateProgress();
            
            // Show notification
            showNotification(`Updated: ${field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}`, 'success');
        }
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Update progress based on filled fields
function updateProgress() {
    const keySkills = document.getElementById('key_skills');
    const personalStatement = document.getElementById('personal_statement');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    if (!progressFill || !progressText) return;
    
    let filled = 0;
    const total = 2;
    
    if (keySkills && keySkills.value.trim()) filled++;
    if (personalStatement && personalStatement.value.trim()) filled++;
    
    const percentage = (filled / total) * 100;
    progressFill.style.width = `${percentage}%`;
    
    if (percentage === 0) {
        progressText.textContent = 'Ready to begin';
    } else if (percentage === 100) {
        progressText.textContent = 'Application ready!';
        progressFill.style.backgroundColor = '#10b981';
    } else {
        progressText.textContent = `${filled} of ${total} fields completed`;
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeChat);
} else {
    initializeChat();
}

// Listen for WebSocket updates
window.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'field_update') {
        handleFieldUpdates({ [event.data.field]: event.data.value });
    }
});