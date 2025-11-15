# Aurora Q&A System

An intelligent question-answering system powered by FastAPI, Sentence Transformers, FAISS, and OpenRouter AI. This RAG (Retrieval-Augmented Generation) system provides conversational answers to questions about member messages and preferences.

## 🚀 Quick Start

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file with your OpenRouter API key
echo "OPENROUTER_API_KEY=your_api_key_here" > .env

# 4. Run the application
python src/main.py
```

Visit `http://localhost:8000` to use the chatbot interface.

## ✨ Features

- **RAG-based Q&A**: Retrieval-Augmented Generation for accurate, conversational answers
- **Semantic Search**: FAISS vector database for fast similarity search
- **Conversational Responses**: Natural language answers instead of raw data dumps
- **OpenRouter Integration**: Powered by moonshotai/kimi-k2:free model via OpenRouter
- **Fallback Mechanisms**: Works even when LLM is unavailable
- **Structured Fact Extraction**: Parses locations, dates, restaurants from messages
- **Local Model Storage**: All models downloaded to `data/models/` folder
- **Modern UI**: Beautiful, responsive chatbot interface
- **Production Ready**: Docker support and deployment configurations

## 📦 Architecture

```
┌─────────────┐
│   Frontend  │  (Static HTML/CSS/JS)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         FastAPI Server              │
│  ┌─────────────────────────────┐   │
│  │   Question Processing       │   │
│  │  - Keyword Extraction       │   │
│  │  - Entity Recognition       │   │
│  └────────────┬────────────────┘   │
│               ▼                     │
│  ┌─────────────────────────────┐   │
│  │   FAISS Vector Search       │   │
│  │  - Semantic Similarity      │   │
│  │  - Top-K Retrieval          │   │
│  └────────────┬────────────────┘   │
│               ▼                     │
│  ┌─────────────────────────────┐   │
│  │   Structured Extraction     │   │
│  │  - Restaurants              │   │
│  │  - Locations                │   │
│  │  - Time Phrases             │   │
│  └────────────┬────────────────┘   │
│               ▼                     │
│  ┌─────────────────────────────┐   │
│  │   Answer Generation         │   │
│  │  - OpenRouter LLM (primary)  │   │
│  │  - Structured Fallback      │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## 🎯 Example Queries

The system handles various question types:

**Location Questions:**
```
Q: "Where is Layla going?"
A: "Layla is planning to visit Santorini, Cannes, and Thailand."
```

**Restaurant Questions:**
```
Q: "What are Layla's favorite restaurants?"
A: "Layla has mentioned dining at Le Bernardin and Alinea."
```

**Time-based Questions:**
```
Q: "When is Layla going to Santorini?"
A: "Layla has planned a trip to Santorini for first week of December."
```

**Unsupported Questions (Graceful Handling):**
```
Q: "How many cars does Vikram Desai have?"
A: "I don't have enough information to answer this question."
```

## 🤔 Alternative Approaches Considered

During the design phase, several architectural approaches were evaluated:

### 1. **Pure LLM Approach** (Rejected)
**Concept**: Send all messages directly to the LLM with each query.
- ✅ **Pros**: Simple implementation, no need for embeddings or vector DB
- ❌ **Cons**: 
  - Expensive (every query incurs full context cost)
  - Slow (large prompt processing time)
  - Context window limitations (can't scale beyond ~128k tokens)
  - No caching or optimization possible

### 2. **BM25/TF-IDF Retrieval** (Rejected)
**Concept**: Use traditional keyword-based search instead of semantic embeddings.
- ✅ **Pros**: Fast, lightweight, no model downloads required
- ❌ **Cons**: 
  - Misses semantic similarity ("restaurant" vs "dining")
  - Poor with synonyms and paraphrasing
  - Requires exact keyword matches

### 3. **SQLite Full-Text Search** (Rejected)
**Concept**: Store messages in SQLite with FTS5 for text search.
- ✅ **Pros**: Structured storage, good for exact matches
- ❌ **Cons**: 
  - Limited semantic understanding
  - Requires complex query rewriting
  - Poor handling of natural language questions

### 4. **Hybrid RAG** (✅ Current Implementation)
**Concept**: Semantic embeddings (FAISS) + structured fact extraction + LLM generation.
- ✅ **Pros**: 
  - Semantic understanding of questions
  - Fast vector similarity search
  - Structured fact extraction for consistent answers
  - Graceful fallback when LLM unavailable
  - Conversational, context-aware responses
- ⚠️ **Trade-offs**: 
  - Initial model download (~500MB)
  - Requires embedding generation at startup
  - More complex codebase

### 5. **Fine-tuned Model Approach** (Future Enhancement)
**Concept**: Fine-tune a smaller model (Llama 2, Phi-3) specifically on member data.
- ✅ **Potential Pros**: No API dependency, consistent answers
- ❌ **Challenges**: Requires significant training data, complex training pipeline

### 6. **Graph Database Approach** (Considered)
**Concept**: Model members, locations, events as a knowledge graph.
- ✅ **Pros**: Explicit relationships, complex query capabilities
- ❌ **Cons**: Requires manual schema design, complex extraction

**Decision**: The hybrid RAG approach was chosen for its balance of semantic understanding, speed, and answer quality.

## 📊 Dataset Analysis

**Dataset Size**: 100 messages from 10 unique members

### Member Distribution
- **Most Active**: Sophia Al-Farsi (16 messages), Fatima El-Tahir (15 messages)
- **Least Active**: Amina Van Den Berg (5 messages)
- **Average**: 10 messages per member

### Data Quality Assessment

✅ **Strengths**:
- **Complete fields**: All 100 messages have user_name, user_id, timestamp, and message content
- **Consistent format**: Uniform JSON structure across all messages
- **Reasonable message length**: Average 63.6 characters (range: 47-84 chars)
- **Appropriate date range**: 2024-11-14 to 2025-11-04 (realistic span)
- **No duplicates**: Each message is unique
- **Clean user IDs**: Each member has a consistent UUID

⚠️ **Observations**:
- **Uniform length**: All messages fall in a narrow 47-84 character range, suggesting synthetic/templated data
- **Consistent tone**: All messages follow similar formal, request-based patterns
- **Limited variety**: Messages primarily fall into 3 categories:
  1. Booking requests (restaurants, travel, accommodation)
  2. Thank you notes/feedback
  3. Preference statements

### Impact on System Design

The dataset characteristics influenced several design decisions:
1. **Critical keyword filtering**: Required to prevent name confusion (e.g., searching "Layla" shouldn't return "Lily")
2. **Structured fact extraction**: Needed to parse locations, dates, and restaurants from free text
3. **Fallback mechanisms**: Essential since LLM may not always be available
4. **Conversational rephrasing**: Necessary to avoid returning raw booking requests as answers

## 🏗️ Project Structure

```
aurora_assessment/
├── src/                    # Python source code
│   ├── __init__.py
│   ├── main.py            # FastAPI application entry point
│   └── qa_system.py       # Core Q&A system with RAG implementation
├── static/                 # Frontend static files
│   └── index.html         # Chatbot web interface
├── docker/                 # Docker configuration
│   ├── Dockerfile         # Docker container configuration
│   └── docker-compose.yml # Docker Compose configuration
├── docs/                   # Documentation
│   ├── README.md          # Detailed documentation
│   ├── QUICKSTART.md      # Quick start guide
│   └── RENDER_DEPLOYMENT.md # Deployment guide
├── data/                   # Data storage (auto-created)
│   ├── models/            # ML models cache
│   └── faiss_index.bin    # Vector database index
├── logs/                   # Application logs (auto-created)
├── requirements.txt        # Python dependencies
├── render.yaml            # Render.com deployment config
├── .env                   # Environment variables (create this)
└── README.md              # This file
```

## 📡 API Endpoints

- `GET /` - Web interface
- `GET /api` - API health check
- `POST /api/ask` - Ask a question
- `GET /api/stats` - System statistics
- `POST /api/health` - Detailed health check

### Example API Usage

```bash
# Ask a question
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Where is Layla going?"}'

# Get system stats
curl http://localhost:8000/api/stats
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required: OpenRouter API key
OPENROUTER_API_KEY=your_api_key_here

# Optional
PORT=8000
LOG_LEVEL=INFO
```

### Getting OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai)
2. Sign in or create an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

**Note**: The system uses the `moonshotai/kimi-k2:free` model, which is available for free on OpenRouter.

## 🐳 Docker Deployment

### Option 1: Docker Compose (Recommended)

```bash
cd docker
docker-compose up
```

### Option 2: Manual Docker Build

```bash
cd docker
docker build -f Dockerfile -t aurora-qa ..
docker run -p 8000:8000 --env-file ../.env aurora-qa
```

## 🧪 Development

### Running in Development Mode

```bash
source venv/bin/activate
export LOG_LEVEL=DEBUG
python src/main.py
# Or with auto-reload
cd src
uvicorn main:app --reload --log-level debug
```

### Testing

```bash
# Test the API
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What restaurants has Layla mentioned?"}'

# Check system health
curl http://localhost:8000/api/health
```

## 📦 Dependencies

### Core Dependencies
- **FastAPI** (0.115.6): Modern web framework for building APIs
- **Sentence Transformers** (3.3.1): Generate semantic embeddings
- **FAISS** (1.9.0.post1): Fast vector similarity search
- **OpenRouter API**: LLM integration via OpenRouter (moonshotai/kimi-k2:free model)
- **Uvicorn** (0.34.0): ASGI server for FastAPI

### Supporting Libraries
- **httpx**: Async HTTP client for API calls
- **numpy**: Numerical computing for embeddings
- **python-dotenv**: Environment variable management

See `requirements.txt` for complete list with versions.

## 🚀 Deployment

### Deploy to Render.com

1. Fork this repository
2. Connect to Render.com
3. Create a new Web Service
4. Set environment variables:
   - `OPENROUTER_API_KEY` - Your OpenRouter API key
5. Deploy!

See [RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md) for detailed instructions.

### Deploy with Docker

```bash
# Build
docker build -t aurora-qa .

# Run
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_api_key_here \
  vivektiwari007/aurora-qa-system:latest

# Or pull from Docker Hub
docker pull vivektiwari007/aurora-qa-system:latest
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_api_key_here \
  vivektiwari007/aurora-qa-system:latest
```

## 📝 Key Features Explained

### 1. Semantic Search with FAISS
- Converts questions and messages into 384-dimensional embeddings
- Uses cosine similarity to find relevant messages
- Stores index in `data/faiss_index.bin` for fast startup

### 2. Critical Keyword Filtering
- Extracts proper nouns and locations from questions
- Ensures retrieved messages actually mention the asked-about entities
- Prevents confusion between similar names (Layla vs Lily)

### 3. Structured Fact Extraction
- Identifies restaurants, locations, time phrases in messages
- Uses regex patterns and keyword lists for extraction
- Classifies messages as requests, preferences, or gratitude

### 4. Conversational Answer Generation
- Primary: Uses OpenRouter API with moonshotai/kimi-k2:free model for natural language generation
- Fallback: Structured template-based answers when LLM unavailable
- Filters out irrelevant information (generic thanks, etc.)

## 🔍 Troubleshooting

### Common Issues

**Models not downloading:**
```bash
# Check internet connection
# Ensure data/models/ directory is writable
mkdir -p data/models
chmod 755 data/models
```

**Port already in use:**
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
# Or change port
PORT=8001 python src/main.py
```

**API key errors:**
```bash
# Verify .env file exists and has API key
cat .env
# Check environment variables are loaded
python -c "import os; print(os.getenv('OPENROUTER_API_KEY'))"
```

**Slow startup:**
- First run downloads ~500MB of models (2-3 minutes)
- Subsequent runs use cached models (~10 seconds)

## 📚 Documentation

- [Quick Start Guide](docs/QUICKSTART.md) - Get started in 5 minutes
- [Detailed README](docs/README.md) - Comprehensive documentation
- [Render Deployment](docs/RENDER_DEPLOYMENT.md) - Deploy to production

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is provided as-is for assessment purposes.

## 🔗 Links

- [OpenRouter.ai](https://openrouter.ai) - Get OpenRouter API key
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss)

---

**Built with ❤️ using FastAPI, FAISS, and OpenRouter AI**

**Docker Image**: `vivektiwari007/aurora-qa-system:latest` - Available on [Docker Hub](https://hub.docker.com/r/vivektiwari007/aurora-qa-system)

