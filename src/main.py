# Fix importlib.metadata compatibility for Python 3.9
# Ensure packages_distributions is available (needed by some dependencies)
try:
    import importlib.metadata
    if not hasattr(importlib.metadata, 'packages_distributions'):
        try:
            # Try to use the backport package if available
            import importlib_metadata
            if hasattr(importlib_metadata, 'packages_distributions'):
                importlib.metadata.packages_distributions = importlib_metadata.packages_distributions
        except ImportError:
            # If not available, create a dummy function
            def _dummy_packages_distributions():
                return {}
            importlib.metadata.packages_distributions = _dummy_packages_distributions
except Exception:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Optional
import uvicorn
from contextlib import asynccontextmanager
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to path for imports
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from qa_system import QuestionAnsweringSystem

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
STATIC_DIR = PROJECT_ROOT / "static"

# Global QA system instance
qa_system = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize QA system on startup"""
    global qa_system
    print("Initializing Question Answering System...")
    qa_system = QuestionAnsweringSystem()
    await qa_system.initialize()
    print(f"System ready with {qa_system.num_messages} messages indexed")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Aurora AI/ML Q&A System",
    description="Natural language question answering over member data",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class QuestionRequest(BaseModel):
    question: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "When is Layla planning her trip to London?"
            }
        }
    )


class AnswerResponse(BaseModel):
    answer: str
    confidence: Optional[float] = None
    sources: Optional[List[Dict]] = None


@app.get("/")
async def root():
    """Serve frontend"""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api")
async def api_info():
    """API info endpoint"""
    return {
        "status": "healthy",
        "service": "Aurora Q&A System",
        "messages_indexed": qa_system.num_messages if qa_system else 0,
        "version": "1.0.0"
    }


@app.post("/api/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Answer a natural language question about member data"""
    if not qa_system:
        raise HTTPException(status_code=503, detail="QA system not initialized")
    
    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        result = await qa_system.answer_question(request.question)
        return AnswerResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    if not qa_system:
        raise HTTPException(status_code=503, detail="QA system not initialized")
    
    return qa_system.get_stats()


@app.post("/api/health")
async def health_check():
    """Detailed health check"""
    if not qa_system:
        return {"status": "not_initialized"}
    
    return {
        "status": "healthy",
        "messages_indexed": qa_system.num_messages,
        "embedding_dimension": qa_system.embeddings.shape[1] if qa_system.embeddings is not None else 0,
        "index_built": qa_system.index is not None,
        "api_key_active": bool(qa_system.key_rotator and qa_system.key_rotator.api_key)
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

