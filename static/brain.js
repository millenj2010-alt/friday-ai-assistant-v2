/**
 * Advanced Brain Visualization
 * Detailed neural network with nodes, connections, and activity
 */

class BrainVisualization {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.w = this.canvas.width;
        this.h = this.canvas.height;
        
        this.nodes = [];
        this.connections = [];
        this.pulses = [];
        this.time = 0;
        
        this.initNodes();
        this.animate();
    }

    initNodes() {
        const agentNames = ['learning_agent', 'research_agent', 'memory_agent', 'web_search_agent', 'deepthink_agent'];
        const centerX = this.w / 2;
        const centerY = this.h / 2;
        
        // Center node (Friday's core)
        this.nodes.push({
            x: centerX,
            y: centerY,
            radius: 12,
            color: '#a855f7',
            label: 'FRIDAY',
            type: 'core',
            activity: 0
        });
        
        // Agent nodes in circle
        agentNames.forEach((name, i) => {
            const angle = (i / agentNames.length) * Math.PI * 2 - Math.PI / 2;
            const distance = 80;
            this.nodes.push({
                x: centerX + Math.cos(angle) * distance,
                y: centerY + Math.sin(angle) * distance,
                radius: 8,
                color: '#10a37f',
                label: name.split('_')[0],
                type: 'agent',
                activity: 0,
                angle: angle
            });
        });
        
        // Create connections
        for (let i = 1; i < this.nodes.length; i++) {
            this.connections.push({
                from: 0,
                to: i,
                strength: 0.5
            });
        }
    }

    addPulse(fromIndex, toIndex) {
        this.pulses.push({
            from: fromIndex,
            to: toIndex,
            progress: 0,
            speed: 0.02
        });
    }

    animate = () => {
        // Clear with fade
        this.ctx.fillStyle = 'rgba(13, 13, 13, 0.05)';
        this.ctx.fillRect(0, 0, this.w, this.h);
        
        // Draw connections
        this.connections.forEach(conn => {
            const fromNode = this.nodes[conn.from];
            const toNode = this.nodes[conn.to];
            
            this.ctx.strokeStyle = `rgba(16, 163, 127, ${0.2 + conn.strength * 0.3})`;
            this.ctx.lineWidth = 1 + conn.strength * 2;
            this.ctx.beginPath();
            this.ctx.moveTo(fromNode.x, fromNode.y);
            this.ctx.lineTo(toNode.x, toNode.y);
            this.ctx.stroke();
            
            // Fade connection strength
            conn.strength *= 0.98;
        });
        
        // Draw pulses
        this.pulses = this.pulses.filter(pulse => pulse.progress < 1);
        this.pulses.forEach(pulse => {
            const fromNode = this.nodes[pulse.from];
            const toNode = this.nodes[pulse.to];
            
            const x = fromNode.x + (toNode.x - fromNode.x) * pulse.progress;
            const y = fromNode.y + (toNode.y - fromNode.y) * pulse.progress;
            
            const size = 4 * (1 - pulse.progress);
            this.ctx.fillStyle = `rgba(168, 85, 247, ${1 - pulse.progress})`;
            this.ctx.beginPath();
            this.ctx.arc(x, y, size, 0, Math.PI * 2);
            this.ctx.fill();
            
            pulse.progress += pulse.speed;
        });
        
        // Draw nodes
        this.nodes.forEach((node, i) => {
            // Glow effect
            const glowSize = node.radius + 8 + Math.sin(this.time * 0.05 + i) * 3;
            this.ctx.fillStyle = `rgba(${node.type === 'core' ? '168, 85, 247' : '16, 163, 127'}, ${0.1 + node.activity * 0.2})`;
            this.ctx.beginPath();
            this.ctx.arc(node.x, node.y, glowSize, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Node body
            this.ctx.fillStyle = node.color;
            this.ctx.beginPath();
            this.ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Node border
            this.ctx.strokeStyle = node.color;
            this.ctx.lineWidth = 2;
            this.ctx.stroke();
            
            // Activity indicator
            if (node.activity > 0.1) {
                this.ctx.strokeStyle = `rgba(255, 255, 255, ${node.activity})`;
                this.ctx.lineWidth = 1;
                this.ctx.beginPath();
                this.ctx.arc(node.x, node.y, node.radius + 4, 0, Math.PI * 2);
                this.ctx.stroke();
            }
            
            // Label
            this.ctx.fillStyle = '#ececec';
            this.ctx.font = '10px Inter';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(node.label, node.x, node.y + node.radius + 12);
            
            // Fade activity
            node.activity *= 0.95;
        });
        
        this.time++;
        requestAnimationFrame(this.animate);
    }

    setNodeActivity(nodeIndex, activity) {
        if (this.nodes[nodeIndex]) {
            this.nodes[nodeIndex].activity = Math.min(1, activity);
        }
    }

    setConnectionStrength(fromIndex, toIndex, strength) {
        const conn = this.connections.find(c => c.from === fromIndex && c.to === toIndex);
        if (conn) {
            conn.strength = strength;
        }
    }
}

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BrainVisualization;
}
