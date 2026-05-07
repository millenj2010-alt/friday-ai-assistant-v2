"""
Friday AI v3 - Advanced Distributed AI Assistant
Python Flask Backend with Ollama Integration and 24/7 Learning Agent
"""

import os
import json
import sqlite3
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configuration
OLLAMA_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')
DB_PATH = 'friday_ai.db'

# Global state
learning_agent_active = False
learning_agent_thread = None

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Chat history
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        role TEXT,
        message TEXT
    )''')
    
    # Knowledge base
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_base (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        source TEXT,
        content TEXT,
        confidence REAL DEFAULT 0.5
    )''')
    
    # Agent status
    c.execute('''CREATE TABLE IF NOT EXISTS agent_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT UNIQUE,
        is_active INTEGER DEFAULT 0,
        last_run DATETIME,
        last_error TEXT
    )''')
    
    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def save_chat(role, message):
    """Save chat message"""
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO chat_history (role, message) VALUES (?, ?)', (role, message))
    conn.commit()
    conn.close()

def get_chat_history(limit=50):
    """Get chat history"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM chat_history ORDER BY timestamp DESC LIMIT ?', (limit,))
    messages = [dict(row) for row in c.fetchall()]
    conn.close()
    return list(reversed(messages))

def save_knowledge(source, content, confidence=0.5):
    """Save knowledge"""
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO knowledge_base (source, content, confidence) VALUES (?, ?, ?)', 
              (source, content, confidence))
    conn.commit()
    conn.close()

def get_knowledge(limit=100):
    """Get knowledge base"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM knowledge_base ORDER BY timestamp DESC LIMIT ?', (limit,))
    knowledge = [dict(row) for row in c.fetchall()]
    conn.close()
    return knowledge

def scrape_web(query, max_results=3):
    """Scrape web for knowledge"""
    try:
        # Use DuckDuckGo
        search_url = f"https://duckduckgo.com/html/?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = []
        for result in soup.find_all('a', {'class': 'result__a'})[:max_results]:
            title = result.get_text(strip=True)
            href = result.get('href')
            if title and href and len(title) > 5:
                results.append({'title': title, 'url': href})
                save_knowledge(source=href, content=title, confidence=0.7)
        
        return results
    except Exception as e:
        logger.error(f"Web scraping error: {e}")
        return []

def learning_agent_worker():
    """24/7 learning agent"""
    global learning_agent_active
    
    while True:
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT is_active FROM agent_status WHERE agent_name = ?', ('learning_agent',))
            row = c.fetchone()
            conn.close()
            
            is_active = row['is_active'] if row else 0
            
            if is_active:
                # Get recent chat
                history = get_chat_history(limit=5)
                if history:
                    for msg in history:
                        if msg['role'] == 'user' and len(msg['message']) > 10:
                            logger.info(f"Learning: Scraping for '{msg['message'][:40]}'")
                            scrape_web(msg['message'], max_results=2)
                
                # Update last run
                conn = get_db()
                c = conn.cursor()
                c.execute('UPDATE agent_status SET last_run = ? WHERE agent_name = ?',
                        (datetime.now(), 'learning_agent'))
                conn.commit()
                conn.close()
            
            time.sleep(30)
        except Exception as e:
            logger.error(f"Learning agent error: {e}")
            time.sleep(60)

def init_agents():
    """Initialize agents"""
    conn = get_db()
    c = conn.cursor()
    
    agents = ['learning_agent', 'research_agent', 'memory_agent']
    for agent in agents:
        c.execute('INSERT OR IGNORE INTO agent_status (agent_name, is_active) VALUES (?, ?)',
                 (agent, 0))
    
    conn.commit()
    conn.close()

# Routes

@app.route('/')
def index():
    """Main page"""
    return app.send_static_file('index.html')

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        ollama_ok = response.status_code == 200
    except:
        ollama_ok = False
    
    return jsonify({
        'status': 'ok',
        'ollama': 'connected' if ollama_ok else 'disconnected'
    }), 200

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message'}), 400
        
        # Save user message
        save_chat('user', user_message)
        
        # Get context from history
        history = get_chat_history(limit=5)
        context = "\n".join([f"{m['role']}: {m['message']}" for m in history])
        
        # Generate response
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": f"{context}\nAssistant:",
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result.get('response', 'No response').strip()
            else:
                assistant_message = "Ollama error. Make sure Ollama is running."
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            assistant_message = f"Error: {str(e)}"
        
        # Save assistant message
        save_chat('assistant', assistant_message)
        
        return jsonify({
            'response': assistant_message,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
def chat_history():
    """Get chat history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        history = get_chat_history(limit=limit)
        return jsonify(history), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get agents"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM agent_status')
        agents = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(agents), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/<agent_name>/toggle', methods=['POST'])
def toggle_agent(agent_name):
    """Toggle agent"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT is_active FROM agent_status WHERE agent_name = ?', (agent_name,))
        row = c.fetchone()
        
        if row:
            new_status = 1 - row['is_active']
            c.execute('UPDATE agent_status SET is_active = ? WHERE agent_name = ?',
                     (new_status, agent_name))
        else:
            new_status = 1
            c.execute('INSERT INTO agent_status (agent_name, is_active) VALUES (?, ?)',
                     (agent_name, new_status))
        
        conn.commit()
        conn.close()
        
        return jsonify({'agent': agent_name, 'is_active': new_status}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge', methods=['GET'])
def knowledge():
    """Get knowledge"""
    try:
        limit = request.args.get('limit', 100, type=int)
        knowledge = get_knowledge(limit=limit)
        return jsonify(knowledge), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge/clear', methods=['POST'])
def clear_knowledge():
    """Clear knowledge"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM knowledge_base')
        conn.commit()
        conn.close()
        return jsonify({'status': 'cleared'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize
    init_db()
    init_agents()
    
    # Start learning agent
    learning_thread = threading.Thread(target=learning_agent_worker, daemon=True)
    learning_thread.start()
    
    # Run app
    port = int(os.getenv('NODE_PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
