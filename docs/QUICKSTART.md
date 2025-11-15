# Aurora Q&A System - Quick Start Guide

## ⚡ 5-Minute Setup (Local)

### 1. Clone Repository
```bash
git clone <your-repo>
cd aurora_assessment
```

### 2. Get OpenRouter API Key
Visit https://openrouter.ai and create an account (free)
Navigate to API Keys section and create a new API key

### 3. Setup Environment
```bash
cp .env.example .env
# Edit .env and add your API key:
# OPENROUTER_API_KEY=your_api_key_here
```

### 4. Setup Virtual Environment & Install
```bash
# Activate virtual environment (already created)
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Run Application
```bash
# Make sure you're in the project root
python -m src.main
# OR use the convenience script
./run.sh
```

### 6. Open Browser
```
http://localhost:8000
```

Done! 🎉

**Note:** On first run, models will be downloaded to `data/models/` folder. This may take a few minutes.

---

## 🐳 Using Docker (Easiest)

### Using Docker Compose
```bash
cd docker
docker-compose up
```

### Manual Docker Build
```bash
cd docker
docker build -f Dockerfile -t aurora-qa ..
docker run -p 8000:8000 --env-file ../.env aurora-qa
```

### Using Docker Hub Image
```bash
docker pull vivektiwari007/aurora-qa-system:latest
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_api_key_here \
  vivektiwari007/aurora-qa-system:latest
```

---

## 🚀 Deploy to Render.com (Free)

### 1. Prepare GitHub
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Go to Render.com
- Sign up (free)
- Click "New Web Service"
- Connect GitHub

### 3. Configure
- **Build Command:** (auto)
- **Start Command:** `cd src && python main.py`
- **Environment:** Add `OPENROUTER_API_KEY=your_api_key_here`

### 4. Deploy
Click "Create Web Service" and wait ~3-5 minutes

Your app will be live at: `https://aurora-qa-system.onrender.com`

---

## 📚 Project Structure

```
aurora_assessment/
├── src/                 # Python source code
│   ├── __init__.py
│   ├── main.py         # FastAPI server
│   └── qa_system.py    # Question-answering logic
├── static/              # Frontend files
│   └── index.html      # Chatbot UI
├── docker/              # Docker configuration
│   ├── Dockerfile      # Container configuration
│   └── docker-compose.yml # Docker Compose config
├── docs/                # Documentation
│   ├── README.md       # Project documentation
│   └── QUICKSTART.md    # This file
├── data/                # Downloaded models and data (created automatically)
│   └── models/         # ML models stored here
├── logs/                # Application logs
├── venv/                # Python virtual environment
├── requirements.txt     # Python dependencies
└── .env.example        # Configuration template
```

---

## 🔑 OpenRouter API Key

### Get Free API Key
1. Go to https://openrouter.ai
2. Sign in or create an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

### Configure API Key
Add in `.env`:
```
OPENROUTER_API_KEY=your_api_key_here
```

**Note**: The system uses the `moonshotai/kimi-k2:free` model, which is available for free on OpenRouter.

---

## 🧪 Test It

### Via Web Interface
```
http://localhost:8000
```

### Via API
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "When is Layla planning her trip?"}'
```

---

## 🛠️ Common Commands

```bash
# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Local development
python -m src.main
# OR
cd src && python main.py

# Run with auto-reload
cd src && uvicorn main:app --reload

# Docker Compose
cd docker && docker-compose up

# Manual Docker build
cd docker
docker build -f Dockerfile -t aurora-qa ..
docker run -p 8000:8000 --env-file ../.env aurora-qa

# Check API status
curl http://localhost:8000/api/health -X POST

# Get system stats
curl http://localhost:8000/api/stats
```

---

## 📱 Frontend Features

✨ Modern chatbot interface  
💬 Real-time message delivery  
🎯 Confidence scoring  
📚 Source attribution  
📱 Mobile responsive  
⚡ Smooth animations  

---

## 🚨 Troubleshooting

### API key not found?
- Check `.env` file exists
- Verify `OPENROUTER_API_KEY` is set
- Get your API key from https://openrouter.ai

### Connection error?
- Check internet connection
- Verify Aurora API is accessible
- Check firewall/proxy settings

### Slow startup?
- Normal on first run (downloads models to `data/models/`)
- Takes ~2 minutes first time
- Faster on subsequent runs (uses cached models)

### Docker build fails?
- Make sure you're in the `docker/` directory
- Check all files are present
- Try: `docker build --no-cache -f Dockerfile -t aurora-qa ..`

### Import errors?
- Make sure you're running from project root or src directory
- Ensure virtual environment is activated
- Try: `python -m src.main` from project root

---

## 📊 What You Get

✅ Chatbot interface for asking questions  
✅ OpenRouter integration with moonshotai/kimi-k2:free model  
✅ Semantic search with embeddings  
✅ Answer generation with confidence scores  
✅ Source attribution  
✅ All models stored locally in `data/` folder  
✅ Ready for production deployment  

---

## 🎯 Next Steps

1. ✅ Setup locally and test
2. ✅ Deploy to Render.com
3. ✅ Share your deployment URL
4. ✅ Monitor performance
5. ✅ Monitor API usage on OpenRouter dashboard

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Activate venv | `source venv/bin/activate` |
| Install deps | `pip install -r requirements.txt` |
| Run | `python -m src.main` or `./run.sh` |
| Test | `curl http://localhost:8000/api/health -X POST` |
| Docker Compose | `cd docker && docker-compose up` |
| Docker Build | `cd docker && docker build -f Dockerfile -t aurora-qa ..` |
| Docker Run | `docker run -p 8000:8000 --env-file ../.env aurora-qa` |
| Stats | `curl http://localhost:8000/api/stats` |

---

## 🔗 Useful Links

- Render.com: https://render.com
- Google AI: https://ai.google.dev
- FastAPI: https://fastapi.tiangolo.com/

---

**Ready to launch?** Start with the 5-minute setup above! 🚀
