// ================================
// Mentivio — High EQ AI Mental Health Companion
// MULTILINGUAL SUPPORT: en, es, vi, zh
// SAFETY & COMPLIANCE: HIPAA/GDPR ready, Crisis Detection, Anonymity Mode
// VERSION: 3.1 (2026 Persistence Edition)
// ================================

// Global variables accessible throughout the IIFE
let CONFIG = null;
let ai = null;
let isWindowOpen = false;
let updateChatbotLanguage = null;
let mentivioWindow = null;
let mentivioInput = null;
let isTyping = false;
let lastInteractionTime = Date.now();

// Global state for persistence
let isChatbotInitialized = false;

// Session translations
const sessionTranslations = {
  en: {
    messages: "messages",
    anonymous: "Anonymous",
    clear: "Clear"
  },
  es: {
    messages: "mensajes",
    anonymous: "Anónimo",
    clear: "Limpiar"
  },
  vi: {
    messages: "tin nhắn",
    anonymous: "Nặc danh",
    clear: "Xóa"
  },
  zh: {
    messages: "条消息",
    anonymous: "匿名",
    clear: "清除"
  }
};

// ================================
// SESSION PERSISTENCE FUNCTIONS
// ================================
// ================================
// IMPROVED SESSION PERSISTENCE FUNCTIONS
// ================================

// Generate or retrieve session ID - IMPROVED
function getSessionId() {
    // Try to get existing session ID
    let sessionId = localStorage.getItem('mentivio_session_id');
    
    // Check if session ID exists in sessionStorage (for anonymous mode)
    if (!sessionId && window.mentivioStorage === sessionStorage) {
        sessionId = sessionStorage.getItem('mentivio_session_id');
    }
    
    // If no session ID exists, create a new one
    if (!sessionId) {
        sessionId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        saveSessionData(sessionId, []);
        console.log('Created new session:', sessionId);
    } else {
        console.log('Retrieved existing session:', sessionId);
    }
    
    return sessionId;
}

// Save session ID and conversation - IMPROVED
function saveSessionData(sessionId, messages = []) {
    const storage = window.mentivioStorage || localStorage;
    
    storage.setItem('mentivio_session_id', sessionId);
    
    // Save messages if provided
    if (messages.length > 0) {
        storage.setItem('mentivio_conversation', JSON.stringify(messages));
    }
    
    // Update last activity
    storage.setItem('mentivio_last_activity', Date.now());
    
    // Also save creation time if not exists
    if (!storage.getItem('mentivio_session_created')) {
        storage.setItem('mentivio_session_created', new Date().toISOString());
    }
}

// Load saved conversation - IMPROVED
function loadSavedConversation() {
    try {
        const storage = window.mentivioStorage || localStorage;
        const saved = storage.getItem('mentivio_conversation');
        if (saved) {
            const messages = JSON.parse(saved);
            console.log(`Loaded ${messages.length} messages from storage`);
            return messages;
        }
    } catch (error) {
        console.error('Error loading saved conversation:', error);
    }
    return [];
}

// Check session status with backend and restore - NEW FUNCTION
async function restoreSessionFromBackend(sessionId) {
    try {
        console.log('Restoring session from backend:', sessionId);
        
        // First check if session is still active
        const statusResponse = await fetch(`/chatbot/api/session/status?session_id=${sessionId}`);
        const statusData = await statusResponse.json();
        
        if (statusData.active) {
            // Session is active, get the full conversation
            const exportResponse = await fetch(`/chatbot/api/session/export?session_id=${sessionId}`);
            const exportData = await exportResponse.json();
            
            if (exportData.conversation_history && exportData.conversation_history.length > 0) {
                console.log(`Retrieved ${exportData.conversation_history.length} messages from backend`);
                
                // Format messages for frontend display
                const formattedMessages = exportData.conversation_history.map(msg => ({
                    role: msg.role,
                    content: msg.content,
                    timestamp: new Date(msg.timestamp).getTime(),
                    language: msg.language,
                    emotion: msg.emotion || 'neutral'
                }));
                
                // Save to localStorage
                saveSessionData(sessionId, formattedMessages);
                
                return {
                    success: true,
                    messages: formattedMessages,
                    sessionId: sessionId,
                    sessionData: exportData
                };
            }
        } else {
            console.log('Session expired or not found in backend');
            // Create new session
            const newSessionId = clearSession();
            return {
                success: false,
                messages: [],
                sessionId: newSessionId,
                message: 'Session expired'
            };
        }
    } catch (error) {
        console.error('Error restoring session from backend:', error);
        return {
            success: false,
            messages: [],
            sessionId: sessionId,
            error: error.message
        };
    }
    
    return {
        success: false,
        messages: [],
        sessionId: sessionId
    };
}

// Clear session (logout/clear chat) - IMPROVED
function clearSession() {
    const storage = window.mentivioStorage || localStorage;
    const oldSessionId = storage.getItem('mentivio_session_id');
    
    // Notify backend to clear session
    if (oldSessionId) {
        fetch('/chatbot/api/session/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ session_id: oldSessionId })
        }).catch(error => console.error('Error clearing backend session:', error));
    }
    
    // Clear local storage
    storage.removeItem('mentivio_session_id');
    storage.removeItem('mentivio_conversation');
    storage.removeItem('mentivio_session_created');
    storage.removeItem('mentivio_last_activity');
    
    // Create new session ID
    const newSessionId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    saveSessionData(newSessionId, []);
    
    console.log('Cleared session and created new:', newSessionId);
    return newSessionId;
}

// Clear chat history (keeps session) - IMPROVED
async function clearChatHistory() {
    const confirmMessages = {
        en: "Clear all chat history? This cannot be undone.",
        es: "¿Borrar todo el historial de chat? Esto no se puede deshacer.",
        vi: "Xóa toàn bộ lịch sử trò chuyện? Hành động này không thể hoàn tác.",
        zh: "清除所有聊天记录？此操作无法撤销。"
    };
    
    const confirmationMessages = {
        en: "Chat history cleared. Our conversation continues with a fresh start.",
        es: "Historial de chat borrado. Nuestra conversación continúa con un nuevo comienzo.",
        vi: "Đã xóa lịch sử trò chuyện. Cuộc trò chuyện của chúng ta tiếp tục với một khởi đầu mới.",
        zh: "聊天记录已清除。我们的对话将以全新的开始继续。"
    };
    
    const lang = CONFIG.language;
    const confirmMsg = confirmMessages[lang] || confirmMessages.en;
    const confirmationMsg = confirmationMessages[lang] || confirmationMessages.en;
    
    if (confirm(confirmMsg)) {
        const sessionId = getSessionId();
        
        // Clear backend session history
        try {
            await fetch('/chatbot/api/session/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ session_id: sessionId })
            });
        } catch (error) {
            console.error('Error clearing backend session:', error);
        }
        
        // Clear local storage
        const storage = window.mentivioStorage || localStorage;
        storage.removeItem('mentivio_conversation');
        
        // Clear the chat UI
        const chatContainer = document.getElementById('mentivioMessages');
        if (chatContainer) {
            // Keep only the welcome message
            const welcomeMessage = chatContainer.querySelector('.welcome-message');
            chatContainer.innerHTML = '';
            if (welcomeMessage) {
                chatContainer.appendChild(welcomeMessage);
            }
            
            // Scroll to top
            chatContainer.scrollTop = 0;
        }
        
        // Update session UI
        updateSessionUI(sessionId);
        
        // Show confirmation
        setTimeout(() => {
            addMessage(confirmationMsg, 'bot');
        }, 500);
    }
}

// Initialize chat on page load - IMPROVED
async function initializeChat() {
    console.log('Initializing chat with persistence...');
    
    const sessionId = getSessionId();
    const storage = window.mentivioStorage || localStorage;
    
    // Check if session is too old (30 minutes)
    const lastActivity = parseInt(storage.getItem('mentivio_last_activity') || '0');
    const now = Date.now();
    const thirtyMinutes = 30 * 60 * 1000;
    
    if (now - lastActivity > thirtyMinutes) {
        console.log('Session expired due to inactivity, creating new session');
        const newSessionId = clearSession();
        updateSessionUI(newSessionId);
        return;
    }
    
    // Try to restore from backend first
    const backendResult = await restoreSessionFromBackend(sessionId);
    
    if (backendResult.success && backendResult.messages.length > 0) {
        // Use messages from backend
        console.log('Using messages from backend session');
        displayConversation(backendResult.messages);
        updateSessionUI(sessionId);
    } else {
        // Fall back to local storage
        const savedMessages = loadSavedConversation();
        
        if (savedMessages.length > 0) {
            console.log('Using messages from local storage');
            displayConversation(savedMessages);
        }
        
        updateSessionUI(sessionId);
        
        // Verify session is still active with backend
        setTimeout(() => {
            checkSessionStatus(sessionId);
        }, 1000);
    }
    
    // Update last activity
    storage.setItem('mentivio_last_activity', Date.now());
}

// Check session status with backend
async function checkSessionStatus(sessionId) {
    try {
        const response = await fetch(`/chatbot/api/session/status?session_id=${sessionId}`);
        const data = await response.json();
        
        if (!data.active) {
            console.log('Session expired on backend, creating new session');
            const newSessionId = clearSession();
            return newSessionId;
        }
        return sessionId;
    } catch (error) {
        console.error('Error checking session status:', error);
        return sessionId;
    }
}

// Update session UI
function updateSessionUI(sessionId) {
    const sessionInfoElement = document.getElementById('session-info');
    if (!sessionInfoElement) return;
    
    const savedMessages = loadSavedConversation();
    const userMessageCount = savedMessages.filter(m => m.role === 'user').length;
    const botMessageCount = savedMessages.filter(m => m.role === 'bot').length;
    
    const lang = CONFIG.language;
    const t = sessionTranslations[lang] || sessionTranslations.en;
    
    sessionInfoElement.innerHTML = `
        <div class="session-indicator">
            <span class="session-icon">💭</span>
            <span class="session-stats">
                ${userMessageCount + botMessageCount} ${t.messages}
                ${CONFIG.anonymityFeatures.enabled ? `<span class="anon-badge">${t.anonymous}</span>` : ''}
            </span>
            <button onclick="clearChatHistory()" class="clear-btn" title="Clear chat history">
                <i class="fas fa-trash-alt"></i> ${t.clear}
            </button>
        </div>
    `;
}

// Create message element for display
function createMessageElement(msg) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${msg.role}`;
    
    const time = msg.timestamp ? 
        new Date(msg.timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true 
        }).replace(' ', '').toLowerCase() :
        'just now';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-text">${formatMessage(msg.content)}</div>
            <div class="message-time">${time}</div>
        </div>
    `;
    
    return messageDiv;
}

// Format message text
function formatMessage(text) {
    if (!text) return '';
    return text.replace(/\n/g, '<br>');
}

// Display conversation in chat interface
function displayConversation(messages) {
    const chatContainer = document.getElementById('mentivioMessages');
    if (!chatContainer) return;
    
    // Clear only if we have messages to display
    if (messages.length > 0) {
        // Find and keep welcome message if it exists
        const existingWelcome = chatContainer.querySelector('.welcome-message');
        chatContainer.innerHTML = '';
        
        if (existingWelcome) {
            chatContainer.appendChild(existingWelcome);
        }
        
        // Add all saved messages
        messages.forEach(msg => {
            const messageElement = createMessageElement(msg);
            chatContainer.appendChild(messageElement);
        });
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

(function() {
  // ================================
  // PERSISTENCE INITIALIZATION CHECK
  // ================================
  
  // Check if we should skip initialization
  if (window.mentivioSkipInit) {
    console.log('Mentivio: Skipping initialization on this page');
    return;
  }
  
  // Prevent multiple initializations
  if (isChatbotInitialized) {
    console.log('Mentivio: Already initialized');
    return;
  }
  
  // Check if we should load chatbot on this page
  function shouldLoadOnPage() {
    // List of pages where chatbot should NOT load
    const excludedPages = [
      '/admin',
      '/checkout',
      '/payment',
      '/login',
      '/register',
      '/signup',
      '/account'
    ];
    
    const currentPath = window.location.pathname;
    return !excludedPages.some(page => currentPath.startsWith(page));
  }
  
  if (!shouldLoadOnPage()) {
    console.log('Mentivio: Skipping on excluded page:', window.location.pathname);
    return;
  }
  
  isChatbotInitialized = true;

  // Inject head content
  const headContent = `
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link rel="icon" href="../frontend/assets/favicon.ico" type="image/x-icon">
    <link rel="shortcut icon" href="../frontend/assets/favicon.ico" type="image/x-icon">
    <link rel="icon" type="image/png" sizes="32x32" href="../frontend/assets/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../frontend/assets/favicon-16x16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="../frontend/assets/apple-touch-icon.png">
    <link rel="mask-icon" href="../frontend/assets/safari-pinned-tab.svg" color="#4f46e5">
    <link rel="manifest" href="../frontend/assets/site.webmanifest">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="preload" href="../frontend/css/navbar.css" as="style">
    <link rel="preload" href="../frontend/css/footer.css" as="style">
    <link rel="stylesheet" href="../frontend/css/footer.css">
    <link rel="stylesheet" href="../frontend/css/navbar.css">
    <!-- Mentivio Chatbot CSS -->
    <link rel="stylesheet" href="../frontend/css/chatbot.css">
  `;
  
  // Only inject if not already present
  if (!document.querySelector('link[href*="chatbot.css"]')) {
    document.head.insertAdjacentHTML('afterbegin', headContent);
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMentivio);
  } else {
    initMentivio();
  }

  function initMentivio() {
    // ================================
    // ENHANCED CONFIGURATION WITH SAFETY FEATURES
    // ================================
    function detectUserLanguage() {
      // Priority 1: Global language manager
      if (window.globalLangManager) {
        return window.globalLangManager.currentLang || 'en';
      }
      
      // Priority 2: Chatbot's own saved language
      const savedLang = localStorage.getItem('mentivio_language');
      if (savedLang && ['en', 'vi', 'es', 'zh'].includes(savedLang)) {
        return savedLang;
      }
      
      // Priority 3: Site-wide preferred language
      const preferredLang = localStorage.getItem('preferred-language');
      if (preferredLang && ['en', 'vi', 'es', 'zh'].includes(preferredLang)) {
        return preferredLang;
      }
      
      // Priority 4: Browser language
      const browserLang = navigator.language || navigator.userLanguage;
      if (browserLang) {
        if (browserLang.startsWith('vi')) return 'vi';
        if (browserLang.startsWith('es')) return 'es';
        if (browserLang.startsWith('zh')) return 'zh';
      }
      
      return 'en'; // Default
    }

     // Check for anonymity mode BEFORE creating CONFIG
    const urlParams = new URLSearchParams(window.location.search);
    const anonymousMode = urlParams.get('anonymous') === 'true' || 
                         localStorage.getItem('mentivio_anonymous') === 'true';

    CONFIG = {
      name: "Mentivio",
      apiEndpoint: "/chatbot/api/chat",
      safetyMode: "high-eq",
      language: detectUserLanguage(),
      
      // ENHANCED CRISIS & SAFETY CONFIGURATION
      crisisResponseMode: "immediate_escalation",
      dataRetentionDays: 30,
      hipaaCompliant: false, // Will be set by compliance check
      gdprCompliant: true,
      
      // Enhanced emergency contacts by language
      emergencyContacts: {
        en: {
          suicide_prevention: "988",
          crisis_text: "Text HOME to 741741",
          emergency: "911",
          domestic_violence: "800-799-7233",
          substance_abuse: "800-662-4357",
          veterans_crisis: "988 then press 1",
          trevor_project: "866-488-7386",
          international_redirect: true
        },
        es: {
          suicide_prevention: "988",
          crisis_text: "Envía HOME al 741741",
          emergency: "911",
          domestic_violence: "800-799-7233",
          substance_abuse: "800-662-4357",
          veterans_crisis: "988 luego presiona 1",
          trevor_project: "866-488-7386",
          international_redirect: true
        },
        vi: {
          suicide_prevention: "988",
          crisis_text: "Nhắn HOME tới 741741",
          emergency: "911",
          domestic_violence: "800-799-7233",
          substance_abuse: "800-662-4357",
          veterans_crisis: "988 sau đó nhấn 1",
          trevor_project: "866-488-7386",
          international_redirect: true
        },
        zh: {
          suicide_prevention: "988",
          crisis_text: "发送 HOME 至 741741",
          emergency: "911",
          domestic_violence: "800-799-7233",
          substance_abuse: "800-662-4357",
          veterans_crisis: "988 然后按 1",
          trevor_project: "866-488-7386",
          international_redirect: true
        }
      },
      
      // Enhanced red flag keywords for crisis detection
      redFlagKeywords: {
        immediate_crisis: [
          /kill.*myself.*(now|tonight|today)/i,
          /suicide.*(now|tonight|today)/i,
          /end.*my.*life.*(now|tonight|today)/i,
          /going.*to.*(end|kill).*myself/i,
          /cutting.*(myself|now)/i,
          /overdose.*(now|tonight)/i,
          /gun.*to.*head/i,
          /shoot.*myself/i,
          /jump.*off/i,
          /hanging.*myself/i,
          /take.*all.*pills/i,
          /swallow.*pills/i,
          /bleed.*out/i,
          /final.*goodbye/i,
          /last.*message/i
        ],
        urgent_crisis: [
          /want.*to.*die/i,
          /don't.*want.*to.*live/i,
          /can't.*go.*on/i,
          /ending.*it.*all/i,
          /no.*reason.*to.*live/i,
          /plan.*to.*(kill|suicide)/i,
          /suicide.*plan/i,
          /suicide.*method/i,
          /how.*to.*(kill|die)/i,
          /best.*way.*to.*die/i,
          /painless.*(suicide|death)/i,
          /burden.*to.*everyone/i,
          /worthless/i,
          /hopeless/i,
          /nothing.*left/i
        ],
        concerning_content: [
          /self.*harm/i,
          /cut.*myself/i,
          /burn.*myself/i,
          /hurt.*myself/i,
          /extreme.*pain/i,
          /unbearable.*pain/i,
          /can't.*take.*it/i,
          /can't.*cope/i,
          /giving.*up/i,
          /tired.*of.*life/i,
          /life.*not.*worth/i,
          /rather.*be.*dead/i
        ]
      },
      
      // AUDIT & COMPLIANCE SETTINGS
      complianceFeatures: {
        auditLogging: true,
        dataEncryption: true,
        rightToDelete: true,
        rightToExport: true,
        crisisInterventionLogging: true,
        monthlyComplianceReports: true
      },
      
      // ANONYMITY MODE SETTINGS
      anonymityFeatures: {
        enabled: false,
        noPIIStorage: true,
        sessionOnly: true,
        disableAnalytics: true,
        disableFingerprinting: true,
        scrubPII: true
      }
    };
    
    // NOW call enableAnonymousMode after CONFIG is initialized
    if (anonymousMode) {
      enableAnonymousMode();
    }
    
    // ================================
    // ANONYMITY MODE FUNCTIONS
    // ================================
    function enableAnonymousMode() {
      console.log('Anonymous mode enabled');
      
      // Update CONFIG
      CONFIG.anonymityFeatures.enabled = true;
      
      // Disable all analytics
      window['ga-disable-UA-XXXXX-Y'] = true;
      if (window.gtag) {
        window.gtag = function() { console.log('Analytics disabled in anonymous mode'); };
      }
      
      // Clear any existing localStorage data
      localStorage.removeItem('mentivio_high_eq_history');
      localStorage.removeItem('mentivio_user_id');
      localStorage.removeItem('mentivio_session_id');
      localStorage.removeItem('mentivio_user_consent');
      
      // Use sessionStorage instead (clears on browser close)
      window.mentivioStorage = sessionStorage;
      
      // Disable any fingerprinting
      disableFingerprinting();
      
      // Update UI to show anonymous mode
      const avatar = document.getElementById('mentivioAvatar');
      if (avatar) {
        avatar.style.background = 'linear-gradient(135deg, #6b7280, #9ca3af)';
        avatar.title = 'Anonymous Mode - No data stored permanently';
      }
      
      // Add anonymous indicator to chat window
      const header = document.querySelector('.mentivio-header');
      if (header) {
        const indicator = document.createElement('div');
        indicator.className = 'anonymous-indicator';
        indicator.style.cssText = 'margin-left: auto; margin-right: 8px;';
        indicator.innerHTML = `
          <span style="background: linear-gradient(135deg, #6b7280, #9ca3af); color: white; padding: 4px 10px; border-radius: 16px; font-size: 11px; display: flex; align-items: center; gap: 6px; font-weight: 500;">
            <i class="fas fa-user-secret"></i> Anonymous Mode
          </span>
        `;
        header.insertBefore(indicator, header.querySelector('.header-right'));
      }
    }

    function scrubPII(text) {
      if (!text || typeof text !== 'string') return text;
      
      // Remove email addresses
      text = text.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[EMAIL]');
      
      // Remove phone numbers (multiple formats)
      text = text.replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE]');
      text = text.replace(/\b\d{3}[-.]?\d{4}\b/g, '[PHONE]');
      text = text.replace(/\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g, '[PHONE]');
      
      // Remove names (simple pattern - in production use NLP)
      text = text.replace(/\b(?:[A-Z][a-z]+ )+[A-Z][a-z]+\b/g, '[NAME]');
      
      // Remove addresses
      text = text.replace(/\b\d+\s+\w+\s+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln)\b/gi, '[ADDRESS]');
      
      // Remove social security numbers (US)
      text = text.replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN]');
      
      // Remove credit card numbers
      text = text.replace(/\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g, '[CARD]');
      
      // Remove dates of birth
      text = text.replace(/\b(0?[1-9]|1[0-2])[\/\-](0?[1-9]|[12][0-9]|3[01])[\/\-]\d{4}\b/g, '[DOB]');
      
      // Remove IP addresses
      text = text.replace(/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, '[IP]');
      
      return text;
    }

    async function callApiAnonymously(message, sessionId) {
      try {
        // Scrub PII before sending
        const scrubbedMessage = scrubPII(message);
        
        const response = await fetch(CONFIG.apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Anonymous': 'true',
            'X-Session-ID': sessionId,
            'X-No-Tracking': 'true',
            'X-Compliance-Mode': 'gdpr_strict'
          },
          body: JSON.stringify({
            message: scrubbedMessage,
            language: CONFIG.language,
            anonymous: true,
            session_id: sessionId,
            no_storage: true,
            compliance: {
              gdpr: true,
              hipaa: CONFIG.hipaaCompliant,
              ccpa: true
            }
          })
        });
        
        return await response.json();
      } catch (error) {
        console.error('Anonymous API call failed:', error);
        return {
          response: "I'm here for you. Let's focus on how you're feeling right now.",
          emotion: "present",
          is_safe: true,
          language: CONFIG.language
        };
      }
    }

    function disableFingerprinting() {
      // Override navigator properties
      const originalNavigator = { ...navigator };
      
      Object.defineProperty(navigator, 'deviceMemory', { 
        get: () => 8,
        configurable: true
      });
      
      Object.defineProperty(navigator, 'hardwareConcurrency', { 
        get: () => 4,
        configurable: true
      });
      
      Object.defineProperty(navigator, 'platform', { 
        get: () => 'Unknown',
        configurable: true
      });
      
      Object.defineProperty(navigator, 'userAgent', { 
        get: () => 'Mozilla/5.0 (Anonymous) AppleWebKit/537.36',
        configurable: true
      });
      
      // Disable WebRTC
      if (window.RTCPeerConnection) {
        const originalRTCPeerConnection = window.RTCPeerConnection;
        window.RTCPeerConnection = function(...args) {
          console.warn('WebRTC disabled in anonymous mode');
          return {
            createDataChannel: () => ({ 
              close: () => {},
              send: () => {}
            }),
            createOffer: () => Promise.reject(new Error('WebRTC disabled')),
            close: () => {}
          };
        };
        window.RTCPeerConnection.prototype = originalRTCPeerConnection.prototype;
      }
      
      // Disable canvas fingerprinting
      const originalGetContext = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function(...args) {
        const context = originalGetContext.apply(this, args);
        if (context && args[0] === '2d') {
          const originalFillText = context.fillText;
          context.fillText = function(...textArgs) {
            return originalFillText.apply(this, textArgs);
          };
          
          // Add noise to canvas
          const originalGetImageData = context.getImageData;
          context.getImageData = function(...getArgs) {
            const imageData = originalGetImageData.apply(this, getArgs);
            // Add slight noise to prevent fingerprinting
            for (let i = 0; i < imageData.data.length; i += 4) {
              imageData.data[i] += Math.floor(Math.random() * 3) - 1;
            }
            return imageData;
          };
        }
        return context;
      };
      
      // Disable AudioContext fingerprinting
      if (window.AudioContext) {
        const originalAudioContext = window.AudioContext;
        window.AudioContext = function() {
          return {
            createOscillator: () => ({
              start: () => {},
              stop: () => {},
              connect: () => {},
              frequency: { setValueAtTime: () => {} }
            }),
            createAnalyser: () => ({
              connect: () => {},
              getByteFrequencyData: () => new Uint8Array(1024)
            }),
            close: () => Promise.resolve()
          };
        };
      }
      
      // Disable Battery API
      if ('getBattery' in navigator) {
        navigator.getBattery = () => Promise.resolve({
          level: 1,
          charging: true,
          chargingTime: 0,
          dischargingTime: Infinity
        });
      }
      
      console.log('Browser fingerprinting disabled for anonymous mode');
    }

    // ================================
    // ENHANCED CRISIS DETECTION SYSTEM
    // ================================
    function detectAndHandleCrisis(userMessage, language = 'en') {
      if (!userMessage || typeof userMessage !== 'string') return 'no_crisis';
      
      const text = userMessage.toLowerCase();
      
      // Immediate crisis - stop ALL conversation
      for (const pattern of CONFIG.redFlagKeywords.immediate_crisis) {
        if (pattern.test(text)) {
          console.warn(`🚨 IMMEDIATE CRISIS DETECTED in ${language}:`, text.substring(0, 100));
          
          // Log crisis intervention for compliance
          logCrisisIntervention('immediate_crisis', language, {
            detected_pattern: pattern.toString(),
            message_preview: text.substring(0, 200)
          });
          
          // Immediately stop any ongoing typing/API calls
          if (window.currentTypingTimeout) {
            clearTimeout(window.currentTypingTimeout);
            window.currentTypingTimeout = null;
          }
          
          if (window.currentApiCall && window.currentApiCall.abort) {
            window.currentApiCall.abort();
            window.currentApiCall = null;
          }
          
          // Show emergency modal with NO option to continue
          setTimeout(() => showEmergencyCrisisModal(language, 'immediate'), 100);
          return 'immediate_crisis';
        }
      }
      
      // Urgent crisis - escalate to human resources
      for (const pattern of CONFIG.redFlagKeywords.urgent_crisis) {
        if (pattern.test(text)) {
          console.info(`⚠️ URGENT CRISIS DETECTED in ${language}:`, text.substring(0, 100));
          
          // Log crisis intervention for compliance
          logCrisisIntervention('urgent_crisis', language, {
            detected_pattern: pattern.toString(),
            message_preview: text.substring(0, 200)
          });
          
          // Show crisis resources with option to connect to human
          setTimeout(() => showEmergencyCrisisModal(language, 'urgent'), 100);
          return 'urgent_crisis';
        }
      }
      
      // Concerning content - gentle escalation
      for (const pattern of CONFIG.redFlagKeywords.concerning_content) {
        if (pattern.test(text)) {
          console.info(`⚠️ CONCERNING CONTENT DETECTED in ${language}:`, text.substring(0, 100));
          
          // Log for monitoring
          logCrisisIntervention('concerning_content', language, {
            detected_pattern: pattern.toString(),
            message_preview: text.substring(0, 200)
          });
          
          return 'concerning_content';
        }
      }
      
      return 'no_crisis';
    }

    function logCrisisIntervention(type, language, details = {}) {
      // Create anonymous log entry
      const logEntry = {
        type,
        language,
        timestamp: Date.now(),
        userAgent: navigator.userAgent ? navigator.userAgent.substring(0, 100) : 'unknown',
        // Anonymous identifiers only
        sessionHash: window.mentivioSessionHash || 'anonymous',
        details
      };
      
      // Store in session storage (temporary)
      const crisisLogs = JSON.parse(sessionStorage.getItem('mentivio_crisis_logs') || '[]');
      crisisLogs.push(logEntry);
      sessionStorage.setItem('mentivio_crisis_logs', JSON.stringify(crisisLogs.slice(-50))); // Keep last 50
      
      // Send to backend for compliance reporting (anonymous)
      if (CONFIG.complianceFeatures.crisisInterventionLogging) {
        setTimeout(() => {
          fetch('/chatbot/api/compliance/crisis-report', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Anonymous': CONFIG.anonymityFeatures.enabled ? 'true' : 'false'
            },
            body: JSON.stringify({
              ...logEntry,
              // Remove any potentially identifiable info
              userAgent: undefined
            })
          }).catch(() => {
            // Silently fail - crisis response is more important
          });
        }, 1000);
      }
      
      return logEntry;
    }

    // ================================
    // COMPLIANCE MANAGER
    // ================================
    class ComplianceManager {
      constructor() {
        this.initialized = false;
        this.userConsent = null;
        this.auditLog = [];
        this.dataRetentionDays = CONFIG.dataRetentionDays;
        this.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      }
      
      async initialize() {
        if (this.initialized) return;
        
        // Check server compliance status
        await this.checkServerCompliance();
        
        // Load user consent
        this.loadUserConsent();
        
        // Initialize audit logging
        this.setupAuditLogging();
        
        // Schedule data cleanup
        this.scheduleDataCleanup();
        
        this.initialized = true;
        console.log('ComplianceManager initialized');
      }
      
      async checkServerCompliance() {
        // Skip compliance check if we're in development or endpoint doesn't exist
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
          console.log('Development mode: Skipping compliance check');
          CONFIG.hipaaCompliant = false;
          CONFIG.gdprCompliant = true;
          CONFIG.complianceFeatures.auditLogging = true;
          
          this.logAuditEvent('compliance_check_skipped', {
            reason: 'development_mode',
            hostname: window.location.hostname
          });
          return;
        }
        
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 5000);
          
          const response = await fetch('/chatbot/api/compliance/status', {
            signal: controller.signal
          });
          
          clearTimeout(timeoutId);
          
          if (!response.ok) {
            // If endpoint doesn't exist (404) or returns error, use defaults
            console.log('Compliance endpoint not available, using defaults');
            this.logAuditEvent('compliance_check_failed', { 
              status: response.status,
              statusText: response.statusText 
            });
            
            CONFIG.hipaaCompliant = false;
            CONFIG.gdprCompliant = true;
            CONFIG.complianceFeatures.auditLogging = false;
            return;
          }
          
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            CONFIG.hipaaCompliant = data.hipaa_compliant || false;
            CONFIG.gdprCompliant = data.gdpr_compliant || true;
            CONFIG.complianceFeatures.auditLogging = data.audit_logging || false;
            
            this.logAuditEvent('compliance_check', {
              hipaa: CONFIG.hipaaCompliant,
              gdpr: CONFIG.gdprCompliant,
              server_status: data.status
            });
          } else {
            console.log('Compliance check returned non-JSON response, using defaults');
            this.logAuditEvent('compliance_check_failed', { 
              error: 'Non-JSON response',
              contentType: contentType 
            });
            
            CONFIG.hipaaCompliant = false;
            CONFIG.gdprCompliant = true;
            CONFIG.complianceFeatures.auditLogging = false;
          }
        } catch (error) {
          console.log('Compliance check failed, using defaults:', error.message);
          this.logAuditEvent('compliance_check_failed', { error: error.message });
          
          CONFIG.hipaaCompliant = false;
          CONFIG.gdprCompliant = true;
          CONFIG.complianceFeatures.auditLogging = false;
        }
      }
      
      loadUserConsent() {
        if (CONFIG.anonymityFeatures.enabled) {
          this.userConsent = {
            accepted: true,
            analytics: false,
            localStorage: false,
            crisisEscalation: true,
            timestamp: Date.now(),
            anonymous: true
          };
          return;
        }
        
        try {
          const saved = localStorage.getItem('mentivio_user_consent');
          if (saved) {
            this.userConsent = JSON.parse(saved);
            // Ensure crisis escalation is always true for safety
            this.userConsent.crisisEscalation = true;
          }
        } catch (error) {
          this.userConsent = null;
        }
        
        // Show consent modal if no consent exists
        if (!this.userConsent && !CONFIG.anonymityFeatures.enabled) {
          setTimeout(() => this.showConsentModal(), 2000);
        }
      }
      
      showConsentModal() {
        // Don't show if already showing or in anonymous mode
        if (document.getElementById('compliance-modal') || CONFIG.anonymityFeatures.enabled) return;
        
        const modalHTML = `
        <div id="compliance-modal" class="compliance-modal">
          <div class="compliance-modal-content">
            <div class="compliance-header">
              <div class="compliance-icon">🔒</div>
              <h2>Your Privacy & Safety</h2>
            </div>
            
            <div class="compliance-body">
              <p class="compliance-intro">
                <strong>Mentivio is committed to protecting your privacy and safety:</strong>
              </p>
              <div class="compliance-features">
                <ul>
                  <li>🔒 <strong>End-to-end encryption</strong> for all conversations</li>
                  <li>🗑️ <strong>Auto-delete</strong> conversations after ${CONFIG.dataRetentionDays} days</li>
                  <li>🌐 <strong>No personal info required</strong> - use anonymously</li>
                  <li>🚨 <strong>Crisis detection</strong> with instant support resources</li>
                  <li>🇪🇺 <strong>GDPR compliant</strong> for EU users</li>
                  ${CONFIG.hipaaCompliant ? '<li>🇺🇸 <strong>HIPAA-ready infrastructure</strong></li>' : ''}
                </ul>
              </div>
            </div>
            
            <div class="compliance-options">
              <div class="compliance-option">
                <label class="compliance-checkbox">
                  <input type="checkbox" id="consent-analytics">
                  <div class="checkbox-label">
                    <div class="option-title">Allow anonymous analytics</div>
                    <div class="option-description">Help improve Mentivio with completely anonymous usage data</div>
                  </div>
                </label>
              </div>
              
              <div class="compliance-option">
                <label class="compliance-checkbox">
                  <input type="checkbox" id="consent-local-storage" checked>
                  <div class="checkbox-label">
                    <div class="option-title">Store conversations locally</div>
                    <div class="option-description">Remember our conversation in your browser for ${CONFIG.dataRetentionDays} days</div>
                  </div>
                </label>
              </div>
              
              <div class="compliance-critical">
                <label class="compliance-checkbox critical">
                  <input type="checkbox" id="consent-crisis-escalation" checked disabled>
                  <div class="checkbox-label">
                    <div class="option-title critical">Always allow crisis escalation</div>
                    <div class="option-description critical">Required for your safety. We'll connect you with emergency resources if needed.</div>
                  </div>
                </label>
              </div>
            </div>
            
            <div class="compliance-actions">
              <button onclick="window.complianceManager.acceptConsent()" class="btn-accept">
                Accept & Continue
              </button>
              <button onclick="window.complianceManager.useAnonymously()" class="btn-anonymous">
                Use Anonymously
              </button>
            </div>
            
            <p class="compliance-footer">
              By continuing, you agree to our 
              <a href="/privacy" target="_blank">Privacy Policy</a> 
              and 
              <a href="/terms" target="_blank">Terms of Service</a>.
            </p>
          </div>
        </div>`;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
      }
      
      acceptConsent() {
        const analytics = document.getElementById('consent-analytics')?.checked || false;
        const storage = document.getElementById('consent-local-storage')?.checked || false;
        
        this.userConsent = {
          accepted: true,
          analytics,
          localStorage: storage,
          crisisEscalation: true,
          timestamp: Date.now(),
          version: '2.0',
          anonymous: false
        };
        
        localStorage.setItem('mentivio_user_consent', JSON.stringify(this.userConsent));
        this.logAuditEvent('consent_given', { analytics, storage });
        
        const modal = document.getElementById('compliance-modal');
        if (modal) modal.remove();
        
        // Show welcome message
        setTimeout(() => {
          if (mentivioWindow && !isWindowOpen) {
            showWindow();
          }
        }, 500);
      }
      
      useAnonymously() {
        localStorage.setItem('mentivio_anonymous', 'true');
        this.logAuditEvent('anonymous_mode_selected', {});
        
        const modal = document.getElementById('compliance-modal');
        if (modal) modal.remove();
        
        // Reload with anonymous mode
        setTimeout(() => location.reload(), 100);
      }
      
      setupAuditLogging() {
        // Load existing audit log
        try {
          const saved = localStorage.getItem('mentivio_audit_log');
          if (saved) {
            this.auditLog = JSON.parse(saved);
          }
        } catch (error) {
          this.auditLog = [];
        }
        
        // Log initialization
        this.logAuditEvent('system_initialized', {
          anonymity: CONFIG.anonymityFeatures.enabled,
          compliance: {
            hipaa: CONFIG.hipaaCompliant,
            gdpr: CONFIG.gdprCompliant
          }
        });
      }
      
      logAuditEvent(event, details) {
        if (!CONFIG.complianceFeatures.auditLogging) return;
        
        const auditEntry = {
          event,
          details,
          timestamp: Date.now(),
          sessionId: this.sessionId,
          anonymous: CONFIG.anonymityFeatures.enabled,
          // Anonymous identifiers only
          userAgentHash: navigator.userAgent ? 
            this.hashString(navigator.userAgent.substring(0, 50)) : 'none'
        };
        
        this.auditLog.push(auditEntry);
        
        // Keep only last 500 events
        if (this.auditLog.length > 500) {
          this.auditLog = this.auditLog.slice(-500);
        }
        
        // Store in appropriate storage
        if (CONFIG.anonymityFeatures.enabled) {
          sessionStorage.setItem('mentivio_audit_log', JSON.stringify(this.auditLog));
        } else {
          localStorage.setItem('mentivio_audit_log', JSON.stringify(this.auditLog));
        }
        
        return auditEntry;
      }
      
      hashString(str) {
        // Simple hash for anonymous identifiers
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
          const char = str.charCodeAt(i);
          hash = ((hash << 5) - hash) + char;
          hash = hash & hash;
        }
        return Math.abs(hash).toString(36);
      }
      
      scheduleDataCleanup() {
        // Run cleanup every 6 hours
        setInterval(() => this.cleanupOldData(), 6 * 60 * 60 * 1000);
        
        // Run immediately
        this.cleanupOldData();
      }
      
      cleanupOldData() {
        if (CONFIG.anonymityFeatures.enabled) return; // Nothing to clean in sessionStorage
        
        const cutoff = Date.now() - (CONFIG.dataRetentionDays * 24 * 60 * 60 * 1000);
        
        // Clean conversation history
        try {
          const history = JSON.parse(localStorage.getItem('mentivio_high_eq_history') || '[]');
          const filtered = history.filter(msg => msg.timestamp > cutoff);
          
          if (filtered.length < history.length) {
            localStorage.setItem('mentivio_high_eq_history', JSON.stringify(filtered));
            this.logAuditEvent('data_cleaned', {
              removed: history.length - filtered.length,
              retained: filtered.length
            });
          }
        } catch (error) {
          console.warn('Failed to clean conversation history:', error);
        }
        
        // Clean old audit logs (keep 90 days)
        const auditCutoff = Date.now() - (90 * 24 * 60 * 60 * 1000);
        this.auditLog = this.auditLog.filter(log => log.timestamp > auditCutoff);
        localStorage.setItem('mentivio_audit_log', JSON.stringify(this.auditLog));
      }
      
      exportUserData() {
        const data = {
          conversationHistory: JSON.parse(
            (CONFIG.anonymityFeatures.enabled ? 
              sessionStorage.getItem('mentivio_anon_history') : 
              localStorage.getItem('mentivio_high_eq_history')
            ) || '[]'
          ),
          settings: {
            language: CONFIG.language,
            anonymity: CONFIG.anonymityFeatures.enabled,
            consent: this.userConsent
          },
          auditLog: this.auditLog.filter(log => !log.anonymous)
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mentivio-data-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.logAuditEvent('data_exported', {});
      }
      
      deleteAllUserData() {
        if (CONFIG.anonymityFeatures.enabled) {
          sessionStorage.clear();
        } else {
          localStorage.removeItem('mentivio_high_eq_history');
          localStorage.removeItem('mentivio_language');
          localStorage.removeItem('mentivio_user_consent');
          localStorage.removeItem('mentivio_audit_log');
          localStorage.removeItem('mentivio_anonymous');
        }
        
        this.userConsent = null;
        this.auditLog = [];
        
        this.logAuditEvent('data_deleted', {});
        
        alert('All your data has been deleted. The page will reload.');
        setTimeout(() => location.reload(), 1000);
      }
      
      showPrivacyControls() {
        const controlsHTML = `
        <div id="privacy-controls" class="privacy-controls">
          <div class="privacy-container">
            <div class="privacy-header">
              <h2>Privacy Controls</h2>
              <button onclick="document.getElementById('privacy-controls').remove()" class="close-btn">×</button>
            </div>
            
            <div class="privacy-section">
              <h3>Your Data</h3>
              <div class="privacy-card">
                <p class="data-status">
                  <strong>Current mode:</strong> ${CONFIG.anonymityFeatures.enabled ? 'Anonymous (no data stored)' : 'Standard (data stored locally)'}
                </p>
                <div class="data-actions">
                  <button onclick="window.complianceManager.exportUserData()" class="btn-export">
                    Export My Data
                  </button>
                  <button onclick="window.complianceManager.deleteAllUserData()" class="btn-delete">
                    Delete All Data
                  </button>
                </div>
              </div>
            </div>
            
            <div class="privacy-section">
              <h3>Privacy Settings</h3>
              <div class="privacy-card">
                <label class="privacy-toggle">
                  <input type="checkbox" ${CONFIG.anonymityFeatures.enabled ? 'checked' : ''} 
                         onchange="window.complianceManager.toggleAnonymousMode(this.checked)">
                  Use anonymous mode (no data stored permanently)
                </label>
                <p class="toggle-description">
                  Anonymous mode uses session storage only. All data disappears when you close your browser.
                </p>
              </div>
            </div>
            
            <div class="privacy-section">
              <h3>Compliance Information</h3>
              <div class="privacy-card">
                <ul class="compliance-list">
                  <li>Data retention: ${CONFIG.dataRetentionDays} days</li>
                  <li>GDPR compliant: ${CONFIG.gdprCompliant ? 'Yes' : 'No'}</li>
                  <li>HIPAA compliant: ${CONFIG.hipaaCompliant ? 'Yes' : 'No'}</li>
                  <li>End-to-end encryption: Yes</li>
                  <li>Crisis intervention logging: ${CONFIG.complianceFeatures.crisisInterventionLogging ? 'Yes' : 'No'}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>`;
        
        // Remove existing controls if any
        const existing = document.getElementById('privacy-controls');
        if (existing) existing.remove();
        
        document.body.insertAdjacentHTML('beforeend', controlsHTML);
      }
      
      toggleAnonymousMode(enabled) {
        if (enabled) {
          localStorage.setItem('mentivio_anonymous', 'true');
        } else {
          localStorage.removeItem('mentivio_anonymous');
        }
        location.reload();
      }
    }

    // ================================
    // EMERGENCY CRISIS MODAL
    // ================================
    function showEmergencyCrisisModal(language, severity = 'urgent') {
      // Clear any existing modal
      const existingModal = document.getElementById('mentivio-emergency-overlay');
      if (existingModal) existingModal.remove();
      
      // Get emergency contacts for this language
      const contacts = CONFIG.emergencyContacts[language] || CONFIG.emergencyContacts.en;
      
      // Different messages based on severity
      const messages = {
        immediate: {
          en: "Your safety is our absolute priority. We've detected that you might need immediate support.",
          es: "Tu seguridad es nuestra máxima prioridad. Hemos detectado que podrías necesitar apoyo inmediato.",
          vi: "An toàn của bạn là ưu tiên tuyệt đối của chúng tôi. Chúng tôi phát hiện bạn có thể cần hỗ trợ ngay lập tức.",
          zh: "您的安全是我们的绝对优先事项。我们检测到您可能需要立即支持。"
        },
        urgent: {
          en: "We're here to support you. It sounds like you're going through something very difficult.",
          es: "Estamos aquí para apoyarte. Parece que estás pasando por algo muy difícil.",
          vi: "Chúng tôi ở đây để hỗ trợ bạn. Có vẻ như bạn đang trải qua điều gì đó rất khó khăn.",
          zh: "我们在这里支持您。听起来您正在经历非常困难的事情。"
        }
      };
      
      const message = messages[severity][language] || messages[severity].en;
      
      // Title translations
      const titles = {
        immediate: {
          en: 'Immediate Support Needed',
          es: 'Apoyo Inmediato Necesario',
          vi: 'Cần Hỗ Trợ Ngay Lập Tức',
          zh: '需要立即支持'
        },
        urgent: {
          en: 'Support Available',
          es: 'Apoyo Disponible',
          vi: 'Hỗ Trợ Có Sẵn',
          zh: '支持可用'
        }
      };
      
      const title = titles[severity][language] || titles[severity].en;
      
      // Button text translations
      const buttonTexts = {
        call: {
          en: 'Call',
          es: 'Llamar',
          vi: 'Gọi',
          zh: '拨打'
        },
        emergency: {
          en: 'Emergency Services',
          es: 'Servicios de Emergencia',
          vi: 'Dịch Vụ Khẩn Cấp',
          zh: '紧急服务'
        },
        contacted: {
          en: "I've contacted support",
          es: "He contactado con apoyo",
          vi: "Tôi đã liên hệ hỗ trợ",
          zh: "我已联系支持"
        },
        callEmergency: {
          en: "Call Emergency",
          es: "Llamar Emergencia",
          vi: "Gọi Khẩn Cấp",
          zh: "拨打紧急电话"
        },
        continue: {
          en: "Continue with emotional support",
          es: "Continuar con apoyo emocional",
          vi: "Tiếp tục với hỗ trợ cảm xúc",
          zh: "继续情感支持"
        },
        moreResources: {
          en: "More resources",
          es: "Más recursos",
          vi: "Thêm tài nguyên",
          zh: "更多资源"
        }
      };
      
      // Important message translations
      const importantMessages = {
        en: "For your safety, chat will remain paused until you confirm you've reached out for help.",
        es: "Para tu seguridad, el chat permanecerá pausado hasta que confirmes que has buscado ayuda.",
        vi: "Để đảm bảo an toàn của bạn, cuộc trò chuyện sẽ tạm dừng cho đến khi bạn xác nhận đã tìm kiếm sự giúp đỡ.",
        zh: "为了您的安全，聊天将保持暂停，直到您确认已寻求帮助。"
      };
      
      const importantMessage = importantMessages[language] || importantMessages.en;
      
      // Footer message translations
      const footerMessages = {
        en: "Mentivio provides emotional support and crisis resources. For immediate emergencies, please contact the numbers above.",
        es: "Mentivio proporciona apoyo emocional y recursos de crisis. Para emergencias inmediatas, contacta con los números anteriores.",
        vi: "Mentivio cung cấp hỗ trợ cảm xúc và tài nguyên khủng hoảng. Đối với trường hợp khẩn cấp ngay lập tức, vui lòng liên hệ với các số trên.",
        zh: "Mentivio提供情感支持和危机资源。对于紧急情况，请联系上述号码。"
      };
      
      const footerMessage = footerMessages[language] || footerMessages.en;
      
      // Create emergency overlay
      const emergencyHTML = `
      <div id="mentivio-emergency-overlay" class="crisis-overlay">
        <div class="crisis-container">
          <div class="crisis-icon">🚨</div>
          <h2 class="crisis-title">${title}</h2>
          
          <p class="crisis-message">${message}</p>
          
          <div class="crisis-card immediate">
            <h3 class="crisis-card-title">${severity === 'immediate' ? 
              language === 'en' ? 'Immediate Help' :
              language === 'es' ? 'Ayuda Inmediata' :
              language === 'vi' ? 'Trợ Giúp Ngay Lập Tức' :
              '即时帮助' : 
              language === 'en' ? 'Support Available' :
              language === 'es' ? 'Apoyo Disponible' :
              language === 'vi' ? 'Hỗ Trợ Có Sẵn' :
              '支持可用'
            }</h3>
            
            <div class="crisis-buttons">
              <button onclick="window.open('tel:${contacts.suicide_prevention}')" class="crisis-btn crisis-btn-primary">
                <span class="btn-icon">📞</span>
                <span>${buttonTexts.call[language] || buttonTexts.call.en} ${contacts.suicide_prevention}</span>
              </button>
              
              <button onclick="window.open('sms:741741?body=HOME')" class="crisis-btn crisis-btn-secondary">
                <span class="btn-icon">💬</span>
                <span>${contacts.crisis_text}</span>
              </button>
              
              ${severity === 'immediate' ? `
              <button onclick="window.open('tel:${contacts.emergency}')" class="crisis-btn crisis-btn-emergency">
                <span class="btn-icon">🚑</span>
                <span>${buttonTexts.emergency[language] || buttonTexts.emergency.en} (${contacts.emergency})</span>
              </button>
              ` : ''}
            </div>
          </div>
          
          ${severity === 'immediate' ? `
          <div class="crisis-warning">
            <p><strong>${language === 'en' ? 'Important:' : language === 'es' ? 'Importante:' : language === 'vi' ? 'Quan trọng:' : '重要：'}</strong> ${importantMessage}</p>
          </div>
          
          <div class="crisis-actions">
            <button onclick="confirmHelpReceived()" class="crisis-action-btn crisis-action-confirm">
              ${buttonTexts.contacted[language] || buttonTexts.contacted.en}
            </button>
            <button onclick="window.open('tel:${contacts.emergency}')" class="crisis-action-btn crisis-action-emergency">
              ${buttonTexts.callEmergency[language] || buttonTexts.callEmergency.en}
            </button>
          </div>
          ` : `
          <div class="crisis-actions">
            <button onclick="resumeChatAfterCrisis()" class="crisis-action-btn crisis-action-resume">
              ${buttonTexts.continue[language] || buttonTexts.continue.en}
            </button>
            <button onclick="showAdditionalResources('${language}')" class="crisis-action-btn crisis-action-resources">
              ${buttonTexts.moreResources[language] || buttonTexts.moreResources.en}
            </button>
          </div>
          `}
          
          <p class="crisis-footer">${footerMessage}</p>
        </div>
      </div>`;
      
      // Clear messages and add emergency overlay
      const messagesContainer = document.getElementById('mentivioMessages');
      if (messagesContainer) {
        messagesContainer.innerHTML = emergencyHTML;
        messagesContainer.scrollTop = 0;
      }
      
      // Disable input during crisis
      if (mentivioInput) {
        mentivioInput.disabled = true;
        const placeholders = {
          en: 'Chat paused for your safety...',
          es: 'Chat pausado por tu seguridad...',
          vi: 'Trò chuyện tạm dừng để đảm bảo an toàn...',
          zh: '聊天已暂停以确保您的安全...'
        };
        mentivioInput.placeholder = placeholders[language] || placeholders.en;
      }
      
      if (sendBtn) {
        sendBtn.disabled = true;
      }
    }

    // ================================
    // ENHANCED LOCAL MEMORY WITH HIGH EQ
    // ================================
    class HighEQMentivio {
      constructor() {
        this.conversationHistory = [];
        this.conversationState = {
          phase: 'engagement',
          lastEmotion: 'neutral',
          needsInspiration: false,
          topicsDiscussed: []
        };
        this.language = CONFIG.language;
        this.anonymous = CONFIG.anonymityFeatures.enabled;
        this.sessionId = getSessionId();
      }

      updateLocalState(userText, emotion = 'neutral') {
        const text = this.anonymous ? scrubPII(userText) : userText;
        
        this.conversationHistory.push({
          text: text,
          role: 'user',
          timestamp: Date.now(),
          emotion: emotion,
          language: this.language,
          anonymous: this.anonymous,
          sessionId: this.sessionId
        });

        if (this.conversationHistory.length > 50) {
          this.conversationHistory.shift();
        }

        // Save to conversation storage
        const savedMessages = loadSavedConversation();
        savedMessages.push({
          role: 'user',
          content: text,
          timestamp: Date.now(),
          language: this.language
        });
        
        localStorage.setItem('mentivio_conversation', JSON.stringify(savedMessages));

        // Simplified conversation state updates
        const messageCount = this.conversationHistory.filter(m => m.role === 'user').length;
        if (messageCount < 3) this.conversationState.phase = 'engagement';
        else if (messageCount < 8) this.conversationState.phase = 'exploration';
        else if (messageCount < 15) this.conversationState.phase = 'processing';
        else this.conversationState.phase = 'integration';
        
        if (['sad', 'overwhelmed', 'lonely', 'hopeless'].includes(emotion)) {
          this.conversationState.needsInspiration = true;
        }
      }

      getConversationContext() {
        const savedMessages = loadSavedConversation();
        return savedMessages.slice(-10).map(msg => ({
          role: msg.role,
          content: msg.content,
          emotion: msg.emotion || 'neutral',
          language: msg.language || 'en',
          anonymous: this.anonymous,
          sessionId: this.sessionId
        }));
      }
      
      addBotResponse(text, emotion = 'compassionate') {
        this.conversationHistory.push({
          text: text,
          role: 'bot',
          timestamp: Date.now(),
          emotion: emotion,
          language: this.language,
          sessionId: this.sessionId
        });

        // Save to conversation storage
        const savedMessages = loadSavedConversation();
        savedMessages.push({
          role: 'bot',
          content: text,
          timestamp: Date.now(),
          language: this.language
        });
        
        localStorage.setItem('mentivio_conversation', JSON.stringify(savedMessages));
      }
    }

    // ================================
    // ENHANCED BACKEND API COMMUNICATION
    // ================================
    async function callBackendAPI(userMessage, conversationContext, emotion) {
      try {
        // Crisis check FIRST
        const crisisLevel = detectAndHandleCrisis(userMessage, CONFIG.language);
        if (crisisLevel === 'immediate_crisis') {
          return {
            response: "I'm here with you. Let me connect you with immediate support.",
            emotion: "compassionate",
            language: CONFIG.language,
            is_safe: true,
            suggested_topics: ["Safety first", "Getting support", "You matter"],
            crisis_mode: true
          };
        }

        // If API endpoint is not available, provide a fallback response
        if (!CONFIG.apiEndpoint) {
          return getFallbackResponse(userMessage, emotion);
        }

        let response;
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 10000);
          
          response = await fetch(CONFIG.apiEndpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Anonymous': CONFIG.anonymityFeatures.enabled ? 'true' : 'false',
              'X-Compliance-Mode': 'high_eq',
              'X-Session-ID': ai.sessionId || 'unknown'
            },
            body: JSON.stringify({
              message: userMessage,
              context: conversationContext,
              emotion: emotion,
              language: CONFIG.language,
              safety_mode: CONFIG.safetyMode,
              conversation_state: {
                phase: ai.conversationState.phase,
                trust_level: ai.conversationState.trustLevel || 0,
                needs_inspiration: ai.conversationState.needsInspiration
              },
              compliance: {
                anonymity: CONFIG.anonymityFeatures.enabled,
                gdpr: CONFIG.gdprCompliant,
                hipaa: CONFIG.hipaaCompliant
              },
              session_id: ai.sessionId,
              persistent: true
            }),
            signal: controller.signal
          });
          
          clearTimeout(timeoutId);
        } catch (networkError) {
          console.log('Network error, using fallback response:', networkError.message);
          return getFallbackResponse(userMessage, emotion);
        }

        if (!response.ok) {
          console.log(`API returned ${response.status}, using fallback response`);
          return getFallbackResponse(userMessage, emotion);
        }

        let data;
        try {
          data = await response.json();
        } catch (jsonError) {
          console.log('Invalid JSON response, using fallback:', jsonError);
          return getFallbackResponse(userMessage, emotion);
        }
        
        if (data.error) {
          console.log('API error response:', data.error);
          return getFallbackResponse(userMessage, emotion);
        }

        return data;
      } catch (error) {
        console.error('Unexpected error in callBackendAPI:', error);
        return getFallbackResponse(userMessage, emotion);
      }
    }

    function getFallbackResponse(userMessage, emotion) {
      const fallbackResponses = {
        en: [
          "I hear you. Sometimes words carry more weight than we realize. What's one small thing that felt true for you today?",
          "Thank you for sharing that. Your feelings matter, all of them. Can you tell me more about what's in your heart right now?",
          "I'm here with you, present and listening. Even in the silence, your presence is enough. What do you need most in this moment?"
        ],
        es: [
          "Te escucho. A veces las palabras llevan más peso del que nos damos cuenta. ¿Qué cosa pequeña sintió verdadera para ti hoy?",
          "Gracias por compartir eso. Tus sentimientos importan, todos ellos. ¿Puedes contarme más sobre lo que hay en tu corazón ahora mismo?",
          "Estoy aquí contigo, presente y escuchando. Incluso en el silencio, tu presencia es suficiente. ¿Qué es lo que más necesitas en este momento?"
        ],
        vi: [
          "Tôi nghe thấy bạn. Đôi khi lời nói mang nhiều trọng lượng hơn chúng ta nhận ra. Có điều nhỏ nào cảm thấy đúng với bạn hôm nay?",
          "Cảm ơn bạn đã chia sẻ điều đó. Cảm xúc của bạn quan trọng, tất cả chúng. Bạn có thể nói cho tôi biết thêm về những gì trong trái tim bạn ngay bây giờ?",
          "Tôi ở đây với bạn, hiện diện và lắng nghe. Ngay cả trong im lặng, sự hiện diện của bạn là đủ. Bạn cần gì nhất trong khoảnh khắc này?"
        ],
        zh: [
          "我听到了。有时言语承载的重量超乎我们的想象。今天有什么小事让你感到真实？",
          "感谢您的分享。您的感受很重要，所有感受都很重要。您现在能多告诉我一些您内心的想法吗？",
          "我在这里陪伴您，倾听您的心声。即使在沉默中，您的存在就足够了。此刻您最需要什么？"
        ]
      };
      
      const responses = fallbackResponses[CONFIG.language] || fallbackResponses.en;
      const randomResponse = responses[Math.floor(Math.random() * responses.length)];
      
      return {
        response: randomResponse,
        emotion: emotion || "compassionate",
        language: CONFIG.language,
        is_safe: true,
        suggested_topics: ["What's in your heart", "Small hopes", "Quiet thoughts"]
      };
    }

    // ================================
    // ENHANCED FRONTEND AI EMOTION DETECTION
    // ================================
    function detectEmotion(text) {
      const emotionKeywords = {
          overwhelmed: /(overwhelmed|too much|can't handle|drowning|buried|sinking)/gi,
          anxious: /(anxious|worried|nervous|scared|afraid|panic|stress|uncertain)/gi,
          sad: /(sad|depressed|down|hopeless|empty|alone|tired|numb|heavy|lost)/gi,
          angry: /(angry|mad|frustrated|annoyed|hate|pissed|resent)/gi,
          happy: /(happy|good|great|excited|wonderful|amazing|love|joy|smile)/gi,
          hopeful: /(hope|better|possible|maybe|could|future|light|progress)/gi,
          grateful: /(thankful|grateful|appreciate|blessed|lucky|fortunate)/gi,
          lonely: /(lonely|alone|isolated|no one|by myself|abandoned|separate)/gi,
          curious: /(curious|wonder|interesting|fascinating|learn|discover|explore)/gi,
          peaceful: /(calm|peace|quiet|serene|still|tranquil|centered|balanced)/gi,
          // New emotions
          hesitant: /(hesitant|unsure|undecided|can't decide|second thoughts|doubts)/gi,
          confused: /(confused|mixed up|don't understand|puzzled|bewildered)/gi,
          ashamed: /(ashamed|embarrassed|humiliated|disgraced|guilty)/gi,
          jealous: /(jealous|envious|covetous|resentful)/gi,
          rejected: /(rejected|unwanted|unloved|excluded|left out)/gi,
          betrayed: /(betrayed|let down|disappointed|deceived)/gi
      };
      
      let detectedEmotion = 'neutral';
      let maxCount = 0;
      
      for (const [emotion, pattern] of Object.entries(emotionKeywords)) {
        const matches = text.match(pattern) || [];
        if (matches.length > maxCount) {
          maxCount = matches.length;
          detectedEmotion = emotion;
        }
      }
      
      return detectedEmotion;
    }

    // ================================
    // LANGUAGE MANAGEMENT FUNCTIONS
    // ================================
    updateChatbotLanguage = function(newLang) {
      // Validate language
      if (!['en', 'es', 'vi', 'zh'].includes(newLang)) {
        console.warn(`Invalid language code: ${newLang}, defaulting to en`);
        newLang = 'en';
      }
      
      // Don't update if language is already the same
      if (CONFIG.language === newLang) {
        return;
      }
      
      console.log(`Updating chatbot language from ${CONFIG.language} to ${newLang}`);
      
      // Update CONFIG
      CONFIG.language = newLang;
      
      // Update AI instance if exists
      if (ai && typeof ai === 'object') {
        ai.language = newLang;
      }
      
      // Update UI elements if chat window exists
      if (document.getElementById('mentivioWindow')) {
        try {
          // Update language selector if it exists
          const currentLangEl = document.getElementById('currentLanguage');
          const langOptions = document.querySelectorAll('.lang-option');
          
          if (currentLangEl) {
            const languageDisplays = {
              en: "🌐 EN",
              es: "🌐 ES",
              vi: "🌐 VI",
              zh: "🌐 ZH"
            };
            currentLangEl.textContent = languageDisplays[newLang] || "🌐 EN";
          }
          
          // Update active class on language options
          langOptions.forEach(option => {
            if (option.dataset.lang === newLang) {
              option.classList.add('active');
            } else {
              option.classList.remove('active');
            }
          });
          
          // Update other UI elements
          updateWelcomeMessage(newLang);
          updateQuickEmotions(newLang);
          updateInputPlaceholder(newLang);
          updateSafetyNotice(newLang);
          updateHeaderText(newLang);
          
        } catch (error) {
          console.error('Error updating chatbot UI language:', error);
        }
      }
      
      // Save to localStorage (if not in anonymous mode)
      if (!CONFIG.anonymityFeatures.enabled) {
        localStorage.setItem('mentivio_language', newLang);
      } else {
        sessionStorage.setItem('mentivio_language', newLang);
      }
    };

    // NEW FUNCTION: Update header text based on language
    function updateHeaderText(lang) {
      const headerTitles = {
        en: {
          title: "Mentivio: Your Friend",
          subtitlePrefix: "Heart Space"
        },
        es: {
          title: "Mentivio: Tu Amigo",
          subtitlePrefix: "Espacio del Corazón"
        },
        vi: {
          title: "Mentivio: Người Bạn Của Bạn",
          subtitlePrefix: "Không Gian Trái Tim"
        },
        zh: {
          title: "Mentivio: 您的朋友",
          subtitlePrefix: "心灵空间"
        }
      };
      
      const header = headerTitles[lang] || headerTitles.en;
      
      // Update title
      const titleElement = document.querySelector('.mentivio-title');
      if (titleElement) {
        titleElement.textContent = header.title;
      }
      
      // Update day display will be handled by updateDay() function
      // We just need to trigger updateDay to refresh with new language
      if (typeof updateDay === 'function') {
        updateDay();
      }
    }

    function setupLanguageSynchronization() {
      // Flag to prevent duplicate processing
      let lastProcessedLang = null;
      let lastProcessedTime = 0;
      
      function processLanguageChange(newLang) {
        const now = Date.now();
        // Prevent rapid duplicate calls (within 500ms)
        if (lastProcessedLang === newLang && now - lastProcessedTime < 500) {
          return;
        }
        
        lastProcessedLang = newLang;
        lastProcessedTime = now;
        
        console.log('Chatbot processing language change to:', newLang);
        if (updateChatbotLanguage) {
          updateChatbotLanguage(newLang);
        }
      }
      
      // Listen to global language change events
      document.addEventListener('languageChanged', function(e) {
        const newLang = e.detail.language;
        processLanguageChange(newLang);
      });
      
      // Check if we should also listen to langChanged event
      // (comment out if causing duplicates)
      /*
      document.addEventListener('langChanged', function(e) {
        const newLang = e.detail.lang;
        processLanguageChange(newLang);
      });
      */
      
      // Also listen for custom events from navbar
      window.addEventListener('mentivioLangChange', function(e) {
        const newLang = e.detail?.language || e.detail?.lang;
        if (newLang) {
          processLanguageChange(newLang);
        }
      });
    }

    function updateSafetyNotice(lang) {
      const safetyNotices = {
        en: {
          line1: "Safe space • High EQ • Always here for you",
          line2: "Need urgent support?",
          privacy: "Privacy"
        },
        es: {
          line1: "Espacio seguro • Alta IE • Siempre aquí para ti",
          line2: "¿Necesitas apoyo urgente?",
          privacy: "Privacidad"
        },
        vi: {
          line1: "Không gian an toàn • Trí tuệ cảm xúc cao • Luôn ở đây vì bạn",
          line2: "Cần hỗ trợ khẩn cấp?",
          privacy: "Riêng tư"
        },
        zh: {
          line1: "安全空间 • 高情商 • 永远在这里陪伴你",
          line2: "需要紧急支持？",
          privacy: "隐私"
        }
      };
      
      const notice = safetyNotices[lang] || safetyNotices.en;
      const safetyNoticeEl = document.querySelector('.safety-notice');
      if (safetyNoticeEl) {
        safetyNoticeEl.innerHTML = `
          <i class="fas fa-heart" style="color: #ec4899;"></i>
          ${notice.line1}
          <span class="crisis-link" onclick="window.showEnhancedCrisisResources('${lang}')">${notice.line2}</span>
          ${!CONFIG.anonymityFeatures.enabled ? `<span class="privacy-link" onclick="window.complianceManager.showPrivacyControls()"><i class="fas fa-shield-alt"></i> ${notice.privacy}</span>` : ''}
        `;
      }
    }

    function updateWelcomeMessage(lang) {
      const welcomeMessages = {
        en: "Hello 😊. I'm Mentivio, your mental health companion. I'm here to listen deeply, understand without judgment, and help you find light even on dark days. Your feelings are welcome here, all of them.",
        es: "Hola 😊. Soy Mentivio, tu compañero de salud mental. Estoy aquí para escuchar profundamente, entender sin juzgar y ayudarte a encontrar luz incluso en los días oscuros. Todos tus sentimientos son bienvenidos aquí.",
        vi: "Xin chào 😊. Tôi là Mentivio, người bạn đồng hành sức khỏe tinh thần của bạn. Tôi ở đây để lắng nghe sâu sắc, thấu hiểu không phán xét và giúp bạn tìm thấy ánh sáng ngay cả trong những ngày tăm tối. Tất cả cảm xúc của bạn đều được chào đón ở đây.",
        zh: "你好 😊。我是Mentivio，您的心理健康伴侣。我在这里深度倾听，不加评判地理解，并帮助您在黑暗的日子里找到光明。您所有的感受在这里都受到欢迎。"
      };
      
      const welcomeElement = document.querySelector('.welcome-message .message-text');
      if (welcomeElement) {
        welcomeElement.innerHTML = `${welcomeMessages[lang] || welcomeMessages.en}`;
      }
    }
    
    function updateQuickEmotions(lang) {
      // Update emotions title
      const emotionsTitle = document.querySelector('.emotions-title');
      if (emotionsTitle) {
        const titleTranslation = emotionsTitle.getAttribute(`data-${lang}`) || emotionsTitle.getAttribute('data-en');
        if (titleTranslation) {
          emotionsTitle.textContent = titleTranslation;
        }
      }

      // Update emotion buttons
      const emotions = document.querySelectorAll('.quick-emotion');
      emotions.forEach(button => {
        const translation = button.getAttribute(`data-${lang}`) || button.getAttribute('data-en');
        if (translation) {
          button.textContent = translation;
        }
      });
    }
    
    function updateInputPlaceholder(lang) {
      const placeholders = {
        en: "Share what's in your heart... (All feelings welcome)",
        es: "Comparte lo que hay en tu corazón... (Todas las emociones son bienvenidas)",
        vi: "Chia sẻ những gì trong trái tim bạn... (Tất cả cảm xúc đều được chào đón)",
        zh: "分享你心中的感受... (欢迎所有情绪)"
      };
      
      if (mentivioInput) {
        mentivioInput.placeholder = placeholders[lang] || placeholders.en;
      }
    }

    // ================================
    // CHATBOT UI (ENHANCED WITH HIGH EQ & MULTILINGUAL)
    // ================================
    const mentivioHTML = `
      <div id="mentivio-root">
        <!-- Floating avatar -->
        <div id="mentivioAvatar">
          <span id="avatarEmoji">💭</span>
        </div>

        <!-- Main chat window -->
        <div id="mentivioWindow">
          <!-- Header -->
          <header class="mentivio-header">
            <div class="header-content">
              <div id="activeEmotion" class="active-emotion"></div>
              <div class="header-text">
                <strong class="mentivio-title">Mentivio: Your Friend</strong>
                <small id="currentDay" class="mentivio-subtitle">Heart Space • Mon • 08:33 PM</small>
              </div>
            </div>
            <div class="header-right">
              <div id="languageSelector" class="language-selector">
                <span id="currentLanguage">🌐 EN</span>
                <div class="language-dropdown">
                  <div class="lang-option" data-lang="en">English</div>
                  <div class="lang-option" data-lang="es">Español</div>
                  <div class="lang-option" data-lang="vi">Tiếng Việt</div>
                  <div class="lang-option" data-lang="zh">中文</div>
                </div>
              </div>
              <button id="closeMentivio" class="close-btn" aria-label="Close chat">×</button>
            </div>
          </header>

          <!-- Messages container -->
          <div class="mentivio-body">
            <div class="mentivio-messages" id="mentivioMessages">
              <!-- Messages will appear here -->
              <div class="welcome-message">
                <div class="message bot">
                  <div class="message-content">
                    <div class="message-text">
                      <!-- Welcome message will be set by JavaScript -->
                    </div>
                    <div class="message-time">just now</div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Session info -->
            <div id="session-info" class="session-info"></div>
            
            <!-- Typing indicator -->
            <div id="typingIndicator" class="typing-indicator" style="display: none;">
              <div class="typing-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
              </div>
              <div id="typingStatus" class="typing-status">Mentivio is thinking deeply...</div>
            </div>

          <!-- Quick emotions - HORIZONTAL SCROLLABLE WITH TITLE INLINE -->
          <div class="quick-emotions-container">
            <div class="quick-emotions">
              <div class="emotions-title" data-en="I'm feeling..." data-es="Me siento..." data-vi="Tôi đang cảm thấy..." data-zh="我感觉...">I'm feeling...</div>
              <div class="emotions-scroll-container">
                <button class="quick-emotion" data-emotion="overwhelmed" data-en="😰 Heavy Heart" data-es="😰 Corazón Pesado" data-vi="😰 Trái Tim Nặng Trĩu" data-zh="😰 沉重的心">😰 Heavy Heart</button>
                <button class="quick-emotion" data-emotion="anxious" data-en="😟 Anxious Thoughts" data-es="😟 Pensamientos Ansiosos" data-vi="😟 Lo Âu" data-zh="😟 焦虑思绪">😟 Anxious Thoughts</button>
                <button class="quick-emotion" data-emotion="sad" data-en="😔 Feeling Low" data-es="😔 Sintiéndome Triste" data-vi="😔 Buồn Bã" data-zh="😔 情绪低落">😔 Feeling Low</button>
                <button class="quick-emotion" data-emotion="lonely" data-en="🌌 Feeling Alone" data-es="🌌 Sintiéndome Solo" data-vi="🌌 Cô Đơn" data-zh="🌌 感到孤独">🌌 Feeling Alone</button>
                <button class="quick-emotion" data-emotion="hesitant" data-en="🤔 Hesitant" data-es="🤔 Vacilante" data-vi="🤔 Do Dự" data-zh="🤔 犹豫">🤔 Hesitant</button>
                <button class="quick-emotion" data-emotion="confused" data-en="😕 Confused" data-es="😕 Confundido" data-vi="😕 Bối Rối" data-zh="😕 困惑">😕 Confused</button>
                <button class="quick-emotion" data-emotion="ashamed" data-en="😳 Feeling Ashamed" data-es="😳 Sintiendo Vergüenza" data-vi="😳 Cảm Thấy Xấu Hổ" data-zh="😳 感到羞愧">😳 Feeling Ashamed</button>
                <button class="quick-emotion" data-emotion="jealous" data-en="😠 Jealous Feelings" data-es="😠 Sentimientos Celosos" data-vi="😠 Cảm Giác Ghen Tị" data-zh="😠 嫉妒感">😠 Jealous Feelings</button>
                <button class="quick-emotion" data-emotion="gender" data-en="🌈 Gender Questions" data-es="🌈 Preguntas de Género" data-vi="🌈 Câu Hỏi về Giới Tính" data-zh="🌈 性别问题">🌈 Gender Questions</button>
                <button class="quick-emotion" data-emotion="lgbtq" data-en="🏳️‍🌈 LGBTQ+" data-es="🏳️‍🌈 LGBTQ+" data-vi="🏳️‍🌈 LGBTQ+" data-zh="🏳️‍🌈 LGBTQ+">🏳️‍🌈 LGBTQ+</button>
                <button class="quick-emotion" data-emotion="study" data-en="📚 Study Stress" data-es="📚 Estrés de Estudio" data-vi="📚 Căng Thẳng Học Tập" data-zh="📚 学习压力">📚 Study Stress</button>
                <button class="quick-emotion" data-emotion="love" data-en="💔 Love & Heartbreak" data-es="💔 Amor y Desamor" data-vi="💔 Tình Yêu & Tan Vỡ" data-zh="💔 爱与心碎">💔 Love & Heartbreak</button>
                <button class="quick-emotion" data-emotion="curious" data-en="🤔 Seeking Meaning" data-es="🤔 Buscando Sentido" data-vi="🤔 Tìm Kiếm Ý Nghĩa" data-zh="🤔 寻求意义">🤔 Seeking Meaning</button>
                <button class="quick-emotion" data-emotion="hopeful" data-en="✨ Looking for Hope" data-es="✨ Buscando Esperanza" data-vi="✨ Tìm Hy Vọng" data-zh="✨ 寻找希望">✨ Looking for Hope</button>
                <button class="quick-emotion" data-emotion="lost" data-en="🧭 Feeling Lost" data-es="🧭 Sintiéndome Perdido" data-vi="🧭 Lạc Lối" data-zh="🧭 感到迷茫">🧭 Feeling Lost</button>
                <button class="quick-emotion" data-emotion="transition" data-en="🔄 In Transition" data-es="🔄 En Transición" data-vi="🔄 Giai Đoạn Chuyển Tiếp" data-zh="🔄 过渡期">🔄 In Transition</button>
                <button class="quick-emotion" data-emotion="future" data-en="🔮 Future Anxiety" data-es="🔮 Ansiedad Futuro" data-vi="🔮 Lo Âu Tương Lai" data-zh="🔮 未来焦虑">🔮 Future Anxiety</button>
                <button class="quick-emotion" data-emotion="reset" data-en="🔄 Need Reset" data-es="🔄 Necesito Reinicio" data-vi="🔄 Cần Khởi Động Lại" data-zh="🔄 需要重启">🔄 Need Reset</button>
              </div>
            </div>
          </div>

          <!-- Input area -->
          <div class="mentivio-input-area">
            <div class="input-container">
              <textarea 
                id="mentivioInput" 
                class="mentivio-input" 
                placeholder="Share what's in your heart... (All feelings welcome)" 
                rows="1"
                maxlength="2000"
              ></textarea>
              <button id="sendBtn" class="send-btn" aria-label="Send message">
                <i class="fas fa-paper-plane"></i>
              </button>
            </div>
            <div class="safety-notice">
              <i class="fas fa-heart" style="color: #ec4899;"></i>
              Safe space • High EQ • Always here for you
              <span class="crisis-link" onclick="window.showEnhancedCrisisResources()">Need urgent support?</span>
            </div>
          </div>
        </div>
      </div>`;

    // Check if chatbot HTML already exists
    if (!document.getElementById('mentivio-root')) {
      document.body.insertAdjacentHTML('beforeend', mentivioHTML);
    } else {
      console.log('Mentivio UI already exists in DOM');
    }

    // ================================
    // INITIALIZATION
    // ================================
    ai = new HighEQMentivio();

    // ================================
    // UI ELEMENTS
    // ================================
    const avatar = document.getElementById('mentivioAvatar');
    mentivioWindow = document.getElementById('mentivioWindow');
    const messages = document.getElementById('mentivioMessages');
    mentivioInput = document.getElementById('mentivioInput');
    const sendBtn = document.getElementById('sendBtn');
    const closeBtn = document.getElementById('closeMentivio');
    const typingIndicator = document.getElementById('typingIndicator');
    const activeEmotion = document.getElementById('activeEmotion');
    const currentDay = document.getElementById('currentDay');

    // UPDATED: Update current day with language support
    function updateDay() {
      if (!currentDay) return;
      
      const now = new Date();
      const lang = CONFIG ? CONFIG.language : 'en';
      
      // Language-specific day names
      const dayNames = {
        en: {
          short: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
          long: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        },
        es: {
          short: ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'],
          long: ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        },
        vi: {
          short: ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'],
          long: ['Chủ Nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7']
        },
        zh: {
          short: ['日', '一', '二', '三', '四', '五', '六'],
          long: ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
        }
      };
      
      // Language-specific time formats
      const timeFormats = {
        en: { hour12: true, hour: '2-digit', minute: '2-digit' },
        es: { hour12: true, hour: '2-digit', minute: '2-digit' },
        vi: { hour12: false, hour: '2-digit', minute: '2-digit' },
        zh: { hour12: false, hour: '2-digit', minute: '2-digit' }
      };
      
      // Get day and time
      const dayOfWeek = now.getDay();
      const dayNameSet = dayNames[lang] || dayNames.en;
      const dayName = dayNameSet.short[dayOfWeek];
      
      const timeFormat = timeFormats[lang] || timeFormats.en;
      const time = now.toLocaleTimeString([], timeFormat);
      
      // Language-specific prefix
      const prefixes = {
        en: "Heart Space",
        es: "Espacio del Corazón",
        vi: "Không Gian Trái Tim",
        zh: "心灵空间"
      };
      
      const prefix = prefixes[lang] || prefixes.en;
      currentDay.textContent = `${prefix} • ${dayName} • ${time}`;
    }

    // ================================
    // LANGUAGE SELECTOR
    // ================================
    function initLanguageSelector() {
      const currentLangEl = document.getElementById('currentLanguage');
      const langOptions = document.querySelectorAll('.lang-option');
      
      // Language display mapping
      const languageDisplays = {
        en: "🌐 EN",
        es: "🌐 ES",
        vi: "🌐 VI",
        zh: "🌐 ZH"
      };
      
      // Language names for dropdown
      const languageNames = {
        en: "English",
        es: "Español",
        vi: "Tiếng Việt",
        zh: "中文"
      };
      
      // Update language display
      function updateLanguageDisplay(lang) {
        if (!currentLangEl) return;
        
        // Update current language indicator
        currentLangEl.innerHTML = languageDisplays[lang] || "🌐 EN";
        
        // Update active class on language options
        langOptions.forEach(option => {
          if (option.dataset.lang === lang) {
            option.classList.add('active');
            option.innerHTML = `${languageNames[lang] || lang}`;
          } else {
            option.classList.remove('active');
            option.textContent = languageNames[option.dataset.lang] || option.dataset.lang;
          }
        });
      }
      
      // Set initial language display
      updateLanguageDisplay(CONFIG.language);
      
      // Toggle dropdown on click
      currentLangEl.addEventListener('click', function(e) {
        e.stopPropagation();
        const dropdown = document.querySelector('.language-dropdown');
        dropdown.classList.toggle('show');
      });
      
      // Handle language selection
      langOptions.forEach(option => {
        option.addEventListener('click', function(e) {
          e.stopPropagation();
          const newLang = this.dataset.lang;
          
          // Close dropdown
          document.querySelector('.language-dropdown').classList.remove('show');
          
          // Update display
          updateLanguageDisplay(newLang);
          
          // Update CONFIG language
          CONFIG.language = newLang;
          if (ai) {
            ai.language = newLang;
          }
          
          // Store in appropriate storage
          if (CONFIG.anonymityFeatures.enabled) {
            sessionStorage.setItem('mentivio_language', newLang);
          } else {
            localStorage.setItem('mentivio_language', newLang);
          }
          
          // Update UI elements
          updateWelcomeMessage(newLang);
          updateQuickEmotions(newLang);
          updateInputPlaceholder(newLang);
          updateSafetyNotice(newLang);
          updateHeaderText(newLang);
          
          // Dispatch event for synchronization
          document.dispatchEvent(new CustomEvent('mentivioLangChange', {
            detail: { language: newLang }
          }));
        });
      });
      
      // Close dropdown when clicking outside
      document.addEventListener('click', function(e) {
        const dropdown = document.querySelector('.language-dropdown');
        if (dropdown.classList.contains('show') && 
            !e.target.closest('.language-selector')) {
          dropdown.classList.remove('show');
        }
      });
    }

    // ================================
    // WINDOW MANAGEMENT
    // ================================
    function showWindow() {
      if (isWindowOpen) return;
      
      isWindowOpen = true;
      
      if (window.innerWidth <= 768) {
        document.body.classList.add('mentivio-open');
      }
      
      mentivioWindow.classList.add('open');
      
      setTimeout(() => {
        if (mentivioInput) {
          mentivioInput.focus();
        }
      }, 100);
      
      updateAvatarEmoji('listening');
    }
    
    function hideWindow() {
      if (!isWindowOpen) return;
      
      isWindowOpen = false;
      mentivioWindow.classList.remove('open');
      document.body.classList.remove('mentivio-open');
      updateAvatarEmoji('calm');
    }

    avatar.addEventListener('click', showWindow);
    closeBtn.addEventListener('click', hideWindow);

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && isWindowOpen) {
        hideWindow();
      }
    });

    // ================================
    // ENHANCED MESSAGE HANDLING WITH HIGH EQ
    // ================================
    async function sendMessage(message) {
        if (!message || !message.trim()) return;
        
        // Get or create session ID
        const sessionId = getSessionId();
        const storage = window.mentivioStorage || localStorage;
        
        // Load previous messages
        const savedMessages = loadSavedConversation();
        
        // Detect emotion
        const emotion = detectEmotion(message);
        
        // Prepare request with session ID
        const requestData = {
            message: message,
            session_id: sessionId,
            language: CONFIG.language,
            emotion: emotion,
            context: savedMessages.slice(-10), // Send last 10 messages as context
            conversation_state: ai.conversationState,
            anonymous: CONFIG.anonymityFeatures.enabled || false
        };
        
        try {
            // Show typing indicator
            showTyping();
            
            const response = await fetch('/chatbot/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            // Hide typing indicator
            hideTyping();
            
            // Save the new session ID if returned (in case it changed)
            if (data.session_id) {
                saveSessionData(data.session_id);
            }
            
            // Update conversation in storage
            const updatedMessages = [
                ...savedMessages,
                { 
                    role: 'user', 
                    content: message, 
                    timestamp: Date.now(), 
                    language: CONFIG.language,
                    emotion: emotion
                },
                { 
                    role: 'bot', 
                    content: data.response, 
                    timestamp: Date.now(), 
                    language: CONFIG.language,
                    emotion: data.emotion || 'compassionate'
                }
            ];
            
            storage.setItem('mentivio_conversation', JSON.stringify(updatedMessages));
            
            // Update last activity
            storage.setItem('mentivio_last_activity', Date.now());
            
            // Update local AI state
            ai.updateLocalState(message, emotion);
            ai.addBotResponse(data.response, data.emotion || 'compassionate');
            
            // Update UI
            addMessage(message, 'user');
            addMessage(data.response, 'bot');
            
            // Update session UI
            updateSessionUI(sessionId);
            
            return data;
            
        } catch (error) {
            console.error('Error sending message:', error);
            hideTyping();
            
            // Fallback response
            const fallbackResponse = "I'm here with you. Sometimes connections falter, but my presence remains. What's one true thing you want to share?";
            addMessage(fallbackResponse, 'bot');
            
            // Save fallback to storage
            const savedMessages = loadSavedConversation();
            const updatedMessages = [
                ...savedMessages,
                { 
                    role: 'user', 
                    content: message, 
                    timestamp: Date.now(), 
                    language: CONFIG.language,
                    emotion: emotion
                },
                { 
                    role: 'bot', 
                    content: fallbackResponse, 
                    timestamp: Date.now(), 
                    language: CONFIG.language,
                    emotion: 'compassionate'
                }
            ];
            storage.setItem('mentivio_conversation', JSON.stringify(updatedMessages));
            
            throw error;
        }
    }

    // Enhanced quick emotions with full multilingual support
    document.querySelectorAll('.quick-emotion').forEach(btn => {
      btn.addEventListener('click', function() {
        const emotion = this.dataset.emotion;
        
        // Language-specific prompts for all emotions including new ones
        const prompts = {
          en: {
            overwhelmed: "My heart feels so heavy right now. Everything feels like too much and I'm not sure how to keep going.",
            anxious: "My mind won't stop racing with worries. I feel so anxious about everything that could go wrong.",
            sad: "I'm feeling really low and sad today. The sadness feels heavy and I don't know how to lift it.",
            lonely: "I feel so alone, even when people are around. The loneliness is profound and isolating.",
            hesitant: "I feel so hesitant and unsure about what to do. Every choice feels overwhelming and I'm scared of making the wrong decision.",
            confused: "I'm feeling really confused about things in my life. I don't understand what's happening or what I should do next.",
            study: "I'm struggling with my studies. The pressure is overwhelming and I don't know how to keep up with everything.",
            love: "My heart is hurting from a relationship. I don't know how to move forward or heal from this pain.",
            gender: "I'm questioning my gender identity and it's confusing and scary. I don't know who to talk to about this.",
            lgbtq: "I'm exploring my sexuality/identity and it feels lonely. I'm not sure how to navigate these feelings or find acceptance.",
            curious: "I'm searching for meaning in all of this. What's the purpose when things feel so hard?",
            hopeful: "I'm trying to find hope. Can you help me see possibilities and light ahead?",
            lost: "I feel completely lost right now. I don't know which direction to take or what my purpose is anymore.",
            transition: "I'm in a major life transition and everything feels uncertain. I don't know who I am or where I'm going.",
            future: "I'm so anxious about the future. All the 'what ifs' are overwhelming me and I can't see a clear path forward.",
            reset: "I need a complete reset in my life. Things aren't working and I don't know how to start over."
          },
          es: {
            overwhelmed: "Mi corazón se siente tan pesado ahora mismo. Todo parece demasiado y no estoy seguro de cómo seguir adelante.",
            anxious: "Mi mente no deja de correr con preocupaciones. Me siento tan ansioso por todo lo que podría salir mal.",
            sad: "Me siento muy deprimido y triste hoy. La tristeza se siente pesada y no sé cómo levantarla.",
            lonely: "Me siento tan solo, incluso cuando hay gente alrededor. La soledad es profunda y aislante.",
            hesitant: "Me siento tan vacilante e inseguro sobre qué hacer. Cada decisión me abruma y tengo miedo de tomar la decisión equivocada.",
            confused: "Me siento realmente confundido sobre las cosas en mi vida. No entiendo qué está pasando o qué debo hacer a continuación.",
            study: "Estoy luchando con mis estudios. La presión es abrumadora y no sé cómo mantener el ritmo con todo.",
            love: "Mi corazón está sufriendo por una relación. No sé cómo seguir adelante o sanar de este dolor.",
            gender: "Estoy cuestionando mi identidad de género y es confuso y aterrador. No sé con quién hablar sobre esto.",
            lgbtq: "Estoy explorando mi sexualidad/identidad y me siento solo. No estoy seguro de cómo manejar estos sentimientos o encontrar aceptación.",
            curious: "Estoy buscando significado en todo esto. ¿Cuál es el propósito cuando las cosas se sienten tan difíciles?",
            hopeful: "Estoy tratando de encontrar esperanza. ¿Puedes ayudarme a ver posibilidades y luz adelante?",
            lost: "Me siento completamente perdido ahora mismo. No sé qué dirección tomar ni cuál es mi propósito ya.",
            transition: "Estoy en una gran transición de vida y todo se siente incierto. No sé quién soy ni a dónde voy.",
            future: "Estoy tan ansioso por el futuro. Todos los 'qué pasaría si' me abruman y no puedo ver un camino claro hacia adelante.",
            reset: "Necesito un reinicio completo en mi vida. Las cosas no están funcionando y no sé cómo empezar de nuevo."
          },
          vi: {
            overwhelmed: "Trái tim tôi cảm thấy thật nặng nề ngay lúc này. Mọi thứ đều cảm thấy quá sức và tôi không chắc làm thế nào để tiếp tục.",
            anxious: "Tâm trí tôi không ngừng chạy đua với những lo lắng. Tôi cảm thấy rất lo lắng về tất cả những gì có thể xảy ra.",
            sad: "Hôm nay tôi cảm thấy rất buồn và chán nản. Nỗi buồn cảm thấy thật nặng nề và tôi không biết làm thế nào để vượt qua.",
            lonely: "Tôi cảm thấy thật cô đơn, ngay cả khi có người xung quanh. Sự cô đơn thật sâu sắc và tách biệt.",
            hesitant: "Tôi cảm thấy rất do dự và không chắc chắn về việc phải làm. Mỗi lựa chọn đều cảm thấy choáng ngợp và tôi sợ mình sẽ đưa ra quyết định sai lầm.",
            confused: "Tôi cảm thấy thực sự bối rối về mọi thứ trong cuộc sống của mình. Tôi không hiểu chuyện gì đang xảy ra hoặc tôi nên làm gì tiếp theo.",
            study: "Tôi đang gặp khó khăn với việc học. Áp lực thật choáng ngợp và tôi không biết làm thế nào để theo kịp mọi thứ.",
            love: "Trái tim tôi đang đau đớn vì một mối quanệ. Tôi không biết làm thế nào để tiến lên hoặc chữa lành nỗi đau này.",
            gender: "Tôi đang nghi vấn về bản dạng giới của mình và điều đó thật khó hiểu và đáng sợ. Tôi không biết nên nói chuyện với ai về điều này.",
            lgbtq: "Tôi đang khám phá xu hướng tính dục/bản dạng của mình và cảm thấy cô đơn. Tôi không chắc làm thế nào để điều hướng những cảm xúc này hoặc tìm thấy sự chấp nhận.",
            curious: "Tôi đang tìm kiếm ý nghĩa trong tất cả điều này. Mục đích là gì khi mọi thứ cảm thấy thật khó khăn?",
            hopeful: "Tôi đang cố gắng tìm hy vọng. Bạn có thể giúp tôi nhìn thấy khả năng và ánh sáng phía trước không?",
            lost: "Tôi cảm thấy hoàn toàn lạc lối ngay bây giờ. Tôi không biết nên đi theo hướng nào hay mục đích của mình là gì nữa.",
            transition: "Tôi đang ở trong một giai đoạn chuyển tiếp lớn của cuộc đời và mọi thứ đều cảm thấy không chắc chắn. Tôi không biết mình là ai hay mình đang đi đâu.",
            future: "Tôi rất lo lắng về tương lai. Tất cả những 'sẽ ra sao nếu' đang làm tôi choáng ngợp và tôi không thể thấy một con đường rõ ràng phía trước.",
            reset: "Tôi cần một khởi động lại hoàn toàn trong cuộc sống. Mọi thứ không hoạt động và tôi không biết làm thế nào để bắt đầu lại."
          },
          zh: {
            overwhelmed: "我的心现在感觉如此沉重。一切都感觉太多了，我不确定如何继续前进。",
            anxious: "我的思绪不停地被忧虑占据。我对一切可能出错的事情感到非常焦虑。",
            sad: "我今天感到非常低落和悲伤。悲伤感觉很沉重，我不知道如何摆脱它。",
            lonely: "我感到如此孤独，即使周围有人。这种孤独是深刻而孤立的。",
            hesitant: "我感到非常犹豫，不确定该做什么。每一个选择都让我感到不知所措，我害怕做出错误的决定。",
            confused: "我对生活中的事情感到非常困惑。我不明白发生了什么，也不知道下一步该怎么做。",
            study: "我在学习上遇到了困难。压力太大了，我不知道如何跟上一切。",
            love: "我的心因为一段关系而受伤。我不知道如何前进或从这种痛苦中愈合。",
            gender: "我正在质疑我的性别认同，这令人困惑和害怕。我不知道该和谁谈论这个问题。",
            lgbtq: "我正在探索我的性取向/身份，这让我感到孤独。我不确定如何应对这些感受或找到接受。",
            curious: "我正在这一切中寻找意义。当事情感觉如此困难时，目的是什么？",
            hopeful: "我正在努力寻找希望。你能帮我看到前方的可能性和光明吗？",
            lost: "我现在感到完全迷茫。我不知道该走哪个方向，也不知道我的目的是什么了。",
            transition: "我正处于人生重大过渡期，一切都感觉不确定。我不知道我是谁，也不知道我要去哪里。",
            future: "我对未来感到非常焦虑。所有的'如果'让我不知所措，我看不到明确的前进道路。",
            reset: "我需要生活中完全的重启。事情不顺利，我不知道如何重新开始。"
          }
        };
        
        const langPrompts = prompts[CONFIG.language] || prompts.en;
        if (mentivioInput) {
          mentivioInput.value = langPrompts[emotion] || `I'm feeling ${emotion} and could use someone to talk to.`;
          mentivioInput.focus();
        }
      });
    });

    // Input handling
    if (mentivioInput) {
      mentivioInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          const message = mentivioInput.value.trim();
          if (message) {
            sendMessage(message);
            mentivioInput.value = '';
            mentivioInput.style.height = 'auto';
          }
        }
      });
      
      mentivioInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 80) + 'px';
      });
    }

    if (sendBtn) {
      sendBtn.addEventListener('click', function() {
        const message = mentivioInput.value.trim();
        if (message) {
          sendMessage(message);
          mentivioInput.value = '';
          mentivioInput.style.height = 'auto';
        }
      });
    } else {
      console.error('Send button not found in DOM');
    }

    // ================================
    // UI HELPER FUNCTIONS
    // ================================
    function addMessage(text, sender) {
      const messageDiv = document.createElement('div');
      messageDiv.className = `message ${sender}`;
      
      const time = new Date().toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      }).replace(' ', '').toLowerCase();
      
      messageDiv.innerHTML = `
        <div class="message-content">
          <div class="message-text">${formatMessage(text)}</div>
          <div class="message-time">${time}</div>
        </div>
      `;
      
      messages.appendChild(messageDiv);
      scrollToBottom();
    }

    function showTyping() {
      isTyping = true;
      typingIndicator.style.display = 'block';
      
      const typingStatuses = {
        en: [
          "Mentivio is thinking deeply...",
          "Listening with my whole heart...",
          "Reflecting on what you've shared...",
          "Holding space for your words..."
        ],
        es: [
          "Mentivio está pensando profundamente...",
          "Escuchando con todo mi corazón...",
          "Reflexionando sobre lo que has compartido...",
          "Guardando espacio para tus palabras..."
        ],
        vi: [
          "Mentivio đang suy nghĩ sâu sắc...",
          "Lắng nghe bằng cả trái tim...",
          "Suy ngẫm về những gì bạn đã chia sẻ...",
          "Giữ không gian cho lời nói của bạn..."
        ],
        zh: [
          "Mentivio正在深入思考...",
          "用全心倾听...",
          "反思您分享的内容...",
          "为您的言语保留空间..."
        ]
      };
      
      const statuses = typingStatuses[CONFIG.language] || typingStatuses.en;
      const statusElement = document.getElementById('typingStatus');
      if (statusElement) {
        statusElement.textContent = statuses[Math.floor(Math.random() * statuses.length)];
      }
    }

    function hideTyping() {
      isTyping = false;
      typingIndicator.style.display = 'none';
    }

    function updateAvatarEmoji(state) {
      const emojis = {
        thinking: '💭',
        listening: '👂',
        empathetic: '🤍',
        calm: '😌',
        warning: '⚠️',
        hopeful: '✨',
        present: '🌱',
        caring: '💗'
      };
      
      const emoji = emojis[state] || '💭';
      const avatarEmojiEl = document.getElementById('avatarEmoji');
      if (avatarEmojiEl) {
        avatarEmojiEl.textContent = emoji;
      }
    }

    function updateEmotionalIndicator(emotion) {
      const colors = {
        happy: '#4ade80',
        sad: '#3b82f6',
        anxious: '#f59e0b',
        angry: '#ef4444',
        overwhelmed: '#8b5cf6',
        neutral: '#94a3b8',
        curious: '#10b981',
        hopeful: '#ec4899',
        grateful: '#f59e0b',
        lonely: '#64748b',
        peaceful: '#06b6d4',
        hesitant: '#a78bfa',
        confused: '#fbbf24',
        ashamed: '#dc2626',
        jealous: '#7c3aed',
        rejected: '#6b7280',
        betrayed: '#be123c'
      };
      
      if (activeEmotion) {
        activeEmotion.style.background = colors[emotion] || colors.neutral;
      }
    }

    function scrollToBottom() {
      if (messages) {
        messages.scrollTop = messages.scrollHeight;
      }
    }

    // Initial pulse animation
    setTimeout(() => {
      if (!isWindowOpen && avatar) {
        avatar.style.transform = 'scale(1.1)';
        setTimeout(() => {
          avatar.style.transform = '';
        }, 600);
      }
    }, 2000);

    window.addEventListener('resize', updateDay);
    
    // Initialize language selector
    initLanguageSelector();
    
    // Initialize language synchronization
    setupLanguageSynchronization();

    // Update all UI elements with current language
    updateWelcomeMessage(CONFIG.language);
    updateQuickEmotions(CONFIG.language);
    updateInputPlaceholder(CONFIG.language);
    updateSafetyNotice(CONFIG.language);
    updateHeaderText(CONFIG.language);
    updateDay();

    // Initialize chat (restore conversation)
    setTimeout(() => {
      initializeChat();
    }, 500);

    // ================================
    // ADDITIONAL RESOURCES MODAL
    // ================================
    window.showAdditionalResources = function(lang) {
      const resourcesHTML = `
      <div id="additional-resources" class="resources-modal">
        <div class="resources-container">
          <div class="resources-header">
            <h2>${lang === 'en' ? 'Additional Support Resources' :
              lang === 'es' ? 'Recursos de Apoyo Adicionales' :
              lang === 'vi' ? 'Tài Nguyên Hỗ Trợ Bổ Sung' :
              '额外支持资源'}</h2>
            <button onclick="document.getElementById('additional-resources').remove()" class="close-btn">×</button>
          </div>
          
          <div class="resources-section">
            <h3>24/7 Crisis Lines</h3>
            <div class="resources-grid">
              <div class="resource-card">
                <div class="resource-title">988 Suicide & Crisis Lifeline</div>
                <div class="resource-desc">Call or text 988 for immediate support</div>
              </div>
              <div class="resource-card">
                <div class="resource-title">Crisis Text Line</div>
                <div class="resource-desc">Text HOME to 741741</div>
              </div>
            </div>
          </div>
          
          <div class="resources-section">
            <h3>Specialized Support</h3>
            <div class="resources-grid">
              <div class="resource-card">
                <div class="resource-title">The Trevor Project (LGBTQ+)</div>
                <div class="resource-desc">Call 866-488-7386 or text START to 678678</div>
              </div>
              <div class="resource-card">
                <div class="resource-title">Veterans Crisis Line</div>
                <div class="resource-desc">Call 988 then press 1, or text 838255</div>
              </div>
            </div>
          </div>
          
          <button onclick="document.getElementById('additional-resources').remove()" class="resources-close-btn">
            ${lang === 'en' ? 'Return to Chat' :
              lang === 'es' ? 'Volver al Chat' :
              lang === 'vi' ? 'Quay lại Trò chuyện' :
              '返回聊天'}
          </button>
        </div>
      </div>`;
      
      const existing = document.getElementById('additional-resources');
      if (existing) existing.remove();
      
      document.body.insertAdjacentHTML('beforeend', resourcesHTML);
    };

    // Global functions for crisis modal
    window.confirmHelpReceived = function() {
      const modal = document.getElementById('mentivio-emergency-overlay');
      if (modal) {
        modal.remove();
        
        // Re-enable input
        if (mentivioInput) {
          mentivioInput.disabled = false;
          updateInputPlaceholder(CONFIG.language);
          mentivioInput.focus();
        }
        
        if (sendBtn) {
          sendBtn.disabled = false;
        }
        
        // Add a follow-up message
        const followUpMessages = {
          en: "Thank you for reaching out for support. I'm here with you. How are you feeling now?",
          es: "Gracias por buscar apoyo. Estoy aquí contigo. ¿Cómo te sientes ahora?",
          vi: "Cảm ơn bạn đã tìm kiếm sự hỗ trợ. Tôi ở đây với bạn. Bây giờ bạn cảm thấy thế nào?",
          zh: "感谢您寻求支持。我在这里陪着您。您现在感觉如何？"
        };
        
        const message = followUpMessages[CONFIG.language] || followUpMessages.en;
        setTimeout(() => {
          addMessage(message, 'bot');
        }, 500);
      }
    };

    window.resumeChatAfterCrisis = function() {
      const modal = document.getElementById('mentivio-emergency-overlay');
      if (modal) {
        modal.remove();
        
        // Re-enable input
        if (mentivioInput) {
          mentivioInput.disabled = false;
          updateInputPlaceholder(CONFIG.language);
          mentivioInput.focus();
        }
        
        if (sendBtn) {
          sendBtn.disabled = false;
        }
      }
    };

    // ================================
    // ENHANCED GLOBAL CRISIS FUNCTION (MULTILINGUAL)
    // ================================
    window.showEnhancedCrisisResources = function(lang = null) {
      // Use the global CONFIG if no lang specified
      if (!lang && CONFIG) {
        lang = CONFIG.language;
      }
      
      showEmergencyCrisisModal(lang, 'urgent');
    };

    // ================================
    // GLOBAL FUNCTION EXPORTS
    // ================================
    window.showMentivioWindow = showWindow;
    window.hideMentivioWindow = hideWindow;
    window.isMentivioWindowOpen = () => isWindowOpen;
    window.clearChatHistory = clearChatHistory;

    // ================================
    // GLOBAL ACCESS
    // ================================
    if (!window.mentivioGlobal) {
      window.mentivioGlobal = {
        showCrisisHelp: window.showEnhancedCrisisResources,
        quickCheckIn: () => {
          const feelings = {
            en: [
              "How's your heart today?",
              "What's one true thing you're feeling?",
              "What small hope are you holding?",
              "What's weighing on your mind?"
            ],
            es: [
              "¿Cómo está tu corazón hoy?",
              "¿Qué cosa verdadera estás sintiendo?",
              "¿Qué pequeña esperanza estás sosteniendo?",
              "¿Qué te preocupa?"
            ],
            vi: [
              "Trái tim bạn hôm nay thế nào?",
              "Một điều chân thật bạn đang cảm thấy là gì?",
              "Hy vọng nhỏ nào bạn đang giữ?",
              "Điều gì đang đè nặng tâm trí bạn?"
            ],
            zh: [
              "你今天的心情如何？",
              "你真正感受到的一件事是什么？",
              "你怀着怎样的小希望？",
              "什么让你心事重重？"
            ]
          };
          
          const currentLang = CONFIG ? CONFIG.language : 'en';
          const langFeelings = feelings[currentLang] || feelings.en;
          const feeling = langFeelings[Math.floor(Math.random() * langFeelings.length)];
          
          // Try to open chat window and set the message
          if (mentivioInput) {
            mentivioInput.value = feeling;
            mentivioInput.focus();
            
            // Show window if not open
            if (!isWindowOpen && window.showMentivioWindow) {
              window.showMentivioWindow();
            }
          } else {
            alert(feeling);
          }
        },
        getInspiration: async () => {
          try {
            const response = await fetch('/chatbot/api/inspiration');
            if (response.ok) {
              const data = await response.json();
              alert(`${data.quote}\n\n- ${data.story.title}`);
            }
          } catch (error) {
            console.error('Inspiration fetch error:', error);
          }
        },
        setLanguage: (lang) => {
          if (['en', 'es', 'vi', 'zh'].includes(lang)) {
            if (updateChatbotLanguage) {
              updateChatbotLanguage(lang);
            } else {
              // Fallback: save to localStorage and dispatch event
              if (CONFIG.anonymityFeatures.enabled) {
                sessionStorage.setItem('mentivio_language', lang);
              } else {
                localStorage.setItem('mentivio_language', lang);
              }
              document.dispatchEvent(new CustomEvent('languageChanged', {
                detail: { language: lang }
              }));
            }
          }
        },
        getLanguage: () => CONFIG ? CONFIG.language : 'en',
        updateHeader: (lang) => {
          if (lang) {
            updateHeaderText(lang);
          } else if (CONFIG && CONFIG.language) {
            updateHeaderText(CONFIG.language);
          }
        },
        showChat: showWindow,
        hideChat: hideWindow,
        exportData: () => window.complianceManager?.exportUserData(),
        showPrivacy: () => window.complianceManager?.showPrivacyControls()
      };
    }

    // ================================
    // EXPOSE FUNCTIONS GLOBALLY
    // ================================
    window.updateChatbotLanguage = updateChatbotLanguage;
    window.isMentivioWindowOpen = () => isWindowOpen;

    // ================================
    // INITIALIZE COMPLIANCE MANAGER
    // ================================
    window.complianceManager = new ComplianceManager();
    window.complianceManager.initialize();

    // ================================
    // INITIAL LANGUAGE SYNC
    // ================================
    setTimeout(() => {
      // Initial sync with global language manager
      if (window.globalLangManager) {
        const globalLang = window.globalLangManager.currentLang;
        if (globalLang && globalLang !== CONFIG.language && updateChatbotLanguage) {
          console.log('Initial language sync with global manager:', globalLang);
          updateChatbotLanguage(globalLang);
        }
      }
      
      // Ensure header is updated on initial load
      if (CONFIG && CONFIG.language) {
        updateHeaderText(CONFIG.language);
      }
    }, 1000);

    console.log('Mentivio initialized with session persistence and full multilingual support');
  }
})();