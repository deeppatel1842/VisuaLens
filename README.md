<<<<<<< HEAD
# VisuaLens - Visual Question Answering System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Ollama](https://img.shields.io/badge/Ollama-LLaVA-orange.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A complete Visual Question Answering system that allows you to upload images and ask questions about them using AI vision models. Built with FastAPI backend, vanilla HTML/CSS/JS frontend, and powered by Ollama's LLaVA vision models.

## 🚀 Features

- **Single Command Startup**: Start both backend and frontend with one command
- **Drag & Drop Image Upload**: Intuitive image uploading interface
- **AI-Powered Analysis**: Advanced image understanding using LLaVA 13B model
- **Document Processing**: Enhanced text extraction for resumes, documents, and forms
- **Real-time Responses**: Fast processing with streaming capabilities
- **Session Management**: Track conversation history and manage multiple sessions
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Auto Browser Launch**: Automatically opens your browser to the application

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## ⚡ Quick Start

### One Command to Start Everything:

```bash
# Clone the repository
git clone https://github.com/deeppatel1842/VisuaLens.git
cd VisuaLens

# Create and activate virtual environment
python -m venv visualens_env
# Windows
visualens_env\Scripts\activate
# Linux/Mac
source visualens_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start everything (Backend + Frontend + Browser)
python run_server.py
```

**That's it!** The application will automatically:
- ✅ Start backend API server (port 8000)
- ✅ Start frontend web server (port 3000)
- ✅ Open your browser to the application
- ✅ Display all necessary URLs

## 📦 Prerequisites

### 1. Python 3.8+
Download from [python.org](https://python.org) or use your system package manager.

### 2. Ollama with LLaVA Models
```bash
# Install Ollama from https://ollama.ai
# Then pull the required models:
ollama pull llava:13b    # Primary model (8GB)
ollama pull llava:latest # Fallback model (4.7GB)

# Start Ollama service
ollama serve
```

## 🛠️ Installation

### Option 1: Clone from GitHub (Recommended)
```bash
git clone https://github.com/deeppatel1842/VisuaLens.git
cd VisuaLens
python -m venv visualens_env
visualens_env\Scripts\activate  # Windows
# or
source visualens_env/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Option 2: Download ZIP
1. Download ZIP from GitHub
2. Extract to desired location
3. Follow virtual environment setup above

## 🎯 Usage

### Starting the Application
```bash
# Make sure Ollama is running
ollama serve

# In another terminal, start VisuaLens
cd VisuaLens
visualens_env\Scripts\activate
python run_server.py
```

### Application URLs
- **Main Application**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

### Using the Interface

1. **Upload Image**: 
   - Drag and drop an image onto the upload zone
   - Or click the upload area to select a file
   - Supports: JPEG, PNG, WebP (max 10MB)

2. **Ask Questions**:
   - Type your question in the text field
   - Use suggested quick questions for common queries
   - Click "Ask Question" to get AI analysis

3. **View Results**:
   - Get detailed AI responses about your image
   - See processing time and model information
   - Export session history if needed

### Example Questions to Try:

**General Analysis:**
- "What do you see in this image?"
- "Describe the main objects and their locations"
- "What colors are most prominent?"

**Document Analysis:**
- "Is this a resume? If so, summarize the experience"
- "What text can you read in this document?"
- "Extract the key information from this form"

**Scene Understanding:**
- "What is happening in this scene?"
- "Describe the setting and environment"
- "What activities are taking place?"

## 📚 API Documentation

### Core Endpoints

#### Health Check
```http
GET /health
```
Returns server status and available models.

#### Upload Image
```http
POST /upload
Content-Type: multipart/form-data
```
Upload an image file for processing.

#### Ask Question
```http
POST /ask
Content-Type: application/json

{
  "question": "What do you see?",
  "image_data": "base64_encoded_image",
  "session_id": "optional_session_id"
}
```

#### Session Management
```http
POST /sessions          # Create new session
GET /sessions/{id}      # Get session info
DELETE /sessions/{id}   # Delete session
GET /sessions/{id}/history  # Get session history
```

For complete API documentation, visit: http://localhost:8000/docs

## 📁 Project Structure

```
VisuaLens/
├── src/                          # Backend source code
│   ├── api/                      # FastAPI application
│   │   └── main.py              # Main API endpoints
│   ├── processing/              # Core processing logic
│   │   ├── qa_engine.py         # Q&A processing engine
│   │   └── image_processor.py   # Image processing utilities
│   ├── utils/                   # Utility modules
│   │   ├── ollama_client.py     # Ollama API client
│   │   ├── text_extractor.py    # OCR and text processing
│   │   └── logger.py            # Logging configuration
│   └── models/                  # Data models and schemas
│       └── schemas.py           # Pydantic models
├── frontend/                    # Frontend application
│   ├── index.html              # Main application interface
│   ├── styles.css              # Application styling
│   ├── script.js               # Frontend logic
│   └── README.md               # Frontend documentation
├── config/                     # Configuration files
│   └── settings.py             # Application settings
├── logs/                       # Application logs
├── uploads/                    # Uploaded images storage
├── requirements.txt            # Python dependencies
├── run_server.py              # Unified server startup script
├── .gitignore                 # Git ignore patterns
└── README.md                  # This file
```

## 🔧 Troubleshooting

### Common Issues

#### 1. "Ollama server not accessible"
```bash
# Solution: Start Ollama service
ollama serve

# Verify models are available
ollama list
```

#### 2. "Port already in use"
```bash
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Kill the process or change port in config/settings.py
```

#### 3. "Module not found errors"
```bash
# Ensure virtual environment is activated
visualens_env\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 4. "Frontend not loading"
- Ensure backend started successfully (check terminal output)
- Verify frontend server is running on port 3000
- Check browser console for JavaScript errors
- Try manual navigation to http://localhost:3000

### Performance Tips:

- The first question may take longer as the AI model loads
- Larger images will take more time to process
- For better accuracy with documents, use high-resolution images

## System Requirements

- **RAM**: 8GB minimum (16GB recommended for larger models)
- **Storage**: 10GB free space for AI models
- **Network**: Internet connection for initial model download

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
5. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** for providing the excellent local AI model runtime
- **LLaVA** for the powerful vision-language models
- **FastAPI** for the robust web framework
- **Community** for feedback and contributions

---

**Built with ❤️ for the AI and computer vision community**

**Star ⭐ this repository if you find it helpful!**

## Project Structure

```
VisuaLens/
├── src/                    # Backend source code
│   ├── api/               # FastAPI endpoints
│   ├── processing/        # Image and Q&A processing
│   ├── utils/            # Utilities (Ollama client, logging)
│   └── models/           # Data models
├── frontend/              # Web interface
│   ├── index.html        # Main application
│   ├── styles.css        # Styling
│   └── script.js         # Frontend logic
├── config/               # Configuration files
├── logs/                 # Application logs
├── uploads/              # Uploaded images storage
├── requirements.txt      # Python dependencies
└── run_server.py        # Server startup script
```

## Configuration

The system is pre-configured to work out of the box. Key settings in `config/settings.py`:

- **Host**: 127.0.0.1
- **Port**: 8000
- **Ollama Model**: llava:13b (falls back to llava:latest)
- **Max Image Size**: 10MB
- **Supported Formats**: JPEG, PNG, WebP

## Troubleshooting

### Common Issues:

1. **"Ollama server not accessible"**
   - Make sure Ollama is installed and running: `ollama serve`
   - Check if models are available: `ollama list`

2. **"Port already in use"**
   - Stop any other services running on port 8000 or 3000
   - Or modify the port in the configuration

3. **"Module not found" errors**
   - Make sure the virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

4. **Frontend not loading**
   - Ensure the backend is running first
   - Check browser console for errors
   - Verify the frontend server is running on port 3000

### Performance Tips:

- The first question may take longer as the AI model loads
- Larger images will take more time to process
- For better accuracy with documents, use high-resolution images

## Features

- **Drag & Drop Upload**: Easy image uploading
- **Real-time Processing**: Instant AI responses
- **Session Management**: Track conversation history
- **Responsive Design**: Works on desktop and mobile
- **Document Analysis**: Enhanced processing for text documents
- **Error Handling**: Graceful error messages and recovery

## System Requirements

- **RAM**: 8GB minimum (16GB recommended for larger models)
- **Storage**: 10GB free space for AI models
- **Network**: Internet connection for initial model download

## Support

If you encounter issues:

1. Check the logs in the `logs/visualens.log` file
2. Ensure all prerequisites are installed
3. Verify Ollama is running and models are available
4. Check the browser developer console for frontend errors

---

**Enjoy exploring your images with AI-powered visual intelligence!**
=======
# VisuaLens
Multimodal LLM System
>>>>>>> 2362c320aa73a3a128813a7eda869bcc794c8d50
