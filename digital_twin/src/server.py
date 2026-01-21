"""
FastAPI inference server for digital twin AI.
Provides API endpoints for generating replies with RAG augmentation.
"""
import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn
from dotenv import load_dotenv

# Import RAG and LLM components
from src.rag import DigitalTwinRAG, build_rag_chain

load_dotenv()

# Configuration
API_KEY = os.getenv("API_KEY", "")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
INFERENCE_ENGINE = os.getenv("INFERENCE_ENGINE", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
VLLM_HOST = os.getenv("VLLM_HOST", "0.0.0.0")
VLLM_PORT = int(os.getenv("VLLM_PORT", "8001"))

# Initialize FastAPI app
app = FastAPI(
    title="Digital Twin AI API",
    description="API for generating personalized replies that mimic communication style",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize RAG system
rag_system = None
llm = None
rag_chain = None


def get_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Validate API key if configured."""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key or ""


def initialize_llm():
    """Initialize LLM based on inference engine."""
    global llm, rag_chain
    
    if INFERENCE_ENGINE == "ollama":
        try:
            from langchain_ollama import OllamaLLM
            llm = OllamaLLM(
                model="digital_twin",  # Assumes model is loaded in Ollama
                base_url=OLLAMA_BASE_URL,
                temperature=0.7,
                top_p=0.9,
            )
            print(f"✅ Initialized Ollama LLM at {OLLAMA_BASE_URL}")
        except Exception as e:
            print(f"⚠️ Failed to initialize Ollama: {e}")
            print("Make sure Ollama is running and model is loaded: ollama pull digital_twin")
            llm = None
    
    elif INFERENCE_ENGINE == "vllm":
        try:
            from langchain_community.llms import VLLM
            llm = VLLM(
                model="models/digital_twin",  # Path to model
                trust_remote_code=True,
                max_new_tokens=512,
                temperature=0.7,
            )
            print(f"✅ Initialized vLLM")
        except Exception as e:
            print(f"⚠️ Failed to initialize vLLM: {e}")
            llm = None
    
    else:
        raise ValueError(f"Unknown inference engine: {INFERENCE_ENGINE}")
    
    if llm:
        rag_chain = build_rag_chain(llm, rag_system)


# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global rag_system
    
    print("🚀 Starting Digital Twin API Server...")
    
    # Initialize RAG
    try:
        rag_system = DigitalTwinRAG()
        print("✅ RAG system initialized")
    except Exception as e:
        print(f"⚠️ Failed to initialize RAG: {e}")
        rag_system = None
    
    # Initialize LLM
    try:
        initialize_llm()
    except Exception as e:
        print(f"⚠️ LLM initialization failed: {e}")


# Request/Response models
class GenerateRequest(BaseModel):
    """Request model for generating replies."""
    context: str = Field(..., description="User context/query to respond to")
    use_rag: bool = Field(True, description="Whether to use RAG for retrieval")
    max_length: Optional[int] = Field(512, description="Maximum response length")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")


class GenerateResponse(BaseModel):
    """Response model for generated replies."""
    reply: str = Field(..., description="Generated reply")
    retrieved_examples: Optional[int] = Field(None, description="Number of RAG examples used")
    model: str = Field(..., description="Model used for generation")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    rag_initialized: bool
    llm_initialized: bool
    inference_engine: str


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with health check."""
    return HealthResponse(
        status="healthy",
        rag_initialized=rag_system is not None,
        llm_initialized=llm is not None,
        inference_engine=INFERENCE_ENGINE
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return await root()


@app.post("/generate", response_model=GenerateResponse)
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def generate_reply(
    request: GenerateRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Generate a reply that mimics the target person's communication style.
    
    Args:
        request: GenerateRequest with context and options
        api_key: API key for authentication (if configured)
    
    Returns:
        GenerateResponse with generated reply
    """
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Check inference engine configuration."
        )
    
    if not rag_system and request.use_rag:
        raise HTTPException(
            status_code=503,
            detail="RAG system not initialized. Run index_dataset() first."
        )
    
    try:
        if request.use_rag and rag_system:
            # Use RAG-augmented generation
            context = rag_system.get_retrieval_context(request.context)
            prompt = context["prompt"]
            num_examples = context["num_examples"]
        else:
            # Direct generation without RAG
            from src.rag import DigitalTwinRAG
            temp_rag = DigitalTwinRAG()
            prompt = temp_rag.build_prompt(request.context, retrieved_examples=None)
            num_examples = 0
        
        # Generate reply
        response = llm.invoke(prompt)
        
        # Truncate if needed
        if request.max_length and len(response) > request.max_length:
            response = response[:request.max_length]
        
        return GenerateResponse(
            reply=response.strip(),
            retrieved_examples=num_examples if request.use_rag else None,
            model=INFERENCE_ENGINE
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )


@app.get("/retrieve")
async def retrieve_similar(
    query: str,
    k: int = 5,
    api_key: str = Depends(get_api_key)
):
    """
    Retrieve similar past communications (RAG retrieval).
    
    Args:
        query: Search query
        k: Number of results
        api_key: API key for authentication
    
    Returns:
        List of similar documents
    """
    if not rag_system:
        raise HTTPException(
            status_code=503,
            detail="RAG system not initialized"
        )
    
    try:
        results = rag_system.retrieve_similar(query, k=k)
        return {
            "query": query,
            "results": [
                {
                    "content": doc.page_content[:500],
                    "metadata": doc.metadata
                }
                for doc in results
            ],
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )