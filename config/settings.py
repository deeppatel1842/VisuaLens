"""
VisuaLens Configuration Settings
Central configuration management for the VisuaLens Visual Q&A System
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Info
    app_name: str = "VisuaLens"
    app_version: str = "1.0.0"
    description: str = "Single Image Visual Q&A System using Ollama"
    
    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    reload: bool = True
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llava:13b"
    ollama_alternative_model: str = "llava:latest"
    ollama_timeout: int = 60
    ollama_max_retries: int = 3
    
    # Image Processing Settings
    max_image_size_mb: int = 10
    max_image_dimension: int = 1024
    allowed_image_formats: list = ["JPEG", "PNG", "WebP", "JPG"]
    image_quality: int = 85
    
    # File Upload Settings
    upload_dir: str = "uploads"
    temp_dir: str = "temp"
    cleanup_interval_minutes: int = 60
    
    # Session Management
    session_timeout_minutes: int = 30
    max_history_length: int = 50
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/visualens.log"
    log_rotation: str = "10 MB"
    log_retention: str = "7 days"
    
    # Security Settings
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    max_question_length: int = 500
    rate_limit_per_minute: int = 60
    
    # Performance Settings
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 120
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def create_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        settings.upload_dir,
        settings.temp_dir,
        "logs",
        "frontend/assets"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


if __name__ == "__main__":
    # Test configuration
    print(f"App: {settings.app_name} v{settings.app_version}")
    print(f"Ollama URL: {settings.ollama_base_url}")
    print(f"Model: {settings.ollama_model}")
    print(f"Upload dir: {settings.upload_dir}")
