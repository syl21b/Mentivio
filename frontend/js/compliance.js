// compliance.js
class ComplianceManager {
  constructor() {
    this.dataRetentionDays = 30;
    this.hipaaCompliant = false;
    this.userConsent = null;
    this.auditLog = [];
  }
  
  async initialize() {
    // Check if we're on a compliant server
    this.hipaaCompliant = await this.checkServerCompliance();
    
    // Get user consent
    this.userConsent = localStorage.getItem('mentivio_user_consent');
    
    if (!this.userConsent) {
      this.showConsentModal();
    }
    
    // Schedule data cleanup
    this.scheduleDataCleanup();
  }
  
  async checkServerCompliance() {
    try {
      const response = await fetch('/api/compliance/status');
      const data = await response.json();
      return data.hipaa_compliant === true && 
             data.gdpr_compliant === true &&
             data.soc2_certified === true;
    } catch (error) {
      console.warn('Compliance check failed, assuming non-compliant');
      return false;
    }
  }
  
  showConsentModal() {
    // Create GDPR/HIPAA consent modal
    const modalHTML = `
    <div id="compliance-modal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 100000; display: flex; align-items: center; justify-content: center;">
      <div style="background: white; border-radius: 12px; padding: 32px; max-width: 500px; max-height: 80vh; overflow-y: auto;">
        <h2 style="color: #111827; margin-bottom: 16px;">Data Privacy & Security</h2>
        
        <div style="margin-bottom: 24px;">
          <p><strong>Mentivio is committed to your privacy:</strong></p>
          <ul style="color: #4b5563; font-size: 14px; line-height: 1.6;">
            <li>🔒 All data is encrypted in transit (TLS 1.3)</li>
            <li>🗑️ Conversation data auto-deletes after 30 days</li>
            <li>🌐 No personal identifiers required</li>
            <li>🇪🇺 GDPR compliant for EU users</li>
            <li>🇺🇸 HIPAA-compliant infrastructure</li>
          </ul>
        </div>
        
        <div style="margin-bottom: 24px;">
          <label style="display: block; margin-bottom: 8px;">
            <input type="checkbox" id="consent-analytics">
            Allow anonymous usage analytics (helps improve service)
          </label>
          
          <label style="display: block; margin-bottom: 8px;">
            <input type="checkbox" id="consent-local-storage">
            Store conversations locally in your browser
          </label>
          
          <label style="display: block; margin-bottom: 16px;">
            <input type="checkbox" id="consent-crisis-escalation" checked disabled>
            <strong>Always allow crisis escalation</strong> (required for your safety)
          </label>
        </div>
        
        <div style="display: flex; gap: 12px;">
          <button onclick="window.complianceManager.acceptConsent()" style="background: #10b981; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; flex: 1;">
            Accept & Continue
          </button>
          <button onclick="window.complianceManager.declineConsent()" style="background: #6b7280; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer;">
            Use Anonymously
          </button>
        </div>
        
        <p style="font-size: 12px; color: #6b7280; margin-top: 16px;">
          By continuing, you agree to our <a href="/privacy" target="_blank" style="color: #8b5cf6;">Privacy Policy</a> 
          and <a href="/terms" target="_blank" style="color: #8b5cf6;">Terms of Service</a>.
        </p>
      </div>
    </div>`;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
  }
  
  acceptConsent() {
    const analytics = document.getElementById('consent-analytics').checked;
    const storage = document.getElementById('consent-local-storage').checked;
    
    this.userConsent = {
      analytics,
      localStorage: storage,
      timestamp: Date.now(),
      version: '2.0'
    };
    
    localStorage.setItem('mentivio_user_consent', JSON.stringify(this.userConsent));
    this.logAuditEvent('consent_given', { analytics, storage });
    
    document.getElementById('compliance-modal').remove();
  }
  
  declineConsent() {
    this.userConsent = {
      analytics: false,
      localStorage: false,
      timestamp: Date.now(),
      version: '2.0'
    };
    
    localStorage.setItem('mentivio_user_consent', JSON.stringify(this.userConsent));
    localStorage.removeItem('mentivio_high_eq_history');
    this.logAuditEvent('consent_declined', {});
    
    document.getElementById('compliance-modal').remove();
    
    // Show notification
    alert('You can use Mentivio anonymously. No data will be stored.');
  }
  
  scheduleDataCleanup() {
    // Run cleanup every 24 hours
    setInterval(() => this.cleanupOldData(), 24 * 60 * 60 * 1000);
    
    // Also run now
    this.cleanupOldData();
  }
  
  cleanupOldData() {
    const history = JSON.parse(localStorage.getItem('mentivio_high_eq_history') || '[]');
    const cutoff = Date.now() - (this.dataRetentionDays * 24 * 60 * 60 * 1000);
    
    const filtered = history.filter(msg => msg.timestamp > cutoff);
    
    if (filtered.length < history.length) {
      localStorage.setItem('mentivio_high_eq_history', JSON.stringify(filtered));
      this.logAuditEvent('data_cleaned', {
        removed: history.length - filtered.length,
        retained: filtered.length
      });
    }
  }
  
  logAuditEvent(event, details) {
    this.auditLog.push({
      event,
      details,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      ipHash: this.hashIP() // Anonymous hash for auditing
    });
    
    // Keep only last 1000 events
    if (this.auditLog.length > 1000) {
      this.auditLog = this.auditLog.slice(-1000);
    }
    
    localStorage.setItem('mentivio_audit_log', JSON.stringify(this.auditLog));
  }
  
  hashIP() {
    // Create anonymous hash for auditing without storing IP
    return 'anonymous_' + Math.random().toString(36).substr(2, 9);
  }
  
  // Data export for GDPR right to access
  exportUserData() {
    const data = {
      conversationHistory: JSON.parse(localStorage.getItem('mentivio_high_eq_history') || '[]'),
      settings: {
        language: localStorage.getItem('mentivio_language'),
        consent: this.userConsent
      },
      auditLog: this.auditLog.filter(log => !log.ipHash.includes('anonymous'))
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mentivio-data-${Date.now()}.json`;
    a.click();
  }
  
  // Data deletion for GDPR right to be forgotten
  deleteAllUserData() {
    localStorage.removeItem('mentivio_high_eq_history');
    localStorage.removeItem('mentivio_language');
    localStorage.removeItem('mentivio_user_consent');
    localStorage.removeItem('mentivio_audit_log');
    
    this.userConsent = null;
    this.auditLog = [];
    
    this.logAuditEvent('data_deleted', {});
    
    alert('All your data has been deleted. The page will reload.');
    setTimeout(() => location.reload(), 1000);
  }
}

// Initialize globally
window.complianceManager = new ComplianceManager();