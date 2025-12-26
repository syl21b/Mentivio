
// ULTRA-SIMPLE INSTANT NAVBAR - FORCED FULL WIDTH
(function() {
    // Get language IMMEDIATELY (no async)
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
    
    // Simple translations - EMBEDDED for instant access
    const translations = {
        en: { home: 'Home', assessment: 'Self-Assessment', visualizer: 'Condition Visualizer', resources: 'Resources', about: 'About', crisis: 'Crisis Support', logo: 'Mentivio' },
        vi: { home: 'Trang chủ', assessment: 'Tự Đánh Giá', visualizer: 'Trình Hiển Thị', resources: 'Tài Nguyên', about: 'Giới Thiệu', crisis: 'Hỗ Trợ Khủng Hoảng', logo: 'Mentivio' },
        es: { home: 'Inicio', assessment: 'Autoevaluación', visualizer: 'Visualizador', resources: 'Recursos', about: 'Acerca de', crisis: 'Apoyo en Crisis', logo: 'Mentivio' },
        zh: { home: '首页', assessment: '自我评估', visualizer: '状况可视化', resources: '资源', about: '关于我们', crisis: '危机支持', logo: 'Mentivio' }
    };
    
    const t = translations[currentLang] || translations.en;
    const langCodes = { en: 'EN', vi: 'VI', es: 'ES', zh: 'ZH' };
    const langDisplay = langCodes[currentLang] || 'EN';
    
    // Get current page for active link
    const path = window.location.pathname;
    let currentPage = path.split('/').pop().replace('.html', '') || 'home';
    if (currentPage === 'index') currentPage = 'home';
    
    // Create navbar HTML with INLINE STYLES - NO EXTERNAL DEPENDENCIES
    const navbarHTML = `
        <style>
            /* RESET and FORCE full width */
            * {
                box-sizing: border-box !important;
            }
            
            body {
                margin: 0 !important;
                padding: 0 !important;
                overflow-x: hidden !important;
            }
            
            /* NAVBAR CONTAINER - FORCED FULL WIDTH */
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
            
            /* Dark mode */
            @media (prefers-color-scheme: dark) {
                .mentivio-navbar {
                    background: #0f172a !important;
                    border-bottom: 1px solid #1e293b !important;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
                }
            }
            
            /* NAVBAR INNER - full width flex container */
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
            
            .mentivio-logo:hover {
                color: #7c3aed !important;
            }
            
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
            
            /* Dark mode text colors */
            @media (prefers-color-scheme: dark) {
                .mentivio-nav-link {
                    color: #e5e7eb !important;
                }
                .mentivio-nav-link:hover {
                    color: #a5b4fc !important;
                }
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
            
            /* MOBILE CONTROLS - hidden on desktop */
            .mentivio-mobile-controls {
                display: none !important;
                align-items: center !important;
                gap: 15px !important;
            }
            
            /* MOBILE MENU BUTTON */
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
            
            /* MOBILE RESPONSIVE */
            @media (max-width: 768px) {
                .mentivio-navbar-inner {
                    padding: 0 20px !important;
                }
                
                /* Hide desktop links on mobile */
                .mentivio-desktop-links {
                    display: none !important;
                }
                
                /* Show mobile controls */
                .mentivio-mobile-controls {
                    display: flex !important;
                }
                
                /* Show mobile menu button */
                .mentivio-mobile-menu-btn {
                    display: flex !important;
                }
                
                /* MOBILE DROPDOWN MENU */
                .mentivio-mobile-menu {
                    position: fixed !important;
                    top: 70px !important;
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
                
                .mentivio-mobile-menu.active {
                    display: flex !important;
                }
                
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
                
                .mentivio-mobile-link:last-child {
                    border-bottom: none !important;
                }
                
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
            
            /* VERY SMALL MOBILE */
            @media (max-width: 480px) {
                .mentivio-navbar-inner {
                    padding: 0 16px !important;
                }
            }
        </style>
        
        <!-- NAVBAR -->
        <div class="mentivio-navbar">
            <div class="mentivio-navbar-inner">
                <!-- Logo -->
                <a href="/home.html" class="mentivio-logo">
                    <div style="font-size: 1.5rem;"><i class="fas fa-brain"></i></div>
                    <div>${t.logo}</div>
                </a>
                
                <!-- Desktop Navigation -->
                <div class="mentivio-desktop-links" id="mentivioDesktopLinks">
                    <a href="/home.html" class="mentivio-nav-link ${currentPage === 'home' ? 'active' : ''}">${t.home}</a>
                    <a href="/prediction.html" class="mentivio-nav-link ${currentPage === 'prediction' ? 'active' : ''}">${t.assessment}</a>
                    <a href="/analogy.html" class="mentivio-nav-link ${currentPage === 'analogy' ? 'active' : ''}">${t.visualizer}</a>
                    <a href="/resources.html" class="mentivio-nav-link ${currentPage.includes('resource') || currentPage === 'resources' ? 'active' : ''}">${t.resources}</a>
                    <a href="/about.html" class="mentivio-nav-link ${currentPage === 'about' ? 'active' : ''}">${t.about}</a>
                    <a href="/crisis-support.html" class="mentivio-nav-link crisis">${t.crisis}</a>
                    
                    <!-- Desktop Language Dropdown -->
                    <div class="mentivio-language-wrapper">
                        <select class="mentivio-language-select" id="mentivioLanguageSelect">
                            <option value="en" ${currentLang === 'en' ? 'selected' : ''}>English</option>
                            <option value="vi" ${currentLang === 'vi' ? 'selected' : ''}>Vietnamese</option>
                            <option value="es" ${currentLang === 'es' ? 'selected' : ''}>Spanish</option>
                            <option value="zh" ${currentLang === 'zh' ? 'selected' : ''}>Chinese</option>
                        </select>
                        <div class="mentivio-language-display">${langDisplay}</div>
                    </div>
                </div>
                
                <!-- Mobile Controls -->
                <div class="mentivio-mobile-controls">
                    <!-- Mobile Language (abbreviation only) -->
                    <div class="mentivio-language-wrapper">
                        <select class="mentivio-language-select mentivio-mobile-language-select" id="mentivioMobileLanguageSelect">
                            <option value="en" ${currentLang === 'en' ? 'selected' : ''}>English</option>
                            <option value="vi" ${currentLang === 'vi' ? 'selected' : ''}>Vietnamese</option>
                            <option value="es" ${currentLang === 'es' ? 'selected' : ''}>Spanish</option>
                            <option value="zh" ${currentLang === 'zh' ? 'selected' : ''}>Chinese</option>
                        </select>
                        <div class="mentivio-language-display">${langDisplay}</div>
                    </div>
                    
                    <button class="mentivio-mobile-menu-btn" id="mentivioMobileMenuBtn">
                        <i class="fas fa-bars"></i>
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Mobile Menu (hidden by default) -->
        <div class="mentivio-mobile-menu" id="mentivioMobileMenu">
            <a href="/home.html" class="mentivio-mobile-link ${currentPage === 'home' ? 'active' : ''}">${t.home}</a>
            <a href="/prediction.html" class="mentivio-mobile-link ${currentPage === 'prediction' ? 'active' : ''}">${t.assessment}</a>
            <a href="/analogy.html" class="mentivio-mobile-link ${currentPage === 'analogy' ? 'active' : ''}">${t.visualizer}</a>
            <a href="/resources.html" class="mentivio-mobile-link ${currentPage.includes('resource') || currentPage === 'resources' ? 'active' : ''}">${t.resources}</a>
            <a href="/about.html" class="mentivio-mobile-link ${currentPage === 'about' ? 'active' : ''}">${t.about}</a>
            <a href="/crisis-support.html" class="mentivio-mobile-link crisis">${t.crisis}</a>
        </div>
    `;
    
    // FIRST, remove any existing navbar if present
    const existingNavbar = document.querySelector('.nav-container, .mentivio-navbar');
    if (existingNavbar) {
        existingNavbar.remove();
    }
    
    // Remove existing body padding
    document.body.style.paddingTop = '70px';
    document.body.style.margin = '0';
    document.body.style.overflowX = 'hidden';
    
    // Insert navbar at the VERY BEGINNING of body
    document.body.insertAdjacentHTML('afterbegin', navbarHTML);
    
    // Mobile menu toggle
    const mobileBtn = document.getElementById('mentivioMobileMenuBtn');
    const mobileMenu = document.getElementById('mentivioMobileMenu');
    
    if (mobileBtn && mobileMenu) {
        mobileBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            mobileMenu.classList.toggle('active');
            const icon = this.querySelector('i');
            icon.className = mobileMenu.classList.contains('active') ? 'fas fa-times' : 'fas fa-bars';
        };
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (mobileMenu && mobileBtn && !mobileMenu.contains(event.target) && !mobileBtn.contains(event.target)) {
                mobileMenu.classList.remove('active');
                const icon = mobileBtn.querySelector('i');
                if (icon) icon.className = 'fas fa-bars';
            }
        });
    }

    // Language switcher - for all language selects
    document.querySelectorAll('.mentivio-language-select').forEach(select => {
        select.onchange = function() {
            const lang = this.value;
            
            // Use global language manager if available
            if (window.globalLangManager) {
                window.globalLangManager.changeLanguage(lang);
            } else {
                // Fallback to original behavior
                localStorage.setItem('preferred-language', lang);
                const url = new URL(window.location);
                url.searchParams.set('lang', lang);
                window.location.href = url.toString();
            }
        };
    });

    // Language change event listener
    document.addEventListener('langChanged', (e) => {
        const newLang = e.detail.lang;
        const t = translations[newLang] || translations.en;
        const langCodes = { en: 'EN', vi: 'VI', es: 'ES', zh: 'ZH' };
        
        // Update language display
        document.querySelectorAll('.mentivio-language-display').forEach(display => {
            display.textContent = langCodes[newLang] || 'EN';
        });

        // Update desktop links
        const desktopLinks = document.querySelectorAll('.mentivio-nav-link');
        const keys = ['home', 'assessment', 'visualizer', 'resources', 'about', 'crisis'];
        desktopLinks.forEach((link, index) => {
            if (keys[index]) link.textContent = t[keys[index]];
        });

        // Update mobile links
        const mobileLinks = document.querySelectorAll('.mentivio-mobile-link');
        mobileLinks.forEach((link, index) => {
            if (keys[index]) link.textContent = t[keys[index]];
        });

        // Update logo text
        const logoText = document.querySelector('.mentivio-logo div:last-child');
        if (logoText) logoText.textContent = t.logo;
    });

    // Load Font Awesome if not already loaded
    if (!document.querySelector('link[href*="font-awesome"]') && !document.querySelector('link[href*="fontawesome"]')) {
        const faLink = document.createElement('link');
        faLink.rel = 'stylesheet';
        faLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
        document.head.appendChild(faLink);
    }
})();
