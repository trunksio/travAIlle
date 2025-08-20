// Job listing page functionality

// Wait for config to be available or use fallback
function getBackendUrl() {
    const url = window.BACKEND_URL || 'http://localhost:8000';
    console.log('Using backend URL:', url);
    return url;
}

async function loadJobs() {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const jobsList = document.getElementById('jobsList');
    const jobCount = document.getElementById('jobCount');
    
    try {
        loadingSpinner.style.display = 'block';
        jobsList.style.display = 'none';
        
        const backendUrl = getBackendUrl();
        const apiUrl = `${backendUrl}/api/jobs`;
        console.log('Fetching jobs from:', apiUrl);
        
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            throw new Error(`Failed to load jobs: ${response.status} ${response.statusText}`);
        }
        
        const jobs = await response.json();
        
        // Update job count
        jobCount.textContent = `${jobs.length} positions available`;
        
        // Clear existing jobs
        jobsList.innerHTML = '';
        
        // Render each job
        jobs.forEach(job => {
            const jobCard = createJobCard(job);
            jobsList.appendChild(jobCard);
        });
        
        loadingSpinner.style.display = 'none';
        jobsList.style.display = 'grid';
        
    } catch (error) {
        console.error('Error loading jobs:', error);
        console.error('Backend URL was:', getBackendUrl());
        loadingSpinner.style.display = 'none';
        jobsList.innerHTML = `
            <div class="error-message">
                <h3>Unable to load jobs</h3>
                <p>Error: ${error.message}</p>
                <p style="font-size: 0.9em; color: #666;">Backend URL: ${getBackendUrl()}</p>
                <button onclick="loadJobs()">Retry</button>
            </div>
        `;
        jobsList.style.display = 'block';
    }
}

function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';
    
    // Format the posted date
    const postedDate = new Date(job.posted_date);
    const daysAgo = Math.floor((new Date() - postedDate) / (1000 * 60 * 60 * 24));
    const dateText = daysAgo === 0 ? 'Today' : 
                     daysAgo === 1 ? 'Yesterday' : 
                     `${daysAgo} days ago`;
    
    card.innerHTML = `
        <div class="job-header">
            <h3>${job.title}</h3>
            <span class="company">${job.company}</span>
        </div>
        
        <div class="job-meta">
            <span class="location">📍 ${job.location}</span>
            <span class="salary">💰 ${job.salary_range}</span>
        </div>
        
        <div class="job-description">
            <p>${job.description}</p>
        </div>
        
        <div class="job-requirements">
            <h4>Requirements:</h4>
            <p>${job.requirements}</p>
        </div>
        
        <div class="job-footer">
            <span class="posted-date">Posted ${dateText}</span>
            <button class="apply-btn" onclick="applyForJob('${job.id}', '${job.title.replace(/'/g, "\\'")}')">
                🎤 Apply with Voice
            </button>
        </div>
    `;
    
    return card;
}

function applyForJob(jobId, jobTitle) {
    // Store job info in session storage for the application page
    sessionStorage.setItem('selectedJobId', jobId);
    sessionStorage.setItem('selectedJobTitle', jobTitle);
    
    // Navigate to application page
    window.location.href = 'apply.html';
}

// Load jobs when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure config.js is loaded
    setTimeout(() => {
        loadJobs();
    }, 100);
    
    // Refresh jobs every 30 seconds
    setInterval(loadJobs, 30000);
});