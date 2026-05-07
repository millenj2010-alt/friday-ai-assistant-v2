/**
 * Friday AI v3 - Frontend Application
 * Advanced AI Assistant with Chat and Learning Agents
 */

class FridayAI {
    constructor() {
        this.messages = [];
        this.agents = [];
        this.knowledge = [];
        this.isLoading = false;
        this.init();
    }

    async init() {
        console.log('Initializing Friday AI...');
        
        try {
            // Check health
            await this.checkHealth();
            
            // Load agents
            await this.loadAgents();
            
            // Render UI
            this.render();
            
            // Hide loading screen
            setTimeout(() => {
                document.querySelector('.loading-screen').style.display = 'none';
            }, 500);
        } catch (error) {
            console.error('Init error:', error);
        }
    }

    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            console.log('Health:', data);
            return data;
        } catch (error) {
            console.error('Health check failed:', error);
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

    async loadChatHistory() {
        try {
            const response = await fetch('/api/chat/history?limit=50');
            this.messages = await response.json();
            this.renderMessages();
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    async loadKnowledge() {
        try {
            const response = await fetch('/api/knowledge?limit=100');
            this.knowledge = await response.json();
        } catch (error) {
            console.error('Failed to load knowledge:', error);
        }
    }

    async sendMessage(text) {
        if (!text.trim() || this.isLoading) return;

        this.isLoading = true;

        try {
            // Add user message to UI
            this.messages.push({
                role: 'user',
                message: text,
                timestamp: new Date().toISOString()
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
                message: data.response,
                timestamp: new Date().toISOString()
            });

            this.renderMessages();
        } catch (error) {
            console.error('Chat error:', error);
            this.messages.push({
                role: 'assistant',
                message: `Error: ${error.message}`,
                timestamp: new Date().toISOString()
            });
            this.renderMessages();
        } finally {
            this.isLoading = false;
        }
    }

    async toggleAgent(agentName) {
        try {
            const response = await fetch(`/api/agents/${agentName}/toggle`, {
                method: 'POST'
            });
            const data = await response.json();
            
            // Update local state
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

        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    render() {
        const app = document.getElementById('app');
        
        app.innerHTML = `
            <div class="main-layout">
                <!-- Sidebar -->
                <div class="sidebar">
                    <!-- Agents Section -->
                    <div class="sidebar-section">
                        <div class="sidebar-title">🤖 Agents</div>
                        <div class="agent-list">
                            ${this.agents.map(agent => `
                                <div class="agent-item ${agent.is_active ? 'active' : ''}" 
                                     onclick="app.toggleAgent('${agent.agent_name}')">
                                    <div class="agent-name">${agent.agent_name}</div>
                                    <div class="agent-toggle">${agent.is_active ? '✓' : ''}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Knowledge Section -->
                    <div class="sidebar-section">
                        <div class="sidebar-title">💾 Knowledge Base</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">
                            ${this.knowledge.length} items learned
                        </div>
                    </div>
                </div>

                <!-- Main Content -->
                <div class="content">
                    <!-- Header -->
                    <div class="header">
                        <div class="header-title">F.R.I.D.A.Y</div>
                        <div class="header-status">
                            <div class="status-item">
                                <div class="status-indicator"></div>
                                <span>ONLINE</span>
                            </div>
                        </div>
                    </div>

                    <!-- Chat Container -->
                    <div class="chat-container">
                        <div class="chat-messages"></div>
                        
                        <!-- Chat Input -->
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea 
                                    class="input-field" 
                                    placeholder="Ask Friday anything..."
                                    rows="1"
                                    onkeypress="if(event.key==='Enter' && !event.shiftKey) { app.sendMessage(this.value); this.value=''; }">
                                </textarea>
                                <button 
                                    class="send-button"
                                    onclick="const input = document.querySelector('.input-field'); app.sendMessage(input.value); input.value=''; input.focus();">
                                    Send
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Load chat history
        this.loadChatHistory();
        this.loadKnowledge();
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
    window.app = new FridayAI();
});
