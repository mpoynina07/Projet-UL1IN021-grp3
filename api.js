// api.js - Fichier centralisé pour les appels API

// Gestion du token d'authentification
function getAuthToken() {
    return localStorage.getItem('authToken');
}

function setAuthToken(token) {
    localStorage.setItem('authToken', token);
}

function removeAuthToken() {
    localStorage.removeItem('authToken');
}

// Fonction pour formater les dates
function formatDate(dateString) {
    if (!dateString) return 'Date inconnue';
    
    try {
        const date = new Date(dateString);
        const options = { 
            year: 'numeric', 
            month: '2-digit', 
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        };
        return date.toLocaleDateString('fr-FR', options);
    } catch (e) {
        return dateString;
    }
}

// API Client
const MailBoxAPI = {
    
    // Obtenir le statut de la boîte
    async getMailboxStatus() {
        try {
            const response = await fetch('/api/mail-status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Erreur réseau');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erreur getMailboxStatus:', error);
            return { success: false, has_mail: false };
        }
    },
    
    // Vider la boîte
    async emptyMailbox() {
        try {
            const response = await fetch('/api/empty-mailbox', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Erreur réseau');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erreur emptyMailbox:', error);
            return { success: false };
        }
    },
    
    // Rechercher du courrier (à implémenter côté serveur si nécessaire)
    async searchMail(filters) {
        try {
            const queryParams = new URLSearchParams(filters).toString();
            const response = await fetch(`/api/search-mail?${queryParams}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Erreur réseau');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erreur searchMail:', error);
            return [];
        }
    }
};
