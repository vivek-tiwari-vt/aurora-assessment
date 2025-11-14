# Project Structure

This document describes the reorganized project structure.

## 📁 Directory Layout

```
aurora_assessment/
├── src/                      # Python source code
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application
│   └── qa_system.py         # Q&A system logic
│
├── static/                   # Frontend files
│   └── index.html           # Chatbot web interface
│
├── docker/                   # Docker configuration files
│   ├── Dockerfile           # Docker container config
│   └── docker-compose.yml   # Docker Compose config
│
├── docs/                     # Documentation
│   ├── README.md            # Project documentation
│   ├── QUICKSTART.md        # Quick start guide
│   └── RENDER_DEPLOYMENT.md # Deployment guide
│
├── data/                     # Data storage (auto-created, gitignored)
│   └── models/              # ML models cache
│       └── (SentenceTransformers, HuggingFace models stored here)
│
├── logs/                     # Application logs (auto-created, gitignored)
│
├── venv/                     # Python virtual environment (gitignored)
│   ├── bin/                 # Virtual environment executables
│   ├── lib/                 # Installed packages
│   └── pyvenv.cfg           # Virtual environment config
│
├── .gitignore               # Git ignore rules
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
├── render.yaml              # Render.com deployment config
├── run.sh                   # Convenience run script
└── STRUCTURE.md             # This file
```

## 🔄 Changes Made

### 1. **Reorganized Source Code**
   - Moved `main.py` → `src/main.py`
   - Moved `qa_system.py` → `src/qa_system.py`
   - Created `src/__init__.py` for proper package structure

### 2. **Created Virtual Environment**
   - Created `venv/` directory in project root
   - Virtual environment is ready to use

### 3. **Local Data Storage**
   - Created `data/` directory for all downloads
   - Models stored in `data/models/`
   - FAISS index saved to `data/faiss_index.bin`
   - All downloads stay within project folder

### 4. **Organized Configuration Files**
   - Moved Docker files to `docker/` folder
   - Moved documentation to `docs/` folder
   - Updated all references to new paths

### 5. **Documentation**
   - All documentation in `docs/` folder
   - Updated paths in all documentation files
   - Created `run.sh` for easy execution

## 🚀 Running the Application

### Option 1: Using the run script
```bash
./run.sh
```

### Option 2: Manual activation
```bash
source venv/bin/activate
python -m src.main
```

### Option 3: From src directory
```bash
source venv/bin/activate
cd src
python main.py
```

## 🐳 Docker Commands

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

## 📦 Data Storage

All downloads are stored locally in the project:

- **Models**: `data/models/`
  - SentenceTransformer models
  - HuggingFace transformers cache
  - PyTorch models

- **Indexes**: `data/faiss_index.bin`
  - FAISS vector index

- **Logs**: `logs/`
  - Application logs

## 🔒 Git Ignore

The following are excluded from version control:
- `venv/` - Virtual environment
- `data/` - Downloaded models and data
- `logs/` - Application logs
- `.env` - Environment variables (contains secrets)
- `__pycache__/` - Python cache files
- `*.pyc` - Compiled Python files

## ✅ Benefits

1. **Better Organization**: Clear separation of source, static, data, docker, and docs
2. **Local Storage**: All downloads contained in project folder
3. **Virtual Environment**: Isolated Python environment
4. **Docker Ready**: Organized Docker files in dedicated folder
5. **Documentation**: All docs in one place
6. **Git Friendly**: Proper .gitignore to exclude large files
