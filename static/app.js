/**
 * Friday AI v3 - Claude/ChatGPT Style UI
 */

class FridayAI {
    constructor() {
        this.messages = [];
        this.agents = [];
        this.isLoading = false;
        this.currentPath = null;
        this.init();
    }

    async init() {
        try {
            await this.checkHealth();
            await this.loadAgents();
            this.render();
            
            setTimeout(() => {
                const loading = document.querySelector('.loading-screen');
                if (loading) loading.style.display = 'none';
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
            this.messages.push({
                role: 'user',
                message: text
            });
            this.renderMessages();

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

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

    async listFiles(path = null) {
        try {
            const url = path ? `/api/files?path=${encodeURIComponent(path)}` : '/api/files';
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.path) {
                this.currentPath = data.path;
                this.renderFileExplorer(data);
            }
        } catch (error) {
            console.error('List files error:', error);
        }
    }

    async readFile(path) {
        try {
            const response = await fetch('/api/files/read', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path })
            });
            const data = await response.json();
            
            if (data.content) {
                this.messages.push({
                    role: 'assistant',
                    message: `File: ${path}\n\n${data.content.substring(0, 500)}...`
                });
                this.renderMessages();
            }
        } catch (error) {
            console.error('Read file error:', error);
        }
    }

    renderMessages() {
        const container = document.querySelector('.chat-messages');
        if (!container) return;

        container.innerHTML = this.messages.map(msg => `
            <div class="message ${msg.role}">
                <div class="message-wrapper">
                    <div class="message-label">${msg.role}</div>
                    <div class="message-content">${this.escapeHtml(msg.message)}</div>
                </div>
            </div>
        `).join('');

        container.scrollTop = container.scrollHeight;
    }

    renderFileExplorer(data) {
        const explorer = document.querySelector('.file-explorer');
        if (!explorer) return;

        explorer.innerHTML = `
            <div style="padding: 12px; font-size: 12px; color: var(--text-secondary);">
                ${data.path}
            </div>
            <div style="padding: 12px; max-height: 300px; overflow-y: auto;">
                ${data.items.map(item => `
                    <div style="padding: 6px; cursor: pointer; border-radius: 4px; margin-bottom: 4px; background: var(--bg-tertiary);"
                         onclick="app.${item.type === 'dir' ? 'listFiles' : 'readFile'}('${item.path}')">
                        ${item.type === 'dir' ? '📁' : '📄'} ${item.name}
                    </div>
                `).join('')}
            </div>
        `;
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

                    <div class="sidebar-section">
                        <div class="sidebar-title">📁 Files</div>
                        <button onclick="app.listFiles()" style="width: 100%; padding: 8px; background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 4px; color: var(--text); cursor: pointer; font-size: 12px;">
                            Browse Files
                        </button>
                        <div class="file-explorer" style="margin-top: 8px;"></div>
                    </div>
                </div>

                <div class="content">
                    <div class="header">
                        <div class="header-title">Friday AI</div>
                        <div class="header-status">
                            <div class="status-indicator"></div>
                            <span>ONLINE</span>
                        </div>
                    </div>

                    <div class="chat-container">
                        <div class="chat-messages"></div>
                        
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea 
                                    class="input-field" 
                                    placeholder="Message Friday..."
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
