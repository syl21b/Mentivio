// ULTRA-SIMPLE INSTANT NAVBAR - NO DELAY
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
            /* Critical navbar styles - loaded immediately with CSS Variables */
            :root {
                --primary: #4f46e5;
                --primary-light: #7c3aed;
                --danger: #ef4444;
                --white: #ffffff;
                --dark: #1e293b;
                --darker: #0f172a;
                --gray-light: #f1f5f9;
                --gray: #94a3b8;
                --navbar-bg: rgba(255, 255, 255, 0.55);
                --navbar-border: rgba(0, 0, 0, 0.12);
                --navbar-link: rgba(0, 0, 0, 0.75);
                --navbar-logo: rgba(0, 0, 0, 0.95);
                --navbar-btn-bg: rgba(255, 255, 255, 0.4);
                --navbar-btn-color: rgba(0, 0, 0, 0.85);
                --radius: 8px;
                --transition: all 0.2s ease;
                --shadow-lg: 0 4px 12px rgba(0, 0, 0, 0.08);
            }
            
            /* Dark mode variables */
            @media (prefers-color-scheme: dark) {
                :root {
                    --navbar-bg: rgba(15, 15, 15, 0.55);
                    --navbar-border: rgba(255, 255, 255, 0.12);
                    --navbar-link: rgba(255, 255, 255, 0.75);
                    --navbar-logo: rgba(255, 255, 255, 0.95);
                    --navbar-btn-bg: rgba(255, 255, 255, 0.1);
                    --navbar-btn-color: rgba(255, 255, 255, 0.95);
                }
            }
            
            .nav-container {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: 70px;
                z-index: 1000;
                display: flex;
                align-items: center;
                backdrop-filter: blur(50px);
                -webkit-backdrop-filter: blur(50px);
                
            }
            
            .nav-inner {
                width: 100%;
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .nav-logo {
                display: flex;
                align-items: center;
                gap: 10px;
                text-decoration: none;
                color: var(--primary);
                font-weight: 600;
                font-size: 1.25rem;
                transition: var(--transition);
            }
            
            .nav-logo:hover {
                color: var(--primary-light);
            }
            
            .nav-links {
                display: flex;
                align-items: center;
                gap: 25px;
            }
            
            .nav-link {
                text-decoration: none;
                color: var(--navbar-link);
                font-weight: 500;
                transition: var(--transition);
                padding: 6px 12px;
                border-radius: var(--radius);
            }
            
            .nav-link:hover {
                color: var(--primary);
                background: var(--navbar-btn-bg);
            }
            
            .nav-link.active {
                color: var(--primary);
                font-weight: 600;
                background: var(--navbar-btn-bg);
            }
            
            .nav-link.crisis {
                color: var(--danger) !important;
                font-weight: 600;
                background: rgba(239, 68, 68, 0.1);
            }
            
            .nav-link.crisis:hover {
                background: rgba(239, 68, 68, 0.2);
            }
            
            .language-select-wrapper {
                position: relative;
            }
            
            .language-select {
                opacity: 0;
                position: absolute;
                width: 100%;
                height: 100%;
                cursor: pointer;
                z-index: 1;
            }
            
            .language-select-display {
                padding: 6px 12px;
                background: var(--navbar-btn-bg);
                color: var(--navbar-btn-color);
                border-radius: var(--radius);
                font-size: 0.9rem;
                font-weight: 500;
                transition: var(--transition);
            }
            
            .language-select-wrapper:hover .language-select-display {
                background: var(--gray-light);
            }
            
            @media (prefers-color-scheme: dark) {
                .language-select-wrapper:hover .language-select-display {
                    background: rgba(255, 255, 255, 0.2);
                }
            }
            
            .mobile-controls {
                display: none;
                align-items: center;
                gap: 15px;
            }
            
            .mobile-menu-btn {
                background: var(--navbar-btn-bg);
                color: var(--navbar-btn-color);
                border: 1px solid var(--navbar-border);
                border-radius: var(--radius);
                font-size: 1.25rem;
                cursor: pointer;
                padding: 8px 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: var(--transition);
            }
            
            .mobile-menu-btn:hover {
                background: var(--gray-light);
            }
            
            @media (prefers-color-scheme: dark) {
                .mobile-menu-btn:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
            }
            
            /* Mobile responsive styles */
            @media (max-width: 768px) {
                .mobile-controls {
                    display: flex;
                }
                
                .nav-links {
                    position: fixed;
                    top: 70px;
                    left: 0;
                    right: 0;
                    background: var(--white);
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    flex-direction: column;
                    gap: 0;
                    padding: 20px 0;
                    border-bottom: 1px solid var(--navbar-border);
                    box-shadow: var(--shadow-lg);
                    display: none;
                    z-index: 999;
                }
                
                @media (prefers-color-scheme: dark) {
                    .nav-links {
                        background: var(--darker);
                    }
                }
                
                .nav-links.active {
                    display: flex;
                }
                
                .nav-link {
                    width: 100%;
                    padding: 15px 20px;
                    text-align: center;
                    border-bottom: 1px solid var(--gray-light);
                    border-radius: 0;
                }
                
                @media (prefers-color-scheme: dark) {
                    .nav-link {
                        border-bottom: 1px solid var(--dark);
                    }
                }
                
                .nav-link:last-child {
                    border-bottom: none;
                }
                
                .nav-link:hover, .nav-link.active {
                    background: var(--gray-light);
                }
                
                @media (prefers-color-scheme: dark) {
                    .nav-link:hover, .nav-link.active {
                        background: rgba(255, 255, 255, 0.1);
                    }
                }
                
                /* Hide desktop language selector on mobile */
                .nav-links .language-select-wrapper {
                    display: none;
                }
            }
            
            /* Desktop: hide mobile language selector */
            @media (min-width: 769px) {
                .mobile-controls .language-select-wrapper {
                    display: none;
                }
            }
        </style>
        
    
    <nav class="nav-container">
        <div class="nav-inner">
            <!-- Logo -->
            <a href="/home.html" class="nav-logo">
                <div style="font-size: 1.5rem;"><i class="fas fa-brain"></i></div>
                <div>${t.logo}</div>
            </a>
            
            <!-- Desktop Navigation -->
            <div class="nav-links" id="navLinks">
                <a href="/home.html" class="nav-link ${currentPage === 'home' ? 'active' : ''}">${t.home}</a>
                <a href="/prediction.html" class="nav-link ${currentPage === 'prediction' ? 'active' : ''}">${t.assessment}</a>
                <a href="/analogy.html" class="nav-link ${currentPage === 'analogy' ? 'active' : ''}">${t.visualizer}</a>
                <a href="/resources.html" class="nav-link ${currentPage.includes('resource') || currentPage === 'resources' ? 'active' : ''}">${t.resources}</a>
                <a href="/about.html" class="nav-link ${currentPage === 'about' ? 'active' : ''}">${t.about}</a>
                <a href="/crisis-support.html" class="nav-link crisis">${t.crisis}</a>
                
                <!-- Desktop Language Dropdown -->
                <div class="language-select-wrapper">
                    <select class="language-select" id="languageSelect" name="language">
                        <option value="en" ${currentLang === 'en' ? 'selected' : ''}>English</option>
                        <option value="vi" ${currentLang === 'vi' ? 'selected' : ''}>Vietnamese</option>
                        <option value="es" ${currentLang === 'es' ? 'selected' : ''}>Spanish</option>
                        <option value="zh" ${currentLang === 'zh' ? 'selected' : ''}>Chinese</option>
                    </select>
                    <div class="language-select-display">${langDisplay}</div>
                </div>
            </div>
            
            <!-- Mobile Controls -->
            <div class="mobile-controls">
                <!-- Mobile Language Dropdown (visible only on mobile) -->
                <div class="language-select-wrapper">
                    <select class="language-select mobile-language-select" id="mobileLanguageSelect" name="mobile-language">
                        <option value="en" ${currentLang === 'en' ? 'selected' : ''}>English</option>
                        <option value="vi" ${currentLang === 'vi' ? 'selected' : ''}>Vietnamese</option>
                        <option value="es" ${currentLang === 'es' ? 'selected' : ''}>Spanish</option>
                        <option value="zh" ${currentLang === 'zh' ? 'selected' : ''}>Chinese</option>
                    </select>
                    <div class="language-select-display">${langDisplay}</div>
                </div>
                
                <button class="mobile-menu-btn" aria-label="Toggle menu">
                    <i class="fas fa-bars"></i>
                </button>
            </div>
        </div>
    </nav>
`;
    
    // Add body padding for navbar
    document.body.style.paddingTop = '70px';
    document.body.style.margin = '0';
    
    // Insert navbar FIRST THING
    document.body.insertAdjacentHTML('afterbegin', navbarHTML);
    
    // Mobile menu toggle
    const mobileBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.getElementById('navLinks');
    
    if (mobileBtn && navLinks) {
        mobileBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            navLinks.classList.toggle('active');
            const icon = this.querySelector('i');
            icon.className = navLinks.classList.contains('active') ? 'fas fa-times' : 'fas fa-bars';
        };
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (navLinks && mobileBtn && !navLinks.contains(event.target) && !mobileBtn.contains(event.target)) {
                navLinks.classList.remove('active');
                const icon = mobileBtn.querySelector('i');
                if (icon) icon.className = 'fas fa-bars';
            }
        });
    }

    // Add this inside the load-navbar.js IIFE
    document.addEventListener('langChanged', (e) => {
        const newLang = e.detail.lang;
        const t = translations[newLang] || translations.en;
        const langCodes = { en: 'EN', vi: 'VI', es: 'ES', zh: 'ZH' };
        
        // 1. Update the visible abbreviation (e.g., "EN" to "VI")
        document.querySelectorAll('.language-select-display').forEach(display => {
            display.textContent = langCodes[newLang] || 'EN';
        });

        // 2. Update Navbar Links instantly
        const navLinks = document.getElementById('navLinks');
        if (navLinks) {
            const links = navLinks.querySelectorAll('.nav-link');
            // Order matches your translations object keys
            const keys = ['home', 'assessment', 'visualizer', 'resources', 'about', 'crisis'];
            links.forEach((link, index) => {
                if (keys[index]) link.textContent = t[keys[index]];
            });
        }
        
        // 3. Update Logo text
        const logoText = document.querySelector('.nav-logo div:last-child');
        if (logoText) logoText.textContent = t.logo;
    });
        
    // Language switcher - for both desktop and mobile
    document.querySelectorAll('.language-select').forEach(select => {
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

    
    // Load Font Awesome if not already loaded
    if (!document.querySelector('link[href*="font-awesome"]') && !document.querySelector('link[href*="fontawesome"]')) {
        const faLink = document.createElement('link');
        faLink.rel = 'stylesheet';
        faLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
        document.head.appendChild(faLink);
    }
})();