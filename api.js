const API_BASE_URL = 'http://172.20.10.13:8000';  // IP du Raspberry Pi

class MailBoxAPI {
    // ==================== AUTHENTIFICATION ====================
    
    static async login(username, password) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erreur de connexion');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erreur login:', error);
            return { success: false, error: error.message };
        }
    }

    static async register(userData) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erreur d\'inscription');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erreur register:', error);
            return { success: false, error: error.message };
        }
    }

    // ==================== COURRIERS ====================
    
    static async getMailStatus() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/mail-status`);
            
            if (!response.ok) {
                throw new Error('Erreur de statut');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erreur mail-status:', error);
            return { success: false, has_mail: false, error: true };
        }
    }

    static async getMailHistory(limit = 10) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/mail-history?limit=${limit}`);
            
            if (!response.ok) {
                throw new Error('Erreur d\'historique');
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Erreur mail-history:', error);
            return { success: false, data: [] };
        }
    }

    static async searchMail(filters) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/search-mail`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(filters)
            });
            
            if (!response.ok) {
                throw new Error('Erreur de recherche');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erreur search:', error);
            return { success: false, data: [] };
        }
    }

    static async emptyMailbox() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/empty-mailbox`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Erreur de vidage');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erreur empty mailbox:', error);
            return { success: false };
        }
    }

    // ==================== UTILITAIRE ====================
    
    static async testConnection() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/health`);
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// Fonctions utilitaires
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Test de connexion au démarrage
document.addEventListener('DOMContentLoaded', async function() {
    const isConnected = await MailBoxAPI.testConnection();
    
    if (isConnected) {
        console.log('✅ Connecté à l\'API FastAPI');
    } else {
        console.error('❌ Impossible de se connecter à l\'API');
        alert('⚠️ Impossible de se connecter au serveur. Vérifiez que le Raspberry Pi est allumé et connecté au réseau.');
    }
});