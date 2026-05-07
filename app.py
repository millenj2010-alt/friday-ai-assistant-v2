"""
Friday AI v3 - Python Backend
A distributed AI assistant with Ollama integration
"""

import os
import json
import uuid
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import requests
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'sqlite:///friday_ai.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE MODELS
# ============================================================================

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Agent(db.Model):
    __tablename__ = 'agents'
    id = db.Column(db.Integer, primary_key=True)
    agent_type = db.Column(db.String(50), nullable=False)  # research, memory, task, web_search
    status = db.Column(db.String(50), default='idle')  # idle, thinking, researching, sharing_knowledge
    node_id = db.Column(db.String(120), nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_base'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(120), nullable=False)
    node_id = db.Column(db.String(120), nullable=False)
    confidence = db.Column(db.Float, default=0.5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DistributedNode(db.Model):
    __tablename__ = 'distributed_nodes'
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.String(120), unique=True, nullable=False)
    hostname = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    port = db.Column(db.Integer, default=5000)
    is_active = db.Column(db.Boolean, default=True)
    last_heartbeat = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AgentActivity(db.Model):
    __tablename__ = 'agent_activity'
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    result = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NodeSyncLog(db.Model):
    __tablename__ = 'node_sync_log'
    id = db.Column(db.Integer, primary_key=True)
    source_node = db.Column(db.String(120), nullable=False)
    target_node = db.Column(db.String(120), nullable=False)
    sync_type = db.Column(db.String(50), nullable=False)  # p2p, central
    status = db.Column(db.String(50), nullable=False)  # success, failed
    items_synced = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================================================
# OLLAMA INTEGRATION
# ============================================================================

class OllamaClient:
    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'mistral')
    
    def generate(self, prompt, stream=False):
        """Generate response from Ollama"""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": stream
            }
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            if stream:
                return response.iter_lines()
            else:
                return response.json()
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return {"error": str(e)}
    
    def list_models(self):
        """List available models"""
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return {"models": []}
    
    def health_check(self):
        """Check if Ollama is running"""
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False

ollama_client = OllamaClient()

# ============================================================================
# DISTRIBUTED NODE MANAGER
# ============================================================================

class DistributedNodeManager:
    def __init__(self):
        self.node_id = os.getenv('NODE_ID', f"friday-{str(uuid.uuid4())[:8]}")
        self.discovered_nodes = {}
    
    def register_node(self, hostname, ip_address, port=5000):
        """Register this node"""
        node = DistributedNode(
            node_id=self.node_id,
            hostname=hostname,
            ip_address=ip_address,
            port=port,
            is_active=True
        )
        db.session.add(node)
        db.session.commit()
        logger.info(f"Node registered: {self.node_id}")
    
    def discover_nodes(self):
        """Discover other nodes on the network"""
        nodes = DistributedNode.query.filter(
            DistributedNode.node_id != self.node_id,
            DistributedNode.is_active == True
        ).all()
        return [{"node_id": n.node_id, "ip": n.ip_address, "port": n.port} for n in nodes]
    
    def split_knowledge_base(self):
        """Split knowledge base randomly across nodes"""
        nodes = DistributedNode.query.filter(DistributedNode.is_active == True).all()
        if not nodes:
            return
        
        knowledge_items = KnowledgeBase.query.all()
        import random
        random.shuffle(knowledge_items)
        
        items_per_node = len(knowledge_items) // len(nodes)
        for idx, node in enumerate(nodes):
            start = idx * items_per_node
            end = start + items_per_node if idx < len(nodes) - 1 else len(knowledge_items)
            
            for item in knowledge_items[start:end]:
                item.node_id = node.node_id
            
            logger.info(f"Assigned {end - start} items to {node.node_id}")
        
        db.session.commit()

node_manager = DistributedNodeManager()

# ============================================================================
# MULTI-AGENT SYSTEM
# ============================================================================

class AgentOrchestrator:
    def __init__(self):
        self.agents = {
            'research': self.research_agent,
            'memory': self.memory_agent,
            'task': self.task_agent,
            'web_search': self.web_search_agent
        }
    
    def research_agent(self, query):
        """Research agent - gathers information"""
        prompt = f"Research and provide detailed information about: {query}"
        result = ollama_client.generate(prompt)
        return result.get('response', 'No response')
    
    def memory_agent(self, query):
        """Memory agent - stores and retrieves knowledge"""
        knowledge = KnowledgeBase.query.filter_by(category='memory').first()
        if knowledge:
            return f"Retrieved from memory: {knowledge.content}"
        return "No memory found"
    
    def task_agent(self, query):
        """Task agent - executes tasks"""
        prompt = f"Execute this task: {query}"
        result = ollama_client.generate(prompt)
        return result.get('response', 'Task completed')
    
    def web_search_agent(self, query):
        """Web search agent - searches the web"""
        return f"Web search results for: {query}"
    
    def orchestrate(self, query):
        """Orchestrate all agents"""
        results = {}
        for agent_type, agent_func in self.agents.items():
            try:
                results[agent_type] = agent_func(query)
            except Exception as e:
                results[agent_type] = f"Error: {str(e)}"
        return results

orchestrator = AgentOrchestrator()

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main application"""
    return send_from_directory('static', 'index.html')

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    ollama_status = ollama_client.health_check()
    return jsonify({
        'status': 'ok',
        'ollama': 'connected' if ollama_status else 'disconnected',
        'node_id': node_manager.node_id
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint"""
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Orchestrate agents
    agent_results = orchestrator.orchestrate(user_message)
    
    # Generate final response
    combined_prompt = f"User asked: {user_message}\n\nAgent results:\n"
    for agent_type, result in agent_results.items():
        combined_prompt += f"{agent_type}: {result}\n"
    
    final_response = ollama_client.generate(combined_prompt)
    
    return jsonify({
        'message': user_message,
        'response': final_response.get('response', 'No response'),
        'agents': agent_results
    })

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get all agents"""
    agents = Agent.query.all()
    return jsonify([{
        'id': a.id,
        'type': a.agent_type,
        'status': a.status,
        'node_id': a.node_id,
        'last_activity': a.last_activity.isoformat()
    } for a in agents])

@app.route('/api/agents/<int:agent_id>/status', methods=['PUT'])
def update_agent_status(agent_id):
    """Update agent status"""
    data = request.json
    agent = Agent.query.get(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    agent.status = data.get('status', agent.status)
    agent.last_activity = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Get all distributed nodes"""
    nodes = DistributedNode.query.all()
    return jsonify([{
        'node_id': n.node_id,
        'hostname': n.hostname,
        'ip_address': n.ip_address,
        'port': n.port,
        'is_active': n.is_active,
        'last_heartbeat': n.last_heartbeat.isoformat()
    } for n in nodes])

@app.route('/api/knowledge', methods=['GET'])
def get_knowledge():
    """Get knowledge base"""
    knowledge = KnowledgeBase.query.all()
    return jsonify([{
        'id': k.id,
        'content': k.content,
        'category': k.category,
        'node_id': k.node_id,
        'confidence': k.confidence
    } for k in knowledge])

@app.route('/api/knowledge', methods=['POST'])
def add_knowledge():
    """Add to knowledge base"""
    data = request.json
    knowledge = KnowledgeBase(
        content=data.get('content', ''),
        category=data.get('category', 'general'),
        node_id=node_manager.node_id,
        confidence=data.get('confidence', 0.5)
    )
    db.session.add(knowledge)
    db.session.commit()
    
    return jsonify({'success': True, 'id': knowledge.id})

@app.route('/api/ollama/models', methods=['GET'])
def get_ollama_models():
    """Get available Ollama models"""
    models = ollama_client.list_models()
    return jsonify(models)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Server error'}), 500

# ============================================================================
# INITIALIZATION
# ============================================================================

def init_app():
    """Initialize the application"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Register this node
        import socket
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        node_manager.register_node(hostname, ip_address)
        
        # Create default agents
        for agent_type in ['research', 'memory', 'task', 'web_search']:
            existing = Agent.query.filter_by(
                agent_type=agent_type,
                node_id=node_manager.node_id
            ).first()
            if not existing:
                agent = Agent(
                    agent_type=agent_type,
                    status='idle',
                    node_id=node_manager.node_id
                )
                db.session.add(agent)
        
        db.session.commit()
        logger.info("Application initialized")

if __name__ == '__main__':
    init_app()
    app.run(debug=False, host='0.0.0.0', port=5000)
