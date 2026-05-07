"""
Friday AI v3 - Complete Backend with All Features
"""

import os
import sqlite3
import threading
import time
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import logging
import random

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

OLLAMA_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')
DB_PATH = 'friday_ai.db'

_db_conn = None

def get_db():
    global _db_conn
    if _db_conn is None:
        _db_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _db_conn.row_factory = sqlite3.Row
    return _db_conn

def init_db():
    """Initialize database with all tables"""
    conn = get_db()
    c = conn.cursor()
    
    # Chat history
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        role TEXT,
        message TEXT
    )''')
    
    # Knowledge base
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_base (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        source TEXT,
        content TEXT,
        confidence REAL DEFAULT 0.5
    )''')
    
    # Agent status
    c.execute('''CREATE TABLE IF NOT EXISTS agent_status (
        agent_name TEXT PRIMARY KEY,
        is_active INTEGER DEFAULT 0,
        status TEXT DEFAULT 'idle',
        last_run DATETIME,
        knowledge_count INTEGER DEFAULT 0
    )''')
    
    # Agent activity log
    c.execute('''CREATE TABLE IF NOT EXISTS agent_activity (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        agent_name TEXT,
        action TEXT,
        result TEXT
    )''')
    
    # Distributed nodes
    c.execute('''CREATE TABLE IF NOT EXISTS distributed_nodes (
        id INTEGER PRIMARY KEY,
        node_id TEXT UNIQUE,
        hostname TEXT,
        ip_address TEXT,
        port INTEGER,
        is_active INTEGER DEFAULT 1,
        last_heartbeat DATETIME
    )''')
    
    # Indexes
    c.execute('CREATE INDEX IF NOT EXISTS idx_chat_role ON chat_history(role)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge_base(source)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_agent_activity ON agent_activity(agent_name)')
    
    conn.commit()

def save_chat(role, message):
    """Save chat message"""
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO chat_history (role, message) VALUES (?, ?)', (role, message))
    conn.commit()

def get_chat_history(limit=50):
    """Get chat history"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT role, message, timestamp FROM chat_history ORDER BY id DESC LIMIT ?', (limit,))
    messages = [dict(row) for row in c.fetchall()]
    return list(reversed(messages))

def save_knowledge(source, content, confidence=0.7):
    """Save knowledge"""
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO knowledge_base (source, content, confidence) VALUES (?, ?, ?)', 
              (source, content, confidence))
    conn.commit()

def get_knowledge(limit=100):
    """Get knowledge base"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM knowledge_base ORDER BY id DESC LIMIT ?', (limit,))
    return [dict(row) for row in c.fetchall()]

def log_agent_activity(agent_name, action, result):
    """Log agent activity"""
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO agent_activity (agent_name, action, result) VALUES (?, ?, ?)',
              (agent_name, action, result))
    conn.commit()

def get_agent_activity(limit=50):
    """Get agent activity"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM agent_activity ORDER BY id DESC LIMIT ?', (limit,))
    return [dict(row) for row in c.fetchall()]

def get_brain_state():
    """Get current brain state for visualization"""
    conn = get_db()
    c = conn.cursor()
    
    # Get agent statuses
    c.execute('SELECT agent_name, is_active, status FROM agent_status')
    agents = [dict(row) for row in c.fetchall()]
    
    # Get recent activity
    c.execute('SELECT agent_name, action FROM agent_activity ORDER BY id DESC LIMIT 20')
    activities = [dict(row) for row in c.fetchall()]
    
    # Get knowledge count
    c.execute('SELECT COUNT(*) as count FROM knowledge_base')
    knowledge_count = c.fetchone()['count']
    
    return {
        'agents': agents,
        'activities': activities,
        'knowledge_count': knowledge_count,
        'timestamp': datetime.now().isoformat()
    }

def list_files(path=None):
    """List files in directory"""
    try:
        if path is None:
            path = str(Path.home())
        
        path = Path(path)
        if not path.exists():
            return {'error': 'Path does not exist'}
        
        if not path.is_dir():
            return {'error': 'Not a directory'}
        
        items = []
        for item in path.iterdir():
            try:
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'dir' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else 0
                })
            except:
                pass
        
        return {
            'path': str(path),
            'items': sorted(items, key=lambda x: (x['type'] != 'dir', x['name']))
        }
    except Exception as e:
        return {'error': str(e)}

def read_file(path):
    """Read file content"""
    try:
        path = Path(path)
        if not path.exists():
            return {'error': 'File does not exist'}
        
        if not path.is_file():
            return {'error': 'Not a file'}
        
        if path.stat().st_size > 1024 * 1024:
            return {'error': 'File too large (max 1MB)'}
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return {'content': content, 'path': str(path)}
    except Exception as e:
        return {'error': str(e)}

def scrape_web_fast(query):
    """Fast web scraping"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(
            f"https://duckduckgo.com/html/?q={query}",
            headers=headers,
            timeout=5
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for result in soup.find_all('a', {'class': 'result__a'})[:3]:
            title = result.get_text(strip=True)
            href = result.get('href')
            if title and href and len(title) > 5:
                save_knowledge(href, title, 0.7)
                log_agent_activity('learning_agent', 'web_scrape', f'Found: {title[:50]}')
    except:
        pass

def learning_agent_worker():
    """24/7 learning agent"""
    while True:
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT is_active FROM agent_status WHERE agent_name = ?', ('learning_agent',))
            row = c.fetchone()
            
            if row and row['is_active']:
                c.execute('UPDATE agent_status SET status = ? WHERE agent_name = ?',
                        ('researching', 'learning_agent'))
                conn.commit()
                
                history = get_chat_history(limit=3)
                if history:
                    msg = history[-1]['message']
                    if len(msg) > 15:
                        scrape_web_fast(msg[:50])
                
                c.execute('UPDATE agent_status SET last_run = ?, status = ? WHERE agent_name = ?',
                        (datetime.now(), 'idle', 'learning_agent'))
                conn.commit()
            
            time.sleep(60)
        except:
            time.sleep(60)

# Routes

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/health', methods=['GET'])
def health():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return jsonify({'status': 'ok', 'ollama': 'connected' if r.status_code == 200 else 'error'}), 200
    except:
        return jsonify({'status': 'ok', 'ollama': 'disconnected'}), 200

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        msg = data.get('message', '').strip()
        
        if not msg:
            return jsonify({'error': 'No message'}), 400
        
        save_chat('user', msg)
        
        history = get_chat_history(limit=5)
        context = "\n".join([f"{m['role']}: {m['message'][:100]}" for m in history])
        
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": f"{context}\nAssistant:", "stream": False},
                timeout=30
            )
            response = r.json().get('response', 'No response').strip() if r.status_code == 200 else "Error"
        except:
            response = "Ollama timeout"
        
        save_chat('assistant', response)
        
        return jsonify({'response': response}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
def history():
    return jsonify(get_chat_history(limit=50)), 200

@app.route('/api/agents', methods=['GET'])
def agents():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM agent_status')
    agents = [dict(row) for row in c.fetchall()]
    
    if not agents:
        for a in ['learning_agent', 'research_agent', 'memory_agent', 'web_search_agent']:
            c.execute('INSERT OR IGNORE INTO agent_status (agent_name, is_active, status) VALUES (?, ?, ?)', 
                     (a, 0, 'idle'))
        conn.commit()
        agents = [{'agent_name': a, 'is_active': 0, 'status': 'idle'} for a in ['learning_agent', 'research_agent', 'memory_agent', 'web_search_agent']]
    
    return jsonify(agents), 200

@app.route('/api/agents/<name>/toggle', methods=['POST'])
def toggle_agent(name):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT is_active FROM agent_status WHERE agent_name = ?', (name,))
    row = c.fetchone()
    
    new_status = 0 if row and row['is_active'] else 1
    c.execute('INSERT OR REPLACE INTO agent_status (agent_name, is_active, status) VALUES (?, ?, ?)', 
             (name, new_status, 'idle'))
    conn.commit()
    
    log_agent_activity(name, 'toggled', f'Status: {new_status}')
    
    return jsonify({'agent': name, 'is_active': new_status}), 200

@app.route('/api/brain', methods=['GET'])
def brain():
    """Get brain state for visualization"""
    return jsonify(get_brain_state()), 200

@app.route('/api/knowledge', methods=['GET'])
def knowledge():
    return jsonify(get_knowledge(limit=100)), 200

@app.route('/api/activity', methods=['GET'])
def activity():
    return jsonify(get_agent_activity(limit=50)), 200

@app.route('/api/files', methods=['GET'])
def files():
    path = request.args.get('path', None)
    return jsonify(list_files(path)), 200

@app.route('/api/files/read', methods=['POST'])
def read():
    data = request.json
    path = data.get('path', '')
    return jsonify(read_file(path)), 200

if __name__ == '__main__':
    init_db()
    
    t = threading.Thread(target=learning_agent_worker, daemon=True)
    t.start()
    
    port = int(os.getenv('NODE_PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
