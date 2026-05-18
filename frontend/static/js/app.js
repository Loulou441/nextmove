/**
 * Application principale - TactiCore Web
 */

class TactiCoreApp {
    constructor() {
        this.currentMatch = null;
        this.matches = [];
        this.metrics = [];
        this.actions = [];
        this.init();
    }

    async init() {
        console.log('Initialisation de TactiCore...');

        // Initialiser la synchronisation
        try {
            await syncClient.connect();
        } catch (error) {
            console.warn('Synchronisation WebSocket non disponible, utilisation du polling');
        }

        // Écouter les mises à jour
        syncClient.onUpdate((update) => this.handleSyncUpdate(update));

        // Initialiser les événements UI
        this.initEventListeners();

        // Charger les données initiales
        await this.loadMatches();
        await this.loadDashboard();

        // Définir le device ID
        document.getElementById('deviceId').value = syncClient.deviceId;
    }

    initEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => this.switchSection(e.target.closest('.nav-item')));
        });

        // Créer un match
        document.getElementById('createMatchBtn').addEventListener('click', () => {
            this.openModal('createMatchModal');
        });

        document.getElementById('createMatchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createMatch();
        });

        // Modal close
        document.querySelectorAll('.close').forEach(closeBtn => {
            closeBtn.addEventListener('click', (e) => {
                e.target.closest('.modal').classList.remove('active');
            });
        });

        // Paramètres
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });

        document.getElementById('matchSelector').addEventListener('change', (e) => {
            this.loadMatchActions(e.target.value);
        });
    }

    switchSection(navItem) {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        navItem.classList.add('active');

        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });

        const sectionId = navItem.dataset.section;
        document.getElementById(sectionId).classList.add('active');
    }

    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }

    async createMatch() {
        const teamA = document.getElementById('teamA').value;
        const teamB = document.getElementById('teamB').value;
        const sport = document.getElementById('sport').value;
        const date = new Date(document.getElementById('matchDate').value);

        try {
            const response = await apiClient.createMatch({
                team_a: teamA,
                team_b: teamB,
                sport: sport,
                date: date.toISOString(),
                status: 'pending'
            });

            console.log('Match créé:', response);
            
            // Fermer le modal
            document.getElementById('createMatchModal').classList.remove('active');
            
            // Réinitialiser le formulaire
            document.getElementById('createMatchForm').reset();
            
            // Recharger la liste des matchs
            await this.loadMatches();
            
            this.showNotification('Match créé avec succès!', 'success');
        } catch (error) {
            console.error('Erreur création match:', error);
            this.showNotification('Erreur lors de la création du match', 'error');
        }
    }

    async loadMatches() {
        try {
            const response = await apiClient.getMatches();
            this.matches = response;
            this.renderMatches();
            this.renderMatchSelector();
        } catch (error) {
            console.error('Erreur chargement matches:', error);
        }
    }

    renderMatches() {
        const container = document.getElementById('matchesList');
        
        if (this.matches.length === 0) {
            container.innerHTML = '<p class="empty-state">Aucun match pour le moment</p>';
            return;
        }

        container.innerHTML = this.matches.map(match => `
            <div class="card">
                <h3>${match.team_a} vs ${match.team_b}</h3>
                <p style="color: var(--text-secondary); margin: 10px 0;">
                    <strong>Sport:</strong> ${match.sport}<br>
                    <strong>Date:</strong> ${new Date(match.date).toLocaleDateString('fr-FR')}<br>
                    <strong>Statut:</strong> 
                    <span style="color: ${match.status === 'ongoing' ? 'var(--success-color)' : 'var(--text-secondary)'}">
                        ${match.status}
                    </span>
                </p>
                <div style="display: flex; gap: 10px; margin-top: 15px;">
                    <button class="btn btn-primary" style="flex: 1; font-size: 12px;" onclick="app.updateMatchStatus('${match.id}', '${match.status === 'ongoing' ? 'completed' : 'ongoing'}')">
                        ${match.status === 'ongoing' ? 'Terminer' : 'Démarrer'}
                    </button>
                </div>
            </div>
        `).join('');
    }

    renderMatchSelector() {
        const selector = document.getElementById('matchSelector');
        selector.innerHTML = '<option value="">Choisir un match...</option>' + 
            this.matches.map(match => 
                `<option value="${match.id}">${match.team_a} vs ${match.team_b}</option>`
            ).join('');
    }

    async loadMatchActions(matchId) {
        if (!matchId) {
            document.getElementById('actionsList').innerHTML = 
                '<p class="empty-state">Sélectionnez un match pour voir les actions</p>';
            return;
        }

        try {
            const actions = await apiClient.getActions(matchId);
            this.actions = actions;
            this.renderActions(actions);
        } catch (error) {
            console.error('Erreur chargement actions:', error);
        }
    }

    renderActions(actions) {
        const container = document.getElementById('actionsList');
        
        if (actions.length === 0) {
            container.innerHTML = '<p class="empty-state">Aucune action pour ce match</p>';
            return;
        }

        container.innerHTML = actions.map(action => `
            <div class="card">
                <h4 style="margin-bottom: 10px;">${action.action_type.toUpperCase()}</h4>
                <p style="font-size: 12px; color: var(--text-secondary); margin-bottom: 10px;">
                    <strong>Temps:</strong> ${action.timestamp.toFixed(1)}s<br>
                    <strong>Position:</strong> (${action.coordinates_x}, ${action.coordinates_y})
                </p>
                <p>${action.description}</p>
                ${action.ai_recommendation ? `
                    <div style="margin-top: 10px; padding: 10px; background: rgba(255, 107, 53, 0.1); border-left: 3px solid var(--primary-color); border-radius: 4px;">
                        <strong style="color: var(--primary-color);">Recommandation IA:</strong>
                        <p style="margin-top: 5px;">${action.ai_recommendation}</p>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    async loadDashboard() {
        try {
            const matchCount = this.matches.length;
            document.getElementById('activeMatches').textContent = 
                this.matches.filter(m => m.status === 'ongoing').length;
            document.getElementById('analyzedActions').textContent = 
                this.actions.length;
            document.getElementById('activeConnections').textContent = 
                syncClient.isConnected ? '1' : '0';
        } catch (error) {
            console.error('Erreur chargement dashboard:', error);
        }
    }

    async updateMatchStatus(matchId, status) {
        try {
            await apiClient.updateMatchStatus(matchId, status);
            await this.loadMatches();
            this.showNotification(`Statut du match mis à jour à: ${status}`, 'success');
        } catch (error) {
            console.error('Erreur mise à jour statut:', error);
            this.showNotification('Erreur lors de la mise à jour', 'error');
        }
    }

    saveSettings() {
        const apiUrl = document.getElementById('apiUrl').value;
        const autoSync = document.getElementById('autoSync').checked;

        localStorage.setItem('apiUrl', apiUrl);
        localStorage.setItem('autoSync', autoSync);

        // Mettre à jour l'API client
        apiClient.baseURL = apiUrl;

        this.showNotification('Paramètres enregistrés', 'success');
    }

    handleSyncUpdate(update) {
        console.log('Mise à jour sync reçue:', update);

        switch (update.event_type) {
            case 'match_created':
                this.loadMatches();
                this.showNotification('Nouveau match créé', 'info');
                break;
            case 'match_status_updated':
                this.loadMatches();
                this.showNotification(`Match mis à jour`, 'info');
                break;
            case 'action_added':
                this.loadMatchActions(update.data.match_id);
                this.showNotification('Nouvelle action enregistrée', 'info');
                break;
            case 'metrics_updated':
                this.loadDashboard();
                this.showNotification('Métriques mises à jour', 'info');
                break;
        }

        // Ajouter à la timeline
        this.addFeedItem(update);
    }

    addFeedItem(update) {
        const feed = document.getElementById('realtimeFeed');
        const emptyState = feed.querySelector('.empty-state');
        
        if (emptyState) {
            emptyState.remove();
        }

        const item = document.createElement('div');
        item.className = 'feed-item';
        item.innerHTML = `
            <strong>${update.event_type.replace(/_/g, ' ').toUpperCase()}</strong><br>
            <small>${new Date(update.timestamp).toLocaleTimeString('fr-FR')}</small>
        `;
        
        feed.insertBefore(item, feed.firstChild);

        // Limiter à 50 items
        while (feed.children.length > 50) {
            feed.removeChild(feed.lastChild);
        }
    }

    showNotification(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        // Vous pouvez ajouter une barre de notification visuelle ici
    }
}

// Initialiser l'app au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    window.app = new TactiCoreApp();
});
