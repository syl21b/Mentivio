// ULTRA-SIMPLE INSTANT NAVBAR - FULLY FIXED
(function() {
    // ─── Prevent duplicate execution ───
    if (window._navbarLoaded) {
        console.log('Navbar already loaded, skipping duplicate');
        return;
    }
    window._navbarLoaded = true;

    // ─── Get language ───
    const urlParams = new URLSearchParams(window.location.search);
    const urlLang = urlParams.get('lang');
    let currentLang = 'en';
    
    if (urlLang && ['en', 'vi', 'es', 'zh'].includes(urlLang)) {
        currentLang = urlLang;
        localStorage.setItem('preferred-language', urlLang);
    } else {
        const stored = localStorage.getItem('preferred-language');
        if (stored && ['en', 'vi', 'es', 'zh'].includes(stored)) {
            currentLang = stored;
        }
    }
    
    // ─── Translations – ensure 'map' key exists for ALL languages ───
    const translations = {
        en: { 
            home: 'Home', 
            assessment: 'Self-Assessment', 
            visualizer: 'Condition Visualizer', 
            map: 'Mood Map',  // ✅ Explicitly defined
            resources: 'Resources', 
            about: 'About', 
            crisis: 'Crisis Support', 
            logo: 'Mentivio' 
        },
        vi: { 
            home: 'Trang chủ', 
            assessment: 'Tự Đánh Giá', 
            visualizer: 'Trình Hiển Thị', 
            map: 'Bản đồ tâm trạng',  // ✅ Explicitly defined
            resources: 'Tài Nguyên', 
            about: 'Giới Thiệu', 
            crisis: 'Hỗ Trợ Khủng Hoảng', 
            logo: 'Mentivio' 
        },
        es: { 
            home: 'Inicio', 
            assessment: 'Autoevaluación', 
            visualizer: 'Visualizador', 
            map: 'Mapa de Ánimo',  // ✅ Explicitly defined
            resources: 'Recursos', 
            about: 'Acerca de', 
            crisis: 'Apoyo en Crisis', 
            logo: 'Mentivio' 
        },
        zh: { 
            home: '首页', 
            assessment: '自我评估', 
            visualizer: '状况可视化', 
            map: '情绪地图',  // ✅ Explicitly defined
            resources: '资源', 
            about: '关于我们', 
            crisis: '危机支持', 
            logo: 'Mentivio' 
        }
    };
    
    // ─── Ensure translations exist ───
    function getTranslation(lang, key) {
        const t = translations[lang] || translations.en;
        return t[key] || translations.en[key] || key;
    }
    
    const t = translations[currentLang] || translations.en;
    const langCodes = { en: 'EN', vi: 'VI', es: 'ES', zh: 'ZH' };
    const langDisplay = langCodes[currentLang] || 'EN';
    
    // ─── Get current page ───
    const path = window.location.pathname;
    let currentPage = path.split('/').pop().replace('.html', '') || 'home';
    if (currentPage === 'index') currentPage = 'home';
    
    // ─── Build navbar HTML ───
    function buildNavbarHTML() {
        const t = translations[currentLang] || translations.en;
        const mapText = t.map || 'Mood Map';  // Fallback
        
        return `
            <style>
                /* RESET and FORCE full width */
                * { box-sizing: border-box !important; }
                body { margin: 0 !important; padding: 0 !important; overflow-x: hidden !important; }
                
                .mentivio-navbar {
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    right: 0 !important;
                    width: 100vw !important;
                    min-width: 100vw !important;
                    height: 70px !important;
                    z-index: 10000 !important;
                    display: flex !important;
                    align-items: center !important;
                    background: white !important;
                    border-bottom: 1px solid #e5e7eb !important;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                
                @media (prefers-color-scheme: dark) {
                    .mentivio-navbar {
                        background: #0f172a !important;
                        border-bottom: 1px solid #1e293b !important;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
                    }
                }
                
                .mentivio-navbar-inner {
                    width: 100% !important;
                    max-width: 100% !important;
                    margin: 0 auto !important;
                    padding: 0 40px !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: space-between !important;
                }
                
                .mentivio-logo {
                    display: flex !important;
                    align-items: center !important;
                    gap: 10px !important;
                    text-decoration: none !important;
                    color: #4f46e5 !important;
                    font-weight: 700 !important;
                    font-size: 1.35rem !important;
                    transition: color 0.2s ease !important;
                }
                
                .mentivio-logo:hover { color: #7c3aed !important; }
                
                .mentivio-desktop-links {
                    display: flex !important;
                    align-items: center !important;
                    gap: 20px !important;
                }
                
                .mentivio-nav-link {
                    text-decoration: none !important;
                    color: #374151 !important;
                    font-weight: 500 !important;
                    font-size: 0.95rem !important;
                    padding: 8px 16px !important;
                    border-radius: 8px !important;
                    transition: all 0.2s ease !important;
                }
                
                .mentivio-nav-link:hover {
                    background: rgba(79, 70, 229, 0.1) !important;
                    color: #4f46e5 !important;
                }
                
                .mentivio-nav-link.active {
                    background: rgba(79, 70, 229, 0.1) !important;
                    color: #4f46e5 !important;
                    font-weight: 600 !important;
                }
                
                .mentivio-nav-link.crisis {
                    color: #ef4444 !important;
                    font-weight: 600 !important;
                    background: rgba(239, 68, 68, 0.1) !important;
                    border: 1px solid rgba(239, 68, 68, 0.2) !important;
                }
                
                .mentivio-nav-link.crisis:hover {
                    background: rgba(239, 68, 68, 0.2) !important;
                }
                
                @media (prefers-color-scheme: dark) {
                    .mentivio-nav-link { color: #e5e7eb !important; }
                    .mentivio-nav-link:hover { color: #a5b4fc !important; }
                }
                
                .mentivio-language-wrapper {
                    position: relative !important;
                    margin-left: 10px !important;
                }
                
                .mentivio-language-select {
                    opacity: 0 !important;
                    position: absolute !important;
                    width: 100% !important;
                    height: 100% !important;
                    cursor: pointer !important;
                    z-index: 1 !important;
                }
                
                .mentivio-language-display {
                    padding: 8px 16px !important;
                    background: rgba(79, 70, 229, 0.1) !important;
                    color: #4f46e5 !important;
                    border-radius: 8px !important;
                    font-size: 0.9rem !important;
                    font-weight: 600 !important;
                    min-width: 60px !important;
                    text-align: center !important;
                    display: block !important;
                    transition: all 0.2s ease !important;
                }
                
                .mentivio-language-wrapper:hover .mentivio-language-display {
                    background: #4f46e5 !important;
                    color: white !important;
                }
                
                .mentivio-mobile-controls {
                    display: none !important;
                    align-items: center !important;
                    gap: 15px !important;
                }
                
                .mentivio-mobile-menu-btn {
                    display: none !important;
                    background: rgba(79, 70, 229, 0.1) !important;
                    color: #4f46e5 !important;
                    border: 1px solid rgba(79, 70, 229, 0.2) !important;
                    border-radius: 8px !important;
                    font-size: 1.25rem !important;
                    cursor: pointer !important;
                    padding: 8px 16px !important;
                }
                
                @media (max-width: 768px) {
                    .mentivio-navbar-inner { padding: 0 20px !important; }
                    .mentivio-navbar { height: 60px !important; }
                    body { padding-top: 60px !important; }
                    .mentivio-desktop-links { display: none !important; }
                    .mentivio-mobile-controls { display: flex !important; }
                    .mentivio-mobile-menu-btn {
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                        width: 40px !important;
                        height: 40px !important;
                        padding: 8px !important;
                        font-size: 1.2rem !important;
                    }
                    
                    .mentivio-mobile-menu {
                        position: fixed !important;
                        top: 60px !important;
                        left: 0 !important;
                        right: 0 !important;
                        width: 100vw !important;
                        background: white !important;
                        border-bottom: 1px solid #e5e7eb !important;
                        display: none !important;
                        flex-direction: column !important;
                        z-index: 9999 !important;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
                    }
                    
                    @media (prefers-color-scheme: dark) {
                        .mentivio-mobile-menu {
                            background: #0f172a !important;
                            border-bottom: 1px solid #1e293b !important;
                        }
                    }
                    
                    .mentivio-mobile-menu.active { display: flex !important; }
                    
                    .mentivio-mobile-link {
                        text-decoration: none !important;
                        color: #374151 !important;
                        font-weight: 500 !important;
                        font-size: 1rem !important;
                        padding: 16px 20px !important;
                        border-bottom: 1px solid #f3f4f6 !important;
                        transition: all 0.2s ease !important;
                        text-align: center;
                    }
                    
                    .mentivio-mobile-link:last-child { border-bottom: none !important; }
                    
                    .mentivio-mobile-link:hover {
                        background: rgba(79, 70, 229, 0.1) !important;
                        color: #4f46e5 !important;
                    }
                    
                    .mentivio-mobile-link.active {
                        background: rgba(79, 70, 229, 0.1) !important;
                        color: #4f46e5 !important;
                        font-weight: 600 !important;
                    }
                    
                    .mentivio-mobile-link.crisis {
                        color: #ef4444 !important;
                        background: rgba(239, 68, 68, 0.1) !important;
                        border-left: 4px solid #ef4444 !important;
                    }
                    
                    @media (prefers-color-scheme: dark) {
                        .mentivio-mobile-link {
                            color: #e5e7eb !important;
                            border-bottom: 1px solid #1e293b !important;
                        }
                    }
                }
                
                @media (max-width: 480px) {
                    .mentivio-navbar-inner { padding: 0 16px !important; }
                    .mentivio-navbar { height: 55px !important; }
                    body { padding-top: 55px !important; }
                    .mentivio-mobile-menu { top: 55px !important; }
                    .mentivio-logo { font-size: 1.2rem !important; }
                    .mentivio-language-display { font-size: 0.8rem !important; min-width: 50px !important; }
                }
            </style>
            
            <div class="mentivio-navbar" id="mentivioNavbar">
                <div class="mentivio-navbar-inner">
                    <a href="/home.html" class="mentivio-logo">
                        <div style="font-size: 1.5rem;"><i class="fas fa-brain"></i></div>
                        <div id="nav-logo-text">${t.logo}</div>
                    </a>
                    
                    <div class="mentivio-desktop-links" id="mentivioDesktopLinks">
                        <a href="/home.html" id="nav-home" class="mentivio-nav-link ${currentPage === 'home' ? 'active' : ''}">${t.home}</a>
                        <a href="/prediction.html" id="nav-assessment" class="mentivio-nav-link ${currentPage === 'prediction' ? 'active' : ''}">${t.assessment}</a>
                        <a href="/analogy.html" id="nav-visualizer" class="mentivio-nav-link ${currentPage === 'analogy' ? 'active' : ''}">${t.visualizer}</a>
                        <a href="/map.html" id="nav-map" class="mentivio-nav-link ${currentPage === 'map' ? 'active' : ''}">${mapText}</a>
                        <a href="/resources.html" id="nav-resources" class="mentivio-nav-link ${currentPage.includes('resource') || currentPage === 'resources' ? 'active' : ''}">${t.resources}</a>
                        <a href="/about.html" id="nav-about" class="mentivio-nav-link ${currentPage === 'about' ? 'active' : ''}">${t.about}</a>
                        <a href="/crisis-support.html" id="nav-crisis" class="mentivio-nav-link crisis">${t.crisis}</a>

                        <div class="mentivio-language-wrapper">
                            <select class="mentivio-language-select" id="mentivioLanguageSelect">
                                <option value="en" ${currentLang === 'en' ? 'selected' : ''}>English</option>
                                <option value="es" ${currentLang === 'es' ? 'selected' : ''}>Español</option>
                                <option value="vi" ${currentLang === 'vi' ? 'selected' : ''}>Tiếng Việt</option>
                                <option value="zh" ${currentLang === 'zh' ? 'selected' : ''}>中文</option>
                            </select>
                            <div class="mentivio-language-display">${langDisplay}</div>
                        </div>
                    </div>

                    <div class="mentivio-mobile-controls">
                        <div class="mentivio-language-wrapper">
                            <select class="mentivio-language-select mentivio-mobile-language-select" id="mentivioMobileLanguageSelect">
                                <option value="en" ${currentLang === 'en' ? 'selected' : ''}>English</option>
                                <option value="es" ${currentLang === 'es' ? 'selected' : ''}>Español</option>
                                <option value="vi" ${currentLang === 'vi' ? 'selected' : ''}>Tiếng Việt</option>
                                <option value="zh" ${currentLang === 'zh' ? 'selected' : ''}>中文</option>
                            </select>
                            <div class="mentivio-language-display">${langDisplay}</div>
                        </div>
                        
                        <button class="mentivio-mobile-menu-btn" id="mentivioMobileMenuBtn">
                            <i class="fas fa-bars"></i>
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="mentivio-mobile-menu" id="mentivioMobileMenu">
                <a href="/home.html" id="mobile-nav-home" class="mentivio-mobile-link ${currentPage === 'home' ? 'active' : ''}">${t.home}</a>
                <a href="/prediction.html" id="mobile-nav-assessment" class="mentivio-mobile-link ${currentPage === 'prediction' ? 'active' : ''}">${t.assessment}</a>
                <a href="/analogy.html" id="mobile-nav-visualizer" class="mentivio-mobile-link ${currentPage === 'analogy' ? 'active' : ''}">${t.visualizer}</a>
                <a href="/map.html" id="mobile-nav-map" class="mentivio-mobile-link ${currentPage === 'map' ? 'active' : ''}">${mapText}</a>
                <a href="/resources.html" id="mobile-nav-resources" class="mentivio-mobile-link ${currentPage.includes('resource') || currentPage === 'resources' ? 'active' : ''}">${t.resources}</a>
                <a href="/about.html" id="mobile-nav-about" class="mentivio-mobile-link ${currentPage === 'about' ? 'active' : ''}">${t.about}</a>
                <a href="/crisis-support.html" id="mobile-nav-crisis" class="mentivio-mobile-link crisis">${t.crisis}</a>
            </div>
        `;
    }
    
    // ─── Inject navbar ───
    function injectNavbar() {
        // Remove existing navbar
        const existing = document.querySelector('#mentivioNavbar, .mentivio-navbar, .nav-container');
        if (existing) existing.remove();
        
        // Remove mobile menu
        const existingMenu = document.querySelector('#mentivioMobileMenu');
        if (existingMenu) existingMenu.remove();
        
        // Inject new navbar
        document.body.insertAdjacentHTML('afterbegin', buildNavbarHTML());
        
        // Re-attach event listeners
        attachEventListeners();
    }
    
    // ─── Attach event listeners ───
    function attachEventListeners() {
        // Mobile menu toggle
        const mobileBtn = document.getElementById('mentivioMobileMenuBtn');
        const mobileMenu = document.getElementById('mentivioMobileMenu');
        
        if (mobileBtn && mobileMenu) {
            const newBtn = mobileBtn.cloneNode(true);
            mobileBtn.parentNode.replaceChild(newBtn, mobileBtn);
            
            newBtn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                const menu = document.getElementById('mentivioMobileMenu');
                if (menu) {
                    menu.classList.toggle('active');
                    const icon = this.querySelector('i');
                    if (icon) {
                        icon.className = menu.classList.contains('active') ? 'fas fa-times' : 'fas fa-bars';
                    }
                }
            };
        }
        
        // Close menu when clicking outside
        document.removeEventListener('click', closeMobileMenu);
        document.addEventListener('click', closeMobileMenu);
        
        // Language selectors
        document.querySelectorAll('.mentivio-language-select').forEach(select => {
            const newSelect = select.cloneNode(true);
            select.parentNode.replaceChild(newSelect, select);
            
            newSelect.onchange = function() {
                const lang = this.value;
                if (window.globalLangManager) {
                    window.globalLangManager.changeLanguage(lang);
                } else {
                    localStorage.setItem('preferred-language', lang);
                    const url = new URL(window.location);
                    url.searchParams.set('lang', lang);
                    window.location.href = url.toString();
                }
            };
        });
    }
    
    function closeMobileMenu(event) {
        const menu = document.getElementById('mentivioMobileMenu');
        const btn = document.getElementById('mentivioMobileMenuBtn');
        if (menu && btn && !menu.contains(event.target) && !btn.contains(event.target)) {
            menu.classList.remove('active');
            const icon = btn.querySelector('i');
            if (icon) icon.className = 'fas fa-bars';
        }
    }
    
    // ─── Apply translations to navbar ───
    function updateNavbarTranslations(lang) {
        const t = translations[lang] || translations.en;
        const langCodes = { en: 'EN', vi: 'VI', es: 'ES', zh: 'ZH' };
        
        // Update language display
        document.querySelectorAll('.mentivio-language-display').forEach(display => {
            display.textContent = langCodes[lang] || 'EN';
        });
        
        // Update desktop links by ID
        const desktopMap = {
            'nav-home': t.home || 'Home',
            'nav-assessment': t.assessment || 'Self-Assessment',
            'nav-visualizer': t.visualizer || 'Condition Visualizer',
            'nav-map': t.map || 'Mood Map',  // Always ensure this exists
            'nav-resources': t.resources || 'Resources',
            'nav-about': t.about || 'About',
            'nav-crisis': t.crisis || 'Crisis Support'
        };
        Object.keys(desktopMap).forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = desktopMap[id];
        });
        
        // Update mobile links by ID
        const mobileMap = {
            'mobile-nav-home': t.home || 'Home',
            'mobile-nav-assessment': t.assessment || 'Self-Assessment',
            'mobile-nav-visualizer': t.visualizer || 'Condition Visualizer',
            'mobile-nav-map': t.map || 'Mood Map',  // Always ensure this exists
            'mobile-nav-resources': t.resources || 'Resources',
            'mobile-nav-about': t.about || 'About',
            'mobile-nav-crisis': t.crisis || 'Crisis Support'
        };
        Object.keys(mobileMap).forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = mobileMap[id];
        });
        
        // Update logo text
        const logoText = document.getElementById('nav-logo-text');
        if (logoText) logoText.textContent = t.logo || 'Mentivio';
    }
    
    // ─── Setup MutationObserver ───
    function setupNavbarObserver() {
        const observer = new MutationObserver(function(mutations) {
            const navbar = document.getElementById('mentivioNavbar');
            if (!navbar) {
                console.log('Navbar removed, re-injecting...');
                injectNavbar();
                const currentLang = window.globalLangManager ? window.globalLangManager.currentLang : 'en';
                setTimeout(() => updateNavbarTranslations(currentLang), 0);
                return;
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    // ─── Initialize ───
    function init() {
        injectNavbar();
        setupNavbarObserver();
        
        // Listen for language changes
        document.addEventListener('langChanged', function(e) {
            const lang = e.detail.lang;
            setTimeout(() => updateNavbarTranslations(lang), 0);
        });
        
        document.addEventListener('languageChanged', function(e) {
            const lang = e.detail.language || e.detail.lang;
            setTimeout(() => updateNavbarTranslations(lang), 0);
        });
        
        // Load Font Awesome
        if (!document.querySelector('link[href*="font-awesome"]') && !document.querySelector('link[href*="fontawesome"]')) {
            const faLink = document.createElement('link');
            faLink.rel = 'stylesheet';
            faLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
            document.head.appendChild(faLink);
        }
    }
    
    // ─── Run ───
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();