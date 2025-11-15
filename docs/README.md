# Aurora Q&A System

An intelligent question-answering system powered by FastAPI, Sentence Transformers, FAISS, and OpenRouter AI.

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
│   ├── README.md          # This file
│   ├── QUICKSTART.md      # Quick start guide
│   └── RENDER_DEPLOYMENT.md # Deployment guide
├── data/                   # Data storage (auto-created)
│   └── models/            # ML models cache (SentenceTransformers, etc.)
├── logs/                   # Application logs (auto-created)
├── venv/                   # Python virtual environment
├── requirements.txt        # Python dependencies
├── render.yaml            # Render.com deployment config
├── .gitignore             # Git ignore rules
├── .env.example           # Environment variables template
└── run.sh                 # Convenience run script
```

## ✨ Features

- **RAG-based Q&A**: Retrieval-Augmented Generation for accurate answers
- **Semantic Search**: FAISS vector database for fast similarity search
- **OpenRouter Integration**: Powered by moonshotai/kimi-k2:free model via OpenRouter
- **Local Model Storage**: All models downloaded to `data/models/` folder
- **Modern UI**: Beautiful, responsive chatbot interface
- **Production Ready**: Docker support and deployment configurations

## 🚀 Quick Start

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

### Basic Setup

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file with your OpenRouter API key
echo "OPENROUTER_API_KEY=your_api_key_here" > .env

# 4. Run the application
python -m src.main
```

Visit `http://localhost:8000` to use the chatbot interface.

## 📦 Dependencies

- **FastAPI**: Modern web framework
- **Sentence Transformers**: Embedding models
- **FAISS**: Vector similarity search
- **OpenRouter API**: LLM integration via OpenRouter (moonshotai/kimi-k2:free model)
- **Uvicorn**: ASGI server

See `requirements.txt` for complete list.

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_api_key_here
PORT=8000
LOG_LEVEL=INFO
```

### Model Storage

All models are automatically stored in the `data/models/` directory:
- SentenceTransformer models
- HuggingFace transformers cache
- PyTorch models

This ensures all downloads stay within the project folder.

## 🐳 Docker

### Build and Run with Docker Compose

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

## 📡 API Endpoints

- `GET /` - Web interface
- `GET /api` - API health check
- `POST /api/ask` - Ask a question
- `GET /api/stats` - System statistics
- `POST /api/health` - Detailed health check

### Example API Usage

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "When is Layla planning her trip to London?"}'
```

## 🧪 Development

### Running in Development Mode

```bash
source venv/bin/activate
cd src
uvicorn main:app --reload
```

### Project Organization

- **src/**: All Python source code
- **static/**: Frontend files (HTML, CSS, JS)
- **docker/**: Docker configuration files
- **docs/**: Documentation
- **data/**: All downloaded models and data (gitignored)
- **logs/**: Application logs (gitignored)

## 🤔 Alternative Approaches Considered

During the design phase, several architectural approaches were evaluated:

### 1. **Pure LLM Approach (Rejected)**
**Concept**: Send all messages directly to the LLM with each query.
- ✅ **Pros**: Simple implementation, no need for embeddings or vector DB
- ❌ **Cons**: 
  - Expensive (every query incurs full context cost)
  - Slow (large prompt processing time)
  - Context window limitations (can't scale beyond ~128k tokens)
  - No caching or optimization possible

### 2. **BM25/TF-IDF Retrieval (Rejected)**
**Concept**: Use traditional keyword-based search (BM25) instead of semantic embeddings.
- ✅ **Pros**: Fast, lightweight, no model downloads required
- ❌ **Cons**: 
  - Misses semantic similarity ("restaurant" vs "dining")
  - Poor with synonyms and paraphrasing
  - Requires exact keyword matches
  - Can't handle questions in different forms

### 3. **SQLite Full-Text Search (Rejected)**
**Concept**: Store messages in SQLite with FTS5 for text search.
- ✅ **Pros**: Structured storage, good for exact matches
- ❌ **Cons**: 
  - Limited semantic understanding
  - Requires complex query rewriting
  - Poor handling of natural language questions
  - Similar limitations to BM25

### 4. **Hybrid RAG (Current Implementation)** ✅
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

### 5. **Fine-tuned Model Approach (Future Enhancement)**
**Concept**: Fine-tune a smaller model (Llama 2, Phi-3) specifically on member data.
- ✅ **Potential Pros**: 
  - No API dependency
  - Consistent answers
  - Lower per-query cost
- ❌ **Challenges**: 
  - Requires significant labeled training data
  - Complex training pipeline
  - Model hosting infrastructure needed
  - Difficult to update with new data

### 6. **Graph Database Approach (Considered)**
**Concept**: Model members, locations, events as a knowledge graph (Neo4j, NetworkX).
- ✅ **Pros**: 
  - Explicit relationships
  - Complex query capabilities
  - Good for "who knows who" questions
- ❌ **Cons**: 
  - Requires manual schema design
  - Complex extraction from unstructured text
  - Overhead for simple retrieval
  - Poor with ambiguous or informal text

**Decision**: The hybrid RAG approach was chosen for its balance of semantic understanding, speed, and answer quality. It provides conversational responses while maintaining accuracy through structured fact extraction and fallback mechanisms.

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
- **No conversation threads**: Messages are independent, no back-and-forth dialogue
- **Synthetic patterns**: Consistent formatting suggests generated rather than organic data

### Data Characteristics for QA System

**Positive Aspects**:
- Clean, well-structured data requires minimal preprocessing
- Consistent naming helps with entity extraction
- Request/statement format makes semantic search effective
- No missing or corrupted data to handle

**Challenges**:
- Limited context per member (5-16 messages) means sparse information
- Similar phrasing across messages can lead to multiple similar results
- No explicit relationships or metadata (e.g., trip companions, dates)
- Temporal information is sometimes vague ("first week of December" vs specific dates)

### Impact on System Design

The dataset characteristics influenced several design decisions:
1. **Critical keyword filtering**: Required to prevent name confusion (e.g., searching "Layla" shouldn't return "Lily")
2. **Structured fact extraction**: Needed to parse locations, dates, and restaurants from free text
3. **Fallback mechanisms**: Essential since LLM may not always be available
4. **Conversational rephrasing**: Necessary to avoid returning raw booking requests as answers

## 📝 Notes

- First run will download models (~2 minutes)
- Models are cached in `data/models/` for faster subsequent runs
- FAISS index is saved to `data/faiss_index.bin`
- All downloads are contained within the project folder

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

[Add your license here]

## 🔗 Links

- [Quick Start Guide](QUICKSTART.md)
- [Google AI Studio](https://ai.google.dev)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
