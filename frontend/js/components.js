// Unified Language and Components System
class UnifiedI18n {
    constructor() {
        // Try to get language from localStorage, URL parameter, or browser language
        let storedLang = localStorage.getItem('preferred-language');
        
        // Check for lang parameter in URL (e.g., ?lang=vi)
        const urlParams = new URLSearchParams(window.location.search);
        const urlLang = urlParams.get('lang');
        
        // Use URL parameter if present, otherwise use stored preference
        if (urlLang && ['en', 'vi', 'es', 'zh'].includes(urlLang)) {
            this.currentLang = urlLang;
            localStorage.setItem('preferred-language', urlLang);
        } else if (storedLang && ['en', 'vi', 'es', 'zh'].includes(storedLang)) {
            this.currentLang = storedLang;
        } else {
            // Fallback to browser language detection
            const browserLang = navigator.language.split('-')[0];
            this.currentLang = ['en', 'vi', 'es', 'zh'].includes(browserLang) ? browserLang : 'en';
            localStorage.setItem('preferred-language', this.currentLang);
        }
        
        this.translations = {};
        this.componentCache = new Map();
        this.init();
    }
    
    async init() {
        await this.loadAllTranslations();
        this.loadComponents();
        this.setupEventListeners();
        
        // Wait for DOM to be fully ready before applying language
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.applyLanguage(this.currentLang);
                // Dispatch i18nReady event
                document.dispatchEvent(new CustomEvent('i18nReady', { detail: { language: this.currentLang } }));
            });
        } else {
            // DOM already loaded
            setTimeout(() => {
                this.applyLanguage(this.currentLang);
                // Dispatch i18nReady event
                document.dispatchEvent(new CustomEvent('i18nReady', { detail: { language: this.currentLang } }));
            }, 100);
        }
    }
    
    async loadAllTranslations() {
        try {
            const languages = ['en', 'vi', 'es', 'zh'];
            const loadPromises = languages.map(lang => 
                fetch(`../lang/${lang}.json`)
                    .then(response => {
                        if (!response.ok) throw new Error(`Failed to load ${lang}.json`);
                        return response.json();
                    })
                    .then(data => {
                        this.translations[lang] = data;
                        console.log(`✅ Loaded ${lang} translations`);
                    })
                    .catch(error => {
                        console.error(`❌ Failed to load ${lang} translations:`, error);
                    })
            );
            
            await Promise.all(loadPromises);
            console.log('🌍 All translations loaded');
        } catch (error) {
            console.error('Failed to load translations:', error);
        }
    }

    loadHead() {
        const cacheKey = 'head';
        if (this.componentCache.has(cacheKey)) return;
        
        const headPath = this.getComponentPath('../frontend/head.html');
        fetch(headPath)
            .then(res => res.ok ? res.text() : Promise.reject())
            .then(html => {
                this.componentCache.set(cacheKey, html);
                document.head.insertAdjacentHTML('beforeend', html);
            })
            .catch(() => this.createEmergencyHead());
    }

    // In the createEmergencyHead method
    createEmergencyHead() {
        const currentPath = window.location.pathname;
        const cssPath = currentPath.includes('/resources/') ? '../../css/components.css' : '../css/components.css';
        
        const emergencyHead = `
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <link rel="stylesheet" href="${cssPath}">
            <!-- Base styles if any -->
            <style>
                body { margin: 0; font-family: 'Inter', sans-serif; }
                .navbar, .footer { transition: opacity 0.3s ease; }
            </style>
        `;
        document.head.insertAdjacentHTML('beforeend', emergencyHead);
    }
        
    loadComponents() {
        this.loadHead(); 
        this.loadNavbar();
        this.loadFooter();
    }
    
    loadNavbar() {
        const cacheKey = 'navbar';
        if (this.componentCache.has(cacheKey)) {
            document.body.insertAdjacentHTML('afterbegin', this.componentCache.get(cacheKey));
            // After inserting navbar, initialize it and update language displays
            this.initNavbar();
            this.translateNavbar(this.currentLang);
            // Force update language displays again after a small delay
            setTimeout(() => {
                this.updateLanguageDisplays();
            }, 50);
            return;
        }
        
        const navbarPath = this.getComponentPath('../frontend/navbar.html');
        fetch(navbarPath)
            .then(res => res.ok ? res.text() : Promise.reject())
            .then(html => {
                this.componentCache.set(cacheKey, html);
                document.body.insertAdjacentHTML('afterbegin', html);
                this.initNavbar();
                this.translateNavbar(this.currentLang);
                // Force update language displays again after a small delay
                setTimeout(() => {
                    this.updateLanguageDisplays();
                }, 50);
            })
            .catch(err => {
                console.error('Navbar load failed:', err);
                this.createEmergencyNavbar();
                this.translateNavbar(this.currentLang);
                setTimeout(() => {
                    this.updateLanguageDisplays();
                }, 50);
            });
    }
    
    loadFooter() {
        const cacheKey = 'footer';
        if (this.componentCache.has(cacheKey)) {
            document.body.insertAdjacentHTML('beforeend', this.componentCache.get(cacheKey));
            this.translateFooter(this.currentLang);
            return;
        }
        
        const footerPath = this.getComponentPath('../frontend/footer.html');
        fetch(footerPath)
            .then(res => res.ok ? res.text() : Promise.reject())
            .then(html => {
                this.componentCache.set(cacheKey, html);
                document.body.insertAdjacentHTML('beforeend', html);
                this.translateFooter(this.currentLang);
            })
            .catch(() => {
                this.createEmergencyFooter();
                this.translateFooter(this.currentLang);
            });
    }
    
    initNavbar() {
        setTimeout(() => {
            this.setupLanguageSelect();
            this.setupMobileMenu();
            this.setupNewsletterForm();
            this.setActiveNav();
            this.updateLanguageDisplays();
        }, 100);
    }

    updateLanguageDisplays() {
        // Update dropdown selects
        const selects = [document.getElementById('languageSelect'), document.getElementById('mobileLanguageSelect')];
        selects.forEach(sel => { 
            if(sel) {
                // Ensure we're setting a string value
                const langValue = this.currentLang.toString();
                sel.value = langValue;
            }
        });
        
        // Update display text with language codes
        const languageCodes = {
            en: 'EN',
            vi: 'VI',
            es: 'ES',
            zh: 'ZH'
        };
        
        const displayCode = languageCodes[this.currentLang] || 'EN';
        
        // Update both desktop and mobile displays
        const desktopDisplay = document.querySelector('.language-display');
        const mobileDisplay = document.querySelector('.mobile-language-display');
        
        if (desktopDisplay) {
            desktopDisplay.textContent = displayCode.toString();
        }
        if (mobileDisplay) {
            mobileDisplay.textContent = displayCode.toString();
        }
    }

    setupLanguageSelect() {
        const handleLangChange = (e) => {
            const lang = e.target.value;
            if (lang && ['en', 'vi', 'es', 'zh'].includes(lang)) {
                this.changeLanguage(lang);
            }
        };
        
        const langSelect = document.getElementById('languageSelect');
        if (langSelect) {
            langSelect.value = this.currentLang;
            langSelect.addEventListener('change', handleLangChange);
        }
        
        const mobileLangSelect = document.getElementById('mobileLanguageSelect');
        if (mobileLangSelect) {
            mobileLangSelect.value = this.currentLang;
            mobileLangSelect.addEventListener('change', handleLangChange);
        }
    }

    setupMobileMenu() {
        const mobileBtn = document.getElementById('mobileMenuBtn');
        const navLinks = document.getElementById('navLinks');
        
        if (mobileBtn && navLinks) {
            mobileBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleMobileMenu();
            });
            
            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!navLinks.contains(e.target) && !mobileBtn.contains(e.target) && navLinks.classList.contains('active')) {
                    this.closeMobileMenu();
                }
            });
        }
    }

    toggleMobileMenu() {
        const navLinks = document.getElementById('navLinks');
        const mobileBtn = document.getElementById('mobileMenuBtn');
        if (navLinks && mobileBtn) {
            navLinks.classList.toggle('active');
            mobileBtn.classList.toggle('active');
            const icon = mobileBtn.querySelector('i');
            if(icon) icon.className = navLinks.classList.contains('active') ? 'fas fa-times' : 'fas fa-bars';
        }
    }

    closeMobileMenu() {
        const navLinks = document.getElementById('navLinks');
        const mobileBtn = document.getElementById('mobileMenuBtn');
        if (navLinks) navLinks.classList.remove('active');
        if (mobileBtn) {
            mobileBtn.classList.remove('active');
            const icon = mobileBtn.querySelector('i');
            if(icon) icon.className = 'fas fa-bars';
        }
    }

    setActiveNav() {
        const currentPath = window.location.pathname;
        // Remove .html if present and get page name
        const currentPage = currentPath.replace('.html', '').split('/').pop() || 'home';
        const navLinks = document.querySelectorAll('.nav-links a');
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            const href = link.getAttribute('href');
            
            if (!href) return;
            
            // Extract page name from href (remove leading slash and .html if present)
            const hrefPage = href.replace(/^\/+/, '').replace('.html', '').toLowerCase();
            const currentPageLower = currentPage.toLowerCase();
            
            // Check if current page matches the href
            const isActive = (
                hrefPage === currentPageLower ||
                (currentPageLower === '' && hrefPage === 'home') ||
                (currentPageLower === 'index' && hrefPage === 'home')
            );
            
            // Special handling for resources directory
            const isInResourcesDir = currentPath.includes('/resources/');
            if (hrefPage === 'resources' && (currentPageLower === 'resources' || isInResourcesDir)) {
                link.classList.add('active');
            } else if (isActive) {
                link.classList.add('active');
            }
        });
        
    }

    changeLanguage(lang) {
        console.log('🌍 Changing language to:', lang);
        this.currentLang = lang;
        localStorage.setItem('preferred-language', lang);
        
        // Update UI immediately
        this.updateLanguageDisplays();
        this.translateNavbar(lang);
        this.translateFooter(lang);
        this.applyLanguage(lang);
        
        // Close mobile menu if open
        this.closeMobileMenu();
        
        // Reload conversation messages and reset demos
        if (window.loadConversationMessages) {
            console.log("Reloading conversation messages for new language...");
            window.loadConversationMessages();
        }
        
        if (window.stopAllDemos) {
            window.stopAllDemos();
        }
        
        if (window.resetAllDemos) {
            setTimeout(() => {
                window.resetAllDemos();
                console.log("Reset all demos with new language messages");
            }, 100);
        }
        
        // Force a small reflow to ensure UI updates
        setTimeout(() => {
            document.body.style.display = 'none';
            document.body.offsetHeight; // Trigger reflow
            document.body.style.display = '';
        }, 10);
    }

    applyLanguage(lang) {
        const page = this.getCurrentPage();
        const translations = this.translations[lang]?.[page];
        
        if (!translations) {
            console.warn(`No translations found for ${page} in ${lang}`);
            return;
        }
        
        // Set document language
        document.documentElement.lang = lang;
        
        // Update all translatable elements
        Object.keys(translations).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                try {
                    if (key === 'newsletter-placeholder' || element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                        const value = translations[key];
                        if (typeof value === 'string') {
                            element.placeholder = value;
                        }
                    } else if (translations[key] && translations[key].includes('<') && translations[key].includes('>')) {
                        element.innerHTML = translations[key];
                    } else {
                        const value = translations[key];
                        if (typeof value === 'string') {
                            element.textContent = value;
                        }
                    }
                } catch (error) {
                    console.warn(`Failed to update element ${key}:`, error);
                }
            } else {
                // Try to find element by class or data attribute as fallback
                const fallbackElement = document.querySelector(`[data-translate="${key}"]`);
                if (fallbackElement) {
                    const value = translations[key];
                    if (typeof value === 'string') {
                        fallbackElement.textContent = value;
                    }
                }
            }
        });
        
        // Update page title if available
        if (translations.pageTitle) {
            document.title = translations.pageTitle;
        }
        
        // Trigger a custom event so other components know language changed
        const event = new CustomEvent('languageChanged', { detail: { language: lang } });
        document.dispatchEvent(event);
    }
        
    // FIXED translateNavbar method with debugging
    translateNavbar(lang) {
        const translations = this.getNavbarTranslations(lang);
        if (!translations) {
            console.error('No navbar translations found for language:', lang);
            return;
        }
        
        console.log('Translating navbar with:', translations);
        
        const navLinks = document.querySelectorAll('.nav-links a');
        
        navLinks.forEach((link, index) => {
            const href = link.getAttribute('href') || '';
            const pageName = href.replace(/^\/+/, '').replace('.html', '').toLowerCase();
            
            let translationKey = '';
            if (pageName === 'home' || pageName === '') {
                translationKey = 'home';
            } else if (pageName === 'prediction') {
                translationKey = 'assessment';
            } else if (pageName === 'analogy') {
                translationKey = 'visualizer';
            } else if (pageName === 'resources') {
                translationKey = 'resources';
            } else if (pageName === 'about') {
                translationKey = 'about';
            } else if (pageName === 'crisis-support') {
                translationKey = 'crisis';
            }
            
            if (translationKey && translations[translationKey]) {
                const text = translations[translationKey];
                // Ensure it's a string
                if (typeof text === 'string') {
                    link.textContent = text;
                } else {
                    console.error(`Translation for ${translationKey} is not a string:`, text);
                    link.textContent = String(text); // Convert to string as fallback
                }
            }
        });
        
        const logoText = document.querySelector('.logo-text');
        if (logoText && translations.logo) {
            const logoTextValue = translations.logo;
            if (typeof logoTextValue === 'string') {
                logoText.textContent = logoTextValue;
            } else {
                console.error('Logo translation is not a string:', logoTextValue);
                logoText.textContent = String(logoTextValue);
            }
        }
    }
    
    // FIXED translateFooter method with debugging
    translateFooter(lang) {
        const translations = this.getFooterTranslations(lang);
        if (!translations) {
            console.error('No footer translations found for language:', lang);
            return;
        }
        
        console.log('Translating footer with:', translations);

        // Translate all footer elements with data-translate
        const elements = document.querySelectorAll('[data-translate]');
        elements.forEach(element => {
            const key = element.getAttribute('data-translate');
            if (key && translations[key]) {
                const value = translations[key];
                
                // Debug log
                console.log(`Setting ${key} to:`, value, 'Type:', typeof value);
                
                if (typeof value === 'string') {
                    if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                        element.placeholder = value;
                        element.title = value;
                    } else if (element.tagName === 'BUTTON') {
                        element.textContent = value;
                    } else {
                        element.textContent = value;
                    }
                } else {
                    console.error(`Translation value for ${key} is not a string:`, value);
                    // Convert to string as fallback
                    const stringValue = String(value);
                    element.textContent = stringValue;
                }
            }
        });
    }
    
    getCurrentPage() {
        const path = window.location.pathname;
        // Remove .html extension if present
        const cleanPath = path.replace('.html', '');
        
        // Extract just the page name (last part after slash)
        const pageName = cleanPath.split('/').pop() || 'home';
        
        // Map page names to translation keys
        const pageMap = {
            'home': 'home',
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
            'therapy-resource': 'therapy-resource'
        };
        
        // If page name contains "resource" but isn't in the map, default to resources
        if (pageName.includes('resource') && !pageMap[pageName]) {
            return 'resources';
        }
        
        return pageMap[pageName] || 'home';
    }

    getComponentPath(filename) {
        const currentPath = window.location.pathname;
        const cleanPath = currentPath.replace('.html', '');
        const isInResourcesDir = cleanPath.includes('/resources/');
        
        // Return cleaned path
        if (cleanPath === '/' || cleanPath.endsWith('index')) {
            return filename.replace('../', '');
        }
        
        if (isInResourcesDir) {
            return `../../${filename.replace('../', '')}`;
        }
        
        return filename; 
    }
    
    getNavbarTranslations(lang) {
        const translations = {
            en: { 
                home: 'Home', 
                assessment: 'Self-Assessment', 
                visualizer: 'Condition Visualizer', 
                resources: 'Resources', 
                about: 'About', 
                crisis: 'Crisis Support', 
                logo: 'Mentivio' 
            },
            vi: { 
                home: 'Trang chủ', 
                assessment: 'Tự Đánh Giá', 
                visualizer: 'Trình Hiển Thị', 
                resources: 'Tài Nguyên', 
                about: 'Giới Thiệu', 
                crisis: 'Hỗ Trợ Khủng Hoảng', 
                logo: 'Mentivio' 
            },
            es: { 
                home: 'Inicio', 
                assessment: 'Autoevaluación', 
                visualizer: 'Visualizador', 
                resources: 'Recursos', 
                about: 'Acerca de', 
                crisis: 'Apoyo en Crisis', 
                logo: 'Mentivio' 
            },
            zh: { 
                home: '首页', 
                assessment: '自我评估', 
                visualizer: '状况可视化', 
                resources: '资源', 
                about: '关于我们', 
                crisis: '危机支持', 
                logo: 'Mentivio' 
            }
        };
        return translations[lang] || translations.en;
    }
    
    getFooterTranslations(lang) {
        const translations = {
            en: {
                "logo": "Mentivio",
                "footer-tagline": "A compassionate mental wellness platform providing insights through self-assessment and education.",
                "newsletter-title": "Stay Updated",
                "newsletter-description": "Get mental wellness tips and platform updates.",
                "newsletter-placeholder": "Your email",
                "newsletter-button": "Subscribe",
                "platform-title": "Platform",
                "support-title": "Support",
                "home": "Home",
                "assessment": "Self-Assessment",
                "visualizer": "Condition Visualizer",
                "resources": "Resources",
                "about": "About",
                "crisis": "Crisis Support",
                "contact": "Contact",
                "copyright": "© 2025 Mentivio Mental Health Platform.",
                "disclaimer": "This platform is for educational purposes only. Always consult healthcare professionals for medical advice.",
                "made-by": "Created by Shin Le",
                "newsletterSuccess": "Thank you for subscribing!",
                "newsletterError": "Please enter a valid email address.",
                "emailValidation": "Please enter a valid email address",
                "newsletterSubscribed": "Subscribed successfully!",
                "newsletterErrorTitle": "Subscription Error",
                "newsletterSuccessTitle": "Success!",
                "newsletterProcessing": "Processing...",
                "newsletterTryAgain": "Try again"
            },
            vi: {
                "logo": "Mentivio",
                "footer-tagline": "Một nền tảng sức khỏe tinh thần đầy lòng trắc ẩn cung cấp thông tin chi tiết thông qua tự đánh giá và giáo dục.",
                "newsletter-title": "Cập Nhật",
                "newsletter-description": "Nhận mẹo về sức khỏe tinh thần và cập nhật nền tảng.",
                "newsletter-placeholder": "Email của bạn",
                "newsletter-button": "Đăng ký",
                "platform-title": "Nền Tảng",
                "support-title": "Hỗ Trợ",
                "home": "Trang chủ",
                "assessment": "Tự Đánh Giá",
                "visualizer": "Trình Hiển Thị",
                "resources": "Tài Nguyên",
                "about": "Giới Thiệu",
                "crisis": "Hỗ Trợ Khủng Hoảng",
                "contact": "Liên Hệ",
                "copyright": "© 2025 Nền tảng Sức khỏe Tinh thần Mentivio.",
                "disclaimer": "Nền tảng này chỉ dành cho mục đích giáo dục. Luôn tham khảo ý kiến chuyên gia y tế để được tư vấn y tế.",
                "made-by": "Tạo bởi Shin Le",
                "newsletterSuccess": "Cảm ơn bạn đã đăng ký!",
                "newsletterError": "Vui lòng nhập địa chỉ email hợp lệ.",
                "emailValidation": "Vui lòng nhập địa chỉ email hợp lệ",
                "newsletterSubscribed": "Đăng ký thành công!",
                "newsletterErrorTitle": "Lỗi Đăng Ký",
                "newsletterSuccessTitle": "Thành công!",
                "newsletterProcessing": "Đang xử lý...",
                "newsletterTryAgain": "Thử lại"
            },
            es: {
                "logo": "Mentivio",
                "footer-tagline": "Una plataforma de bienestar mental compasiva que proporciona información a través de la autoevaluación y la educación.",
                "newsletter-title": "Mantente Actualizado",
                "newsletter-description": "Recibe consejos de bienestar mental y actualizaciones de la plataforma.",
                "newsletter-placeholder": "Tu correo electrónico",
                "newsletter-button": "Suscribirse",
                "platform-title": "Plataforma",
                "support-title": "Soporte",
                "home": "Inicio",
                "assessment": "Autoevaluación",
                "visualizer": "Visualizador de Condiciones",
                "resources": "Recursos",
                "about": "Acerca de",
                "crisis": "Soporte en Crisis",
                "contact": "Contacto",
                "copyright": "© 2025 Plataforma de Salud Mental Mentivio.",
                "disclaimer": "Esta plataforma es solo con fines educativos. Siempre consulte a profesionales de la salud para obtener asesoramiento médico.",
                "made-by": "Creado por Shin Le",
                "newsletterSuccess": "¡Gracias por suscribirte!",
                "newsletterError": "Por favor, introduce una dirección de correo electrónico válida.",
                "emailValidation": "Por favor, introduce una dirección de correo electrónico válida",
                "newsletterSubscribed": "¡Suscripción exitosa!",
                "newsletterErrorTitle": "Error de Suscripción",
                "newsletterSuccessTitle": "¡Éxito!",
                "newsletterProcessing": "Procesando...",
                "newsletterTryAgain": "Intentar de nuevo"
            },
            zh: {
                "logo": "Mentivio",
                "footer-tagline": "一个富有同情心的心理健康平台，通过自我评估和教育提供见解。",
                "newsletter-title": "保持更新",
                "newsletter-description": "获取心理健康提示和平台更新。",
                "newsletter-placeholder": "您的电子邮件",
                "newsletter-button": "订阅",
                "platform-title": "平台",
                "support-title": "支持",
                "home": "首页",
                "assessment": "自我评估",
                "visualizer": "状况可视化",
                "resources": "资源",
                "about": "关于",
                "crisis": "危机支持",
                "contact": "联系我们",
                "copyright": "© 2025 Mentivio 心理健康平台。",
                "disclaimer": "此平台仅供教育目的。请务必咨询医疗专业人员以获取医疗建议。",
                "made-by": "由 Shin Le 创建",
                "newsletterSuccess": "感谢您的订阅！",
                "newsletterError": "请输入有效的电子邮件地址。",
                "emailValidation": "请输入有效的电子邮件地址",
                "newsletterSubscribed": "订阅成功！",
                "newsletterErrorTitle": "订阅错误",
                "newsletterSuccessTitle": "成功！",
                "newsletterProcessing": "处理中...",
                "newsletterTryAgain": "重试"
            }
        };
        
        return translations[lang] || translations.en;
    }
        
    setupEventListeners() {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.changeLanguage(e.target.dataset.lang));
        });
    }
    
    createEmergencyNavbar() {
        const currentPath = window.location.pathname;
        const cleanPath = currentPath.replace('.html', '');
        const isInResourcesDir = cleanPath.includes('/resources/');
        
        // Determine path prefix based on current location
        let relativePrefix = '';
        if (isInResourcesDir) {
            relativePrefix = '../'; // Go up one level from resources
        }
        // If already at root, no prefix needed

        const navbarHTML = `
            <nav class="navbar">
                <div class="nav-container">
                    <a href="${relativePrefix}home" class="logo">
                        <div class="logo-icon"><i class="fas fa-brain"></i></div>
                        <div class="logo-text">Mentivio</div>
                    </a>
                    <div class="mobile-controls">
                        <div class="mobile-language-container">
                            <select class="mobile-language-select" id="mobileLanguageSelect">
                                <option value="en">English</option>
                                <option value="vi">Vietnamese</option>
                                <option value="es">Spanish</option>
                                <option value="zh">Chinese</option>
                            </select>
                            <div class="mobile-language-display">EN</div>
                        </div>
                        <button class="mobile-menu-btn" id="mobileMenuBtn" aria-label="Toggle navigation menu">
                            <i class="fas fa-bars"></i>
                        </button>
                    </div>
                    <div class="nav-links" id="navLinks">
                        <a href="${relativePrefix}home">Home</a>
                        <a href="${relativePrefix}prediction">Self-Assessment</a>
                        <a href="${relativePrefix}analogy">Condition Visualizer</a>
                        <a href="${relativePrefix}resources">Resources</a>
                        <a href="${relativePrefix}about">About</a>
                        <a href="${relativePrefix}crisis-support" class="crisis-link">Crisis Support</a>
                        <div class="nav-language-dropdown">
                            <select class="language-select" id="languageSelect">
                                <option value="en">English</option>
                                <option value="vi">Vietnamese</option>
                                <option value="es">Spanish</option>
                                <option value="zh">Chinese</option>
                            </select>
                            <div class="language-display">EN</div>
                        </div>
                    </div>
                </div>
            </nav>
        `;
        document.body.insertAdjacentHTML('afterbegin', navbarHTML);
        this.initNavbar();
    }
            
    createEmergencyFooter() {
        const currentPath = window.location.pathname;
        const isInResourcesDir = currentPath.includes('/resources/');
        
        let relativePrefix = '';
        if (isInResourcesDir) {
            relativePrefix = '../../frontend/';
        } else if (currentPath.includes('/frontend/')) {
            relativePrefix = ''; 
        } else {
            relativePrefix = 'frontend/';
        }
        
        const footerHTML = `
            <footer class="footer">
                <div class="footer-content">
                    <div class="footer-section">
                        <h4>About Mentivio</h4>
                        <p>A compassionate mental health platform designed to provide insights and promote mental wellness awareness.</p>
                    </div>
                    <div class="footer-section">
                        <h4>Quick Links</h4>
                        <ul>
                            <li><a href="${relativePrefix}home.html">Home</a></li>
                            <li><a href="${relativePrefix}prediction.html">Self-Assessment</a></li>
                            <li><a href="${relativePrefix}analogy.html">Condition Visualizer</a></li>
                            <li><a href="${relativePrefix}resources.html">Resources</a></li>
                        </ul>
                    </div>
                    <div class="footer-section">
                        <h4>Connect</h4>
                        <div class="social-links">
                            <a href="#" aria-label="Facebook"><i class="fab fa-facebook-f"></i></a>
                            <a href="https://github.com/syl21b" aria-label="Github"><i class="fab fa-github"></i></a>
                            <a href="https://syl21b.github.io/shinle-portfolio/" aria-label="Portfolio"><i class="fas fa-briefcase"></i></a>
                            <a href="https://linkedin.com/in/shin-le-b9727a238" aria-label="LinkedIn"><i class="fab fa-linkedin-in"></i></a>
                        </div>
                    </div>
                </div>
                <div class="copyright">
                    <p>&copy; 2025 Mentivio Mental Health Platform. Created by Shin Le.</p>
                </div>
            </footer>
        `;
        document.body.insertAdjacentHTML('beforeend', footerHTML);
    }

    setupNewsletterForm() {
        const newsletterForm = document.querySelector('.newsletter-box-form');
        if (newsletterForm) {
            newsletterForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const emailInput = newsletterForm.querySelector('input[type="email"]');
                const email = emailInput.value.trim();
                
                if (email && this.validateEmail(email)) {
                    // Show success message in current language
                    const successMessage = this.getTranslation('prediction.newsletterSuccess', 'Thank you for subscribing!');
                    alert(successMessage);
                    emailInput.value = '';
                } else {
                    const errorMessage = this.getTranslation('prediction.newsletterError', 'Please enter a valid email address.');
                    alert(errorMessage);
                }
            });
        }
    }

    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    // Helper method to get translation safely
    getTranslation(path, defaultValue = '') {
        const parts = path.split('.');
        let value = this.translations[this.currentLang];
        
        for (const part of parts) {
            if (value && value[part] !== undefined) {
                value = value[part];
            } else {
                return defaultValue;
            }
        }
        return value || defaultValue;
    }
}



// Initialize the unified system
document.addEventListener('DOMContentLoaded', () => {
    window.i18n = new UnifiedI18n();
});