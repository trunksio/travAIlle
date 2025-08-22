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
        
        // Update job count with translation
        const countText = window.i18n ? window.i18n.t('positionsAvailable', jobs.length) : `${jobs.length} positions available`;
        jobCount.textContent = countText;
        
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
    
    // Get current language
    const lang = window.i18n ? window.i18n.getCurrentLanguage() : 'en';
    
    // Get localized content
    const title = lang === 'de' && job.title_de ? job.title_de : job.title;
    const department = lang === 'de' && job.department_de ? job.department_de : job.department;
    const description = lang === 'de' && job.description_de ? job.description_de : job.description;
    const location = lang === 'de' && job.location_de ? job.location_de : job.location;
    const teamSize = lang === 'de' && job.team_size_de ? job.team_size_de : job.team_size;
    const growthPath = lang === 'de' && job.growth_path_de ? job.growth_path_de : job.growth_path;
    const requirements = lang === 'de' && job.requirements_de ? job.requirements_de : job.requirements;
    
    // Format the posted date
    const postedDate = new Date(job.posted_date);
    const daysAgo = Math.floor((new Date() - postedDate) / (1000 * 60 * 60 * 24));
    
    // Get translated labels
    const t = window.i18n ? window.i18n.t.bind(window.i18n) : (key) => key;
    
    let dateText;
    if (lang === 'de') {
        dateText = daysAgo === 0 ? 'Heute veröffentlicht' : 
                   daysAgo === 1 ? 'Gestern veröffentlicht' : 
                   `Vor ${daysAgo} Tagen veröffentlicht`;
    } else {
        dateText = daysAgo === 0 ? 'Posted today' : 
                   daysAgo === 1 ? 'Posted yesterday' : 
                   `Posted ${daysAgo} days ago`;
    }
    
    card.innerHTML = `
        <h3>${title}</h3>
        <div class="job-department">${department}</div>
        
        <div class="job-meta">
            <span>📍 ${location}</span>
            ${teamSize ? `<span>👥 ${teamSize}</span>` : ''}
        </div>
        
        <div class="job-description">
            <p>${description}</p>
        </div>
        
        <div class="job-requirements">
            <strong>${t('whatWereLookingFor')}:</strong>
            <p>${requirements}</p>
        </div>
        
        ${growthPath ? `
        <div class="growth-path">
            <strong>${t('careerGrowth')}:</strong> ${growthPath}
        </div>
        ` : ''}
        
        <button class="apply-btn" onclick="applyForJob('${job.id}', '${title.replace(/'/g, "\\'")}', '${department}')">
            ${t('applyForThisRole')}
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