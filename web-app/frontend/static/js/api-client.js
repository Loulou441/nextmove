/**
 * API Client - Gestion des requêtes vers le backend
 */

class APIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.timeout = 30000;
    }

    async request(method, endpoint, data = null) {
        const url = `${this.baseURL}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            timeout: this.timeout,
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${method} ${endpoint}):`, error);
            throw error;
        }
    }

    // Matches endpoints
    createMatch(matchData) {
        return this.request('POST', '/api/matches', matchData);
    }

    getMatches() {
        return this.request('GET', '/api/matches');
    }

    getMatch(matchId) {
        return this.request('GET', `/api/matches/${matchId}`);
    }

    updateMatchStatus(matchId, status) {
        return this.request('PUT', `/api/matches/${matchId}/status?status=${status}`);
    }

    // Actions endpoints
    addAction(matchId, actionData) {
        return this.request('POST', `/api/matches/${matchId}/actions`, actionData);
    }

    getActions(matchId) {
        return this.request('GET', `/api/matches/${matchId}/actions`);
    }

    // Metrics endpoints
    saveMetrics(matchId, metricsData) {
        return this.request('POST', `/api/matches/${matchId}/metrics`, metricsData);
    }

    getMetrics(matchId) {
        return this.request('GET', `/api/matches/${matchId}/metrics`);
    }

    // Sync endpoints
    registerDevice(deviceId) {
        return this.request('POST', `/api/sync/register/${deviceId}`);
    }

    unregisterDevice(deviceId) {
        return this.request('POST', `/api/sync/unregister/${deviceId}`);
    }

    getUpdates(deviceId) {
        return this.request('GET', `/api/sync/updates/${deviceId}`);
    }

    // Health check
    healthCheck() {
        return this.request('GET', '/health');
    }
}

// Instance globale
const apiClient = new APIClient();
