/**
 * Friday AI v3 - Complete Frontend Application
 */

class FridayAI {
    constructor() {
        this.messages = [];
        this.agents = [];
        this.knowledge = [];
        this.activities = [];
        this.isLoading = false;
        this.brainState = null;
        this.animationId = null;
        this.init();
    }

    async init() {
        try {
            await this.checkHealth();
            await this.loadAgents();
            await this.loadKnowledge();
            await this.loadActivities();
            this.render();
            this.startBrainAnimation();
            
            setTimeout(() => {
                const loading = document.querySelector('.loading-screen');
                if (loading) loading.style.display = 'none';
            }, 500);
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

    async loadKnowledge() {
        try {
            const response = await fetch('/api/knowledge');
            this.knowledge = await response.json();
        } catch (error) {
            console.error('Failed to load knowledge:', error);
        }
    }

    async loadActivities() {
        try {
            const response = await fetch('/api/activity');
            this.activities = await response.json();
        } catch (error) {
            console.error('Failed to load activities:', error);
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

    async loadBrainState() {
        try {
            const response = await fetch('/api/brain');
            this.brainState = await response.json();
        } catch (error) {
            console.error('Failed to load brain state:', error);
        }
    }

    async sendMessage(text, deepthink = false) {
        if (!text.trim() || this.isLoading) return;

        this.isLoading = true;
        const input = document.querySelector('.input-field');
        input.value = '';

        try {
            this.messages.push({
                role: 'user',
                message: text,
                timestamp: new Date().toISOString()
            });
            this.renderMessages();

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, deepthink: deepthink })
            });

            const data = await response.json();

            this.messages.push({
                role: 'assistant',
                message: data.response || 'No response',
                timestamp: new Date().toISOString()
            });

            this.renderMessages();
            await this.loadBrainState();
        } catch (error) {
            this.messages.push({
                role: 'assistant',
                message: `Error: ${error.message}`,
                timestamp: new Date().toISOString()
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
            await this.loadBrainState();
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
                    message: `📄 File: ${path}\n\n${data.content.substring(0, 500)}...`,
                    timestamp: new Date().toISOString()
                });
                this.renderMessages();
            }
        } catch (error) {
            console.error('Read file error:', error);
        }
    }

    async writeFile(path, content) {
        try {
            const response = await fetch('/api/files/write', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path, content })
            });
            const data = await response.json();
            
            if (data.success) {
                this.messages.push({
                    role: 'assistant',
                    message: `✅ File written: ${path}`,
                    timestamp: new Date().toISOString()
                });
                this.renderMessages();
            }
        } catch (error) {
            console.error('Write file error:', error);
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
            <div style="padding: 8px; font-size: 10px; color: var(--text-secondary); margin-bottom: 8px;">
                📍 ${data.path}
            </div>
            ${data.items.map(item => `
                <div class="file-item" onclick="app.${item.type === 'dir' ? 'listFiles' : 'readFile'}('${item.path}')">
                    ${item.type === 'dir' ? '📁' : '📄'} ${item.name}
                </div>
            `).join('')}
        `;
    }

    startBrainAnimation() {
        const canvas = document.getElementById('brain-canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        let time = 0;

        const animate = () => {
            ctx.fillStyle = 'rgba(13, 13, 13, 0.1)';
            ctx.fillRect(0, 0, w, h);

            // Draw nodes
            const agents = this.agents || [];
            agents.forEach((agent, i) => {
                const angle = (i / agents.length) * Math.PI * 2;
                const x = w / 2 + Math.cos(angle) * 60;
                const y = h / 2 + Math.sin(angle) * 60;

                ctx.fillStyle = agent.is_active ? '#10a37f' : '#404040';
                ctx.beginPath();
                ctx.arc(x, y, 6, 0, Math.PI * 2);
                ctx.fill();

                ctx.strokeStyle = agent.is_active ? 'rgba(16, 163, 127, 0.5)' : 'rgba(64, 64, 64, 0.3)';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.arc(x, y, 10, 0, Math.PI * 2);
                ctx.stroke();
            });

            // Draw center
            ctx.fillStyle = '#a855f7';
            ctx.beginPath();
            ctx.arc(w / 2, h / 2, 8, 0, Math.PI * 2);
            ctx.fill();

            time += 0.01;
            this.animationId = requestAnimationFrame(animate);
        };

        animate();
    }

    render() {
        const app = document.getElementById('app');
        
        app.innerHTML = `
            <div class="main-layout">
                <div class="sidebar">
                    <!-- Brain Visualization -->
                    <div class="brain-section">
                        <div class="sidebar-title">🧠 Brain</div>
                        <canvas id="brain-canvas"></canvas>
                    </div>

                    <!-- Agents -->
                    <div class="sidebar-section">
                        <div class="sidebar-title">🤖 Agents</div>
                        <div class="agent-list">
                            ${this.agents.map(agent => `
                                <div class="agent-item ${agent.is_active ? 'active' : ''}" 
                                     onclick="app.toggleAgent('${agent.agent_name}')">
                                    <div>
                                        <div>${agent.agent_name}</div>
                                        <div class="agent-status">${agent.status || 'idle'}</div>
                                    </div>
                                    <div class="agent-toggle">${agent.is_active ? '✓' : ''}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Files -->
                    <div class="sidebar-section">
                        <div class="sidebar-title">📁 Files</div>
                        <button onclick="app.listFiles()" style="width: 100%; padding: 8px; background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 4px; color: var(--text); cursor: pointer; font-size: 12px;">
                            Browse Files
                        </button>
                        <div class="file-explorer"></div>
                    </div>

                    <!-- Knowledge -->
                    <div class="knowledge-section">
                        <div class="sidebar-title">💾 Knowledge (${this.knowledge.length})</div>
                        ${this.knowledge.slice(0, 5).map(item => `
                            <div class="knowledge-item">${this.escapeHtml(item.content.substring(0, 40))}</div>
                        `).join('')}
                    </div>

                    <!-- Activity -->
                    <div class="activity-section">
                        <div class="sidebar-title">📊 Activity</div>
                        ${this.activities.slice(0, 8).map(item => `
                            <div class="activity-item">${item.agent_name}: ${item.action}</div>
                        `).join('')}
                    </div>
                </div>

                <div class="content">
                    <div class="header">
                        <div class="header-title">Friday AI</div>
                        <div class="header-status">
                            <div class="status-item">
                                <div class="status-indicator"></div>
                                <span>ONLINE</span>
                            </div>
                            <div class="status-item">
                                Agents: ${this.agents.filter(a => a.is_active).length}/${this.agents.length}
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
                                <button 
                                    class="send-button" 
                                    style="background: #a855f7; margin-left: 4px;"
                                    onclick="app.sendMessage(document.querySelector('.input-field').value, true)" 
                                    title="DeepThink Mode">
                                    🧠
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.loadChatHistory();
        this.startBrainAnimation();
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
