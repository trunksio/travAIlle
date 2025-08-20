// Internal Jobs Listing Page

function getBackendUrl() {
    const url = window.BACKEND_URL || 'http://localhost:5010';
    console.log('Using backend URL:', url);
    return url;
}

async function loadJobs() {
    const jobsList = document.getElementById('jobsList');
    const jobCount = document.getElementById('jobCount');
    
    try {
        const backendUrl = getBackendUrl();
        const apiUrl = `${backendUrl}/api/jobs`;
        console.log('Fetching internal positions from:', apiUrl);
        
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            throw new Error(`Failed to load positions: ${response.status} ${response.statusText}`);
        }
        
        const jobs = await response.json();
        
        // Update job count
        jobCount.textContent = `${jobs.length} positions available`;
        
        // Clear existing jobs
        jobsList.innerHTML = '';
        
        // Render each internal position
        jobs.forEach(job => {
            const jobCard = createJobCard(job);
            jobsList.appendChild(jobCard);
        });
        
    } catch (error) {
        console.error('Error loading positions:', error);
        jobsList.innerHTML = `
            <div class="error-message">
                <h3>Unable to load positions</h3>
                <p>Please try again or contact HR for assistance.</p>
                <button onclick="loadJobs()" class="btn-primary">Retry</button>
            </div>
        `;
    }
}

function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';
    
    // Format the posted date
    const postedDate = new Date(job.posted_date);
    const daysAgo = Math.floor((new Date() - postedDate) / (1000 * 60 * 60 * 24));
    const dateText = daysAgo === 0 ? 'Posted today' : 
                     daysAgo === 1 ? 'Posted yesterday' : 
                     `Posted ${daysAgo} days ago`;
    
    card.innerHTML = `
        <h3>${job.title}</h3>
        <div class="job-department">${job.department}</div>
        
        <div class="job-meta">
            <span>📍 ${job.location}</span>
            ${job.team_size ? `<span>👥 ${job.team_size}</span>` : ''}
        </div>
        
        <div class="job-description">
            <p>${job.description}</p>
        </div>
        
        <div class="job-requirements">
            <strong>What we're looking for:</strong>
            <p>${job.requirements}</p>
        </div>
        
        ${job.growth_path ? `
        <div class="growth-path">
            <strong>Career Growth:</strong> ${job.growth_path}
        </div>
        ` : ''}
        
        <button class="apply-btn" onclick="applyForJob('${job.id}', '${job.title.replace(/'/g, "\\'")}', '${job.department}')">
            Apply for This Role →
        </button>
    `;
    
    return card;
}

function applyForJob(jobId, jobTitle, department) {
    // Store job info in session storage for the application page
    sessionStorage.setItem('selectedJobId', jobId);
    sessionStorage.setItem('selectedJobTitle', jobTitle);
    sessionStorage.setItem('selectedDepartment', department);
    
    // Navigate to application page
    window.location.href = 'apply.html';
}

// Load jobs when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure config.js is loaded
    setTimeout(() => {
        loadJobs();
    }, 100);
    
    // Refresh jobs every 60 seconds
    setInterval(loadJobs, 60000);
});