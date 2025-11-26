// Load components (navbar and footer)
function loadComponents() {
    loadNavbar();
    loadFooter();
}

// Improved navbar loading with better path detection
function loadNavbar() {
    const currentPath = window.location.pathname;
    let navbarPath;
    
    // Determine the correct path based on current location
    if (currentPath.includes('/resources/')) {
        navbarPath = '../navbar.html';
    } else if (currentPath === '/' || currentPath.endsWith('Home.html')) {
        navbarPath = '../navbar.html';
    } else {
        navbarPath = 'navbar.html';
    }
    
    console.log('Loading navbar from:', navbarPath);
    
    const xhr = new XMLHttpRequest();
    xhr.open('GET', navbarPath, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            document.body.insertAdjacentHTML('afterbegin', xhr.responseText);
            initNavbar(); // Initialize navbar functionality after loading
            setActiveNav();
        } else if (xhr.readyState === 4) {
            console.error('Failed to load navbar. Status:', xhr.status);
            createEmergencyNavbar();
        }
    };
    xhr.onerror = function() {
        console.error('Network error loading navbar');
        createEmergencyNavbar();
    };
    xhr.send();
}

// Improved footer loading
function loadFooter() {
    const currentPath = window.location.pathname;
    let footerPath;
    const timestamp = new Date().getTime();
    
    if (currentPath.includes('/resources/')) {
        footerPath = `../footer.html?t=${timestamp}`;
    } else {
        footerPath = `footer.html?t=${timestamp}`;
    }
    
    console.log('Loading footer from:', footerPath);
    
    const xhr = new XMLHttpRequest();
    xhr.open('GET', footerPath, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            document.body.insertAdjacentHTML('beforeend', xhr.responseText);
        } else {
            console.error('Failed to load footer');
        }
    };
    xhr.send();
}

// Initialize navbar functionality
function initNavbar() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');
    const navbar = document.querySelector('.navbar');
    
    if (mobileMenuBtn && navLinks) {
        // Mobile menu toggle
        mobileMenuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            navLinks.classList.toggle('active');
            mobileMenuBtn.classList.toggle('active');
            const icon = this.querySelector('i');
            
            if (navLinks.classList.contains('active')) {
                icon.className = 'fas fa-times';
                document.body.style.overflow = 'hidden'; // Prevent background scrolling
            } else {
                icon.className = 'fas fa-bars';
                document.body.style.overflow = '';
            }
        });
        
        // Close menu when clicking on a link (for single page navigation)
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('active');
                mobileMenuBtn.classList.remove('active');
                mobileMenuBtn.querySelector('i').className = 'fas fa-bars';
                document.body.style.overflow = '';
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!navbar.contains(e.target)) {
                navLinks.classList.remove('active');
                mobileMenuBtn.classList.remove('active');
                mobileMenuBtn.querySelector('i').className = 'fas fa-bars';
                document.body.style.overflow = '';
            }
        });
        
        // Handle window resize
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                navLinks.classList.remove('active');
                mobileMenuBtn.classList.remove('active');
                mobileMenuBtn.querySelector('i').className = 'fas fa-bars';
                document.body.style.overflow = '';
            }
        });
        
        // Add touch events for better mobile experience
        let startX = 0;
        let currentX = 0;
        
        navLinks.addEventListener('touchstart', function(e) {
            startX = e.touches[0].clientX;
        }, { passive: true });
        
        navLinks.addEventListener('touchmove', function(e) {
            currentX = e.touches[0].clientX;
        }, { passive: true });
        
        navLinks.addEventListener('touchend', function() {
            const diff = startX - currentX;
            // If swiped left more than 50px, close menu
            if (diff > 50 && window.innerWidth <= 768) {
                navLinks.classList.remove('active');
                mobileMenuBtn.classList.remove('active');
                mobileMenuBtn.querySelector('i').className = 'fas fa-bars';
                document.body.style.overflow = '';
            }
        }, { passive: true });
    }
}

// Emergency navbar fallback
function createEmergencyNavbar() {
    const currentPath = window.location.pathname;
    let basePath = '';
    
    if (currentPath.includes('/resources/')) {
        basePath = '../';
    } else {
        basePath = './';
    }
    
    const emergencyNavbar = `
        <nav class="navbar" style="background: white; padding: 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.1); position: sticky; top: 0; z-index: 1000;">
            <div class="nav-container">
                <div class="logo">
                    <div class="logo-icon">
                        <i class="fas fa-brain"></i>
                    </div>
                    <div class="logo-text">Mentivio</div>
                </div>
                <button class="mobile-menu-btn" id="mobileMenuBtn">
                    <i class="fas fa-bars"></i>
                </button>
                <div class="nav-links" id="navLinks">
                    <a href="${basePath}Home.html">Home</a>
                    <a href="${basePath}MenHel_prediction.html">Self-Assessment</a>
                    <a href="${basePath}MenHel_analogy.html">Visualizer</a>
                    <a href="${basePath}resources.html">Resources</a>
                    <a href="${basePath}About.html">About</a>
                    <a href="${basePath}crisis-support.html" class="crisis-link">Crisis Support</a>
                </div>
            </div>
        </nav>
    `;
    document.body.insertAdjacentHTML('afterbegin', emergencyNavbar);
    initNavbar();
    setActiveNav();
}

// Set active navigation link
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

// Load components when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadComponents);
} else {
    loadComponents();
}