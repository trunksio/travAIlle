// Translation system for English and German

const translations = {
    en: {
        // Header
        appTitle: "Career Growth Portal",
        tagline: "Discover Your Next Role Within Our Organization",
        
        // Navigation
        backToOpportunities: "← Back to Opportunities",
        
        // Home page
        welcomeTitle: "Grow Your Career With Us",
        welcomeText: "Explore internal opportunities and take the next step in your professional journey. Our AI-powered application assistant makes it easy to articulate your strengths and apply with confidence.",
        currentOpportunities: "Current Internal Opportunities",
        loadingPositions: "Loading positions...",
        loadingOpportunities: "Loading opportunities...",
        applyNow: "Apply Now",
        learnMore: "Learn More",
        department: "Department",
        location: "Location",
        postedDate: "Posted",
        teamSize: "Team Size",
        growthPath: "Growth Path",
        requirements: "Requirements",
        whatWereLookingFor: "What we're looking for",
        careerGrowth: "Career Growth",
        applyForThisRole: "Apply for This Role →",
        
        // Apply page
        yourInformation: "Your Information",
        fillDetails: "Please fill in your current details",
        fullName: "Full Name",
        employeeId: "Employee ID",
        currentDepartment: "Current Department",
        email: "Email",
        phone: "Phone",
        
        tellUsAboutFit: "Tell Us About Your Fit",
        aiAssistHelp: "Our AI assistant will help you articulate your experience",
        keySkills: "Key Skills & Experience",
        keySkillsPlaceholder: "Share your skills with our AI assistant...",
        whyGoodFit: "Why You're a Good Fit",
        whyGoodFitPlaceholder: "Tell our AI assistant why you're interested...",
        
        progressReady: "Ready to begin",
        progressComplete: "Application ready!",
        progressStatus: "fields completed",
        
        aiCoachTitle: "AI Career Coach Chat",
        aiCoachHelp: "I'll help you build your application through our conversation",
        chatPlaceholder: "Tell me about your experience, paste your CV text, or ask questions about the role...",
        send: "Send",
        
        submitApplication: "Submit Application",
        submitHelp: "Make sure all fields are complete before submitting",
        
        // Success message
        successTitle: "🎉 Application Submitted Successfully!",
        successMessage: "Thank you for taking this step in your career journey with us.",
        successReview: "The hiring manager will review your application and reach out soon.",
        exploreMore: "Explore More Opportunities",
        
        // Chat messages
        chatGreeting: (jobTitle) => `Hello! I'm here to help you with your application for the ${jobTitle} position. 

You can start by telling me about your current role and experience, or you can paste your CV text here. I'll help you craft compelling responses for your application.

What would you like to share first?`,
        
        // Field status
        aiGenerated: "✓ AI Generated",
        
        // Job count
        positionsAvailable: (count) => `${count} positions available`,
        
        // Footer
        footerText: "© 2024 Internal Career Portal | HR Department | Your growth is our priority",
        
        // Application form
        applicationForm: "Application Form"
    },
    
    de: {
        // Header
        appTitle: "Karriere-Entwicklungsportal",
        tagline: "Entdecken Sie Ihre nächste Rolle in unserem Unternehmen",
        
        // Navigation
        backToOpportunities: "← Zurück zu Stellenangeboten",
        
        // Home page
        welcomeTitle: "Entwickeln Sie Ihre Karriere mit uns",
        welcomeText: "Erkunden Sie interne Möglichkeiten und machen Sie den nächsten Schritt in Ihrer beruflichen Laufbahn. Unser KI-gestützter Bewerbungsassistent hilft Ihnen, Ihre Stärken klar zu formulieren.",
        currentOpportunities: "Aktuelle interne Stellenangebote",
        loadingPositions: "Positionen werden geladen...",
        loadingOpportunities: "Stellenangebote werden geladen...",
        applyNow: "Jetzt bewerben",
        learnMore: "Mehr erfahren",
        department: "Abteilung",
        location: "Standort",
        postedDate: "Veröffentlicht",
        teamSize: "Teamgröße",
        growthPath: "Entwicklungspfad",
        requirements: "Anforderungen",
        whatWereLookingFor: "Was wir suchen",
        careerGrowth: "Karriereentwicklung",
        applyForThisRole: "Für diese Stelle bewerben →",
        
        // Apply page
        yourInformation: "Ihre Informationen",
        fillDetails: "Bitte geben Sie Ihre aktuellen Daten ein",
        fullName: "Vollständiger Name",
        employeeId: "Mitarbeiter-ID",
        currentDepartment: "Aktuelle Abteilung",
        email: "E-Mail",
        phone: "Telefon",
        
        tellUsAboutFit: "Erzählen Sie uns von Ihrer Eignung",
        aiAssistHelp: "Unser KI-Assistent hilft Ihnen, Ihre Erfahrungen zu artikulieren",
        keySkills: "Schlüsselkompetenzen & Erfahrung",
        keySkillsPlaceholder: "Teilen Sie Ihre Fähigkeiten mit unserem KI-Assistenten...",
        whyGoodFit: "Warum Sie gut geeignet sind",
        whyGoodFitPlaceholder: "Erzählen Sie unserem KI-Assistenten, warum Sie interessiert sind...",
        
        progressReady: "Bereit zu beginnen",
        progressComplete: "Bewerbung fertig!",
        progressStatus: "Felder ausgefüllt",
        
        aiCoachTitle: "KI-Karriereberater Chat",
        aiCoachHelp: "Ich helfe Ihnen, Ihre Bewerbung durch unser Gespräch zu erstellen",
        chatPlaceholder: "Erzählen Sie mir von Ihrer Erfahrung, fügen Sie Ihren Lebenslauf ein oder stellen Sie Fragen zur Stelle...",
        send: "Senden",
        
        submitApplication: "Bewerbung absenden",
        submitHelp: "Stellen Sie sicher, dass alle Felder vollständig sind, bevor Sie absenden",
        
        // Success message
        successTitle: "🎉 Bewerbung erfolgreich eingereicht!",
        successMessage: "Vielen Dank, dass Sie diesen Schritt in Ihrer Karriere bei uns machen.",
        successReview: "Der Personalverantwortliche wird Ihre Bewerbung prüfen und sich bald bei Ihnen melden.",
        exploreMore: "Weitere Stellenangebote erkunden",
        
        // Chat messages
        chatGreeting: (jobTitle) => `Hallo! Ich bin hier, um Ihnen bei Ihrer Bewerbung für die Position ${jobTitle} zu helfen.

Sie können damit beginnen, mir von Ihrer aktuellen Rolle und Erfahrung zu erzählen, oder Sie können Ihren Lebenslauf hier einfügen. Ich helfe Ihnen, überzeugende Antworten für Ihre Bewerbung zu formulieren.

Was möchten Sie zuerst teilen?`,
        
        // Field status
        aiGenerated: "✓ KI generiert",
        
        // Job count
        positionsAvailable: (count) => `${count} Stellen verfügbar`,
        
        // Footer
        footerText: "© 2024 Internes Karriereportal | Personalabteilung | Ihr Wachstum ist unsere Priorität",
        
        // Application form
        applicationForm: "Bewerbungsformular"
    }
};

// Language management
class LanguageManager {
    constructor() {
        this.currentLanguage = localStorage.getItem('preferredLanguage') || 'en';
        this.observers = [];
    }
    
    getCurrentLanguage() {
        return this.currentLanguage;
    }
    
    setLanguage(lang) {
        this.currentLanguage = lang;
        localStorage.setItem('preferredLanguage', lang);
        this.notifyObservers();
        this.updatePageTranslations();
    }
    
    translate(key, ...args) {
        const keys = key.split('.');
        let translation = translations[this.currentLanguage];
        
        for (const k of keys) {
            translation = translation?.[k];
        }
        
        // If translation is a function, call it with arguments
        if (typeof translation === 'function') {
            return translation(...args);
        }
        
        return translation || key;
    }
    
    // Short alias for translate
    t(key, ...args) {
        return this.translate(key, ...args);
    }
    
    observe(callback) {
        this.observers.push(callback);
    }
    
    notifyObservers() {
        this.observers.forEach(callback => callback(this.currentLanguage));
    }
    
    updatePageTranslations() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.translate(key);
            
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });
        
        // Update all elements with data-i18n-placeholder attribute
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.translate(key);
        });
        
        // Update document title if on a specific page
        if (window.location.pathname.includes('apply.html')) {
            document.title = `${this.translate('submitApplication')} - ${this.translate('appTitle')}`;
        } else {
            document.title = this.translate('appTitle');
        }
    }
    
    // Get all translations for current language (useful for passing to backend)
    getCurrentTranslations() {
        return translations[this.currentLanguage];
    }
}

// Create global instance
window.i18n = new LanguageManager();

// Initialize translations when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.i18n.updatePageTranslations();
    });
} else {
    window.i18n.updatePageTranslations();
}