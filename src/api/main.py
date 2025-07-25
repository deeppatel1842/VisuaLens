"""
VisuaLens FastAPI Application
Main backend server with endpoin        # Initialize Q&A engine
        logger.info("Initializing Q&A engine...")
        qa_engine = await create_qa_engine(ollama_client=ollama_client)
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        # Don't raise - let the app start without Q&A functionality
        logger.warning("Starting in limited mode without Q&A functionality")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown completed")load, Q&A processing, and session management
"""

import os
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# FastAPI and related imports
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn

# Logging
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Local imports
from config.settings import settings, create_directories
from src.models.schemas import (
    VisionQARequest, QAResponse, UploadResponse, HistoryResponse, 
    HealthCheckResponse, ErrorResponse, create_success_response, create_error_response
)
from src.processing.qa_engine import create_qa_engine
from src.utils.ollama_client import create_ollama_client

# Global variables for dependency injection
qa_engine = None
ollama_client = None
session_storage = {}  # Simple in-memory storage for demo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global qa_engine, ollama_client
    
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Create necessary directories
    create_directories()
    
    # Configure logging
    logger.add(
        settings.log_file,
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    
    try:
        # Initialize Ollama client
        logger.info("Initializing Ollama client...")
        ollama_client = await create_ollama_client()
        
        # Initialize Q&A engine
        logger.info("Initializing Q&A engine...")
        qa_engine = await create_qa_engine(ollama_client=ollama_client)
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        # Don't raise - let the app start without Q&A functionality
        logger.warning("Starting in limited mode without Q&A functionality")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Cleanup sessions
    session_manager.cleanup_old_sessions(max_age_minutes=0)  # Clean all
    
    logger.info("✅ Application shutdown completed")


# Initialize the FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class SessionManager:
    """Simple session management for tracking Q&A history"""
    
    def __init__(self):
        self.sessions = {}
    
    def create_session(self) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'id': session_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'history': [],
            'question_count': 0,
            'total_tokens': 0
        }
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID"""
        return self.sessions.get(session_id)
    
    def update_session_activity(self, session_id: str):
        """Update last activity timestamp"""
        if session_id in self.sessions:
            self.sessions[session_id]['last_activity'] = datetime.now()
    
    def add_qa_to_session(self, session_id: str, qa_data: Dict[str, Any]):
        """Add Q&A pair to session history"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session['history'].append(qa_data)
            session['question_count'] += 1
            session['total_tokens'] += qa_data.get('tokens', {}).get('total', 0)
            self.update_session_activity(session_id)
    
    def cleanup_old_sessions(self, max_age_minutes: int = 60):
        """Remove sessions older than max_age_minutes"""
        current_time = datetime.now()
        to_remove = []
        
        for session_id, session in self.sessions.items():
            age = (current_time - session['last_activity']).total_seconds() / 60
            if age > max_age_minutes:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")
        
        return len(to_remove)


# Initialize session manager
session_manager = SessionManager()


# Dependency functions
async def get_qa_engine():
    """Dependency to get Q&A engine"""
    if qa_engine is None:
        raise HTTPException(status_code=503, detail="Q&A engine not initialized")
    return qa_engine


async def get_ollama_client():
    """Dependency to get Ollama client"""
    if ollama_client is None:
        raise HTTPException(status_code=503, detail="Ollama client not initialized")
    return ollama_client


def get_session_manager():
    """Dependency to get session manager"""
    return session_manager


# API Endpoints

@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "description": settings.description,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint to verify system status"""
    try:
        if ollama_client is None:
            return HealthCheckResponse(
                status="limited",
                base_url=settings.ollama_base_url,
                error="Ollama client not initialized - running in limited mode"
            )
        
        # Check Ollama server health
        health_result = await ollama_client.health_check()
        
        # Get available models
        models = await ollama_client.list_models()
        model_names = [m.get('name', 'unknown') for m in models]
        
        return HealthCheckResponse(
            status=health_result['status'],
            server_info=health_result.get('server_info'),
            base_url=health_result.get('base_url', ollama_client.base_url),
            models=model_names
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="error",
            base_url=settings.ollama_base_url,
            error=str(e)
        )


@app.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload and process an image file
    Handles validation, processing, and temporary storage
    """
    start_time = time.time()
    
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {file.content_type}. Only images are allowed."
            )
        
        # Check file size
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > settings.max_image_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size} bytes. Maximum: {settings.max_image_size_mb}MB"
            )
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Process image (this will be implemented in the image processing module)
        from src.processing.image_processor import process_uploaded_image
        
        processing_result = await process_uploaded_image(
            image_data=contents,
            filename=file.filename,
            content_type=file.content_type,
            image_id=image_id
        )
        
        if not processing_result['success']:
            raise HTTPException(
                status_code=400,
                detail=f"Image processing failed: {processing_result.get('error')}"
            )
        
        # Schedule cleanup of temporary files
        background_tasks.add_task(
            cleanup_temp_files, 
            image_id, 
            delay_minutes=settings.cleanup_interval_minutes
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Image uploaded and processed: {image_id} ({processing_time:.2f}s)")
        
        return UploadResponse(
            success=True,
            image_id=image_id,
            filename=processing_result.get('filename'),
            processing_info=processing_result.get('processing_info'),
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return UploadResponse(
            success=False,
            error="Upload processing failed",
            details=str(e)
        )


@app.post("/ask", response_model=QAResponse)
async def ask_question(
    file: UploadFile = File(...),
    question: str = Form(...),
    system_prompt: Optional[str] = Form(None),
    use_alternative_model: bool = Form(False),
    session_id: Optional[str] = Form(None),
    engine: Any = Depends(get_qa_engine),
    sessions: SessionManager = Depends(get_session_manager)
):
    """
    Ask a question about an uploaded image
    Combines image and question processing
    """
    start_time = time.time()
    
    try:
        # Create or validate session
        if not session_id:
            session_id = sessions.create_session()
        elif not sessions.get_session(session_id):
            session_id = sessions.create_session()
        
        # Read image data
        image_data = await file.read()
        
        # Validate image
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}"
            )
        
        # Process the question
        logger.info(f"Processing question in session {session_id}: {question[:50]}...")
        
        result = await engine.ask_question(
            question=question,
            image_data=image_data,
            system_prompt=system_prompt,
            use_alternative_model=use_alternative_model,
            session_id=session_id
        )
        
        # Add to session history if successful
        if result.success:
            qa_data = {
                'id': str(uuid.uuid4()),
                'question': question,
                'answer': result.answer,
                'model': result.model,
                'timestamp': result.timestamp,
                'response_time': result.response_time,
                'tokens': result.tokens.dict() if result.tokens else None,
                'image_size': len(image_data)
            }
            
            sessions.add_qa_to_session(session_id, qa_data)
        
        total_time = time.time() - start_time
        logger.info(f"Question processed in {total_time:.2f}s")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question processing failed: {e}")
        return create_error_response(
            error="Question processing failed",
            details=str(e),
            response_class=QAResponse
        )


@app.get("/history", response_model=HistoryResponse) 
async def get_session_history(
    session_id: Optional[str] = None,
    limit: int = 50,
    sessions: SessionManager = Depends(get_session_manager)
):
    """
    Get Q&A history for a session
    """
    try:
        if not session_id:
            # Return empty history
            return HistoryResponse(
                success=True,
                history=[],
                total_items=0
            )
        
        session = sessions.get_session(session_id)
        if not session:
            return HistoryResponse(
                success=False,
                error="Session not found",
                details=f"Session {session_id} does not exist or has expired"
            )
        
        # Get limited history
        history = session['history'][-limit:] if limit else session['history']
        
        from src.models.schemas import SessionInfo, HistoryItem
        
        session_info = SessionInfo(
            session_id=session['id'],
            created_at=session['created_at'],
            last_activity=session['last_activity'],
            question_count=session['question_count'],
            total_tokens=session['total_tokens']
        )
        
        history_items = [
            HistoryItem(**item) for item in history
        ]
        
        return HistoryResponse(
            success=True,
            session=session_info,
            history=history_items,
            total_items=len(session['history'])
        )
        
    except Exception as e:
        logger.error(f"History retrieval failed: {e}")
        return HistoryResponse(
            success=False,
            error="Failed to retrieve history",
            details=str(e)
        )


@app.post("/session/new")
async def create_new_session(
    sessions: SessionManager = Depends(get_session_manager)
):
    """Create a new session"""
    try:
        session_id = sessions.create_session()
        return {
            "success": True,
            "session_id": session_id,
            "message": "New session created"
        }
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")


@app.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    sessions: SessionManager = Depends(get_session_manager)
):
    """Delete a session"""
    try:
        if session_id in sessions.sessions:
            del sessions.sessions[session_id]
            return {
                "success": True,
                "message": f"Session {session_id} deleted"
            }
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session deletion failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")


# Utility functions

async def cleanup_temp_files(image_id: str, delay_minutes: int = 60):
    """Background task to cleanup temporary files"""
    import asyncio
    await asyncio.sleep(delay_minutes * 60)  # Convert to seconds
    
    # This would cleanup temporary files associated with image_id
    logger.info(f"Cleaned up temporary files for image: {image_id}")


# Mount static files for frontend (will be used in Phase 3)
if Path("frontend").exists():
    app.mount("/static", StaticFiles(directory="frontend"), name="static")


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Endpoint not found",
            "details": f"The requested endpoint {request.url.path} was not found"
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": "An unexpected error occurred. Please try again later."
        }
    )


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
