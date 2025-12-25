// ULTRA-SIMPLE INSTANT FOOTER - NO DELAY
(function() {
    // Get language IMMEDIATELY (same as navbar)
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

    // Footer translations
    const translations = {
        en: {
            home: 'Home', assessment: 'Self-Assessment', visualizer: 'Condition Visualizer', resources: 'Resources', about: 'About', crisis: 'Crisis Support', 
            tagline: 'Your mental wellness companion',
            quickLinks: 'Quick Links',
            resources: 'Resources',
            support: 'Support',
            contact: 'Contact',
            privacy: 'Privacy Policy',
            terms: 'Terms of Service',
            crisis: '24/7 Crisis Support',
            email: 'support@mentivio.com',
            copyright: '© 2025 Mentivio. All rights reserved.',
            disclaimer: 'This tool is for informational purposes only and is not a substitute for professional medical advice.'
        },
        vi: {
            home: 'Trang chủ', assessment: 'Tự Đánh Giá', visualizer: 'Trình Hiển Thị', resources: 'Tài Nguyên', about: 'Giới Thiệu', crisis: 'Hỗ Trợ Khủng Hoảng', 
            tagline: 'Người bạn đồng hành sức khỏe tinh thần của bạn',
            quickLinks: 'Liên kết nhanh',
            resources: 'Tài nguyên',
            support: 'Hỗ trợ',
            contact: 'Liên hệ',
            privacy: 'Chính sách bảo mật',
            terms: 'Điều khoản dịch vụ',
            crisis: 'Hỗ trợ khủng hoảng 24/7',
            email: 'support@mentivio.com',
            copyright: '© 2025 Mentivio. Mọi quyền được bảo lưu.',
            disclaimer: 'Công cụ này chỉ dành cho mục đích thông tin và không thay thế cho lời khuyên y tế chuyên nghiệp.'
        },
        es: {
            home: 'Inicio', assessment: 'Autoevaluación', visualizer: 'Visualizador', resources: 'Recursos', about: 'Acerca de', crisis: 'Apoyo en Crisis', 
            tagline: 'Tu compañero de bienestar mental',
            quickLinks: 'Enlaces rápidos',
            resources: 'Recursos',
            support: 'Apoyo',
            contact: 'Contacto',
            privacy: 'Política de privacidad',
            terms: 'Términos de servicio',
            crisis: 'Apoyo en crisis 24/7',
            email: 'support@mentivio.com',
            copyright: '© 2025 Mentivio. Todos los derechos reservados.',
            disclaimer: 'Esta herramienta es solo para fines informativos y no sustituye el asesoramiento médico profesional.'
        },
        zh: {
            home: '首页', assessment: '自我评估', visualizer: '状况可视化', resources: '资源', about: '关于我们', crisis: '危机支持',
            tagline: '您的心理健康伴侣',
            quickLinks: '快速链接',
            resources: '资源',
            support: '支持',
            contact: '联系我们',
            privacy: '隐私政策',
            terms: '服务条款',
            crisis: '24/7 危机支持',
            email: 'support@mentivio.com',
            copyright: '© 2025 Mentivio。保留所有权利。',
            disclaimer: '此工具仅用于提供信息，不能替代专业医疗建议。'
        }
    };
    
    const t = translations[currentLang] || translations.en;
    
    // Create footer HTML with INLINE STYLES
    const footerHTML = `
        <style>
            /* Critical footer styles - loaded immediately with CSS Variables */
            :root {
                --primary: #4f46e5;
                --primary-light: #7c3aed;
                --danger: #ef4444;
                --white: #ffffff;
                --dark: #1e293b;
                --darker: #0f172a;
                --gray-light: #f1f5f9;
                --gray: #94a3b8;
                --footer-bg: rgba(255, 255, 255, 0.95);
                --footer-border: rgba(0, 0, 0, 0.1);
                --footer-text: rgba(0, 0, 0, 0.7);
                --footer-heading: rgba(0, 0, 0, 0.9);
                --radius: 8px;
                --transition: all 0.2s ease;
            }
            
            /* Dark mode variables */
            @media (prefers-color-scheme: dark) {
                :root {
                    --footer-bg: rgba(15, 23, 42, 0.95);
                    --footer-border: rgba(255, 255, 255, 0.1);
                    --footer-text: rgba(255, 255, 255, 0.7);
                    --footer-heading: rgba(255, 255, 255, 0.9);
                }
            }
            
            .footer-container {
                background: var(--footer-bg);
                border-top: 1px solid var(--footer-border);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                margin-top: auto;
            }
            
            .footer-content {
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 40px;
            }
            
            .footer-section {
                display: flex;
                flex-direction: column;
            }
            
            .footer-logo {
                display: flex;
                align-items: center;
                gap: 10px;
                text-decoration: none;
                color: var(--primary);
                font-weight: 600;
                font-size: 1.5rem;
                margin-bottom: 15px;
            }
            
            .footer-tagline {
                color: var(--footer-text);
                font-size: 0.95rem;
                line-height: 1.5;
                margin-bottom: 20px;
            }
            
            .footer-heading {
                color: var(--footer-heading);
                font-weight: 600;
                font-size: 1.1rem;
                margin-bottom: 20px;
            }
            
            .footer-links {
                list-style: none;
                padding: 0;
                margin: 0;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .footer-link {
                text-decoration: none;
                color: var(--footer-text);
                font-size: 0.95rem;
                transition: var(--transition);
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .footer-link:hover {
                color: var(--primary);
                transform: translateX(5px);
            }
            
            .footer-link.crisis {
                color: var(--danger);
                font-weight: 600;
            }
            
            .footer-contact {
                color: var(--footer-text);
                font-size: 0.95rem;
                line-height: 1.6;
                margin: 0;
            }
            
            .footer-bottom {
                max-width: 1200px;
                margin: 0 auto;
                padding: 25px 20px;
                border-top: 1px solid var(--footer-border);
                display: flex;
                flex-direction: column;
                gap: 15px;
                align-items: center;
                text-align: center;
            }
            
            .footer-copyright {
                color: var(--footer-text);
                font-size: 0.9rem;
                opacity: 0.8;
            }
            
            .footer-disclaimer {
                color: var(--footer-text);
                font-size: 0.8rem;
                opacity: 0.7;
                max-width: 600px;
                line-height: 1.5;
            }
            
            .footer-social {
                display: flex;
                gap: 15px;
                margin-top: 10px;
            }
            
            .social-link {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 36px;
                height: 36px;
                background: var(--gray-light);
                color: var(--footer-text);
                border-radius: var(--radius);
                text-decoration: none;
                transition: var(--transition);
            }
            
            .social-link:hover {
                background: var(--primary);
                color: var(--white);
                transform: translateY(-2px);
            }
            
            @media (prefers-color-scheme: dark) {
                .social-link {
                    background: rgba(255, 255, 255, 0.1);
                }
            }
            
            /* Mobile responsive */
            @media (max-width: 768px) {
                .footer-content {
                    grid-template-columns: 1fr;
                    gap: 30px;
                    padding: 30px 20px;
                }
                
                .footer-bottom {
                    padding: 20px;
                }
                
                .footer-disclaimer {
                    font-size: 0.75rem;
                }
            }
        </style>
        
        <footer class="footer-container">
            <div class="footer-content">
                <!-- Logo & Tagline -->
                <div class="footer-section">
                    <a href="/home.html" class="footer-logo">
                        <i class="fas fa-brain"></i>
                        <span>Mentivio</span>
                    </a>
                    <p class="footer-tagline">${t.tagline}</p>
                    <div class="footer-social">
                        <a href="https://www.facebook.com/groups/2027247394734437/" class="social-link" aria-label="Facebook">
                            <i class="fab fa-facebook-f"></i>
                        </a>
                        <a href="https://www.instagram.com/mentivio1?igsh=aTFuNjk4M254NjIy" class="social-link" aria-label="Instagram">
                            <i class="fab fa-instagram"></i>
                        </a>
                         <a href="https://linkedin.com/in/shin-le-b9727a238"  class="social-link" aria-label="LinkedIn">
                            <i class="fab fa-linkedin-in"></i>
                        </a>
                        <a href="https://syl21b.github.io/shinle-portfolio/" class="social-link" aria-label="Portfolio" >
                        <i class="fas fa-briefcase"></i>
                        </a>
                    </div>
                </div>
                
            <!-- Quick Links -->
            <div class="footer-section">
                <h3 class="footer-heading">${t.quickLinks}</h3>
                <ul class="footer-links">
                    <li><a href="/home.html" class="footer-link"><i class="fas fa-home"></i> ${translations[currentLang].home || 'Home'}</a></li>
                    <li><a href="/prediction.html" class="footer-link"><i class="fas fa-clipboard-check"></i> ${translations[currentLang].assessment || 'Self-Assessment'}</a></li>
                    <li><a href="/analogy.html" class="footer-link"><i class="fas fa-eye"></i> ${translations[currentLang].visualizer || 'Condition Visualizer'}</a></li>
                    <li><a href="/about.html" class="footer-link"><i class="fas fa-info-circle"></i> ${translations[currentLang].about || 'About'}</a></li>
                </ul>
            </div>
            
            <!-- Resources & Support -->
            <div class="footer-section">
                <h3 class="footer-heading">${t.support}</h3>
                <ul class="footer-links">
                    <li><a href="/crisis-support.html" class="footer-link crisis"><i class="fas fa-life-ring"></i> ${t.crisis}</a></li>
                    <li><a href="/resources.html" class="footer-link"><i class="fas fa-book"></i> ${t.resources}</a></li>
                    <li><a href="/privacy.html" class="footer-link"><i class="fas fa-shield-alt"></i> ${t.privacy}</a></li>
                    <li><a href="/terms.html" class="footer-link"><i class="fas fa-file-contract"></i> ${t.terms}</a></li>
                </ul>
            </div>
            
            <!-- Contact -->
            <div class="footer-section">
                <h3 class="footer-heading">${t.contact}</h3>
                <p class="footer-contact">
                    <i class="fas fa-envelope" style="margin-right: 8px;"></i>
                    ${t.email}
                </p>
                <!-- ... rest of contact section ... -->
            </div>
        </div>
        
        <!-- Bottom Bar -->
        <div class="footer-bottom">
            <p class="footer-copyright">${t.copyright}</p>
            <p class="footer-disclaimer">${t.disclaimer}</p>
        </div>
    </footer>
`;
    
    // Insert footer at the end of body
    document.body.insertAdjacentHTML('beforeend', footerHTML);
    
    // Load Font Awesome if not already loaded (in case navbar didn't load it)
    if (!document.querySelector('link[href*="font-awesome"]') && !document.querySelector('link[href*="fontawesome"]')) {
        const faLink = document.createElement('link');
        faLink.rel = 'stylesheet';
        faLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
        document.head.appendChild(faLink);
    }

    // Add this inside the load-footer.js IIFE
    document.addEventListener('langChanged', (e) => {
            const newLang = e.detail.lang;
            const t = translations[newLang] || translations.en;

            // 1. Update Footer Headings
            const headings = document.querySelectorAll('.footer-heading');
            if (headings[0]) headings[0].textContent = t.quickLinks;
            if (headings[1]) headings[1].textContent = t.support;
            if (headings[2]) headings[2].textContent = t.contact;

            // 2. Update the Quick Links section
            const quickLinks = document.querySelectorAll('.footer-section')[1].querySelectorAll('.footer-link');
            if (quickLinks.length >= 4) {
                quickLinks[0].innerHTML = `<i class="fas fa-home"></i> ${t.home}`;
                quickLinks[1].innerHTML = `<i class="fas fa-clipboard-check"></i> ${t.assessment}`;
                quickLinks[2].innerHTML = `<i class="fas fa-eye"></i> ${t.visualizer}`;
                quickLinks[3].innerHTML = `<i class="fas fa-info-circle"></i> ${t.about}`;
            }

            // 3. Update the Support section links
            const supportLinks = document.querySelectorAll('.footer-section')[2].querySelectorAll('.footer-link');
            if (supportLinks.length >= 4) {
                supportLinks[0].innerHTML = `<i class="fas fa-life-ring"></i> ${t.crisis}`;
                supportLinks[1].innerHTML = `<i class="fas fa-book"></i> ${t.resources}`;
                supportLinks[2].innerHTML = `<i class="fas fa-shield-alt"></i> ${t.privacy}`;
                supportLinks[3].innerHTML = `<i class="fas fa-file-contract"></i> ${t.terms}`;
            }

            // 4. Update Tagline, Copyright, and Contact
            const tagline = document.querySelector('.footer-tagline');
            if (tagline) tagline.textContent = t.tagline;
            
            const copyright = document.querySelector('.footer-copyright');
            if (copyright) copyright.textContent = t.copyright;

            const contactEmail = document.querySelector('.footer-contact');
            if (contactEmail) {
                contactEmail.innerHTML = `<i class="fas fa-envelope" style="margin-right: 8px;"></i> ${t.email}`;
            }
        });

    // Add smooth scroll for anchor links within the footer
    document.querySelectorAll('.footer-link[href^="#"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
})();