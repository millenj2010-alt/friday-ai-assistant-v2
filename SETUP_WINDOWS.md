# Friday AI v3 - Python Edition - Windows Setup Guide

## ✨ The Good News

This version of Friday AI runs on **Python only** - NO Node.js, NO Docker required!

## 🚀 Quick Start (3 Steps)

### Step 1: Install Python (One-time)

1. Download Python from: https://www.python.org/downloads/
2. Run the installer
3. **IMPORTANT**: Check the box "Add Python to PATH"
4. Click "Install Now"
5. Wait for installation to complete
6. Restart your computer

### Step 2: Install Ollama (One-time)

1. Download Ollama from: https://ollama.ai
2. Run the installer
3. Click "Next" → "Next" → Finish
4. Ollama will start automatically
5. Wait for it to finish loading

### Step 3: Run Friday AI

1. Extract this folder anywhere on your computer
2. **Double-click `run.bat`**
3. Wait for it to say "Starting Friday AI on http://localhost:5000"
4. Open your browser to: **http://localhost:5000**
5. Click "Login with Manus"
6. Start chatting with Friday!

That's it! 🎉

## 📋 What You Need

- **Windows 10 or later**
- **Python 3.8+** (from python.org)
- **Ollama** (from ollama.ai)
- **~2GB free disk space**
- **Internet connection** (for first setup)

## 🔧 Manual Setup (If run.bat doesn't work)

### Step 1: Open Command Prompt

1. Press `Win + R`
2. Type `cmd`
3. Press Enter

### Step 2: Navigate to Friday AI folder

```
cd C:\Users\YourUsername\Downloads\friday-ai-python
```

(Replace the path with where you extracted the folder)

### Step 3: Install dependencies

```
pip install -r requirements.txt
```

### Step 4: Run the app

```
python app.py
```

### Step 5: Open in browser

Go to: http://localhost:5000

## 🐛 Troubleshooting

### "Python is not installed"
- Download Python from https://www.python.org/downloads/
- **Important**: Check "Add Python to PATH" during installation
- Restart your computer
- Try again

### "Ollama is not running"
- Download Ollama from https://ollama.ai
- Install it
- Make sure it's running (check system tray)
- Try again

### "Failed to install dependencies"
- Open Command Prompt
- Run: `pip install --upgrade pip`
- Then: `pip install -r requirements.txt`

### "Port 5000 is already in use"
- Open Command Prompt
- Run: `netstat -ano | findstr :5000`
- Find the PID and close that application
- Try again

### Browser shows "Cannot connect"
- Make sure the command window is still running
- Check that it says "Running on http://localhost:5000"
- Try refreshing the browser (F5)

## 📖 Using Friday AI

### Login
- Click "Login with Manus"
- Enter your credentials

### Chat
- Type your question in the chat box
- Press Enter or click Send
- Friday will respond using the Ollama AI

### Brain Visualization
- Watch the animated neural network
- See agents working in real-time
- Monitor agent status (idle, thinking, researching, sharing knowledge)

### Multi-Device Setup
- Run this on multiple computers
- They will automatically discover each other
- Knowledge will be split across all devices
- Reduces storage on each computer

## 🎯 Features

✅ Local AI (Ollama) - No cloud AI
✅ Multi-Agent System - Research, Memory, Task, Web Search
✅ Brain Visualization - Real-time neural network
✅ Distributed Architecture - Split knowledge across devices
✅ Auto-Discovery - Devices find each other automatically
✅ Dark Theme - Futuristic UI with glowing effects
✅ Chat Interface - Talk to Friday naturally

## 🔐 Security

- All processing is local
- No data sent to cloud
- No tracking or analytics
- Open source (check GitHub)

## 📞 Support

- **GitHub**: https://github.com/millenj2010-alt/friday-ai-assistant-v2
- **Issues**: Report bugs on GitHub
- **Documentation**: See README.md

## 🎓 Next Steps

1. **Customize Ollama Model**
   - Edit `.env` file
   - Change `OLLAMA_MODEL=mistral` to another model
   - Restart Friday AI

2. **Set Up Multiple Devices**
   - Extract Friday AI on another computer
   - Run `run.bat`
   - They'll automatically connect!

3. **Add Knowledge**
   - Chat with Friday
   - It learns and stores knowledge
   - Knowledge is shared across devices

## ⚙️ Configuration

Create a `.env` file in the Friday AI folder:

```
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=mistral
DATABASE_URL=sqlite:///friday_ai.db
NODE_ID=friday-node-1
```

## 🚀 Performance Tips

- Use SSD for faster database access
- Close other applications to free up RAM
- Use a good internet connection for first setup
- Restart Friday AI if it gets slow

---

**Enjoy Friday AI! 🧠✨**

Questions? Check the README.md or visit GitHub!
