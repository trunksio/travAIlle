// Language Switcher Component

function createLanguageSwitcher() {
    const switcher = document.createElement('div');
    switcher.className = 'language-switcher';
    switcher.innerHTML = `
        <button class="lang-btn ${window.i18n.getCurrentLanguage() === 'en' ? 'active' : ''}" data-lang="en">
            <span class="flag">🇬🇧</span> EN
        </button>
        <button class="lang-btn ${window.i18n.getCurrentLanguage() === 'de' ? 'active' : ''}" data-lang="de">
            <span class="flag">🇩🇪</span> DE
        </button>
    `;
    
    // Add event listeners
    switcher.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const lang = e.currentTarget.getAttribute('data-lang');
            
            // Update active state
            switcher.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
            e.currentTarget.classList.add('active');
            
            // Set language
            window.i18n.setLanguage(lang);
            
            // Reload page content if needed
            if (typeof loadJobs === 'function') {
                loadJobs(); // Reload jobs in new language
            }
            
            // Reinitialize chat if it exists
            if (typeof initializeChat === 'function') {
                // Clear chat history and reinitialize with new language
                conversationHistory = [];
                const chatMessages = document.getElementById('chatMessages');
                if (chatMessages) {
                    chatMessages.innerHTML = '';
                    // Add greeting in new language
                    setTimeout(() => {
                        const jobTitle = sessionStorage.getItem('selectedJobTitle') || '';
                        addChatMessage('assistant', window.i18n.t('chatGreeting', jobTitle));
                    }, 500);
                }
            }
        });
    });
    
    return switcher;
}

// Insert language switcher when DOM is ready
function insertLanguageSwitcher() {
    // Find header or create a container for the switcher
    const header = document.querySelector('header .header-content');
    if (header) {
        // Check if switcher already exists
        if (!header.querySelector('.language-switcher')) {
            const switcher = createLanguageSwitcher();
            header.appendChild(switcher);
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', insertLanguageSwitcher);
} else {
    insertLanguageSwitcher();
}

// Listen for language changes to update the switcher
window.i18n.observe((newLang) => {
    const switcher = document.querySelector('.language-switcher');
    if (switcher) {
        switcher.querySelectorAll('.lang-btn').forEach(btn => {
            if (btn.getAttribute('data-lang') === newLang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
});