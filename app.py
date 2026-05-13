"""
Friday AI v4 - Complete Backend with All Endpoints
"""

import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

OLLAMA_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')
NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY', '')
DB_PATH = 'friday_ai.db'

_db_conn = None

def get_db():
    global _db_conn
    if _db_conn is None:
        _db_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _db_conn.row_factory = sqlite3.Row
    return _db_conn

def init_db():
    """Initialize database"""
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            content TEXT,
            role TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            fact TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            name TEXT,
            status TEXT,
            enabled BOOLEAN DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    db.commit()
    
    # Insert default agents
    try:
        db.execute('INSERT INTO agents (user_id, name, status, enabled) VALUES (1, "system", "idle", 1)')
        db.execute('INSERT INTO agents (user_id, name, status, enabled) VALUES (1, "research", "idle", 1)')
        db.execute('INSERT INTO agents (user_id, name, status, enabled) VALUES (1, "memory", "idle", 1)')
        db.execute('INSERT INTO agents (user_id, name, status, enabled) VALUES (1, "learning", "idle", 1)')
        db.commit()
    except:
        pass

init_db()

# ==================== AUTH ====================

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json or {}
        username = data.get('username', '')
        password = data.get('password', '')
        
        if username == 'admin' and password == 'friday':
            return jsonify({'success': True, 'user_id': 1, 'username': 'admin'})
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/me', methods=['GET'])
def get_me():
    return jsonify({'user_id': 1, 'username': 'admin'})

# ==================== CHAT ====================

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json or {}
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message'}), 400
        
        reply = None
        
        # Try NVIDIA API first if key is available
        if NVIDIA_API_KEY:
            try:
                logger.info(f"Trying NVIDIA API with key: {NVIDIA_API_KEY[:10]}...")
                response = requests.post(
                    'https://integrate.api.nvidia.com/v1/chat/completions',
                    headers={'Authorization': f'Bearer {NVIDIA_API_KEY}', 'Content-Type': 'application/json'},
                    json={
                        'model': 'meta/llama-2-70b-chat',
                        'messages': [{'role': 'user', 'content': message}],
                        'temperature': 0.7,
                        'max_tokens': 1024
                    },
                    timeout=60
                )
                logger.info(f"NVIDIA response status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    reply = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
                    logger.info(f"NVIDIA reply: {reply[:50]}...")
            except Exception as nvidia_error:
                logger.error(f"NVIDIA API error: {nvidia_error}")
        
        # Fall back to Ollama if NVIDIA failed or no key
        if not reply:
            try:
                logger.info(f"Trying Ollama at {OLLAMA_URL}")
                response = requests.post(
                    f'{OLLAMA_URL}/api/generate',
                    json={'model': OLLAMA_MODEL, 'prompt': message, 'stream': False},
                    timeout=60
                )
                logger.info(f"Ollama response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    reply = result.get('response', 'No response')
                    logger.info(f"Ollama reply: {reply[:50]}...")
                else:
                    logger.error(f"Ollama error: {response.status_code}")
                    reply = f"Ollama error: {response.status_code}"
            except Exception as ollama_error:
                logger.error(f"Ollama error: {ollama_error}")
                reply = f"Error: {str(ollama_error)}"
        
        if not reply:
            reply = "I'm thinking..."
        
        # Save to DB
        db = get_db()
        db.execute('INSERT INTO messages (user_id, content, role) VALUES (?, ?, ?)', 
                  (1, message, 'user'))
        db.execute('INSERT INTO messages (user_id, content, role) VALUES (?, ?, ?)', 
                  (1, reply, 'assistant'))
        db.commit()
        
        return jsonify({'reply': reply})
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    try:
        db = get_db()
        messages = db.execute('SELECT * FROM messages WHERE user_id = ? ORDER BY timestamp', (1,)).fetchall()
        return jsonify([dict(m) for m in messages])
    except Exception as e:
        logger.error(f"Get messages error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== AGENTS ====================

@app.route('/api/agents', methods=['GET'])
def get_agents():
    try:
        db = get_db()
        agents = db.execute('SELECT * FROM agents WHERE user_id = ?', (1,)).fetchall()
        return jsonify([dict(a) for a in agents])
    except Exception as e:
        logger.error(f"Get agents error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent/<name>', methods=['GET'])
def get_agent(name):
    try:
        db = get_db()
        agent = db.execute('SELECT * FROM agents WHERE user_id = ? AND name = ?', (1, name)).fetchone()
        if agent:
            return jsonify(dict(agent))
        return jsonify({'error': 'Agent not found'}), 404
    except Exception as e:
        logger.error(f"Get agent error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent/<name>/toggle', methods=['POST'])
def toggle_agent(name):
    try:
        db = get_db()
        agent = db.execute('SELECT * FROM agents WHERE user_id = ? AND name = ?', (1, name)).fetchone()
        if agent:
            new_status = 0 if agent['enabled'] else 1
            db.execute('UPDATE agents SET enabled = ? WHERE user_id = ? AND name = ?', (new_status, 1, name))
            db.commit()
            return jsonify({'success': True, 'enabled': new_status})
        return jsonify({'error': 'Agent not found'}), 404
    except Exception as e:
        logger.error(f"Toggle agent error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== MEMORY ====================

@app.route('/api/memory', methods=['GET'])
def get_memory():
    try:
        db = get_db()
        knowledge = db.execute('SELECT * FROM knowledge WHERE user_id = ? ORDER BY timestamp DESC LIMIT 50', (1,)).fetchall()
        return jsonify([dict(k) for k in knowledge])
    except Exception as e:
        logger.error(f"Get memory error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory', methods=['POST'])
def add_memory():
    try:
        data = request.json or {}
        fact = data.get('fact', '')
        
        if fact:
            db = get_db()
            db.execute('INSERT INTO knowledge (user_id, fact) VALUES (?, ?)', (1, fact))
            db.commit()
            return jsonify({'success': True})
        return jsonify({'error': 'No fact'}), 400
    except Exception as e:
        logger.error(f"Add memory error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ACTIVITY ====================

@app.route('/api/activity', methods=['GET'])
def get_activity():
    try:
        return jsonify({
            'recent': [
                {'agent': 'system', 'action': 'initialized', 'time': datetime.now().isoformat()},
                {'agent': 'learning', 'action': 'scanning web', 'time': datetime.now().isoformat()},
            ]
        })
    except Exception as e:
        logger.error(f"Get activity error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== STATUS ====================

@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        status = {'ollama': 'offline', 'nvidia': 'offline', 'models': 0}
        
        try:
            response = requests.get(f'{OLLAMA_URL}/api/tags', timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                status['ollama'] = 'online' if models else 'offline'
                status['models'] = len(models)
        except:
            pass
        
        if NVIDIA_API_KEY:
            status['nvidia'] = 'online'
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"Get status error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== STATIC ====================

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
