// Unified Language and Components System
class UnifiedI18n {
    constructor() {
        this.currentLang = localStorage.getItem('preferred-language') || 'en';
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

    createEmergencyHead() {
        // Adjust path based on current location to ensure CSS loads
        const currentPath = window.location.pathname;
        const cssPath = currentPath.includes('/resources/') ? '../../css/nav-footer.css' : '../css/nav-footer.css';
        
        const emergencyHead = `
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <link rel="stylesheet" href="${cssPath}">
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
            this.initNavbar();
            this.translateNavbar(this.currentLang);
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
            })
            .catch(err => {
                console.error('Navbar load failed:', err);
                this.createEmergencyNavbar();
                this.translateNavbar(this.currentLang);
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
            this.setActiveNav();
            this.updateLanguageDisplays();
        }, 100);
    }

    updateLanguageDisplays() {
        const selects = [document.getElementById('languageSelect'), document.getElementById('mobileLanguageSelect')];
        const desktopDisplay = document.querySelector('.language-display');
        const mobileDisplay = document.querySelector('.mobile-language-display');
        
        // Update select values
        selects.forEach(sel => { if(sel) sel.value = this.currentLang; });
        
        // Update displays with language codes
        const languageCodes = {
            en: 'EN',
            vi: 'VI',
            es: 'ES',
            zh: 'ZH'
        };
        
        const displayCode = languageCodes[this.currentLang] || 'EN';
        
        if (desktopDisplay) desktopDisplay.textContent = displayCode;
        if (mobileDisplay) mobileDisplay.textContent = displayCode;
    }

    updateAllLanguageDisplays(lang) {
        const languageCodes = {
            en: 'EN',
            vi: 'VI',
            es: 'ES',
            zh: 'ZH'
        };
        
        const displayCode = languageCodes[lang] || 'EN';
        
        // Update desktop display
        const desktopDisplay = document.querySelector('.language-display');
        if (desktopDisplay) desktopDisplay.textContent = displayCode;
        
        // Update mobile display
        const mobileDisplay = document.querySelector('.mobile-language-display');
        if (mobileDisplay) mobileDisplay.textContent = displayCode;
    }

    setupLanguageSelect() {
        const handleLangChange = (e) => this.changeLanguage(e.target.value);
        
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
        const currentPage = window.location.pathname.split('/').pop() || 'Home.html';
        const navLinks = document.querySelectorAll('.nav-links a');
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            // Check if href contains the filename rather than exact matching
            if (link.getAttribute('href') && link.getAttribute('href').includes(currentPage)) {
                link.classList.add('active');
            }
        });
    }

    changeLanguage(lang) {
        console.log('🌍 Changing language to:', lang);
        this.currentLang = lang;
        localStorage.setItem('preferred-language', lang);
        
        // Update UI immediately
        this.updateAllLanguageDisplays(lang);  // Update both displays
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

    // Also update the applyLanguage method to be more aggressive:
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
                        element.placeholder = translations[key];
                    } else if (translations[key].includes('<') && translations[key].includes('>')) {
                        element.innerHTML = translations[key];
                    } else {
                        element.textContent = translations[key];
                    }
                } catch (error) {
                    console.warn(`Failed to update element ${key}:`, error);
                }
            } else {
                // Try to find element by class or data attribute as fallback
                const fallbackElement = document.querySelector(`[data-translate="${key}"]`);
                if (fallbackElement) {
                    fallbackElement.textContent = translations[key];
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
        
    // --- UPDATED TRANSLATE NAVBAR METHOD ---
    translateNavbar(lang) {
        const translations = this.getNavbarTranslations(lang);
        if (!translations) return;
        
        const navLinks = document.querySelectorAll('.nav-links a');
        
        navLinks.forEach(link => {
            // Get the href attribute (e.g., "../frontend/Home.html")
            const href = link.getAttribute('href') || '';
            
            // We use .includes() to check the filename, ignoring the directory path (../frontend/)
            // This ensures it works regardless of folder depth
            if (href.includes('Home.html') || (href.endsWith('/') && !href.includes('.'))) {
                link.textContent = translations.home;
            } else if (href.includes('MenHel_prediction.html')) {
                link.textContent = translations.assessment;
            } else if (href.includes('MenHel_analogy.html')) {
                link.textContent = translations.visualizer;
            } else if (href.includes('resources.html')) {
                link.textContent = translations.resources;
            } else if (href.includes('About.html')) {
                link.textContent = translations.about;
            } else if (href.includes('crisis-support.html')) {
                link.textContent = translations.crisis;
            }
        });
        
        const logoText = document.querySelector('.logo-text');
        if (logoText && translations.logo) {
            logoText.textContent = translations.logo;
        }
    }
    
    // --- UPDATED TRANSLATE FOOTER METHOD ---
    translateFooter(lang) {
        const translations = this.getFooterTranslations(lang);
        if (!translations) return;

        // Select all elements with data-translate attribute
        const elements = document.querySelectorAll('[data-translate]');
        elements.forEach(element => {
            const key = element.getAttribute('data-translate');
            if (translations[key]) {
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                    element.placeholder = translations[key];
                } else {
                    element.textContent = translations[key];
                }
            }
        });
    }
    
    getCurrentPage() {
        const path = window.location.pathname;
        if (path.includes('anxiety-resource')) return 'anxiety-resource';
        if (path.includes('bipolar-resource')) return 'bipolar-resource';
        if (path.includes('depression-resource')) return 'depression-resource';
        if (path.includes('medication-resource')) return 'medication-resource';
        if (path.includes('mindfulness-resource')) return 'mindfulness-resource';
        if (path.includes('ptsd-resource')) return 'ptsd-resource';
        if (path.includes('selfcare-resource')) return 'selfcare-resource';
        if (path.includes('therapy-resource')) return 'therapy-resource';
        if (path.includes('resources')) return 'resources';
        if (path.includes('MenHel_prediction')) return 'prediction';
        if (path.includes('MenHel_analogy')) return 'analogy';
        if (path.includes('About')) return 'about';
        if (path.includes('crisis-support')) return 'crisis';
        return 'Home';
    }

    getComponentPath(filename) {
        const currentPath = window.location.pathname;
        const isInResourcesDir = currentPath.includes('/resources/');
        
        // Return cleaned path
        if (currentPath === '/' || currentPath.endsWith('index.html')) return filename.replace('../', '');
        if (isInResourcesDir) return `../../${filename.replace('../', '')}`;
        return filename; 
    }
    
    getNavbarTranslations(lang) {
        const translations = {
            en: { home: 'Home', assessment: 'Self-Assessment', visualizer: 'Condition Visualizer', resources: 'Resources', about: 'About', crisis: 'Crisis Support', logo: 'Mentivio' },
            vi: { home: 'Trang chủ', assessment: 'Tự Đánh Giá', visualizer: 'Trình Hiển Thị', resources: 'Tài Nguyên', about: 'Giới Thiệu', crisis: 'Hỗ Trợ Khủng Hoảng', logo: 'Mentivio' },
            es: { home: 'Inicio', assessment: 'Autoevaluación', visualizer: 'Visualizador', resources: 'Recursos', about: 'Acerca de', crisis: 'Apoyo en Crisis', logo: 'Mentivio' },
            zh: { home: '首页', assessment: '自我评估', visualizer: '状况可视化', resources: '资源', about: '关于我们', crisis: '危机支持', logo: 'Mentivio' }
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
                "made-by": "Create by Shin Le"
            },
            vi: {
                "logo": "Mentivio",
                "footer-tagline": "Nền tảng sức khỏe tinh thần đầy lòng trắc ẩn cung cấp thông tin chi tiết thông qua tự đánh giá và giáo dục.",
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
                "made-by": "Tạo bởi Shin Le"
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
                "made-by": "Creado por Shin Le"
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
                "made-by": "由 Shin Le 创建"
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
        const isInResourcesDir = currentPath.includes('/resources/');
        
        // Base path calculation: if in resources, go up 2 levels, otherwise go up 1 level or stay root
        let relativePrefix = '';
        if (isInResourcesDir) {
            relativePrefix = '../../frontend/';
        } else if (currentPath.includes('/frontend/')) {
            relativePrefix = ''; // Already in frontend
        } else {
            relativePrefix = 'frontend/';
        }

        const navbarHTML = `
            <nav class="navbar">
                <div class="nav-container">
                    <a href="${relativePrefix}Home.html" class="logo">
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
                        <a href="${relativePrefix}Home.html">Home</a>
                        <a href="${relativePrefix}MenHel_prediction.html">Self-Assessment</a>
                        <a href="${relativePrefix}MenHel_analogy.html">Condition Visualizer</a>
                        <a href="${relativePrefix}resources.html">Resources</a>
                        <a href="${relativePrefix}About.html">About</a>
                        <a href="${relativePrefix}crisis-support.html" class="crisis-link">Crisis Support</a>
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
                            <li><a href="${relativePrefix}Home.html">Home</a></li>
                            <li><a href="${relativePrefix}MenHel_prediction.html">Self-Assessment</a></li>
                            <li><a href="${relativePrefix}MenHel_analogy.html">Condition Visualizer</a></li>
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
}


// Initialize the unified system
document.addEventListener('DOMContentLoaded', () => {
    window.i18n = new UnifiedI18n();
});