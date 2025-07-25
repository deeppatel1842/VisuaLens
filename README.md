
# VisuaLens - Visual Question Answering System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Ollama](https://img.shields.io/badge/Ollama-LLaVA-orange.svg)](https://ollama.ai)


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


## 🔄 System Workflow

<p align="center">
  <img src="https://github.com/deeppatel1842/VisuaLens/blob/main/VisuaLens_workflow.png" alt="Workflow Diagram" width="700"/>
</p>

---

## 🖼️ Sample Output

<p align="center">
  <img src="https://github.com/deeppatel1842/VisuaLens/blob/main/Output/output_1.png" alt="Sample Output" width="700"/>
</p>

---
## ⚡ Quick Start

```bash
# Clone repo
git clone https://github.com/deeppatel1842/VisuaLens.git
cd VisuaLens

# Setup virtual environment
python -m venv visualens_env
# Windows
visualens_env\Scripts\activate
# macOS/Linux
source visualens_env/bin/activate

# Install requirements
pip install -r requirements.txt

# Start Ollama and pull models
ollama serve
ollama pull llava:13b

# Start application
python run_server.py
