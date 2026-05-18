/**
 * Sync Client - Gestion de la synchronisation en temps réel
 */

class SyncClient {
    constructor(apiClient, baseURL = 'ws://localhost:8000') {
        this.apiClient = apiClient;
        this.baseURL = baseURL;
        this.deviceId = this.generateDeviceId();
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.updateCallbacks = [];
    }

    generateDeviceId() {
        let deviceId = localStorage.getItem('deviceId');
        if (!deviceId) {
            deviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            localStorage.setItem('deviceId', deviceId);
        }
        return deviceId;
    }

    async connect() {
        // D'abord, enregistrer le device
        try {
            await this.apiClient.registerDevice(this.deviceId);
            console.log('Device enregistré:', this.deviceId);
        } catch (error) {
            console.error('Erreur lors de l\'enregistrement du device:', error);
        }

        // Essayer de connexion WebSocket
        return this.connectWebSocket();
    }

    connectWebSocket() {
        return new Promise((resolve, reject) => {
            try {
                const wsURL = `${this.baseURL}/api/sync/ws/${this.deviceId}`;
                this.ws = new WebSocket(wsURL);

                this.ws.onopen = () => {
                    console.log('WebSocket connecté');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    this.updateUIStatus(true);
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (error) {
                        console.error('Erreur parsing message:', error);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket erreur:', error);
                    this.isConnected = false;
                    this.updateUIStatus(false);
                };

                this.ws.onclose = () => {
                    console.log('WebSocket fermé');
                    this.isConnected = false;
                    this.updateUIStatus(false);
                    this.attemptReconnect();
                };

                // Timeout si pas de connexion après 5s
                setTimeout(() => {
                    if (this.ws.readyState !== WebSocket.OPEN) {
                        reject(new Error('WebSocket connection timeout'));
                    }
                }, 5000);

            } catch (error) {
                this.isConnected = false;
                this.updateUIStatus(false);
                this.attemptReconnect();
                reject(error);
            }
        });
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);
            
            setTimeout(() => {
                this.connectWebSocket().catch(error => {
                    console.error('Reconnexion échouée:', error);
                    this.startPolling();
                });
            }, this.reconnectDelay);
        } else {
            console.log('Max reconnect attempts atteint, passage au polling');
            this.startPolling();
        }
    }

    startPolling() {
        console.log('Démarrage du polling...');
        setInterval(() => {
            this.apiClient.getUpdates(this.deviceId)
                .then(response => {
                    if (response.updates && response.updates.length > 0) {
                        response.updates.forEach(update => {
                            this.handleMessage({ type: 'updates', data: [update] });
                        });
                    }
                })
                .catch(error => console.error('Erreur polling:', error));
        }, 5000);
    }

    handleMessage(message) {
        if (message.type === 'updates' && message.data) {
            message.data.forEach(update => {
                this.notifyCallbacks(update);
            });
        }
    }

    onUpdate(callback) {
        this.updateCallbacks.push(callback);
    }

    notifyCallbacks(update) {
        this.updateCallbacks.forEach(callback => {
            try {
                callback(update);
            } catch (error) {
                console.error('Erreur dans callback:', error);
            }
        });
    }

    updateUIStatus(isOnline) {
        const statusElement = document.getElementById('syncStatus');
        if (statusElement) {
            const dot = statusElement.querySelector('.status-dot');
            const text = statusElement.querySelector('.status-text');
            
            if (isOnline) {
                dot.classList.remove('offline');
                dot.classList.add('online');
                text.textContent = 'En ligne';
            } else {
                dot.classList.remove('online');
                dot.classList.add('offline');
                text.textContent = 'Hors ligne';
            }
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
        this.isConnected = false;
        this.updateUIStatus(false);
    }
}

// Instance globale
const syncClient = new SyncClient(apiClient);
