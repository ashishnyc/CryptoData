class WebSocketService {
    constructor() {
        this.connect();
        this.handlers = new Map();
    }

    connect() {
        this.ws = new WebSocket(`ws://${window.location.host}/ws`);

        this.ws.onopen = () => {
            console.log('Connected to WebSocket');
            this.heartbeat();
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const handlers = this.handlers.get(data.type) || [];
            handlers.forEach(handler => handler(data.payload));
        };

        this.ws.onclose = () => {
            console.log('WebSocket Disconnected');
            clearInterval(this.heartbeatInterval);
            setTimeout(() => this.connect(), 5000);
        };
    }

    heartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    }

    subscribe(type, handler) {
        if (!this.handlers.has(type)) {
            this.handlers.set(type, []);
        }
        this.handlers.get(type).push(handler);

        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'subscribe', channel: type }));
        }
    }

    unsubscribe(type, handler) {
        const handlers = this.handlers.get(type);
        if (handlers) {
            this.handlers.set(type, handlers.filter(h => h !== handler));
        }
    }
}

export const wsService = new WebSocketService();