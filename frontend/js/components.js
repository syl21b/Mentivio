// Cache for components
const componentCache = new Map();

// Load components with caching
function loadComponents() {
    loadNavbar();
    loadFooter();
}

// Optimized navbar loading with caching
function loadNavbar() {
    const cacheKey = 'navbar';
    
    // Check cache first
    if (componentCache.has(cacheKey)) {
        document.body.insertAdjacentHTML('afterbegin', componentCache.get(cacheKey));
        initNavbar();
        return;
    }
    
    const navbarPath = getComponentPath('navbar.html');
    
    fetch(navbarPath)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.text();
        })
        .then(html => {
            // Cache the HTML
            componentCache.set(cacheKey, html);
            document.body.insertAdjacentHTML('afterbegin', html);
            initNavbar();
        })
        .catch(error => {
            console.error('Failed to load navbar:', error);
            createEmergencyNavbar();
        });
}

// Optimized footer loading with caching
function loadFooter() {
    const cacheKey = 'footer';
    
    if (componentCache.has(cacheKey)) {
        document.body.insertAdjacentHTML('beforeend', componentCache.get(cacheKey));
        return;
    }
    
    const footerPath = getComponentPath('footer.html');
    
    fetch(footerPath)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.text();
        })
        .then(html => {
            componentCache.set(cacheKey, html);
            document.body.insertAdjacentHTML('beforeend', html);
        })
        .catch(error => {
            console.error('Failed to load footer:', error);
            createEmergencyFooter();
        });
}

// Helper function to determine correct path - FIXED VERSION
function getComponentPath(filename) {
    const currentPath = window.location.pathname;
    const isHomePage = currentPath === '/' || currentPath.endsWith('Home.html') || currentPath.endsWith('index.html');
    
    if (isHomePage) {
        return filename; // For home page, components are in same directory
    } else if (currentPath.includes('/resources/') || currentPath.includes('/pages/')) {
        return `../${filename}`; // For subdirectories, go up one level
    } else {
        return filename; // Default to same directory
    }
}

// Fast navbar initialization
function initNavbar() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');
    
    if (mobileMenuBtn && navLinks) {
        // Ensure menu starts closed
        navLinks.classList.remove('active');
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
        
        // Mobile menu toggle
        mobileMenuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isOpening = !navLinks.classList.contains('active');
            
            navLinks.classList.toggle('active');
            mobileMenuBtn.classList.toggle('active');
            mobileMenuBtn.setAttribute('aria-expanded', isOpening ? 'true' : 'false');
            
            const icon = this.querySelector('i');
            if (icon) {
                icon.className = isOpening ? 'fas fa-times' : 'fas fa-bars';
            }
            document.body.style.overflow = isOpening ? 'hidden' : '';
        });
        
        // Close menu when clicking links
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                closeMobileMenu();
            });
        });
        
        // Set active navigation
        setActiveNav();
    }
}

function closeMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');
    
    if (navLinks) navLinks.classList.remove('active');
    if (mobileMenuBtn) {
        mobileMenuBtn.classList.remove('active');
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
        const icon = mobileMenuBtn.querySelector('i');
        if (icon) icon.className = 'fas fa-bars';
    }
    document.body.style.overflow = '';
}

function setActiveNav() {
    const currentPage = window.location.pathname.split('/').pop() || 'Home.html';
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        const linkHref = link.getAttribute('href');
        const linkPage = linkHref.split('/').pop();
        
        if (linkPage === currentPage || (currentPage === '' && linkPage === 'Home.html')) {
            link.classList.add('active');
        }
    });
}

// Emergency fallbacks
function createEmergencyNavbar() {
    const basePath = getComponentPath('').replace('navbar.html', '');
    const navbarHTML = `
        <nav class="navbar">
            <div class="nav-container">
                <a href="${basePath}Home.html" class="logo">
                    <div class="logo-icon"><i class="fas fa-brain"></i></div>
                    <div class="logo-text">Mentivio</div>
                </a>
                <button class="mobile-menu-btn" id="mobileMenuBtn" aria-label="Toggle navigation menu">
                    <i class="fas fa-bars"></i>
                </button>
                <div class="nav-links" id="navLinks">
                    <a href="${basePath}Home.html">Home</a>
                    <a href="${basePath}MenHel_prediction.html">Self-Assessment</a>
                    <a href="${basePath}MenHel_analogy.html">Condition Visualizer</a>
                    <a href="${basePath}resources.html">Resources</a>
                    <a href="${basePath}About.html">About</a>
                    <a href="${basePath}crisis-support.html" class="crisis-link">Crisis Support</a>
                </div>
            </div>
        </nav>
    `;
    document.body.insertAdjacentHTML('afterbegin', navbarHTML);
    initNavbar();
}

function createEmergencyFooter() {
    const basePath = getComponentPath('').replace('footer.html', '');
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
                        <li><a href="${basePath}Home.html">Home</a></li>
                        <li><a href="${basePath}MenHel_prediction.html">Self-Assessment</a></li>
                        <li><a href="${basePath}MenHel_analogy.html">Condition Visualizer</a></li>
                        <li><a href="${basePath}resources.html">Resources</a></li>
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

// Start loading immediately
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadComponents);
} else {
    loadComponents();
}