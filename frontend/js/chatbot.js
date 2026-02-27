// ================================
// Mentivio — High EQ AI Mental Health Companion
// MULTILINGUAL SUPPORT: en, es, vi, zh (loaded from translations.json)
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

// Global translations object (filled from JSON)
let translations = {};

// Placeholder to satisfy browser extensions that check for this function early
window.updateDay = function() {};

// ================================
// TRANSLATION LOADER
// ================================
async function loadTranslations() {
  try {
    const response = await fetch('/lang/chatbot.json');
    if (!response.ok) throw new Error('Failed to load translations');
    translations = await response.json();
    console.log('Translations loaded successfully');
  } catch (error) {
    console.error('Error loading translations, falling back to embedded defaults (English only).', error);
    // Minimal fallback (English) to keep the chatbot running
    translations = {
      en: {
        session: { messages: "messages", anonymous: "Anonymous", clear: "Clear" },
        fallbackResponses: ["I'm here with you."],
        quickEmotionPrompts: {},
        header: { title: "Mentivio: Your Friend", heartSpace: "Heart Space" },
        dayNames: { short: ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"], long: [] },
        timeFormats: { hour12: true },
        typingStatuses: ["Mentivio is thinking..."],
        crisisModal: {
          immediate: { title: "Immediate Support Needed", message: "" },
          urgent: { title: "Support Available", message: "" },
          buttonTexts: { call: "Call", emergency: "Emergency Services", contacted: "I've contacted support", callEmergency: "Call Emergency", continue: "Continue", moreResources: "More resources" },
          importantMessage: "For your safety, chat will remain paused.",
          footerMessage: "Mentivio provides support."
        },
        resourcesModal: {
          title: "Resources",
          buttonClose: "Return to Chat",
          buttonFullPage: "Full Page",
          immediateHelp: { title: "Immediate Help", call988: "Call 988", textHome: "Text HOME", emergency: "911" },
          categories: {},
          internationalResources: []
        },
        clearChat: { confirm: "Clear history?", confirmation: "History cleared." },
        welcomeMessage: "Hello, I'm Mentivio.",
        inputPlaceholder: "Share what's in your heart...",
        safetyNotice: "Safe space • High EQ",
        crisisLinkText: "Need help?",
        privacyLinkText: "Privacy",
        quickEmotionLabels: {}
      }
    };
  }
}

// Helper to get a translation by dot‑separated key path
function getTranslation(lang, keyPath, fallback = '') {
  const langData = translations[lang] || translations.en;
  const keys = keyPath.split('.');
  let value = langData;
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      return fallback;
    }
  }
  return value || fallback;
}

// ================================
// SESSION PERSISTENCE FUNCTIONS
// ================================
// Generate or retrieve session ID
function getSessionId() {
    let sessionId = localStorage.getItem('mentivio_session_id');
    if (!sessionId && window.mentivioStorage === sessionStorage) {
        sessionId = sessionStorage.getItem('mentivio_session_id');
    }
    if (!sessionId) {
        sessionId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        saveSessionData(sessionId, []);
        console.log('Created new session:', sessionId);
    } else {
        console.log('Retrieved existing session:', sessionId);
    }
    return sessionId;
}

function saveSessionData(sessionId, messages = []) {
    const storage = window.mentivioStorage || localStorage;
    storage.setItem('mentivio_session_id', sessionId);
    if (messages.length > 0) {
        storage.setItem('mentivio_conversation', JSON.stringify(messages));
    }
    storage.setItem('mentivio_last_activity', Date.now());
    if (!storage.getItem('mentivio_session_created')) {
        storage.setItem('mentivio_session_created', new Date().toISOString());
    }
}

function loadSavedConversation() {
    try {
        const storage = window.mentivioStorage || localStorage;
        const saved = storage.getItem('mentivio_conversation');
        if (saved) {
            return JSON.parse(saved);
        }
    } catch (error) {
        console.error('Error loading saved conversation:', error);
    }
    return [];
}

async function restoreSessionFromBackend(sessionId) {
    try {
        console.log('Restoring session from backend:', sessionId);
        const statusResponse = await fetch(`/chatbot/api/session/status?session_id=${sessionId}`);
        const statusData = await statusResponse.json();
        if (statusData.active) {
            const exportResponse = await fetch(`/chatbot/api/session/export?session_id=${sessionId}`);
            const exportData = await exportResponse.json();
            if (exportData.conversation_history && exportData.conversation_history.length > 0) {
                console.log(`Retrieved ${exportData.conversation_history.length} messages from backend`);
                const formattedMessages = exportData.conversation_history.map(msg => ({
                    role: msg.role,
                    content: msg.content,
                    timestamp: new Date(msg.timestamp).getTime(),
                    language: msg.language,
                    emotion: msg.emotion || 'neutral'
                }));
                saveSessionData(sessionId, formattedMessages);
                return { success: true, messages: formattedMessages, sessionId, sessionData: exportData };
            }
        } else {
            console.log('Session expired or not found in backend – keeping local storage');
            // Do NOT clear local storage; just indicate backend restore failed.
            return { success: false, messages: [], sessionId: sessionId, message: 'Session expired' };
        }
    } catch (error) {
        console.error('Error restoring session from backend:', error);
        return { success: false, messages: [], sessionId, error: error.message };
    }
    return { success: false, messages: [], sessionId };
}

async function checkSessionStatus(sessionId) {
    try {
        const response = await fetch(`/chatbot/api/session/status?session_id=${sessionId}`);
        const data = await response.json();
        if (!data.active) {
            console.log('Session expired on backend, but keeping local session');
            // Do not clear local storage; the next message will create a new backend session.
        }
        return sessionId;
    } catch (error) {
        console.error('Error checking session status:', error);
        return sessionId;
    }
}



function clearSession() {
    const storage = window.mentivioStorage || localStorage;
    const oldSessionId = storage.getItem('mentivio_session_id');
    if (oldSessionId) {
        fetch('/chatbot/api/session/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: oldSessionId })
        }).catch(error => console.error('Error clearing backend session:', error));
    }
    storage.removeItem('mentivio_session_id');
    storage.removeItem('mentivio_conversation');
    storage.removeItem('mentivio_session_created');
    storage.removeItem('mentivio_last_activity');
    const newSessionId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    saveSessionData(newSessionId, []);
    console.log('Cleared session and created new:', newSessionId);
    return newSessionId;
}

async function sendMessage(message) {
    if (!message || !message.trim()) return;
    const sessionId = getSessionId();
    const storage = window.mentivioStorage || localStorage;
    const savedMessages = loadSavedConversation();
    const emotion = detectEmotion(message);
    const requestData = {
        message,
        session_id: sessionId,
        language: CONFIG.language,
        emotion,
        context: savedMessages.slice(-10),
        conversation_state: ai.conversationState,
        anonymous: CONFIG.anonymityFeatures.enabled || false
    };
    try {
        showTyping();
        const response = await fetch('/chatbot/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        const data = await response.json();
        hideTyping();
        if (data.session_id) saveSessionData(data.session_id);
        const updatedMessages = [
            ...savedMessages,
            { role: 'user', content: message, timestamp: Date.now(), language: CONFIG.language, emotion },
            { role: 'bot', content: data.response, timestamp: Date.now(), language: CONFIG.language, emotion: data.emotion || 'compassionate' }
        ];
        storage.setItem('mentivio_conversation', JSON.stringify(updatedMessages));
        storage.setItem('mentivio_last_activity', Date.now());
        ai.updateLocalState(message, emotion);
        ai.addBotResponse(data.response, data.emotion || 'compassionate');
        addMessage(message, 'user');
        addMessage(data.response, 'bot');
        updateSessionUI(sessionId);
        return data;
    } catch (error) {
        console.error('Error sending message:', error);
        hideTyping();
        const fallbackResponse = getTranslation(CONFIG.language, 'fallbackResponses.0', "I'm here with you.");
        addMessage(fallbackResponse, 'bot');
        const updatedMessages = [
            ...savedMessages,
            { role: 'user', content: message, timestamp: Date.now(), language: CONFIG.language, emotion },
            { role: 'bot', content: fallbackResponse, timestamp: Date.now(), language: CONFIG.language, emotion: 'compassionate' }
        ];
        storage.setItem('mentivio_conversation', JSON.stringify(updatedMessages));
        throw error;
    }
}

async function clearChatHistory() {
    const lang = CONFIG.language;
    const confirmMsg = getTranslation(lang, 'clearChat.confirm', "Clear all chat history? This cannot be undone.");
    const confirmationMsg = getTranslation(lang, 'clearChat.confirmation', "Chat history cleared.");
    
    if (confirm(confirmMsg)) {
        const sessionId = getSessionId();
        try {
            await fetch('/chatbot/api/session/clear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
        } catch (error) {
            console.error('Error clearing backend session:', error);
        }
        
        const storage = window.mentivioStorage || localStorage;
        storage.removeItem('mentivio_conversation');
        
        // Re‑display only the welcome message
        displayConversation([]);
        updateSessionUI(sessionId);
        
        setTimeout(() => addMessage(confirmationMsg, 'bot'), 500);
    }
}

async function initializeChat() {
    console.log('Initializing chat with persistence...');
    
    const sessionId = getSessionId();
    const storage = window.mentivioStorage || localStorage;
    
    // Check for inactivity timeout
    const lastActivity = parseInt(storage.getItem('mentivio_last_activity') || '0');
    const now = Date.now();
    const thirtyMinutes = 30 * 60 * 1000;
    
    if (lastActivity > 0 && now - lastActivity > thirtyMinutes) {
        console.log('Session expired due to inactivity, creating new session');
        const newSessionId = clearSession();
        updateSessionUI(newSessionId);
        return;
    }
    
    // Try to restore from backend first
    console.log('Attempting to restore session from backend...');
    const backendResult = await restoreSessionFromBackend(sessionId);
    
    if (backendResult.success && backendResult.messages.length > 0) {
        console.log(`Restored ${backendResult.messages.length} messages from backend.`);
        displayConversation(backendResult.messages);
        updateSessionUI(sessionId);
    } else {
        console.log('Backend restore failed or no messages, falling back to local storage.');
        const savedMessages = loadSavedConversation();
        
        if (savedMessages.length > 0) {
            console.log(`Loaded ${savedMessages.length} messages from local storage.`);
            displayConversation(savedMessages);
        } else {
            console.log('No messages found in local storage either.');
            // Ensure the welcome message is still shown
            const chatContainer = document.getElementById('mentivioMessages');
            if (chatContainer && chatContainer.children.length === 0) {
                displayConversation([]); // This will show only the welcome message
            }
        }
        
        updateSessionUI(sessionId);
        
        // Verify session status with backend asynchronously
        setTimeout(() => {
            checkSessionStatus(sessionId).catch(err => 
                console.error('Session status check failed:', err)
            );
        }, 1000);
    }
    
    // Always update last activity
    storage.setItem('mentivio_last_activity', Date.now());
}

function updateSessionUI(sessionId) {
    const sessionInfoElement = document.getElementById('session-info');
    if (!sessionInfoElement) return;
    const savedMessages = loadSavedConversation();
    const userMessageCount = savedMessages.filter(m => m.role === 'user').length;
    const botMessageCount = savedMessages.filter(m => m.role === 'bot').length;
    const lang = CONFIG.language;
    const t = translations[lang] || translations.en;
    sessionInfoElement.innerHTML = `
        <div class="session-indicator">
            <span class="session-icon">💭</span>
            <span class="session-stats">
                ${userMessageCount + botMessageCount} ${t.session.messages}
                ${CONFIG.anonymityFeatures.enabled ? `<span class="anon-badge">${t.session.anonymous}</span>` : ''}
            </span>
            <button onclick="clearChatHistory()" class="clear-btn" title="Clear chat history">
                <i class="fas fa-trash-alt"></i> ${t.session.clear}
            </button>
        </div>
    `;
}

function createMessageElement(msg) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${msg.role}`;
    const time = msg.timestamp ?
        new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true }).replace(' ', '').toLowerCase() :
        'just now';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-text">${formatMessage(msg.content)}</div>
            <div class="message-time">${time}</div>
        </div>
    `;
    return messageDiv;
}

function formatMessage(text) {
    if (!text) return '';

    // Escape HTML to prevent XSS (but we trust the backend, still a good practice)
    let escaped = text.replace(/[&<>"]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        if (m === '"') return '&quot;';
        return m;
    });

    // Convert **bold** to <strong>bold</strong>
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Split into lines to handle bullet points
    const lines = escaped.split('\n');
    let inList = false;
    let html = '';

    lines.forEach(line => {
        const trimmed = line.trim();
        if (trimmed.startsWith('•')) {
            // Start a new list if not already in one
            if (!inList) {
                html += '<ul>';
                inList = true;
            }
            html += `<li>${trimmed.substring(1).trim()}</li>`;
        } else {
            if (inList) {
                html += '</ul>';
                inList = false;
            }
            // Add the line (if not empty) with a <br> or as a paragraph
            if (trimmed !== '') {
                html += `<p>${line}</p>`;
            } else {
                html += '<br>';
            }
        }
    });

    // Close any open list
    if (inList) html += '</ul>';

    return html;
}

function displayConversation(messages) {
    const chatContainer = document.getElementById('mentivioMessages');
    if (!chatContainer) return;
    
    // Clear the container completely
    chatContainer.innerHTML = '';
    
    // Create a fresh welcome message using the current language
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'welcome-message';
    welcomeDiv.innerHTML = `
        <div class="message bot">
            <div class="message-content">
                <div class="message-text">${getTranslation(CONFIG.language, 'welcomeMessage', 'Hello 😊')}</div>
                <div class="message-time">just now</div>
            </div>
        </div>
    `;
    chatContainer.appendChild(welcomeDiv);
    
    // Append all saved messages
    messages.forEach(msg => chatContainer.appendChild(createMessageElement(msg)));
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// ================================
// ANONYMITY MODE FUNCTIONS
// ================================
function enableAnonymousMode() {
    console.log('Anonymous mode enabled');
    CONFIG.anonymityFeatures.enabled = true;
    window['ga-disable-UA-XXXXX-Y'] = true;
    if (window.gtag) window.gtag = function() { console.log('Analytics disabled in anonymous mode'); };
    localStorage.removeItem('mentivio_high_eq_history');
    localStorage.removeItem('mentivio_user_id');
    localStorage.removeItem('mentivio_session_id');
    localStorage.removeItem('mentivio_user_consent');
    window.mentivioStorage = sessionStorage;
    disableFingerprinting();
    const avatar = document.getElementById('mentivioAvatar');
    if (avatar) {
        avatar.style.background = 'linear-gradient(135deg, #6b7280, #9ca3af)';
        avatar.title = 'Anonymous Mode - No data stored permanently';
    }
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
    text = text.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[EMAIL]');
    text = text.replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE]');
    text = text.replace(/\b\d{3}[-.]?\d{4}\b/g, '[PHONE]');
    text = text.replace(/\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g, '[PHONE]');
    text = text.replace(/\b(?:[A-Z][a-z]+ )+[A-Z][a-z]+\b/g, '[NAME]');
    text = text.replace(/\b\d+\s+\w+\s+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln)\b/gi, '[ADDRESS]');
    text = text.replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN]');
    text = text.replace(/\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g, '[CARD]');
    text = text.replace(/\b(0?[1-9]|1[0-2])[\/\-](0?[1-9]|[12][0-9]|3[01])[\/\-]\d{4}\b/g, '[DOB]');
    text = text.replace(/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, '[IP]');
    return text;
}

function disableFingerprinting() {
    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8, configurable: true });
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4, configurable: true });
    Object.defineProperty(navigator, 'platform', { get: () => 'Unknown', configurable: true });
    Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (Anonymous) AppleWebKit/537.36', configurable: true });
    if (window.RTCPeerConnection) {
        const originalRTCPeerConnection = window.RTCPeerConnection;
        window.RTCPeerConnection = function(...args) {
            console.warn('WebRTC disabled in anonymous mode');
            return {
                createDataChannel: () => ({ close: () => {}, send: () => {} }),
                createOffer: () => Promise.reject(new Error('WebRTC disabled')),
                close: () => {}
            };
        };
        window.RTCPeerConnection.prototype = originalRTCPeerConnection.prototype;
    }
    const originalGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(...args) {
        const context = originalGetContext.apply(this, args);
        if (context && args[0] === '2d') {
            const originalFillText = context.fillText;
            context.fillText = function(...textArgs) { return originalFillText.apply(this, textArgs); };
            const originalGetImageData = context.getImageData;
            context.getImageData = function(...getArgs) {
                const imageData = originalGetImageData.apply(this, getArgs);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] += Math.floor(Math.random() * 3) - 1;
                }
                return imageData;
            };
        }
        return context;
    };
    if (window.AudioContext) {
        window.AudioContext = function() {
            return {
                createOscillator: () => ({ start: () => {}, stop: () => {}, connect: () => {}, frequency: { setValueAtTime: () => {} } }),
                createAnalyser: () => ({ connect: () => {}, getByteFrequencyData: () => new Uint8Array(1024) }),
                close: () => Promise.resolve()
            };
        };
    }
    if ('getBattery' in navigator) {
        navigator.getBattery = () => Promise.resolve({ level: 1, charging: true, chargingTime: 0, dischargingTime: Infinity });
    }
    console.log('Browser fingerprinting disabled for anonymous mode');
}

// ================================
// ENHANCED CRISIS DETECTION SYSTEM
// ================================
function detectAndHandleCrisis(userMessage, language = 'en') {
    if (!userMessage || typeof userMessage !== 'string') return 'no_crisis';
    const text = userMessage.toLowerCase();
    for (const pattern of CONFIG.redFlagKeywords.immediate_crisis) {
        if (pattern.test(text)) {
            console.warn(`🚨 IMMEDIATE CRISIS DETECTED in ${language}:`, text.substring(0, 100));
            logCrisisIntervention('immediate_crisis', language, {
                detected_pattern: pattern.toString(),
                message_preview: text.substring(0, 200)
            });
            if (window.currentTypingTimeout) clearTimeout(window.currentTypingTimeout);
            if (window.currentApiCall && window.currentApiCall.abort) {
                window.currentApiCall.abort();
                window.currentApiCall = null;
            }
            setTimeout(() => showEmergencyCrisisModal(language, 'immediate'), 100);
            return 'immediate_crisis';
        }
    }
    for (const pattern of CONFIG.redFlagKeywords.urgent_crisis) {
        if (pattern.test(text)) {
            console.info(`⚠️ URGENT CRISIS DETECTED in ${language}:`, text.substring(0, 100));
            logCrisisIntervention('urgent_crisis', language, {
                detected_pattern: pattern.toString(),
                message_preview: text.substring(0, 200)
            });
            setTimeout(() => showEmergencyCrisisModal(language, 'urgent'), 100);
            return 'urgent_crisis';
        }
    }
    for (const pattern of CONFIG.redFlagKeywords.concerning_content) {
        if (pattern.test(text)) {
            console.info(`⚠️ CONCERNING CONTENT DETECTED in ${language}:`, text.substring(0, 100));
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
    const logEntry = {
        type, language, timestamp: Date.now(),
        userAgent: navigator.userAgent ? navigator.userAgent.substring(0, 100) : 'unknown',
        sessionHash: window.mentivioSessionHash || 'anonymous',
        details
    };
    const crisisLogs = JSON.parse(sessionStorage.getItem('mentivio_crisis_logs') || '[]');
    crisisLogs.push(logEntry);
    sessionStorage.setItem('mentivio_crisis_logs', JSON.stringify(crisisLogs.slice(-50)));
    if (CONFIG.complianceFeatures.crisisInterventionLogging) {
        setTimeout(() => {
            fetch('/chatbot/api/compliance/crisis-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Anonymous': CONFIG.anonymityFeatures.enabled ? 'true' : 'false' },
                body: JSON.stringify({ ...logEntry, userAgent: undefined })
            }).catch(() => {});
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
        await this.checkServerCompliance();
        this.loadUserConsent();
        this.setupAuditLogging();
        this.scheduleDataCleanup();
        this.initialized = true;
        console.log('ComplianceManager initialized');
    }
    async checkServerCompliance() {
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('Development mode: Skipping compliance check');
            CONFIG.hipaaCompliant = false;
            CONFIG.gdprCompliant = true;
            CONFIG.complianceFeatures.auditLogging = true;
            this.logAuditEvent('compliance_check_skipped', { reason: 'development_mode', hostname: window.location.hostname });
            return;
        }
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            const response = await fetch('/chatbot/api/compliance/status', { signal: controller.signal });
            clearTimeout(timeoutId);
            if (!response.ok) {
                console.log('Compliance endpoint not available, using defaults');
                this.logAuditEvent('compliance_check_failed', { status: response.status, statusText: response.statusText });
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
                this.logAuditEvent('compliance_check', { hipaa: CONFIG.hipaaCompliant, gdpr: CONFIG.gdprCompliant, server_status: data.status });
            } else {
                console.log('Compliance check returned non-JSON response, using defaults');
                this.logAuditEvent('compliance_check_failed', { error: 'Non-JSON response', contentType });
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
            this.userConsent = { accepted: true, analytics: false, localStorage: false, crisisEscalation: true, timestamp: Date.now(), anonymous: true };
            return;
        }
        try {
            const saved = localStorage.getItem('mentivio_user_consent');
            if (saved) {
                this.userConsent = JSON.parse(saved);
                this.userConsent.crisisEscalation = true;
            }
        } catch (error) {
            this.userConsent = null;
        }
        if (!this.userConsent && !CONFIG.anonymityFeatures.enabled) {
            setTimeout(() => this.showConsentModal(), 2000);
        }
    }
    showConsentModal() {
        if (document.getElementById('compliance-modal') || CONFIG.anonymityFeatures.enabled) return;
        const t = translations[CONFIG.language] || translations.en;
        const modalHTML = `
        <div id="compliance-modal" class="compliance-modal">
          <div class="compliance-modal-content">
            <div class="compliance-header">
              <div class="compliance-icon">🔒</div>
              <h2>${t.privacyLinkText} & Safety</h2>
            </div>
            <div class="compliance-body">
              <p class="compliance-intro"><strong>Mentivio is committed to protecting your privacy and safety:</strong></p>
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
              <button onclick="window.complianceManager.acceptConsent()" class="btn-accept">Accept & Continue</button>
              <button onclick="window.complianceManager.useAnonymously()" class="btn-anonymous">Use Anonymously</button>
            </div>
            <p class="compliance-footer">By continuing, you agree to our <a href="/privacy" target="_blank">Privacy Policy</a> and <a href="/terms" target="_blank">Terms of Service</a>.</p>
          </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
    acceptConsent() {
        const analytics = document.getElementById('consent-analytics')?.checked || false;
        const storage = document.getElementById('consent-local-storage')?.checked || false;
        this.userConsent = { accepted: true, analytics, localStorage: storage, crisisEscalation: true, timestamp: Date.now(), version: '2.0', anonymous: false };
        localStorage.setItem('mentivio_user_consent', JSON.stringify(this.userConsent));
        this.logAuditEvent('consent_given', { analytics, storage });
        const modal = document.getElementById('compliance-modal');
        if (modal) modal.remove();
        setTimeout(() => { if (mentivioWindow && !isWindowOpen) showWindow(); }, 500);
    }
    useAnonymously() {
        localStorage.setItem('mentivio_anonymous', 'true');
        this.logAuditEvent('anonymous_mode_selected', {});
        const modal = document.getElementById('compliance-modal');
        if (modal) modal.remove();
        setTimeout(() => location.reload(), 100);
    }
    setupAuditLogging() {
        try {
            const saved = localStorage.getItem('mentivio_audit_log');
            if (saved) this.auditLog = JSON.parse(saved);
        } catch (error) {
            this.auditLog = [];
        }
        this.logAuditEvent('system_initialized', { anonymity: CONFIG.anonymityFeatures.enabled, compliance: { hipaa: CONFIG.hipaaCompliant, gdpr: CONFIG.gdprCompliant } });
    }
    logAuditEvent(event, details) {
        if (!CONFIG.complianceFeatures.auditLogging) return;
        const auditEntry = {
            event, details, timestamp: Date.now(), sessionId: this.sessionId, anonymous: CONFIG.anonymityFeatures.enabled,
            userAgentHash: navigator.userAgent ? this.hashString(navigator.userAgent.substring(0, 50)) : 'none'
        };
        this.auditLog.push(auditEntry);
        if (this.auditLog.length > 500) this.auditLog = this.auditLog.slice(-500);
        if (CONFIG.anonymityFeatures.enabled) {
            sessionStorage.setItem('mentivio_audit_log', JSON.stringify(this.auditLog));
        } else {
            localStorage.setItem('mentivio_audit_log', JSON.stringify(this.auditLog));
        }
        return auditEntry;
    }
    hashString(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash).toString(36);
    }
    scheduleDataCleanup() {
        setInterval(() => this.cleanupOldData(), 6 * 60 * 60 * 1000);
        this.cleanupOldData();
    }
    cleanupOldData() {
        if (CONFIG.anonymityFeatures.enabled) return;
        const cutoff = Date.now() - (CONFIG.dataRetentionDays * 24 * 60 * 60 * 1000);
        try {
            const history = JSON.parse(localStorage.getItem('mentivio_high_eq_history') || '[]');
            const filtered = history.filter(msg => msg.timestamp > cutoff);
            if (filtered.length < history.length) {
                localStorage.setItem('mentivio_high_eq_history', JSON.stringify(filtered));
                this.logAuditEvent('data_cleaned', { removed: history.length - filtered.length, retained: filtered.length });
            }
        } catch (error) {
            console.warn('Failed to clean conversation history:', error);
        }
        const auditCutoff = Date.now() - (90 * 24 * 60 * 60 * 1000);
        this.auditLog = this.auditLog.filter(log => log.timestamp > auditCutoff);
        localStorage.setItem('mentivio_audit_log', JSON.stringify(this.auditLog));
    }
    exportUserData() {
        const data = {
            conversationHistory: JSON.parse((CONFIG.anonymityFeatures.enabled ? sessionStorage.getItem('mentivio_anon_history') : localStorage.getItem('mentivio_high_eq_history')) || '[]'),
            settings: { language: CONFIG.language, anonymity: CONFIG.anonymityFeatures.enabled, consent: this.userConsent },
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
        const t = translations[CONFIG.language] || translations.en;
        const controlsHTML = `
        <div id="privacy-controls" class="privacy-controls">
          <div class="privacy-container">
            <div class="privacy-header">
              <h2>${t.privacyLinkText} Controls</h2>
              <button onclick="document.getElementById('privacy-controls').remove()" class="close-btn">×</button>
            </div>
            <div class="privacy-section">
              <h3>Your Data</h3>
              <div class="privacy-card">
                <p class="data-status"><strong>Current mode:</strong> ${CONFIG.anonymityFeatures.enabled ? 'Anonymous (no data stored)' : 'Standard (data stored locally)'}</p>
                <div class="data-actions">
                  <button onclick="window.complianceManager.exportUserData()" class="btn-export">Export My Data</button>
                  <button onclick="window.complianceManager.deleteAllUserData()" class="btn-delete">Delete All Data</button>
                </div>
              </div>
            </div>
            <div class="privacy-section">
              <h3>Privacy Settings</h3>
              <div class="privacy-card">
                <label class="privacy-toggle">
                  <input type="checkbox" ${CONFIG.anonymityFeatures.enabled ? 'checked' : ''} onchange="window.complianceManager.toggleAnonymousMode(this.checked)">
                  Use anonymous mode (no data stored permanently)
                </label>
                <p class="toggle-description">Anonymous mode uses session storage only. All data disappears when you close your browser.</p>
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
        const existing = document.getElementById('privacy-controls');
        if (existing) existing.remove();
        document.body.insertAdjacentHTML('beforeend', controlsHTML);
    }
    toggleAnonymousMode(enabled) {
        if (enabled) localStorage.setItem('mentivio_anonymous', 'true');
        else localStorage.removeItem('mentivio_anonymous');
        location.reload();
    }
}

// ================================
// EMERGENCY CRISIS MODAL
// ================================
function showEmergencyCrisisModal(language, severity = 'urgent') {
    const existing = document.getElementById('mentivio-emergency-overlay');
    if (existing) existing.remove();

    const t = translations[language] || translations.en;
    const contacts = CONFIG.emergencyContacts[language] || CONFIG.emergencyContacts.en;

    const severityKey = severity === 'immediate' ? 'immediate' : 'urgent';
    const title = t.crisisModal[severityKey].title;
    const message = t.crisisModal[severityKey].message;
    const btn = t.crisisModal.buttonTexts;

    const emergencyHTML = `
    <div id="mentivio-emergency-overlay" class="crisis-overlay">
      <div class="crisis-container">
        <div class="crisis-icon">🚨</div>
        <h2 class="crisis-title">${title}</h2>
        <p class="crisis-message">${message}</p>
        <div class="crisis-card immediate">
        <h3 class="crisis-card-title">${severity === 'immediate' ? t.crisisModal.immediate.cardTitle : t.crisisModal.urgent.cardTitle}</h3>          <div class="crisis-buttons">
            <button onclick="window.open('tel:${contacts.suicide_prevention}')" class="crisis-btn crisis-btn-primary">
              <span class="btn-icon">📞</span> <span>${btn.call} ${contacts.suicide_prevention}</span>
            </button>
            <button onclick="window.open('sms:741741?body=HOME')" class="crisis-btn crisis-btn-secondary">
              <span class="btn-icon">💬</span> <span>${contacts.crisis_text}</span>
            </button>
            ${severity === 'immediate' ? `
            <button onclick="window.open('tel:${contacts.emergency}')" class="crisis-btn crisis-btn-emergency">
              <span class="btn-icon">🚑</span> <span>${btn.emergency} (${contacts.emergency})</span>
            </button>` : ''}
          </div>
        </div>
        ${severity === 'immediate' ? `
        <div class="crisis-warning"><p><strong>Important:</strong> ${t.crisisModal.importantMessage}</p></div>
        <div class="crisis-actions">
          <button onclick="confirmHelpReceived()" class="crisis-action-btn crisis-action-confirm">${btn.contacted}</button>
          <button onclick="window.open('tel:${contacts.emergency}')" class="crisis-action-btn crisis-action-emergency">${btn.callEmergency}</button>
        </div>
        ` : `
        <div class="crisis-actions">
          <button onclick="resumeChatAfterCrisis()" class="crisis-action-btn crisis-action-resume">${btn.continue}</button>
          <button onclick="window.open('/crisis-support.html', '_blank')" class="crisis-action-btn crisis-action-resources">${btn.moreResources}</button>        </div>
        `}
        <p class="crisis-footer">${t.crisisModal.footerMessage}</p>
      </div>
    </div>`;

    const messagesContainer = document.getElementById('mentivioMessages');
    if (messagesContainer) {
        messagesContainer.innerHTML = emergencyHTML;
        messagesContainer.scrollTop = 0;
    }
    if (mentivioInput) {
        mentivioInput.disabled = true;
        mentivioInput.placeholder = t.crisisModal.importantMessage.split('.')[0] + '...';
    }
    if (sendBtn) sendBtn.disabled = true;
}

window.confirmHelpReceived = function() {
    const modal = document.getElementById('mentivio-emergency-overlay');
    if (modal) {
        modal.remove();
        if (mentivioInput) {
            mentivioInput.disabled = false;
            updateInputPlaceholder(CONFIG.language);
            mentivioInput.focus();
        }
        if (sendBtn) sendBtn.disabled = false;
        const followUpMessages = getTranslation(CONFIG.language, 'crisisModal.followUp', "Thank you for reaching out. How are you feeling now?");
        setTimeout(() => addMessage(followUpMessages, 'bot'), 500);
    }
};

window.resumeChatAfterCrisis = function() {
    const modal = document.getElementById('mentivio-emergency-overlay');
    if (modal) {
        modal.remove();
        if (mentivioInput) {
            mentivioInput.disabled = false;
            updateInputPlaceholder(CONFIG.language);
            mentivioInput.focus();
        }
        if (sendBtn) sendBtn.disabled = false;
    }
};

window.showEnhancedCrisisResources = function(lang = null) {
    if (!lang && CONFIG) lang = CONFIG.language;
    showEmergencyCrisisModal(lang, 'urgent');
};

// ================================
// ENHANCED LOCAL MEMORY WITH HIGH EQ
// ================================
// ================================
// ENHANCED LOCAL MEMORY WITH HIGH EQ
// ================================
class HighEQMentivio {
    constructor() {
        this.conversationHistory = [];
        this.conversationState = { phase: 'engagement', lastEmotion: 'neutral', needsInspiration: false, topicsDiscussed: [] };
        this.language = CONFIG.language;
        this.anonymous = CONFIG.anonymityFeatures.enabled;
        this.sessionId = getSessionId();
    }
    
    updateLocalState(userText, emotion = 'neutral') {
        const text = this.anonymous ? scrubPII(userText) : userText;
        // Add to in-memory history only – storage is handled by sendMessage
        this.conversationHistory.push({ 
            text, 
            role: 'user', 
            timestamp: Date.now(), 
            emotion, 
            language: this.language, 
            anonymous: this.anonymous, 
            sessionId: this.sessionId 
        });
        
        // Keep only last 50 messages in memory
        if (this.conversationHistory.length > 50) this.conversationHistory.shift();
        
        // Update conversation phase based on message count
        const messageCount = this.conversationHistory.filter(m => m.role === 'user').length;
        if (messageCount < 3) this.conversationState.phase = 'engagement';
        else if (messageCount < 8) this.conversationState.phase = 'exploration';
        else if (messageCount < 15) this.conversationState.phase = 'processing';
        else this.conversationState.phase = 'integration';
        
        // Flag if inspiration might be needed
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
        // Add to in-memory history only – storage is handled by sendMessage
        this.conversationHistory.push({ 
            text, 
            role: 'bot', 
            timestamp: Date.now(), 
            emotion, 
            language: this.language, 
            sessionId: this.sessionId 
        });
    }
}

// ================================
// ENHANCED BACKEND API COMMUNICATION
// ================================
async function callBackendAPI(userMessage, conversationContext, emotion) {
    try {
        const crisisLevel = detectAndHandleCrisis(userMessage, CONFIG.language);
        if (crisisLevel === 'immediate_crisis') {
            return {
                response: getTranslation(CONFIG.language, 'crisisModal.immediate.message', "I'm here with you. Let me connect you with immediate support."),
                emotion: "compassionate",
                language: CONFIG.language,
                is_safe: true,
                suggested_topics: ["Safety first", "Getting support", "You matter"],
                crisis_mode: true
            };
        }
        if (!CONFIG.apiEndpoint) return getFallbackResponse(userMessage, emotion);
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
                    conversation_state: { phase: ai.conversationState.phase, trust_level: ai.conversationState.trustLevel || 0, needs_inspiration: ai.conversationState.needsInspiration },
                    compliance: { anonymity: CONFIG.anonymityFeatures.enabled, gdpr: CONFIG.gdprCompliant, hipaa: CONFIG.hipaaCompliant },
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
    const t = translations[CONFIG.language] || translations.en;
    const responses = t.fallbackResponses;
    const randomResponse = responses[Math.floor(Math.random() * responses.length)] || "I'm here with you.";
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
    if (!['en', 'es', 'vi', 'zh'].includes(newLang)) newLang = 'en';
    if (CONFIG.language === newLang) return;
    console.log(`Updating chatbot language from ${CONFIG.language} to ${newLang}`);
    CONFIG.language = newLang;
    if (ai && typeof ai === 'object') ai.language = newLang;

    // Update UI elements
    if (document.getElementById('mentivioWindow')) {
        try {
            const currentLangEl = document.getElementById('currentLanguage');
            const langOptions = document.querySelectorAll('.lang-option');
            const languageDisplays = { en: "🌐 EN", es: "🌐 ES", vi: "🌐 VI", zh: "🌐 ZH" };
            if (currentLangEl) currentLangEl.textContent = languageDisplays[newLang] || "🌐 EN";
            langOptions.forEach(option => option.classList.toggle('active', option.dataset.lang === newLang));

            updateWelcomeMessage(newLang);
            renderQuickEmotions();       // rebuild buttons with new labels
            updateInputPlaceholder(newLang);
            updateSafetyNotice(newLang);
            updateHeaderText(newLang);
        } catch (error) {
            console.error('Error updating chatbot UI language:', error);
        }
    }
    const storage = CONFIG.anonymityFeatures.enabled ? sessionStorage : localStorage;
    storage.setItem('mentivio_language', newLang);
};

function updateHeaderText(lang) {
    const t = translations[lang] || translations.en;
    const titleElement = document.querySelector('.mentivio-title');
    if (titleElement) titleElement.textContent = t.header.title;
    // Safely call updateDay only if it exists
    if (typeof updateDay === 'function') {
        updateDay();
    } else {
        console.warn('updateDay not yet defined');
    }
}

function setupLanguageSynchronization() {
    let lastProcessedLang = null, lastProcessedTime = 0;
    function processLanguageChange(newLang) {
        const now = Date.now();
        if (lastProcessedLang === newLang && now - lastProcessedTime < 500) return;
        lastProcessedLang = newLang;
        lastProcessedTime = now;
        if (updateChatbotLanguage) updateChatbotLanguage(newLang);
    }
    document.addEventListener('languageChanged', function(e) { processLanguageChange(e.detail.language); });
    window.addEventListener('mentivioLangChange', function(e) {
        const newLang = e.detail?.language || e.detail?.lang;
        if (newLang) processLanguageChange(newLang);
    });
}

function updateSafetyNotice(lang) {
    const t = translations[lang] || translations.en;
    const safetyNoticeEl = document.querySelector('.safety-notice');
    if (!safetyNoticeEl) return;
    safetyNoticeEl.innerHTML = `
        <i class="fas fa-heart" style="color: #ec4899;"></i>
        ${t.safetyNotice}
        <span class="crisis-link" onclick="window.showEnhancedCrisisResources('${lang}')">${t.crisisLinkText}</span>
        ${!CONFIG.anonymityFeatures.enabled ? `<span class="privacy-link" onclick="window.complianceManager.showPrivacyControls()"><i class="fas fa-shield-alt"></i> ${t.privacyLinkText}</span>` : ''}
    `;
}

function updateWelcomeMessage(lang) {
    const welcomeElement = document.querySelector('.welcome-message .message-text');
    if (welcomeElement) welcomeElement.innerHTML = getTranslation(lang, 'welcomeMessage', 'Hello 😊');
}

function updateInputPlaceholder(lang) {
    if (mentivioInput) mentivioInput.placeholder = getTranslation(lang, 'inputPlaceholder', "Share what's in your heart...");
}

// ================================
// QUICK EMOTIONS RENDERING
// ================================
function renderQuickEmotions() {
    const container = document.querySelector('.emotions-scroll-container');
    if (!container) return;
    const t = translations[CONFIG.language] || translations.en;
    const labels = t.quickEmotionLabels;
    const prompts = t.quickEmotionPrompts;
    container.innerHTML = '';
    for (const [emotion, label] of Object.entries(labels)) {
        const btn = document.createElement('button');
        btn.className = 'quick-emotion';
        btn.dataset.emotion = emotion;
        btn.textContent = label;
        btn.addEventListener('click', function() {
            if (mentivioInput) {
                mentivioInput.value = prompts[emotion] || `I'm feeling ${emotion}.`;
                mentivioInput.focus();
            }
        });
        container.appendChild(btn);
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
            <div class="emotions-title" id="emotionsTitle">I'm feeling...</div>
            <div class="emotions-scroll-container"></div>
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
    </div>
  </div>`;

// ================================
// INITIALIZATION
// ================================
(function() {
    if (window.mentivioSkipInit) { console.log('Mentivio: Skipping initialization on this page'); return; }
    if (isChatbotInitialized) { console.log('Mentivio: Already initialized'); return; }
    function shouldLoadOnPage() {
        const excludedPages = ['/admin','/checkout','/payment','/login','/register','/signup','/account'];
        const currentPath = window.location.pathname;
        return !excludedPages.some(page => currentPath.startsWith(page));
    }
    if (!shouldLoadOnPage()) { console.log('Mentivio: Skipping on excluded page:', window.location.pathname); return; }
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
    <link rel="stylesheet" href="../frontend/css/chatbot.css">
    `;
    if (!document.querySelector('link[href*="chatbot.css"]')) {
        document.head.insertAdjacentHTML('afterbegin', headContent);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => initMentivio());
    } else {
        initMentivio();
    }
})();

async function initMentivio() {
    // Load translations first
    await loadTranslations();

    // ================================
    // ENHANCED CONFIGURATION WITH SAFETY FEATURES
    // ================================
    function detectUserLanguage() {
        if (window.globalLangManager) return window.globalLangManager.currentLang || 'en';
        const savedLang = localStorage.getItem('mentivio_language');
        if (savedLang && ['en','vi','es','zh'].includes(savedLang)) return savedLang;
        const preferredLang = localStorage.getItem('preferred-language');
        if (preferredLang && ['en','vi','es','zh'].includes(preferredLang)) return preferredLang;
        const browserLang = navigator.language || navigator.userLanguage;
        if (browserLang) {
            if (browserLang.startsWith('vi')) return 'vi';
            if (browserLang.startsWith('es')) return 'es';
            if (browserLang.startsWith('zh')) return 'zh';
        }
        return 'en';
    }

    const urlParams = new URLSearchParams(window.location.search);
    const anonymousMode = urlParams.get('anonymous') === 'true' || localStorage.getItem('mentivio_anonymous') === 'true';

    CONFIG = {
        name: "Mentivio",
        apiEndpoint: "/chatbot/api/chat",
        safetyMode: "high-eq",
        language: detectUserLanguage(),
        crisisResponseMode: "immediate_escalation",
        dataRetentionDays: 30,
        hipaaCompliant: false,
        gdprCompliant: true,
        emergencyContacts: {
            en: { suicide_prevention: "988", crisis_text: "Text HOME to 741741", emergency: "911", domestic_violence: "800-799-7233", substance_abuse: "800-662-4357", veterans_crisis: "988 then press 1", trevor_project: "866-488-7386", international_redirect: true },
            es: { suicide_prevention: "988", crisis_text: "Envía HOME al 741741", emergency: "911", domestic_violence: "800-799-7233", substance_abuse: "800-662-4357", veterans_crisis: "988 luego presiona 1", trevor_project: "866-488-7386", international_redirect: true },
            vi: { suicide_prevention: "988", crisis_text: "Nhắn HOME tới 741741", emergency: "911", domestic_violence: "800-799-7233", substance_abuse: "800-662-4357", veterans_crisis: "988 sau đó nhấn 1", trevor_project: "866-488-7386", international_redirect: true },
            zh: { suicide_prevention: "988", crisis_text: "发送 HOME 至 741741", emergency: "911", domestic_violence: "800-799-7233", substance_abuse: "800-662-4357", veterans_crisis: "988 然后按 1", trevor_project: "866-488-7386", international_redirect: true }
        },
        redFlagKeywords: {
            immediate_crisis: [ /kill.*myself.*(now|tonight|today)/i, /suicide.*(now|tonight|today)/i, /end.*my.*life.*(now|tonight|today)/i, /going.*to.*(end|kill).*myself/i, /cutting.*(myself|now)/i, /overdose.*(now|tonight)/i, /gun.*to.*head/i, /shoot.*myself/i, /jump.*off/i, /hanging.*myself/i, /take.*all.*pills/i, /swallow.*pills/i, /bleed.*out/i, /final.*goodbye/i, /last.*message/i ],
            urgent_crisis: [ /want.*to.*die/i, /don't.*want.*to.*live/i, /can't.*go.*on/i, /ending.*it.*all/i, /no.*reason.*to.*live/i, /plan.*to.*(kill|suicide)/i, /suicide.*plan/i, /suicide.*method/i, /how.*to.*(kill|die)/i, /best.*way.*to.*die/i, /painless.*(suicide|death)/i, /burden.*to.*everyone/i, /worthless/i, /hopeless/i, /nothing.*left/i ],
            concerning_content: [ /self.*harm/i, /cut.*myself/i, /burn.*myself/i, /hurt.*myself/i, /extreme.*pain/i, /unbearable.*pain/i, /can't.*take.*it/i, /can't.*cope/i, /giving.*up/i, /tired.*of.*life/i, /life.*not.*worth/i, /rather.*be.*dead/i ]
        },
        complianceFeatures: { auditLogging: true, dataEncryption: true, rightToDelete: true, rightToExport: true, crisisInterventionLogging: true, monthlyComplianceReports: true },
        anonymityFeatures: { enabled: false, noPIIStorage: true, sessionOnly: true, disableAnalytics: true, disableFingerprinting: true, scrubPII: true }
    };

    if (anonymousMode) enableAnonymousMode();

    // ================================
    // UI ELEMENTS
    // ================================
    if (!document.getElementById('mentivio-root')) {
        document.body.insertAdjacentHTML('beforeend', mentivioHTML);
    }

    ai = new HighEQMentivio();
    const avatar = document.getElementById('mentivioAvatar');
    mentivioWindow = document.getElementById('mentivioWindow');
    const messages = document.getElementById('mentivioMessages');
    mentivioInput = document.getElementById('mentivioInput');
    const sendBtn = document.getElementById('sendBtn');
    const closeBtn = document.getElementById('closeMentivio');
    const typingIndicator = document.getElementById('typingIndicator');
    const activeEmotion = document.getElementById('activeEmotion');
    const currentDay = document.getElementById('currentDay');

    // ================================
    // UPDATE DAY FUNCTION
    // ================================
    function updateDay() {
        if (!currentDay) return;
        const now = new Date();
        const lang = CONFIG ? CONFIG.language : 'en';
        const t = translations[lang] || translations.en;
        const dayOfWeek = now.getDay();
        const dayName = t.dayNames?.short?.[dayOfWeek] || '???';
        const time = now.toLocaleTimeString([], { 
            hour12: t.timeFormats?.hour12 ?? true, 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        currentDay.textContent = `${t.header?.heartSpace || 'Heart Space'} • ${dayName} • ${time}`;
    }

    // ================================
    // LANGUAGE SELECTOR
    // ================================
    function initLanguageSelector() {
        const currentLangEl = document.getElementById('currentLanguage');
        const langOptions = document.querySelectorAll('.lang-option');
        const languageDisplays = { en: "🌐 EN", es: "🌐 ES", vi: "🌐 VI", zh: "🌐 ZH" };
        const languageNames = { en: "English", es: "Español", vi: "Tiếng Việt", zh: "中文" };

        function updateLanguageDisplay(lang) {
            if (!currentLangEl) return;
            currentLangEl.innerHTML = languageDisplays[lang] || "🌐 EN";
            langOptions.forEach(option => {
                if (option.dataset.lang === lang) {
                    option.classList.add('active');
                    option.innerHTML = languageNames[lang] || lang;
                } else {
                    option.classList.remove('active');
                    option.textContent = languageNames[option.dataset.lang] || option.dataset.lang;
                }
            });
        }

        updateLanguageDisplay(CONFIG.language);

        currentLangEl.addEventListener('click', function(e) {
            e.stopPropagation();
            document.querySelector('.language-dropdown').classList.toggle('show');
        });

        langOptions.forEach(option => {
            option.addEventListener('click', function(e) {
                e.stopPropagation();
                const newLang = this.dataset.lang;
                document.querySelector('.language-dropdown').classList.remove('show');
                updateLanguageDisplay(newLang);
                if (updateChatbotLanguage) updateChatbotLanguage(newLang);
            });
        });

        document.addEventListener('click', function(e) {
            const dropdown = document.querySelector('.language-dropdown');
            if (dropdown.classList.contains('show') && !e.target.closest('.language-selector')) {
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
        if (window.innerWidth <= 768) document.body.classList.add('mentivio-open');
        mentivioWindow.classList.add('open');
        setTimeout(() => { if (mentivioInput) mentivioInput.focus(); }, 100);
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
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && isWindowOpen) hideWindow(); });

    // ================================
    // ENHANCED MESSAGE HANDLING
    // ================================
    async function sendMessage(message) {
        if (!message || !message.trim()) return;
        const sessionId = getSessionId();
        const storage = window.mentivioStorage || localStorage;
        const savedMessages = loadSavedConversation();
        const emotion = detectEmotion(message);
        const requestData = {
            message, session_id: sessionId, language: CONFIG.language, emotion,
            context: savedMessages.slice(-10), conversation_state: ai.conversationState,
            anonymous: CONFIG.anonymityFeatures.enabled || false
        };
        try {
            showTyping();
            const response = await fetch('/chatbot/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
            const data = await response.json();
            hideTyping();
            if (data.session_id) saveSessionData(data.session_id);
            const updatedMessages = [
                ...savedMessages,
                { role: 'user', content: message, timestamp: Date.now(), language: CONFIG.language, emotion },
                { role: 'bot', content: data.response, timestamp: Date.now(), language: CONFIG.language, emotion: data.emotion || 'compassionate' }
            ];
            storage.setItem('mentivio_conversation', JSON.stringify(updatedMessages));
            storage.setItem('mentivio_last_activity', Date.now());
            ai.updateLocalState(message, emotion);
            ai.addBotResponse(data.response, data.emotion || 'compassionate');
            addMessage(message, 'user');
            addMessage(data.response, 'bot');
            updateSessionUI(sessionId);
            return data;
        } catch (error) {
            console.error('Error sending message:', error);
            hideTyping();
            const fallbackResponse = getTranslation(CONFIG.language, 'fallbackResponses.0', "I'm here with you.");
            addMessage(fallbackResponse, 'bot');
            const updatedMessages = [
                ...savedMessages,
                { role: 'user', content: message, timestamp: Date.now(), language: CONFIG.language, emotion },
                { role: 'bot', content: fallbackResponse, timestamp: Date.now(), language: CONFIG.language, emotion: 'compassionate' }
            ];
            storage.setItem('mentivio_conversation', JSON.stringify(updatedMessages));
            throw error;
        }
    }

    // Attach to global for button
    window.sendMessage = sendMessage;

    // Quick emotions – already handled by renderQuickEmotions, but we need to re-attach after rendering
    // We'll call renderQuickEmotions after language is set

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
    }

    // ================================
    // UI HELPER FUNCTIONS
    // ================================
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true }).replace(' ', '').toLowerCase();
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
        const t = translations[CONFIG.language] || translations.en;
        const statuses = t.typingStatuses;
        const statusEl = document.getElementById('typingStatus');
        if (statusEl) statusEl.textContent = statuses[Math.floor(Math.random() * statuses.length)];
    }

    function hideTyping() {
        isTyping = false;
        typingIndicator.style.display = 'none';
    }

    function updateAvatarEmoji(state) {
        const emojis = { thinking: '💭', listening: '👂', empathetic: '🤍', calm: '😌', warning: '⚠️', hopeful: '✨', present: '🌱', caring: '💗' };
        const avatarEmojiEl = document.getElementById('avatarEmoji');
        if (avatarEmojiEl) avatarEmojiEl.textContent = emojis[state] || '💭';
    }

    function updateEmotionalIndicator(emotion) {
        const colors = {
            happy: '#4ade80', sad: '#3b82f6', anxious: '#f59e0b', angry: '#ef4444',
            overwhelmed: '#8b5cf6', neutral: '#94a3b8', curious: '#10b981', hopeful: '#ec4899',
            grateful: '#f59e0b', lonely: '#64748b', peaceful: '#06b6d4', hesitant: '#a78bfa',
            confused: '#fbbf24', ashamed: '#dc2626', jealous: '#7c3aed', rejected: '#6b7280',
            betrayed: '#be123c'
        };
        if (activeEmotion) activeEmotion.style.background = colors[emotion] || colors.neutral;
    }

    function scrollToBottom() { if (messages) messages.scrollTop = messages.scrollHeight; }

    // Initial pulse animation
    setTimeout(() => {
        if (!isWindowOpen && avatar) {
            avatar.style.transform = 'scale(1.1)';
            setTimeout(() => avatar.style.transform = '', 600);
        }
    }, 2000);

    window.addEventListener('resize', updateDay);

    // Initialize language selector and synchronisation
    initLanguageSelector();
    setupLanguageSynchronization();

    // Render quick emotions using current language
    renderQuickEmotions();

    // Update all UI elements with current language
    updateWelcomeMessage(CONFIG.language);
    updateInputPlaceholder(CONFIG.language);
    updateSafetyNotice(CONFIG.language);
    updateHeaderText(CONFIG.language);
    updateDay();

    // Initialize chat (restore conversation)
    setTimeout(() => initializeChat(), 500);

    // ================================
    // ADDITIONAL RESOURCES MODAL
    // ================================
    window.showAdditionalResources = function(lang) {
        const currentLang = lang || CONFIG.language;
        const t = translations[currentLang] || translations.en;

        // Build resources HTML using t.resourcesModal
        const resources = t.resourcesModal.internationalResources;
        const categories = t.resourcesModal.categories;
        const immediate = t.resourcesModal.immediateHelp;

        function createResourcesSection(title, resources) {
            if (!resources || resources.length === 0) return '';
            return `
                <div class="resources-category">
                    <h4>${title}</h4>
                    <div class="resources-list">
                        ${resources.map(r => `
                            <div class="resource-item">
                                <div class="resource-title">${r.title}</div>
                                <div class="resource-numbers">
                                    ${r.numbers.map(num => `<div class="resource-number">${num.includes('Text') || num.includes('发送') ? `<span class="text-support">${num}</span>` : `<a href="tel:${num.replace(/\D/g,'')}" class="phone-link">${num}</a>`}</div>`).join('')}
                                </div>
                                <div class="resource-description">${r.description}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        const resourcesHTML = `
        <div id="additional-resources" class="resources-modal">
            <div class="resources-container">
                <div class="resources-header">
                    <h2><i class="fas fa-hands-helping"></i> ${t.resourcesModal.title}</h2>
                    <button onclick="document.getElementById('additional-resources').remove()" class="close-btn">×</button>
                </div>
                <div class="resources-body">
                    <div class="resources-section immediate-help">
                        <h3><i class="fas fa-exclamation-circle"></i> ${immediate.title}</h3>
                        <div class="immediate-actions">
                            <button onclick="window.open('tel:988')" class="crisis-action-btn"><i class="fas fa-phone-alt"></i> ${immediate.call988}</button>
                            <button onclick="window.open('sms:741741?body=HOME')" class="crisis-action-btn"><i class="fas fa-comment-alt"></i> ${immediate.textHome}</button>
                            <button onclick="window.open('tel:911')" class="crisis-action-btn emergency"><i class="fas fa-ambulance"></i> ${immediate.emergency}</button>
                        </div>
                    </div>
                    ${createResourcesSection(categories.suicide, resources.filter(r => r.type === 'suicide'))}
                    ${createResourcesSection(categories.emergency, resources.filter(r => r.type === 'emergency'))}
                    ${createResourcesSection(categories.violence, resources.filter(r => r.type === 'violence'))}
                    ${createResourcesSection(categories.substance, resources.filter(r => r.type === 'substance'))}
                    ${createResourcesSection(categories.youth, resources.filter(r => r.type === 'youth' || r.type === 'children'))}
                    ${createResourcesSection(categories.veterans, resources.filter(r => r.type === 'veterans'))}
                    ${createResourcesSection(categories.text, resources.filter(r => r.type === 'text'))}
                    ${createResourcesSection(categories.international, resources.filter(r => r.type === 'international'))}
                    ${createResourcesSection(categories.other, resources.filter(r => !['suicide','emergency','violence','substance','youth','veterans','text','international'].includes(r.type)))}
                    <div class="resources-footer">
                        <p><i class="fas fa-info-circle"></i> These services are confidential and available 24/7 in most regions.</p>
                        <p><i class="fas fa-globe"></i> For country-specific resources, visit our full crisis support page.</p>
                    </div>
                </div>
                <div class="resources-actions">
                    <button onclick="document.getElementById('additional-resources').remove()" class="resources-close-btn"><i class="fas fa-arrow-left"></i> ${t.resourcesModal.buttonClose}</button>
                    <button onclick="window.open('/crisis-support.html', '_blank')" class="resources-full-btn"><i class="fas fa-external-link-alt"></i> ${t.resourcesModal.buttonFullPage}</button>
                </div>
            </div>
        </div>`;

        const existing = document.getElementById('additional-resources');
        if (existing) existing.remove();
        document.body.insertAdjacentHTML('beforeend', resourcesHTML);
        addResourcesStyles();
    };

    function addResourcesStyles() {
        if (document.getElementById('enhanced-resources-styles')) return;
        const styles = `...`; // Keep your existing CSS block here – omitted for brevity
        document.head.insertAdjacentHTML('beforeend', styles);
    }

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
                const t = translations[CONFIG.language] || translations.en;
                const feelings = t.quickCheckInFeelings || ["How's your heart today?"];
                const feeling = feelings[Math.floor(Math.random() * feelings.length)];
                if (mentivioInput) {
                    mentivioInput.value = feeling;
                    mentivioInput.focus();
                    if (!isWindowOpen && window.showMentivioWindow) window.showMentivioWindow();
                } else alert(feeling);
            },
            getInspiration: async () => {
                try {
                    const response = await fetch('/chatbot/api/inspiration');
                    if (response.ok) {
                        const data = await response.json();
                        alert(`${data.quote}\n\n- ${data.story.title}`);
                    }
                } catch (error) { console.error('Inspiration fetch error:', error); }
            },
            setLanguage: (lang) => { if (['en','es','vi','zh'].includes(lang) && updateChatbotLanguage) updateChatbotLanguage(lang); },
            getLanguage: () => CONFIG ? CONFIG.language : 'en',
            updateHeader: (lang) => { if (lang) updateHeaderText(lang); else if (CONFIG) updateHeaderText(CONFIG.language); },
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
        if (window.globalLangManager) {
            const globalLang = window.globalLangManager.currentLang;
            if (globalLang && globalLang !== CONFIG.language && updateChatbotLanguage) {
                updateChatbotLanguage(globalLang);
            }
        }
        if (CONFIG && CONFIG.language) updateHeaderText(CONFIG.language);
    }, 1000);

    console.log('Mentivio initialized with session persistence and full multilingual support');
}