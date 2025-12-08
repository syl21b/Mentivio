/**
 * Component Loader - Optimized with caching
 * Loads navbar, footer, and head components dynamically
 */

class ComponentLoader {
    constructor() {
        this.componentCache = new Map();
        this.initialized = false;
        this.config = {
            componentDir: '../frontend/',
            debug: true
        };
        this.init();
    }
    
    async init() {
        if (this.initialized) {
            this.log('Already initialized');
            return;
        }
        
        this.log('Initializing ComponentLoader...');
        
        try {
            // Load head first (contains CSS and meta tags)
            await this.loadHead();
            
            // Load navbar and footer in parallel
            await Promise.all([
                this.loadNavbar(),
                this.loadFooter()
            ]);
            
            this.initialized = true;
            this.log('All components loaded successfully', 'success');
            
            // Dispatch custom event when done
            document.dispatchEvent(new CustomEvent('componentsLoaded', {
                detail: { timestamp: Date.now() }
            }));
            
        } catch (error) {
            this.log(`Initialization failed: ${error.message}`, 'error');
        }
    }
    
    // Debug logging helper
    log(message, level = 'info') {
        if (!this.config.debug) return;
        
        const styles = {
            info: 'color: #3498db',
            success: 'color: #2ecc71',
            warning: 'color: #f39c12',
            error: 'color: #e74c3c'
        };
        
        console.log(`%c[ComponentLoader] ${message}`, styles[level] || styles.info);
    }
    
    // Determine correct path based on current location
    getComponentPath(filename) {
        const currentPath = window.location.pathname;
        
        this.log(`Calculating path for: ${filename} on page: ${currentPath}`);
        
        // Remove any leading ../ from filename if present
        const cleanFilename = filename.replace(/^\.\.\//, '');
        
        // Determine base path
        let basePath = this.config.componentDir;
        
        // Check if we're in the resources directory
        if (currentPath.includes('/resources/')) {
            // For files inside resources/ directory
            if (currentPath.endsWith('.html') && !currentPath.includes('/frontend/')) {
                basePath = '../frontend/';
            } else {
                basePath = '../../frontend/';
            }
        } else if (currentPath.includes('/pages/')) {
            basePath = '../../frontend/';
        } else if (currentPath.includes('/frontend/')) {
            basePath = '';
        } else if (currentPath === '/' || currentPath.endsWith('Home.html') || currentPath.endsWith('index.html')) {
            basePath = 'frontend/';
        }
        
        const fullPath = basePath + cleanFilename;
        this.log(`Resolved path: ${fullPath}`, 'success');
        return fullPath;
    }

    
    // Load component with caching
    async loadComponent(name, filename, position = 'beforeend', element = document.body) {
        const cacheKey = `${name}_${filename}`;
        
        // Check cache first
        if (this.componentCache.has(cacheKey)) {
            this.log(`Loading ${name} from cache`, 'success');
            element.insertAdjacentHTML(position, this.componentCache.get(cacheKey));
            return this.componentCache.get(cacheKey);
        }
        
        try {
            const path = this.getComponentPath(filename);
            this.log(`Fetching ${name} from: ${path}`);
            
            const response = await fetch(path);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const html = await response.text();
            
            // Validate HTML
            if (!html.trim()) {
                throw new Error('Empty response');
            }
            
            // Cache the component
            this.componentCache.set(cacheKey, html);
            
            // Insert into DOM
            element.insertAdjacentHTML(position, html);
            this.log(`Successfully loaded ${name}`, 'success');
            
            return html;
        } catch (error) {
            this.log(`Failed to load ${name}: ${error.message}`, 'error');
            throw error;
        }
    }
    
    // Load head component
    async loadHead() {
        try {
            await this.loadComponent('head', 'head.html', 'beforeend', document.head);
        } catch (error) {
            this.log('Falling back to emergency head', 'warning');
            this.createEmergencyHead();
        }
    }
    
    // Load navbar component
    async loadNavbar() {
        try {
            await this.loadComponent('navbar', 'navbar.html', 'afterbegin');
            this.initNavbar();
        } catch (error) {
            this.log('Falling back to emergency navbar', 'warning');
            this.createEmergencyNavbar();
        }
    }
    
    // Load footer component
    async loadFooter() {
        try {
            await this.loadComponent('footer', 'footer.html', 'beforeend');
        } catch (error) {
            this.log('Falling back to emergency footer', 'warning');
            this.createEmergencyFooter();
        }
    }
    
    // Initialize navbar functionality
    initNavbar() {
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const navLinks = document.getElementById('navLinks');
        
        if (!mobileMenuBtn || !navLinks) {
            this.log('Navbar elements not found', 'warning');
            return;
        }
        
        // Ensure menu starts closed
        navLinks.classList.remove('active');
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
        
        // Mobile menu toggle
        mobileMenuBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const isOpening = !navLinks.classList.contains('active');
            navLinks.classList.toggle('active');
            mobileMenuBtn.classList.toggle('active');
            mobileMenuBtn.setAttribute('aria-expanded', isOpening.toString());
            
            // Update icon
            const icon = mobileMenuBtn.querySelector('i');
            if (icon) {
                icon.className = isOpening ? 'fas fa-times' : 'fas fa-bars';
            }
            
            // Prevent body scrolling when menu is open
            document.body.style.overflow = isOpening ? 'hidden' : '';
            this.log(`Mobile menu ${isOpening ? 'opened' : 'closed'}`);
        });
        
        // Close menu when clicking links
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navLinks.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                this.closeMobileMenu();
            }
        });
        
        // Close menu on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeMobileMenu();
            }
        });
        
        // Set active navigation
        this.setActiveNav();
        
        this.log('Navbar initialized');
    }
    
    // Set active navigation based on current page
    setActiveNav() {
        const currentPage = window.location.pathname.split('/').pop() || 'Home.html';
        const navLinks = document.querySelectorAll('.nav-links a');
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            const href = link.getAttribute('href');
            
            // Check for resources directory
            const isInResourcesDir = window.location.pathname.includes('/resources/');
            
            if (href && (href.includes(currentPage) || 
                (currentPage === '' && href.includes('Home.html')) ||
                (currentPage === 'index.html' && href.includes('Home.html')) ||
                (isInResourcesDir && href.includes('resources.html')))) {
                link.classList.add('active');
            }
        });
        
        this.log(`Active nav set for: ${currentPage}`);
    }
    
    // Close mobile menu
    closeMobileMenu() {
        const navLinks = document.getElementById('navLinks');
        const mobileBtn = document.getElementById('mobileMenuBtn');
        
        if (navLinks) navLinks.classList.remove('active');
        if (mobileBtn) {
            mobileBtn.classList.remove('active');
            mobileBtn.setAttribute('aria-expanded', 'false');
            const icon = mobileBtn.querySelector('i');
            if (icon) icon.className = 'fas fa-bars';
        }
        
        document.body.style.overflow = '';
    }
    
    // Calculate relative prefix for URLs
    calculateRelativePrefix() {
        const currentPath = window.location.pathname;
        
        // Check if we're accessing an HTML file in the resources directory
        if (currentPath.includes('/resources/') && currentPath.endsWith('.html')) {
            return '../frontend/';
        } else if (currentPath.includes('/resources/')) {
            return '../../frontend/';
        } else if (currentPath.includes('/pages/')) {
            return '../../frontend/';
        } else if (currentPath.includes('/frontend/')) {
            return '';
        } else if (currentPath === '/' || currentPath.endsWith('index.html')) {
            return 'frontend/';
        } else {
            return 'frontend/';
        }
    }
        
    // Emergency head (minimal fallback)
    createEmergencyHead() {
        const currentPath = window.location.pathname;
        
        const emergencyHead = `
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        `;
        
        document.head.insertAdjacentHTML('beforeend', emergencyHead);
        this.log('Emergency head created');
    }
    
    // Emergency navbar (fallback when fetch fails)
createEmergencyNavbar() {
    const currentPath = window.location.pathname;
    let relativePrefix = '../frontend/';
    
    // Check if we're in resources directory
    if (currentPath.includes('/resources/') && currentPath.endsWith('.html')) {
        relativePrefix = '../frontend/';
    }
    
        const navbarHTML = `
            <nav class="navbar">
                <div class="nav-container">
                    <a href="${relativePrefix}Home.html" class="logo">
                        <div class="logo-icon"><i class="fas fa-brain"></i></div>
                        <div class="logo-text">Mentivio</div>
                    </a>
                    <div class="mobile-controls">
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
                    </div>
                </div>
            </nav>
        `;
        
        document.body.insertAdjacentHTML('afterbegin', navbarHTML);
        this.initNavbar();
        this.log('Emergency navbar created');
    }
    
    // Emergency footer
    createEmergencyFooter() {
        const relativePrefix = this.calculateRelativePrefix();
        
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
        this.log('Emergency footer created');
    }
    
    // Clear cache (public method)
    clearCache() {
        this.componentCache.clear();
        this.log('Cache cleared');
    }
    
    // Get cache size (public method)
    getCacheSize() {
        return this.componentCache.size;
    }
    
    // Check if initialized (public method)
    isInitialized() {
        return this.initialized;
    }
    
    // Preload components (public method)
    async preloadComponents() {
        const components = [
            { name: 'navbar', file: 'navbar.html' },
            { name: 'footer', file: 'footer.html' },
            { name: 'head', file: 'head.html' }
        ];
        
        this.log('Preloading components...');
        
        try {
            await Promise.all(components.map(comp => 
                this.loadComponent(comp.name, comp.file, 'none')
            ));
            this.log('Components preloaded successfully', 'success');
        } catch (error) {
            this.log('Preloading failed: ' + error.message, 'error');
        }
    }
}

// Auto-initialize
(function() {
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.componentLoader = new ComponentLoader();
        });
    } else {
        // DOM already loaded, initialize immediately
        setTimeout(() => {
            window.componentLoader = new ComponentLoader();
        }, 0);
    }
})();