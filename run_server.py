#!/usr/bin/env python3
"""
VisuaLens Unified Server Startup Script
Starts both backend API and frontend servers simultaneously
"""

import sys
import os
import asyncio
import uvicorn
import threading
import time
import http.server
import socketserver
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from config.settings import settings, create_directories
from loguru import logger


def setup_logging():
    """Configure logging for the server"""
    # Remove default logger
    logger.remove()
    
    # Console logging
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # File logging
    log_file = project_root / "logs" / "server.log"
    log_file.parent.mkdir(exist_ok=True)
    
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )


def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn ASGI server'),
        ('PIL', 'PIL/Pillow for image processing'),
        ('httpx', 'HTTP client for Ollama'),
        ('pydantic', 'Data validation'),
        ('loguru', 'Logging')
    ]
    
    missing = []
    
    for module, description in required_modules:
        try:
            __import__(module)
            logger.info(f"[OK] {description} available")
        except ImportError:
            missing.append((module, description))
            logger.error(f"[ERROR] {description} missing")
    
    if missing:
        logger.error("Missing dependencies:")
        for module, description in missing:
            logger.error(f"  - {module}: {description}")
        logger.error("Install missing dependencies with:")
        logger.error(f"  pip install {' '.join(m[0] for m in missing)}")
        return False
    
    return True


async def check_ollama_connection():
    """Check if Ollama server is accessible"""
    try:
        from src.utils.ollama_client import OllamaVisionClient
        
        client = OllamaVisionClient()
        is_healthy = await client.health_check()
        
        if is_healthy:
            logger.info("Connected to Ollama server successfully")
            
            # Get available models
            models = await client.list_models()
            if models:
                logger.info(f"Available models: {models}")
            else:
                logger.warning("No vision models found - you may need to install llava")
                logger.info("Install with: ollama pull llava")
        else:
            logger.warning("Ollama server not accessible")
            logger.info("Make sure Ollama is running: ollama serve")
        
        return is_healthy
        
    except Exception as e:
        logger.error(f"Ollama connection failed: {e}")
        logger.info("Ensure Ollama is installed and running")
        return False


def create_server_config():
    """Create uvicorn server configuration"""
    return {
        "app": "src.api.main:app",
        "host": settings.host,
        "port": settings.port,
        "reload": settings.debug,
        "log_level": "info" if not settings.debug else "debug",
        "access_log": True,
        "use_colors": True,
        "loop": "auto"
    }


def start_frontend_server():
    """Start the frontend server in a separate thread"""
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            # Suppress default logging to avoid spam
            pass
    
    try:
        with socketserver.TCPServer(("localhost", 3000), QuietHTTPRequestHandler) as httpd:
            logger.info("Frontend server started on http://localhost:3000")
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            logger.warning("Frontend port 3000 already in use - frontend may already be running")
        else:
            logger.error(f"Failed to start frontend server: {e}")
    except Exception as e:
        logger.error(f"Frontend server error: {e}")


def open_browser():
    """Open browser to the application after a delay"""
    import webbrowser
    time.sleep(3)  # Wait for servers to start
    try:
        webbrowser.open("http://localhost:3000")
        logger.info("Opened browser to http://localhost:3000")
    except Exception as e:
        logger.info("Could not auto-open browser - please manually open http://localhost:3000")


async def startup_checks():
    """Run all startup checks"""
    logger.info("VisuaLens Server Starting...")
    logger.info("=" * 50)
    
    # Check dependencies
    logger.info("Checking dependencies...")
    if not check_dependencies():
        return False
    
    # Check Ollama
    logger.info("Checking Ollama connection...")
    ollama_ok = await check_ollama_connection()
    
    # Create necessary directories
    logger.info("Setting up directories...")
    create_directories()
    
    # Log configuration
    logger.info("Server Configuration:")
    logger.info(f"  Host: {settings.host}")
    logger.info(f"  Port: {settings.port}")
    logger.info(f"  Debug: {settings.debug}")
    logger.info(f"  Upload dir: {settings.upload_dir}")
    logger.info(f"  Logs dir: {settings.log_file}")
    
    logger.info("=" * 50)
    
    if not ollama_ok:
        logger.warning("Starting without Ollama connection")
        logger.warning("Some features may not work until Ollama is available")
    
    return True


def main():
    """Main entry point - starts both backend and frontend servers"""
    # Setup logging first
    setup_logging()
    
    # Run startup checks
    if not asyncio.run(startup_checks()):
        logger.error("Startup checks failed")
        sys.exit(1)
    
    # Get server configuration
    config = create_server_config()
    
    # Start servers
    logger.info("Starting VisuaLens Unified Server...")
    logger.info("=" * 50)
    logger.info(f"Backend API: http://{config['host']}:{config['port']}")
    logger.info("Frontend App: http://localhost:3000")
    logger.info("API Documentation: http://localhost:8000/docs")
    logger.info("To stop servers: Ctrl+C")
    logger.info("=" * 50)
    
    try:
        # Start frontend server in a separate thread
        frontend_thread = threading.Thread(target=start_frontend_server, daemon=True)
        frontend_thread.start()
        
        # Start browser opener in a separate thread
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start backend server (this will block)
        logger.info("Starting backend server...")
        uvicorn.run(**config)
        
    except KeyboardInterrupt:
        logger.info("Servers stopped by user")
        logger.info("Thank you for using VisuaLens!")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
