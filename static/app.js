/**
 * Friday AI v3 - Optimized Frontend
 */

class FridayAI {
    constructor() {
        this.messages = [];
        this.agents = [];
        this.isLoading = false;
        this.init();
    }

    async init() {
        try {
            await this.checkHealth();
            await this.loadAgents();
            this.render();
            
            setTimeout(() => {
                document.querySelector('.loading-screen').style.display = 'none';
            }, 300);
        } catch (error) {
            console.error('Init error:', error);
        }
    }

    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
        }
    }

    async loadAgents() {
        try {
            const response = await fetch('/api/agents');
            this.agents = await response.json();
        } catch (error) {
            console.error('Failed to load agents:', error);
        }
    }

    async loadChatHistory() {
        try {
            const response = await fetch('/api/chat/history');
            this.messages = await response.json();
            this.renderMessages();
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    async sendMessage(text) {
        if (!text.trim() || this.isLoading) return;

        this.isLoading = true;
        const input = document.querySelector('.input-field');
        input.value = '';

        try {
            // Add user message
            this.messages.push({
                role: 'user',
                message: text
            });
            this.renderMessages();

            // Send to server
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            // Add assistant response
            this.messages.push({
                role: 'assistant',
                message: data.response || 'No response'
            });

            this.renderMessages();
        } catch (error) {
            this.messages.push({
                role: 'assistant',
                message: `Error: ${error.message}`
            });
            this.renderMessages();
        } finally {
            this.isLoading = false;
            input.focus();
        }
    }

    async toggleAgent(agentName) {
        try {
            const response = await fetch(`/api/agents/${agentName}/toggle`, {
                method: 'POST'
            });
            const data = await response.json();
            
            const agent = this.agents.find(a => a.agent_name === agentName);
            if (agent) {
                agent.is_active = data.is_active;
            }
            
            this.render();
        } catch (error) {
            console.error('Toggle agent error:', error);
        }
    }

    renderMessages() {
        const container = document.querySelector('.chat-messages');
        if (!container) return;

        container.innerHTML = this.messages.map(msg => `
            <div class="message ${msg.role}">
                <div class="message-label">${msg.role}</div>
                <div class="message-content">${this.escapeHtml(msg.message)}</div>
            </div>
        `).join('');

        container.scrollTop = container.scrollHeight;
    }

    render() {
        const app = document.getElementById('app');
        
        app.innerHTML = `
            <div class="main-layout">
                <div class="sidebar">
                    <div class="sidebar-section">
                        <div class="sidebar-title">🤖 Agents</div>
                        <div class="agent-list">
                            ${this.agents.map(agent => `
                                <div class="agent-item ${agent.is_active ? 'active' : ''}" 
                                     onclick="app.toggleAgent('${agent.agent_name}')">
                                    <div>${agent.agent_name}</div>
                                    <div class="agent-toggle">${agent.is_active ? '✓' : ''}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <div class="content">
                    <div class="header">
                        <div class="header-title">F.R.I.D.A.Y</div>
                        <div class="header-status">
                            <div class="status-item">
                                <div class="status-indicator"></div>
                                <span>ONLINE</span>
                            </div>
                        </div>
                    </div>

                    <div class="chat-container">
                        <div class="chat-messages"></div>
                        
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea 
                                    class="input-field" 
                                    placeholder="Ask Friday anything..."
                                    rows="1"
                                    onkeypress="if(event.key==='Enter' && !event.shiftKey) { event.preventDefault(); app.sendMessage(this.value); }">
                                </textarea>
                                <button 
                                    class="send-button"
                                    onclick="app.sendMessage(document.querySelector('.input-field').value)">
                                    Send
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.loadChatHistory();
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

document.addEventListener('DOMContentLoaded', () => {
    window.app = new FridayAI();
});
