// Friday AI v3 - Frontend Application

class FridayAI {
    constructor() {
        this.isLoggedIn = false;
        this.userId = null;
        this.agents = [];
        this.messages = [];
        console.log('FridayAI initialized');
        this.init();
    }

    async init() {
        console.log('Initializing app...');
        try {
            await this.checkHealth();
        } catch (error) {
            console.error('Init error:', error);
        }
        this.render();
        this.setupEventListeners();
    }

    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            console.log('Health check:', data);
            this.isLoggedIn = true;
            await this.loadAgents();
        } catch (error) {
            console.error('Health check failed:', error);
            this.isLoggedIn = false;
        }
    }

    async loadAgents() {
        try {
            const response = await fetch('/api/agents');
            this.agents = await response.json();
            console.log('Agents loaded:', this.agents);
        } catch (error) {
            console.error('Failed to load agents:', error);
        }
    }

    async sendMessage(message) {
        if (!message.trim()) return;

        // Add user message to UI
        this.messages.push({ role: 'user', content: message });
        this.renderMessages();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            // Add assistant response
            this.messages.push({ role: 'assistant', content: data.response });

            // Add agent results
            if (data.agents) {
                for (const [agentType, result] of Object.entries(data.agents)) {
                    this.messages.push({
                        role: 'agent',
                        agent: agentType,
                        content: result
                    });
                }
            }

            this.renderMessages();
        } catch (error) {
            console.error('Chat error:', error);
            this.messages.push({
                role: 'assistant',
                content: 'Error: Could not process your message'
            });
            this.renderMessages();
        }
    }

    renderMessages() {
        const messagesContainer = document.querySelector('.chat-messages');
        if (!messagesContainer) return;

        messagesContainer.innerHTML = this.messages.map(msg => {
            if (msg.role === 'user') {
                return `<div class="message user">${this.escapeHtml(msg.content)}</div>`;
            } else if (msg.role === 'agent') {
                return `<div class="message agent-result"><strong>${msg.agent}:</strong> ${this.escapeHtml(msg.content)}</div>`;
            } else {
                return `<div class="message assistant">${this.escapeHtml(msg.content)}</div>`;
            }
        }).join('');

        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    drawBrain() {
        const canvas = document.querySelector('.brain-canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.fillStyle = 'rgba(10, 10, 21, 0.5)';
        ctx.fillRect(0, 0, width, height);

        // Draw neural network nodes
        const agents = ['research', 'memory', 'task', 'web_search'];
        const colors = {
            research: '#3b82f6',
            memory: '#06b6d4',
            task: '#10b981',
            web_search: '#f59e0b'
        };

        const centerX = width / 2;
        const centerY = height / 2;
        const radius = 80;

        // Draw connections
        ctx.strokeStyle = 'rgba(168, 85, 247, 0.3)';
        ctx.lineWidth = 1;
        for (let i = 0; i < agents.length; i++) {
            for (let j = i + 1; j < agents.length; j++) {
                const angle1 = (i / agents.length) * Math.PI * 2;
                const angle2 = (j / agents.length) * Math.PI * 2;
                const x1 = centerX + Math.cos(angle1) * radius;
                const y1 = centerY + Math.sin(angle1) * radius;
                const x2 = centerX + Math.cos(angle2) * radius;
                const y2 = centerY + Math.sin(angle2) * radius;
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.stroke();
            }
        }

        // Draw nodes
        agents.forEach((agent, index) => {
            const angle = (index / agents.length) * Math.PI * 2;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;

            // Node glow
            const gradient = ctx.createRadialGradient(x, y, 0, x, y, 15);
            gradient.addColorStop(0, colors[agent] + '60');
            gradient.addColorStop(1, colors[agent] + '00');
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(x, y, 15, 0, Math.PI * 2);
            ctx.fill();

            // Node circle
            ctx.fillStyle = colors[agent];
            ctx.beginPath();
            ctx.arc(x, y, 8, 0, Math.PI * 2);
            ctx.fill();

            // Node border
            ctx.strokeStyle = colors[agent];
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(x, y, 8, 0, Math.PI * 2);
            ctx.stroke();
        });

        // Draw center
        ctx.fillStyle = '#a855f7';
        ctx.beginPath();
        ctx.arc(centerX, centerY, 5, 0, Math.PI * 2);
        ctx.fill();
    }

    renderAgentMonitor() {
        const monitor = document.querySelector('.agent-monitor');
        if (!monitor) return;

        const agents = ['research', 'memory', 'task', 'web_search'];
        const statuses = ['idle', 'thinking', 'researching', 'sharing_knowledge'];

        monitor.innerHTML = agents.map(agent => {
            const status = statuses[Math.floor(Math.random() * statuses.length)];
            return `
                <div class="agent-card">
                    <div class="agent-name">${agent}</div>
                    <div class="agent-status ${status}">${status}</div>
                </div>
            `;
        }).join('');
    }

    render() {
        const root = document.getElementById('root');
        if (!root) {
            console.error('Root element not found!');
            return;
        }

        if (!this.isLoggedIn) {
            root.innerHTML = `
                <div class="login-container">
                    <div class="login-box">
                        <div class="login-title">Friday AI</div>
                        <div class="login-subtitle">Advanced Distributed AI Assistant</div>
                        <button class="login-button" onclick="app.login()">
                            Login with Manus
                        </button>
                    </div>
                </div>
            `;
        } else {
            root.innerHTML = `
                <div class="app-container">
                    <div class="brain-section">
                        <div class="brain-title">🧠 Friday's Brain</div>
                        <div class="brain-container">
                            <canvas class="brain-canvas" width="400" height="300"></canvas>
                        </div>
                        <div class="agent-monitor"></div>
                    </div>
                    <div class="chat-section">
                        <div class="chat-header">💬 Chat with Friday</div>
                        <div class="chat-messages"></div>
                        <div class="chat-input-container">
                            <input type="text" class="chat-input" placeholder="Ask Friday anything..." />
                            <button class="send-button">Send</button>
                        </div>
                    </div>
                </div>
            `;

            // Draw brain
            setTimeout(() => this.drawBrain(), 100);

            // Render agent monitor
            this.renderAgentMonitor();

            // Render messages
            this.renderMessages();

            // Setup chat input
            const input = document.querySelector('.chat-input');
            const sendButton = document.querySelector('.send-button');

            if (input && sendButton) {
                const handleSend = () => {
                    const message = input.value;
                    if (message.trim()) {
                        this.sendMessage(message);
                        input.value = '';
                    }
                };

                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') handleSend();
                });

                sendButton.addEventListener('click', handleSend);
            }

            // Redraw brain periodically
            setInterval(() => this.drawBrain(), 2000);
        }
    }

    setupEventListeners() {
        // Add any global event listeners here
    }

    login() {
        // Simulate login
        this.isLoggedIn = true;
        this.userId = 'user_' + Math.random().toString(36).substr(2, 9);
        this.render();
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, creating app...');
    window.app = new FridayAI();
});

// Fallback if DOMContentLoaded already fired
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.app) {
            console.log('Creating app from fallback...');
            window.app = new FridayAI();
        }
    });
} else {
    if (!window.app) {
        console.log('Creating app immediately...');
        window.app = new FridayAI();
    }
}
