// GLOBAL LANGUAGE MANAGER - IMPROVED VERSION
class GlobalLanguageManager {
    constructor() {
        this.currentLang = this.getSavedLanguage();
        this.translations = {};
        this.isLoading = false;
        this.init();
    }
    
    getSavedLanguage() {
        const urlParams = new URLSearchParams(window.location.search);
        const urlLang = urlParams.get('lang');
        
        if (urlLang && ['en', 'vi', 'es', 'zh'].includes(urlLang)) {
            localStorage.setItem('preferred-language', urlLang);
            return urlLang;
        }
        
        const storedLang = localStorage.getItem('preferred-language');
        if (storedLang && ['en', 'vi', 'es', 'zh'].includes(storedLang)) {
            return storedLang;
        }
        
        const browserLang = navigator.language.split('-')[0];
        const defaultLang = ['en', 'vi', 'es', 'zh'].includes(browserLang) ? browserLang : 'en';
        localStorage.setItem('preferred-language', defaultLang);
        return defaultLang;
    }
    
    async init() {
        await this.loadTranslations();
        this.setupLanguageSwitchers();
        this.applyLanguage(this.currentLang);
        this.dispatchLanguageChangeEvent();
    }
    
    async loadTranslations() {
        try {
            this.isLoading = true;
            const response = await fetch(`../lang/${this.currentLang}.json`);
            if (!response.ok) {
                throw new Error(`Failed to load translations: ${response.status}`);
            }
            this.translations = await response.json();  // <-- This loads the entire JSON file
            console.log(`Loaded translations for ${this.currentLang}:`, this.translations);
        } catch (error) {
            console.error('Failed to load translations:', error);
            // Load English as fallback
            try {
                const fallbackResponse = await fetch('../lang/en.json');
                this.translations = await fallbackResponse.json();
            } catch (fallbackError) {
                console.error('Failed to load fallback translations:', fallbackError);
                this.translations = {};
            }
        } finally {
            this.isLoading = false;
        }
    }
    
    // Helper method for other components to get translations
    t(key, page = null, defaultValue = '') {
        if (this.isLoading) {
            console.warn('Translations still loading for key:', key);
            return defaultValue || key;
        }
        
        const pageKey = page || this.getCurrentPage();
        console.log(`Looking for translation: page=${pageKey}, key=${key}`);
        
        // Try to get translation from nested structure
        let translation = this.translations;
        
        // If translations are organized by page
        if (translation[pageKey]) {
            translation = translation[pageKey];
        }
        
        // Split key by dots for nested access
        const parts = key.split('.');
        for (const part of parts) {
            if (translation && translation[part] !== undefined) {
                translation = translation[part];
            } else {
                console.warn(`Translation not found for key: ${key} in page: ${pageKey}`);
                return defaultValue || key;
            }
        }
        
        console.log(`Found translation for ${key}:`, translation);
        return translation;
    }
    
    // Simple method to get translation without page context
    getTranslation(key, defaultValue = '') {
        return this.t(key, this.getCurrentPage(), defaultValue);
    }
    
    // Rest of the class remains the same...
    setupLanguageSwitchers() {
        // Setup for dynamically loaded language switchers (navbar/footer)
        this.setupLanguageSelectEvents();
        
        // Also listen for clicks on existing language links
        document.addEventListener('click', (e) => {
            const langBtn = e.target.closest('.lang-btn');
            if (langBtn && langBtn.dataset.lang) {
                e.preventDefault();
                this.changeLanguage(langBtn.dataset.lang);
            }
        });
    }
    
    setupLanguageSelectEvents() {
        const setupSelect = (select) => {
            if (select) {
                select.value = this.currentLang;
                select.onchange = (e) => {
                    this.changeLanguage(e.target.value);
                };
            }
        };
        
        setupSelect(document.getElementById('languageSelect'));
        setupSelect(document.getElementById('mobileLanguageSelect'));
        document.querySelectorAll('.language-select').forEach(setupSelect);
    }
    
    async changeLanguage(lang) {
        if (!['en', 'vi', 'es', 'zh'].includes(lang)) return;
        
        this.currentLang = lang;
        localStorage.setItem('preferred-language', lang);
        
        // Update URL without reloading
        const url = new URL(window.location);
        url.searchParams.set('lang', lang);
        window.history.replaceState({}, '', url);
        
        // Reload translations
        await this.loadTranslations();
        
        // Apply language to page content
        this.applyLanguage(lang);
        
        // Dispatch event for navbar/footer to update
        this.dispatchLanguageChangeEvent();
    }
    
    dispatchLanguageChangeEvent() {
        document.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { 
                language: this.currentLang,
                translations: this.translations 
            }
        }));
        
        document.dispatchEvent(new CustomEvent('langChanged', {
            detail: { lang: this.currentLang }
        }));
    }
    
    applyLanguage(lang) {
        document.documentElement.lang = lang;
        
        const page = this.getCurrentPage();
        const pageTranslations = this.translations[page] || {};
        
        console.log(`Applying language ${lang} for page ${page}`, pageTranslations);
        
        // Apply to all elements with ids that match translation keys
        Object.keys(pageTranslations).forEach(key => {
            const element = document.getElementById(key);
            
            // Skip if this is the "exercises" object (not a string)
            if (key === 'exercises' && typeof pageTranslations[key] === 'object') {
                return; // Skip, this is used by showExercise function
            }
            
            if (element) {
                this.applyTranslationToElement(element, pageTranslations[key]);
            }
        });
        
        // DON'T apply prediction translations to other pages
        // Only apply general/common translations from the root level
        Object.keys(this.translations).forEach(pageKey => {
            // Skip if it's the current page (already processed) or if it's an object
            if (pageKey === page || typeof this.translations[pageKey] !== 'object') {
                return;
            }
            
            // Check if this is a common/shared translation section
            const isCommonSection = ['app', 'common', 'shared'].includes(pageKey);
            if (isCommonSection) {
                Object.keys(this.translations[pageKey]).forEach(key => {
                    const element = document.getElementById(key);
                    if (element) {
                        this.applyTranslationToElement(element, this.translations[pageKey][key]);
                    }
                });
            }
        });
        
        // Update page title
        const titleElement = document.getElementById('page-title');
        let titleText = '';
        
        if (pageTranslations['page-title']) {
            titleText = pageTranslations['page-title'];
        } else if (this.translations['page-title']) {
            titleText = this.translations['page-title'];
        } else if (this.translations.app?.title) {
            titleText = this.translations.app.title;
        }
        
        if (titleText && titleElement) {
            titleElement.textContent = titleText;
            document.title = titleText;
        } else if (titleElement) {
            document.title = titleElement.textContent || document.title;
        }
        
        // Update language selectors
        document.querySelectorAll('.language-select').forEach(select => {
            select.value = lang;
        });
    }
    
    applyTranslationToElement(element, translation) {
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            if (element.getAttribute('placeholder') !== null) {
                element.placeholder = translation;
            } else {
                element.value = translation;
            }
        } else if (element.tagName === 'META' && element.getAttribute('name') === 'description') {
            element.setAttribute('content', translation);
        } else if (element.tagName === 'TITLE') {
            // Handle title element specifically
            element.textContent = translation;
            // Also update document.title for consistency
            document.title = translation;
        } else {
            const containsHTML = /<[a-z][\s\S]*>/i.test(translation);
            if (containsHTML) {
                element.innerHTML = translation;
            } else {
                element.textContent = translation;
            }
        }
    }
    
    getCurrentPage() {
        const path = window.location.pathname;
        const fileName = path.split('/').pop().replace('.html', '') || 'home';
        
        const pageMap = {
            'home': 'home',
            'index': 'home',
            'prediction': 'prediction',
            'analogy': 'analogy',
            'resources': 'resources',
            'about': 'about',
            'crisis-support': 'crisis',
            'anxiety-resource': 'anxiety-resource',
            'bipolar-resource': 'bipolar-resource',
            'depression-resource': 'depression-resource',
            'medication-resource': 'medication-resource',
            'mindfulness-resource': 'mindfulness-resource',
            'ptsd-resource': 'ptsd-resource',
            'selfcare-resource': 'selfcare-resource',
            'therapy-resource': 'therapy-resource',
            'privacy': 'privacy',
            'terms': 'terms'
        };
        
        return pageMap[fileName] || 'home';
    }
    
    setElementContent(elementId, translationKey, page = null) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const translation = this.t(translationKey, page, true);
        element.innerHTML = translation;
    }
}

// Initialize global language manager
window.globalLangManager = new GlobalLanguageManager();

// Update the event listener
document.addEventListener('langChanged', (e) => {
    const lang = e.detail.lang;
    
    // Update language selectors
    document.querySelectorAll('.language-select').forEach(select => {
        select.value = lang;
    });

    // Update URL without reloading
    const url = new URL(window.location);
    url.searchParams.set('lang', lang);
    window.history.replaceState({}, '', url);
});

// Helper function to safely apply translations with HTML
function applyTranslationWithHTML(elementId, translationKey, page = null) {
    if (window.globalLangManager) {
        window.globalLangManager.setElementContent(elementId, translationKey, page);
    }
}