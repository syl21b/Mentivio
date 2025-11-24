// Load components (navbar and footer)
function loadComponents() {
    loadNavbar();
    loadFooter();
    initMobileMenu();
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

// Emergency navbar fallback
function createEmergencyNavbar() {
    const currentPath = window.location.pathname;
    let basePath = '';
    
    // Remove the '/frontend/' duplication
    if (currentPath.includes('/resources/')) {
        basePath = '../';  // Changed from '../frontend/'
    } else {
        basePath = './';   // For main pages
    }
    
    const emergencyNavbar = `
        <nav class="navbar" style="background: #667eea; color: white; padding: 1rem; border-bottom: 2px solid #5a67d8;">
            <div class="nav-container">
                <div class="logo">
                    <div class="logo-icon">
                        <i class="fas fa-brain"></i>
                    </div>
                    <div class="logo-text">Mentivio</div>
                </div>
                <div class="nav-links">
                    <a href="${basePath}Home.html">Home</a>
                    <a href="${basePath}MenHel_prediction.html">Self-Assessment</a>
                    <a href="${basePath}MenHel_analogy.html">Visualizer</a>
                    <a href="${basePath}resources.html">Resources</a>
                    <a href="${basePath}About.html">About</a>
                </div>
            </div>
        </nav>
    `;
    document.body.insertAdjacentHTML('afterbegin', emergencyNavbar);
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

// Initialize mobile menu functionality
function initMobileMenu() {
    // This will be called after navbar loads
    setTimeout(() => {
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const navLinks = document.getElementById('navLinks');
        
        if (mobileMenuBtn && navLinks) {
            mobileMenuBtn.addEventListener('click', function() {
                navLinks.classList.toggle('active');
                const icon = this.querySelector('i');
                if (navLinks.classList.contains('active')) {
                    icon.className = 'fas fa-times';
                } else {
                    icon.className = 'fas fa-bars';
                }
            });
        }
    }, 100);
}

// Load components when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadComponents);
} else {
    loadComponents();
}