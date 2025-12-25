// main.js - Coordinate all components
(function() {
    // Function to get correct path based on current location
    function getCorrectPath(relativePath) {
        // If we're in a subdirectory (like resources/), go up one level
        const path = window.location.pathname;
        const isInSubdirectory = path.split('/').length > 2;
        
        if (isInSubdirectory && !relativePath.startsWith('/')) {
            return '../' + relativePath;
        }
        return relativePath;
    }
    
    // Override anchor clicks to ensure correct paths
    document.addEventListener('click', function(e) {
        const anchor = e.target.closest('a');
        if (anchor && anchor.href && anchor.getAttribute('href').endsWith('.html')) {
            const href = anchor.getAttribute('href');
            
            // Don't intercept if it's an absolute URL or has protocol
            if (href.startsWith('http') || href.startsWith('//') || href.startsWith('#')) {
                return;
            }
            
            // Ensure correct path
            if (!href.startsWith('/') && window.location.pathname.includes('/')) {
                e.preventDefault();
                const correctPath = getCorrectPath(href);
                window.location.href = correctPath;
            }
        }
    });
    
    // Initialize language manager
    if (!window.globalLangManager) {
        window.globalLangManager = new GlobalLanguageManager();
    }
})();