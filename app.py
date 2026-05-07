"""
Friday AI v3 - Advanced with File Access
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
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        role TEXT,
        message TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_base (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        source TEXT,
        content TEXT,
        confidence REAL DEFAULT 0.5
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS agent_status (
        agent_name TEXT PRIMARY KEY,
        is_active INTEGER DEFAULT 0,
        last_run DATETIME
    )''')
    
    c.execute('CREATE INDEX IF NOT EXISTS idx_chat_role ON chat_history(role)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge_base(source)')
    
    conn.commit()

def save_chat(role, message):
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO chat_history (role, message) VALUES (?, ?)', (role, message))
    conn.commit()

def get_chat_history(limit=20):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT role, message FROM chat_history ORDER BY id DESC LIMIT ?', (limit,))
    messages = [dict(row) for row in c.fetchall()]
    return list(reversed(messages))

def save_knowledge(source, content, confidence=0.7):
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO knowledge_base (source, content, confidence) VALUES (?, ?, ?)', 
              (source, content, confidence))
    conn.commit()

def get_knowledge(limit=50):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM knowledge_base ORDER BY id DESC LIMIT ?', (limit,))
    return [dict(row) for row in c.fetchall()]

def list_files(path=None):
    """List files in a directory"""
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
        
        # Limit file size to 1MB
        if path.stat().st_size > 1024 * 1024:
            return {'error': 'File too large (max 1MB)'}
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return {'content': content, 'path': str(path)}
    except Exception as e:
        return {'error': str(e)}

def scrape_web_fast(query):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(
            f"https://duckduckgo.com/html/?q={query}",
            headers=headers,
            timeout=5
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for result in soup.find_all('a', {'class': 'result__a'})[:2]:
            title = result.get_text(strip=True)
            href = result.get('href')
            if title and href and len(title) > 5:
                save_knowledge(href, title, 0.7)
    except:
        pass

def learning_agent_worker():
    while True:
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT is_active FROM agent_status WHERE agent_name = ?', ('learning_agent',))
            row = c.fetchone()
            
            if row and row['is_active']:
                history = get_chat_history(limit=3)
                if history:
                    msg = history[-1]['message']
                    if len(msg) > 15:
                        scrape_web_fast(msg[:50])
                
                c.execute('UPDATE agent_status SET last_run = ? WHERE agent_name = ?',
                        (datetime.now(), 'learning_agent'))
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
        for a in ['learning_agent', 'research_agent', 'memory_agent']:
            c.execute('INSERT OR IGNORE INTO agent_status (agent_name, is_active) VALUES (?, ?)', (a, 0))
        conn.commit()
        agents = [{'agent_name': a, 'is_active': 0} for a in ['learning_agent', 'research_agent', 'memory_agent']]
    
    return jsonify(agents), 200

@app.route('/api/agents/<name>/toggle', methods=['POST'])
def toggle_agent(name):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT is_active FROM agent_status WHERE agent_name = ?', (name,))
    row = c.fetchone()
    
    new_status = 0 if row and row['is_active'] else 1
    c.execute('INSERT OR REPLACE INTO agent_status (agent_name, is_active) VALUES (?, ?)', (name, new_status))
    conn.commit()
    
    return jsonify({'agent': name, 'is_active': new_status}), 200

@app.route('/api/knowledge', methods=['GET'])
def knowledge():
    return jsonify(get_knowledge(limit=100)), 200

@app.route('/api/files', methods=['GET'])
def files():
    """List files in directory"""
    path = request.args.get('path', None)
    return jsonify(list_files(path)), 200

@app.route('/api/files/read', methods=['POST'])
def read():
    """Read file content"""
    data = request.json
    path = data.get('path', '')
    return jsonify(read_file(path)), 200

if __name__ == '__main__':
    init_db()
    
    t = threading.Thread(target=learning_agent_worker, daemon=True)
    t.start()
    
    port = int(os.getenv('NODE_PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
