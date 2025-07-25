"""
Ollama Client for VisuaLens
Handles communication with the Ollama server for vision-language model inference
"""

import base64
import json
import time
from typing import Dict, Any, Optional, List
import httpx
import asyncio
from loguru import logger
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config.settings import settings


class OllamaVisionClient:
    """Client for interacting with Ollama vision models (LLaVA, BakLLaVA)"""
    
    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        timeout: int = None,
        max_retries: int = None
    ):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama server URL (defaults to settings)
            model: Model name (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
            max_retries: Maximum retry attempts (defaults to settings)
        """
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.alternative_model = settings.ollama_alternative_model
        self.timeout = timeout or settings.ollama_timeout
        self.max_retries = max_retries or settings.ollama_max_retries
        
        # Ensure base_url doesn't end with slash
        self.base_url = self.base_url.rstrip('/')
        
        # API endpoints
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.version_endpoint = f"{self.base_url}/api/version"
        self.tags_endpoint = f"{self.base_url}/api/tags"
        
        logger.info(f"Initialized OllamaVisionClient with model: {self.model}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Ollama server is healthy and accessible
        
        Returns:
            Dict containing health status and server info
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.version_endpoint)
                
                if response.status_code == 200:
                    version_info = response.json()
                    logger.info(f"Ollama server healthy - Version: {version_info.get('version', 'unknown')}")
                    return {
                        "status": "healthy",
                        "server_info": version_info,
                        "base_url": self.base_url
                    }
                else:
                    logger.error(f"Ollama server unhealthy - Status: {response.status_code}")
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}",
                        "base_url": self.base_url
                    }
                    
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                "status": "unreachable",
                "error": str(e),
                "base_url": self.base_url
            }
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models
        
        Returns:
            List of available models with metadata
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.tags_endpoint)
                
                if response.status_code == 200:
                    models_data = response.json()
                    models = models_data.get('models', [])
                    logger.info(f"Found {len(models)} available models")
                    return models
                else:
                    logger.error(f"Failed to list models - Status: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def _encode_image_base64(self, image_data: bytes) -> str:
        """
        Encode image data to base64 string
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Base64 encoded image string
        """
        return base64.b64encode(image_data).decode('utf-8')
    
    def _build_vision_prompt(self, question: str, image_base64: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        Build the prompt structure for vision models
        
        Args:
            question: User's question about the image
            image_base64: Base64 encoded image
            system_prompt: Optional system prompt override
            
        Returns:
            Formatted prompt dictionary for Ollama API
        """
        if system_prompt is None:
            system_prompt = (
                "You are a helpful AI assistant that can analyze images and answer questions about them. "
                "Provide clear, accurate, and detailed responses based on what you can observe in the image. "
                "Be specific about what you see and avoid making assumptions about things not visible in the image."
            )
        
        # Format the prompt for vision models
        prompt = f"System: {system_prompt}\n\nImage: [IMAGE]\n\nQuestion: {question}\n\nAnswer:"
        
        return {
            "model": self.model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_ctx": 4096
            }
        }
    
    async def ask_about_image(
        self,
        question: str,
        image_data: bytes,
        system_prompt: str = None,
        use_alternative_model: bool = False
    ) -> Dict[str, Any]:
        """
        Ask a question about an image using the vision model
        
        Args:
            question: Question about the image
            image_data: Raw image bytes
            system_prompt: Optional system prompt override
            use_alternative_model: Whether to use alternative model if primary fails
            
        Returns:
            Dictionary containing the response and metadata
        """
        start_time = time.time()
        
        # Encode image
        try:
            image_base64 = self._encode_image_base64(image_data)
            logger.debug(f"Encoded image to base64 ({len(image_base64)} chars)")
        except Exception as e:
            logger.error(f"Failed to encode image: {e}")
            return {
                "success": False,
                "error": "Failed to encode image",
                "details": str(e)
            }
        
        # Build prompt
        current_model = self.alternative_model if use_alternative_model else self.model
        prompt_data = self._build_vision_prompt(question, image_base64, system_prompt)
        prompt_data["model"] = current_model
        
        # Try to get response with retries
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending vision request to {current_model} (attempt {attempt + 1})")
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.generate_endpoint,
                        json=prompt_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        response_time = time.time() - start_time
                        
                        logger.info(f"Received response in {response_time:.2f}s")
                        
                        return {
                            "success": True,
                            "answer": result.get("response", "").strip(),
                            "model": current_model,
                            "response_time": response_time,
                            "tokens": {
                                "prompt": result.get("prompt_eval_count", 0),
                                "response": result.get("eval_count", 0),
                                "total": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                            },
                            "done": result.get("done", False),
                            "metadata": {
                                "question": question,
                                "attempt": attempt + 1,
                                "image_size": len(image_data)
                            }
                        }
                    else:
                        logger.warning(f"HTTP {response.status_code}: {response.text}")
                        if attempt == self.max_retries - 1:
                            return {
                                "success": False,
                                "error": f"HTTP {response.status_code}",
                                "details": response.text
                            }
                        
            except asyncio.TimeoutError:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": "Request timeout",
                        "details": f"Request timed out after {self.timeout}s"
                    }
                        
            except Exception as e:
                logger.error(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": "Request failed",
                        "details": str(e)
                    }
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        # If we get here, all retries failed
        return {
            "success": False,
            "error": "All retry attempts failed",
            "details": f"Failed after {self.max_retries} attempts"
        }
    
    async def simple_vision_test(self, test_image_path: str = None) -> Dict[str, Any]:
        """
        Run a simple test to verify vision functionality
        
        Args:
            test_image_path: Path to test image (optional)
            
        Returns:
            Test result dictionary
        """
        if test_image_path and Path(test_image_path).exists():
            with open(test_image_path, 'rb') as f:
                image_data = f.read()
            question = "What do you see in this image?"
        else:
            # Create a simple test image (1x1 pixel PNG)
            # This is a minimal PNG image for testing purposes
            test_png = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            )
            image_data = test_png
            question = "What color is this image?"
        
        logger.info("Running simple vision test...")
        
        result = await self.ask_about_image(
            question=question,
            image_data=image_data
        )
        
        if result.get("success"):
            logger.info("Vision test passed!")
        else:
            logger.error("Vision test failed!")
        
        return result


# Convenience function for easy import
async def create_ollama_client(**kwargs) -> OllamaVisionClient:
    """
    Create and return an OllamaVisionClient instance
    
    Args:
        **kwargs: Arguments to pass to OllamaVisionClient constructor
        
    Returns:
        Configured OllamaVisionClient instance
    """
    client = OllamaVisionClient(**kwargs)
    
    # Test connection
    health = await client.health_check()
    if health["status"] != "healthy":
        logger.warning(f"Ollama server health check failed: {health}")
    
    return client


if __name__ == "__main__":
    # Simple test script
    async def main():
        print("Testing Ollama Vision Client...")
        
        client = await create_ollama_client()
        
        # Health check
        health = await client.health_check()
        print(f"Health check: {health}")
        
        # List models
        models = await client.list_models()
        print(f"Available models: {[m.get('name', 'unknown') for m in models]}")
        
        # Simple vision test
        test_result = await client.simple_vision_test()
        print(f"Vision test: {test_result}")
    
    asyncio.run(main())
