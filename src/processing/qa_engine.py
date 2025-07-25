"""
Core Q&A Engine for VisuaLens
Handles prompt engineering, response processing, and vision Q&A logic
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import sys
from loguru import logger

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.utils.ollama_client import OllamaVisionClient
from src.utils.text_extractor import text_extractor
from src.models.schemas import QAResponse, TokenInfo, create_success_response, create_error_response
from config.settings import settings


class PromptTemplate:
    """Templates for different types of vision prompts"""
    
    SYSTEM_DEFAULT = (
        "You are a helpful AI assistant that can analyze images and answer questions about them. "
        "Provide clear, accurate, and detailed responses based on what you can observe in the image. "
        "Be specific about what you see and avoid making assumptions about things not visible in the image."
    )
    
    SYSTEM_DETAILED = (
        "You are an expert image analyst. Examine the image carefully and provide detailed, accurate responses. "
        "Focus on what is actually visible in the image. Be specific about objects, colors, text, people, "
        "settings, and any other observable details. If something is not clearly visible, say so."
    )
    
    SYSTEM_CONCISE = (
        "You are a helpful assistant. Analyze the image and provide clear, concise answers. "
        "Focus on the most important and relevant details that answer the user's question directly."
    )
    
    # Question-specific templates
    OBJECT_DETECTION = (
        "Carefully examine this image and identify all objects, items, and elements you can see. "
        "Question: {question}"
    )
    
    SCENE_DESCRIPTION = (
        "Describe what is happening in this image, including the setting, context, and any activities. "
        "Question: {question}"
    )
    
    TEXT_READING = (
        "Look for any text, signs, writing, or readable content in this image and transcribe what you see. "
        "Question: {question}"
    )
    
    DOCUMENT_ANALYSIS = (
        "This appears to be a document or text-based image. Please read and analyze the content carefully. "
        "Focus on understanding the structure, main topics, key information, and provide a comprehensive analysis. "
        "If it's a resume or CV, identify experience, skills, education, and career details. "
        "If it's a professional document, extract key points, dates, and relevant information. "
        "Question: {question}"
    )
    
    TECHNICAL_ANALYSIS = (
        "Analyze this image from a technical perspective, looking at composition, design, charts, or technical elements. "
        "Question: {question}"
    )


class QuestionClassifier:
    """Classifies questions to apply appropriate prompt templates"""
    
    OBJECT_KEYWORDS = [
        'what objects', 'identify', 'recognize', 'detect', 'find', 'locate', 
        'what is', 'what are', 'how many', 'count', 'list'
    ]
    
    SCENE_KEYWORDS = [
        'what is happening', 'describe', 'scene', 'setting', 'context', 
        'activity', 'situation', 'environment', 'background'
    ]
    
    TEXT_KEYWORDS = [
        'text', 'read', 'sign', 'writing', 'words', 'letters', 'document', 
        'label', 'caption', 'title', 'transcribe', 'summary', 'summarize',
        'resume', 'cv', 'experience', 'education', 'skills', 'qualification',
        'professional', 'career', 'job', 'work', 'employment', 'analyze',
        'extract', 'content', 'information'
    ]
    
    TECHNICAL_KEYWORDS = [
        'chart', 'graph', 'diagram', 'ui', 'interface', 'design', 'color', 
        'composition', 'technical', 'analysis', 'structure'
    ]
    
    @classmethod
    def classify_question(cls, question: str) -> str:
        """
        Classify question type based on keywords
        
        Args:
            question: User's question
            
        Returns:
            Question category: 'object', 'scene', 'text', 'technical', or 'general'
        """
        question_lower = question.lower()
        
        # Check for specific categories
        if any(keyword in question_lower for keyword in cls.TEXT_KEYWORDS):
            return 'text'
        elif any(keyword in question_lower for keyword in cls.TECHNICAL_KEYWORDS):
            return 'technical'
        elif any(keyword in question_lower for keyword in cls.OBJECT_KEYWORDS):
            return 'object'
        elif any(keyword in question_lower for keyword in cls.SCENE_KEYWORDS):
            return 'scene'
        else:
            return 'general'


class ResponseProcessor:
    """Processes and validates model responses"""
    
    @staticmethod
    def clean_response(response: str) -> str:
        """
        Clean and format the model response
        
        Args:
            response: Raw response from model
            
        Returns:
            Cleaned response text
        """
        if not response:
            return "I was unable to generate a response. Please try again."
        
        # Remove common prefixes that models sometimes add
        prefixes_to_remove = [
            "Answer:", "Response:", "A:", "Based on the image,", 
            "Looking at the image,", "In this image,"
        ]
        
        cleaned = response.strip()
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        # Ensure response ends with proper punctuation
        if cleaned and not cleaned.endswith(('.', '!', '?')):
            cleaned += '.'
        
        return cleaned
    
    @staticmethod
    def validate_response(response: str, question: str) -> Tuple[bool, str]:
        """
        Validate response quality and relevance
        
        Args:
            response: Model response
            question: Original question
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if not response or len(response.strip()) < 5:
            return False, "Response too short"
        
        # Check for obvious hallucination indicators
        hallucination_indicators = [
            "I cannot see", "I don't see", "There is no image", 
            "No image provided", "Unable to see"
        ]
        
        response_lower = response.lower()
        if any(indicator in response_lower for indicator in hallucination_indicators):
            # These might be valid responses, so we'll accept them but log
            logger.warning(f"Potential hallucination detected: {response[:100]}")
        
        # Check for minimum relevance (very basic)
        if len(response) > 1000:
            logger.warning("Response is very long, might be hallucinating")
        
        return True, "Valid response"
    
    @staticmethod
    def extract_confidence(response: str) -> Optional[float]:
        """
        Try to extract confidence score from response
        
        Args:
            response: Model response
            
        Returns:
            Confidence score between 0 and 1, or None if not found
        """
        # This is a placeholder - LLaVA doesn't typically provide confidence scores
        # We could implement heuristics based on response length, certainty words, etc.
        
        confidence_words = {
            'certain': 0.9, 'sure': 0.8, 'likely': 0.7, 'probably': 0.6,
            'might': 0.4, 'possibly': 0.3, 'unsure': 0.2, 'unclear': 0.1
        }
        
        response_lower = response.lower()
        for word, score in confidence_words.items():
            if word in response_lower:
                return score
        
        # Default confidence based on response characteristics
        if len(response) > 100 and '.' in response:
            return 0.7  # Seems like a complete response
        elif len(response) > 50:
            return 0.6  # Reasonable response
        else:
            return 0.4  # Short response, lower confidence
        
        return None


class VisionQAEngine:
    """Main Q&A engine for vision tasks"""
    
    def __init__(self, ollama_client: Optional[OllamaVisionClient] = None):
        """
        Initialize the Q&A engine
        
        Args:
            ollama_client: Optional pre-configured Ollama client
        """
        self.ollama_client = ollama_client
        self.response_processor = ResponseProcessor()
        self.prompt_templates = PromptTemplate()
        self.question_classifier = QuestionClassifier()
        
        logger.info("Initialized VisionQAEngine")
    
    async def get_ollama_client(self) -> OllamaVisionClient:
        """Get or create Ollama client"""
        if self.ollama_client is None:
            from src.utils.ollama_client import create_ollama_client
            self.ollama_client = await create_ollama_client()
        return self.ollama_client
    
    def build_system_prompt(self, question_type: str, custom_prompt: str = None) -> str:
        """
        Build appropriate system prompt based on question type
        
        Args:
            question_type: Type of question (object, scene, text, technical, general)
            custom_prompt: Optional custom system prompt
            
        Returns:
            Appropriate system prompt
        """
        if custom_prompt:
            return custom_prompt
        
        prompt_map = {
            'object': self.prompt_templates.SYSTEM_DETAILED,
            'scene': self.prompt_templates.SYSTEM_DETAILED,
            'text': self.prompt_templates.SYSTEM_DETAILED,
            'technical': self.prompt_templates.SYSTEM_DETAILED,
            'general': self.prompt_templates.SYSTEM_DEFAULT
        }
        
        return prompt_map.get(question_type, self.prompt_templates.SYSTEM_DEFAULT)
    
    def enhance_question(self, question: str, question_type: str) -> str:
        """
        Enhance question with context-specific prompting
        
        Args:
            question: Original question
            question_type: Classified question type
            
        Returns:
            Enhanced question prompt
        """
        template_map = {
            'object': self.prompt_templates.OBJECT_DETECTION,
            'scene': self.prompt_templates.SCENE_DESCRIPTION,
            'text': self.prompt_templates.DOCUMENT_ANALYSIS,
            'technical': self.prompt_templates.TECHNICAL_ANALYSIS
        }
        
        template = template_map.get(question_type)
        if template:
            return template.format(question=question)
        else:
            return question
    
    def enhance_question_with_context(self, question: str, question_type: str, text_analysis: Dict[str, Any] = None) -> str:
        """
        Enhance question with text analysis context for better document processing
        
        Args:
            question: Original question
            question_type: Classified question type
            text_analysis: Text extraction analysis results
            
        Returns:
            Enhanced question with context
        """
        # Start with the basic enhanced question
        enhanced_question = self.enhance_question(question, question_type)
        
        # Add text analysis context if available
        if text_analysis and text_analysis.get('success'):
            context_parts = []
            
            # Add document type context
            if text_analysis.get('is_document'):
                doc_type = text_analysis.get('document_type', 'unknown')
                context_parts.append(f"This appears to be a {doc_type.replace('_', ' ')}.")
            
            # Add image characteristics
            if text_analysis.get('image_characteristics'):
                chars = text_analysis['image_characteristics']
                if chars.get('aspect_ratio'):
                    ratio = chars['aspect_ratio']
                    if 0.7 <= ratio <= 0.8:
                        context_parts.append("The document format suggests this is likely a resume or CV.")
                    elif ratio > 1.2:
                        context_parts.append("This appears to be a landscape-oriented document.")
            
            # Add preprocessing note
            if text_analysis.get('preprocessing_applied'):
                context_parts.append("The image has been enhanced for better text recognition.")
            
            # Combine context with enhanced question
            if context_parts:
                context = " ".join(context_parts)
                enhanced_question = f"{context} {enhanced_question}"
                logger.debug(f"Added context to question: {context}")
        
        return enhanced_question
    
    async def ask_question(
        self,
        question: str,
        image_data: bytes,
        system_prompt: str = None,
        use_alternative_model: bool = False,
        session_id: str = None
    ) -> QAResponse:
        """
        Ask a question about an image
        
        Args:
            question: User's question
            image_data: Raw image bytes
            system_prompt: Optional system prompt override
            use_alternative_model: Whether to use alternative model
            session_id: Optional session ID for tracking
            
        Returns:
            QAResponse with answer and metadata
        """
        start_time = time.time()
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        try:
            # Classify question
            question_type = self.question_classifier.classify_question(question)
            logger.info(f"Classified question as: {question_type}")
            
            # Apply text extraction and image preprocessing for document analysis
            text_analysis = None
            enhanced_image_data = image_data
            
            if question_type in ['text', 'document'] or any(keyword in question.lower() for keyword in ['resume', 'cv', 'document', 'text', 'extract']):
                logger.info("Applying text extraction and image enhancement for document analysis")
                
                # Extract text information
                text_analysis = text_extractor.extract_text_simple(image_data)
                logger.info(f"Text analysis result: {text_analysis}")
                
                # Enhance image for better vision model processing
                enhanced_image_data = text_extractor.enhance_image_for_vision(image_data)
                logger.info("Image enhanced for vision model processing")
            
            # Build system prompt
            system_prompt = self.build_system_prompt(question_type, system_prompt)
            
            # Enhance question with text analysis context if available
            enhanced_question = self.enhance_question_with_context(question, question_type, text_analysis)
            
            # Get Ollama client
            client = await self.get_ollama_client()
            
            # Ask the question using enhanced image
            logger.info(f"Asking question: {question[:100]}...")
            response = await client.ask_about_image(
                question=enhanced_question,
                image_data=enhanced_image_data,
                system_prompt=system_prompt,
                use_alternative_model=use_alternative_model
            )
            
            if not response.get('success'):
                logger.error(f"Ollama request failed: {response.get('error')}")
                return create_error_response(
                    error=response.get('error', 'Unknown error'),
                    details=response.get('details'),
                    response_class=QAResponse
                )
            
            # Process response
            raw_answer = response.get('answer', '')
            cleaned_answer = self.response_processor.clean_response(raw_answer)
            
            # Validate response
            is_valid, validation_reason = self.response_processor.validate_response(
                cleaned_answer, question
            )
            
            if not is_valid:
                logger.warning(f"Response validation failed: {validation_reason}")
                # Still return the response but log the issue
            
            # Extract confidence (optional)
            confidence = self.response_processor.extract_confidence(cleaned_answer)
            
            # Build token info
            token_info = None
            if response.get('tokens'):
                token_info = TokenInfo(**response['tokens'])
            
            # Calculate total response time
            total_time = time.time() - start_time
            
            # Build metadata
            metadata = {
                'question_type': question_type,
                'enhanced_question': enhanced_question,
                'original_question': question,
                'validation_status': validation_reason,
                'confidence': confidence,
                'image_size': len(image_data),
                'enhanced_image_size': len(enhanced_image_data),
                'text_analysis': text_analysis,
                'session_id': session_id
            }
            
            # Create successful response
            qa_response = QAResponse(
                success=True,
                answer=cleaned_answer,
                model=response.get('model'),
                response_time=total_time,
                tokens=token_info,
                session_id=session_id,
                metadata=metadata
            )
            
            logger.info(f"Successfully generated answer in {total_time:.2f}s")
            return qa_response
            
        except Exception as e:
            logger.error(f"Error in ask_question: {e}")
            return create_error_response(
                error="Internal error during Q&A processing",
                details=str(e),
                response_class=QAResponse
            )
    
    async def test_engine(self, test_image_path: str = None) -> Dict[str, Any]:
        """
        Test the Q&A engine with a simple question
        
        Args:
            test_image_path: Optional path to test image
            
        Returns:
            Test results
        """
        logger.info("Testing VisionQAEngine...")
        
        # Create or load test image
        if test_image_path and Path(test_image_path).exists():
            with open(test_image_path, 'rb') as f:
                image_data = f.read()
            test_question = "Describe this image in detail."
        else:
            # Use minimal test image
            import base64
            test_png = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            )
            image_data = test_png
            test_question = "What color is this image?"
        
        # Test the engine
        result = await self.ask_question(
            question=test_question,
            image_data=image_data
        )
        
        success = result.success and result.answer is not None
        logger.info(f"Engine test {'passed' if success else 'failed'}")
        
        return {
            'success': success,
            'response': result.dict() if hasattr(result, 'dict') else str(result),
            'test_question': test_question,
            'image_size': len(image_data)
        }


# Convenience function for easy import
async def create_qa_engine(**kwargs) -> VisionQAEngine:
    """
    Create and return a VisionQAEngine instance
    
    Args:
        **kwargs: Arguments to pass to VisionQAEngine constructor
        
    Returns:
        Configured VisionQAEngine instance
    """
    engine = VisionQAEngine(**kwargs)
    
    # Ensure Ollama client is ready
    await engine.get_ollama_client()
    
    return engine


if __name__ == "__main__":
    # Test script
    import asyncio
    
    async def main():
        print("Testing VisionQAEngine...")
        
        engine = await create_qa_engine()
        test_result = await engine.test_engine()
        
        print(f"Test result: {test_result}")
    
    asyncio.run(main())
