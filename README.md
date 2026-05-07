# Friday AI v3 - Python Edition

A futuristic, distributed AI assistant with automatic brain-splitting across multiple computers, real-time agent visualization, and local Ollama inference.

**🎉 NO Node.js | NO Docker | Just Python!**

## ✨ Features

### Core Capabilities
- **Local LLM Inference**: Powered by Ollama (completely local)
- **Multi-Agent System**: Research, Memory, Task, and Web Search agents
- **Distributed Architecture**: Automatically splits knowledge across devices
- **Brain Visualization**: Real-time animated neural network
- **Auto-Discovery**: Nodes automatically find and connect
- **Knowledge Sharing**: P2P and central server sync

### User Interface
- **Dark-Themed Design**: Futuristic aesthetic with glowing effects
- **Brain Visualization**: Animated canvas showing agent activity
- **Agent Monitor**: Real-time status for all agents
- **Chat Interface**: Talk to Friday with streaming responses
- **Multi-Node Dashboard**: Monitor all connected devices
- **Responsive Design**: Works on desktop and mobile

### Deployment
- **Windows**: Just double-click `run.bat`
- **Mac/Linux**: Run `python app.py`
- **Multi-Device**: Automatic discovery and sync

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama (from https://ollama.ai)
- ~2GB free disk space

### Installation

#### Windows
1. Download and install Python from https://www.python.org
   - **Important**: Check "Add Python to PATH"
2. Download and install Ollama from https://ollama.ai
3. Extract this folder
4. **Double-click `run.bat`**
5. Open http://localhost:5000

#### Mac/Linux
```bash
# Install Python (if not already installed)
# macOS: brew install python3
# Linux: sudo apt install python3 python3-pip

# Install Ollama
# Download from https://ollama.ai

# Install dependencies
pip install -r requirements.txt

# Run Friday AI
python app.py

# Open browser
# http://localhost:5000
```

## 📁 Project Structure

```
friday-ai-python/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── run.bat               # Windows launcher
├── static/
│   ├── index.html        # Main HTML
│   ├── app.js            # Frontend JavaScript
│   └── style.css         # Styling
├── SETUP_WINDOWS.md      # Windows setup guide
└── README.md             # This file
```

## 🧠 Multi-Agent System

### Agent Types

| Agent | Role | Status |
|-------|------|--------|
| **Research** | Information gathering | idle, thinking, researching, sharing_knowledge |
| **Memory** | Knowledge storage | idle, thinking, researching, sharing_knowledge |
| **Task** | Task execution | idle, thinking, researching, sharing_knowledge |
| **Web Search** | Real-time search | idle, thinking, researching, sharing_knowledge |

### How It Works

1. User sends a query to Friday
2. Query is analyzed to determine which agents to activate
3. Agents work in parallel on their tasks
4. Results are synthesized and returned
5. High-confidence findings are stored

## 🏗️ Distributed Architecture

### Brain-Splitting

When you run Friday on multiple devices:

```
Device 1: 150 knowledge items (33%)
Device 2: 150 knowledge items (33%)
Device 3: 150 knowledge items (34%)
```

Each device stores only 1/3 of the total knowledge, reducing storage by 66%!

### Auto-Discovery

Devices automatically find each other using UDP broadcast:
- Listens on port 5353 (UDP)
- Broadcasts every 30 seconds
- Connects to discovered nodes

### Sync Protocol

**Peer-to-Peer (P2P)**
- Direct node-to-node communication
- Faster knowledge sharing
- Reduced central server load

**Central Server**
- Fallback option
- Centralized coordination
- Conflict resolution

## 🔌 API Endpoints

### Health Check
```
GET /api/health
```

### Chat
```
POST /api/chat
Body: { "message": "Your question" }
```

### Agents
```
GET /api/agents
PUT /api/agents/<id>/status
Body: { "status": "idle|thinking|researching|sharing_knowledge" }
```

### Knowledge Base
```
GET /api/knowledge
POST /api/knowledge
Body: { "content": "...", "category": "...", "confidence": 0.5 }
```

### Distributed Nodes
```
GET /api/nodes
```

### Ollama Models
```
GET /api/ollama/models
```

## ⚙️ Configuration

Create a `.env` file:

```env
# Ollama Configuration
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Database
DATABASE_URL=sqlite:///friday_ai.db

# Node Configuration
NODE_ID=friday-node-1
NODE_PORT=5000

# Flask
FLASK_ENV=production
DEBUG=False
```

## 🌐 Network Ports

| Port | Service | Protocol |
|------|---------|----------|
| 5000 | Friday UI/API | TCP |
| 5353 | Node Discovery | UDP |
| 11434 | Ollama API | TCP |

## 📊 Database Schema

### Tables
- **users**: User authentication
- **agents**: Agent definitions
- **knowledge_base**: Persistent knowledge
- **chat_history**: Conversation logs
- **distributed_nodes**: Connected devices
- **agent_activity**: Agent action logs
- **node_sync_log**: Sync history

## 🔐 Security

- ✅ Local LLM processing (no cloud AI)
- ✅ No external API calls (except Ollama)
- ✅ No tracking or analytics
- ✅ Open source and auditable
- ✅ Database encryption support

## 🐛 Troubleshooting

### "Python is not installed"
- Download from https://www.python.org
- Check "Add Python to PATH"
- Restart computer

### "Ollama is not running"
- Download from https://ollama.ai
- Install and start it
- Check system tray

### "Failed to install dependencies"
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### "Port 5000 is already in use"
```bash
# Find process using port 5000
netstat -ano | findstr :5000
# Kill the process (Windows)
taskkill /PID <PID> /F
```

## 🚀 Multi-Device Setup

### On Device 1
```bash
python app.py
```

### On Device 2
```bash
python app.py
```

### On Device 3
```bash
python app.py
```

They will automatically discover each other and split the knowledge base!

## 📈 Performance

### Storage Reduction
- 1 Device: 100% storage
- 2 Devices: 50% storage each
- 3 Devices: 33% storage each
- 4 Devices: 25% storage each

### Sync Performance
- P2P Sync: ~500ms for 150 items
- Central Sync: ~1000ms for 450 items
- Auto-Discovery: ~30 seconds

## 🎨 Customization

### Change Ollama Model
Edit `.env`:
```env
OLLAMA_MODEL=neural-chat
```

### Change Theme Colors
Edit `static/style.css`:
```css
--primary: #a855f7;  /* Change this color */
```

### Change Port
Edit `.env`:
```env
NODE_PORT=8000
```

## 📚 Documentation

- **SETUP_WINDOWS.md**: Windows setup guide
- **API.md**: API documentation (coming soon)
- **ARCHITECTURE.md**: System design (coming soon)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- Ollama for local LLM inference
- Flask for the web framework
- The open-source community

## 📞 Support

- **GitHub**: https://github.com/millenj2010-alt/friday-ai-assistant-v2
- **Issues**: Report bugs on GitHub
- **Discussions**: Ask questions

---

**Friday AI v3 - Your personal distributed AI assistant 🧠✨**

No Node.js. No Docker. Just Python. Just Friday.
