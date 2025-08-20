// Elevenlabs Voice Widget Integration

// Wait for session to be initialized
let checkSessionInterval = setInterval(() => {
    if (window.APPLICATION_SESSION_ID) {
        clearInterval(checkSessionInterval);
        initializeElevenlabs();
    }
}, 100);

function initializeElevenlabs() {
    const agentId = window.ELEVENLABS_AGENT_ID || getAgentIdFromEnv();
    
    if (!agentId) {
        console.error('Elevenlabs Agent ID not configured');
        updateStatus('error', 'Voice assistant not configured');
        showManualInstructions();
        return;
    }
    
    // Create the Elevenlabs widget container
    const widgetContainer = document.getElementById('elevenlabs-widget');
    
    // Embed the Elevenlabs conversational AI widget
    const iframe = document.createElement('iframe');
    iframe.id = 'elevenlabs-iframe';
    iframe.src = `https://elevenlabs.io/convai/embed/${agentId}`;
    iframe.width = '100%';
    iframe.height = '600';
    iframe.frameBorder = '0';
    iframe.allow = 'microphone';
    
    // Add custom parameters for MCP integration
    const params = new URLSearchParams({
        session_id: window.APPLICATION_SESSION_ID,
        mcp_server: window.MCP_SERVER_URL || 'http://localhost:3000',
        job_id: sessionStorage.getItem('selectedJobId'),
        custom_prompt: generateCustomPrompt()
    });
    
    iframe.src += '?' + params.toString();
    
    widgetContainer.innerHTML = '';
    widgetContainer.appendChild(iframe);
    
    // Listen for messages from the iframe (if Elevenlabs supports it)
    window.addEventListener('message', handleElevenlabsMessage);
    
    // Update status
    updateStatus('ready', 'Click "Start" in the voice assistant to begin');
    
    // Add initial transcript entry
    addToTranscript('system', 'Voice assistant initialized. Click Start to begin your interview.');
}

function generateCustomPrompt() {
    const jobTitle = sessionStorage.getItem('selectedJobTitle');
    const sessionId = window.APPLICATION_SESSION_ID;
    
    return `You are conducting a job interview for the position of ${jobTitle}. 
    The session ID is ${sessionId}. 
    Use the update_application_field tool to update form fields as the candidate provides information.
    Ask for: name, email, phone, years of experience, key skills, and why they're interested in this position.
    Be conversational and encouraging. Update fields in real-time as they speak.`;
}

function handleElevenlabsMessage(event) {
    // Handle any messages from the Elevenlabs widget
    if (event.data && event.data.type) {
        console.log('Elevenlabs message:', event.data);
        
        if (event.data.type === 'conversation_started') {
            updateStatus('active', 'Interview in progress...');
            addToTranscript('system', 'Voice interview started');
        } else if (event.data.type === 'conversation_ended') {
            updateStatus('completed', 'Interview completed');
            addToTranscript('system', 'Voice interview ended');
        }
    }
}

function showManualInstructions() {
    const widgetContainer = document.getElementById('elevenlabs-widget');
    
    widgetContainer.innerHTML = `
        <div class="manual-setup">
            <h3>Voice Assistant Setup Required</h3>
            <p>To enable voice applications, you need to:</p>
            <ol>
                <li>Create an Elevenlabs account at <a href="https://elevenlabs.io" target="_blank">elevenlabs.io</a></li>
                <li>Create a conversational AI agent</li>
                <li>Configure the agent with MCP tool access</li>
                <li>Add your Agent ID to the environment variables</li>
            </ol>
            
            <div class="demo-mode">
                <h4>Demo Mode (Without Voice)</h4>
                <p>You can still test the form by manually entering data:</p>
                <button onclick="fillDemoData()" class="demo-btn">Fill Demo Data</button>
            </div>
        </div>
    `;
}

function fillDemoData() {
    // Demo data for testing without voice
    const demoData = {
        name: 'John Doe',
        email: 'john.doe@example.com',
        phone: '+1 (555) 123-4567',
        years_experience: '5',
        skills: 'Python, JavaScript, React, Node.js, AWS, Docker',
        cover_letter: 'I am excited about this opportunity because it aligns perfectly with my experience in full-stack development and my passion for building scalable applications.'
    };
    
    // Simulate real-time updates
    let delay = 0;
    Object.entries(demoData).forEach(([field, value]) => {
        setTimeout(() => {
            updateFormField(field, value);
            addToTranscript('user', `${field}: ${value}`);
            updateProgress();
        }, delay);
        delay += 1000;
    });
    
    updateStatus('demo', 'Demo mode - Data being filled');
}

function getAgentIdFromEnv() {
    // Try to get from meta tag or global variable
    const metaTag = document.querySelector('meta[name="elevenlabs-agent-id"]');
    if (metaTag) {
        return metaTag.content;
    }
    
    // Check if it's defined as a global
    if (typeof ELEVENLABS_AGENT_ID !== 'undefined') {
        return ELEVENLABS_AGENT_ID;
    }
    
    return null;
}

// Alternative: Direct Elevenlabs SDK integration (if available)
function initializeElevenlabsSDK() {
    // This would be used if Elevenlabs provides a JavaScript SDK
    // For now, we're using the iframe embed method
    
    /*
    const elevenlabs = new ElevenlabsConversationalAI({
        agentId: window.ELEVENLABS_AGENT_ID,
        onTranscript: (text, speaker) => {
            addToTranscript(speaker === 'agent' ? 'assistant' : 'user', text);
        },
        onToolCall: (tool, args) => {
            console.log('Tool called:', tool, args);
            // This would be handled by the MCP integration
        },
        customContext: {
            session_id: window.APPLICATION_SESSION_ID,
            mcp_server: window.MCP_SERVER_URL,
            job_id: sessionStorage.getItem('selectedJobId')
        }
    });
    
    elevenlabs.start();
    */
}