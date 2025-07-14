import os
import logging
import requests
from django.conf import settings
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from .cache_service import TitleSuggestionCache

logger = logging.getLogger(__name__)

class HuggingFaceServiceError(Exception):
    """Custom exception for HuggingFace service errors"""
    pass

class ModelLoadError(HuggingFaceServiceError):
    """Error when loading model fails"""
    pass

class APIError(HuggingFaceServiceError):
    """Error when API request fails"""
    pass

class HuggingFaceTitleGenerator:
    """
    Service class to generate blog post title suggestions using Hugging Face models
    """
    
    def __init__(self):
        """
        Initialize the Hugging Face model and tokenizer
        """
        try:
            self.api_key = settings.HUGGINGFACE_API_KEY
            if not self.api_key:
                logger.warning("HuggingFace API key not set. Falling back to local model.")
                self.api_mode = False
            else:
                self.api_mode = True
                
            # Model name for title generation
            self.model_name = "facebook/bart-large-cnn"  # Good summarization model
            
            # Load local model if not using API
            if not self.api_mode:
                try:
                    self._load_local_model()
                except Exception as e:
                    logger.error(f"Failed to load local model: {str(e)}")
                    raise ModelLoadError(f"Failed to load local model: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace service: {str(e)}")
            raise HuggingFaceServiceError(f"Service initialization failed: {str(e)}")

    def _load_local_model(self):
        """
        Load the local Hugging Face model and tokenizer
        """
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self.summarizer = pipeline(
                "summarization", 
                model=self.model, 
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1  # Use GPU if available
            )
            logger.info(f"Local model '{self.model_name}' loaded successfully")
        except Exception as e:
            logger.error(f"Error loading local model: {str(e)}")
            self.summarizer = None
            raise ModelLoadError(f"Failed to load model components: {str(e)}")

    def generate_titles(self, content, num_suggestions=3):
        """
        Generate blog post title suggestions using Hugging Face
        
        Args:
            content (str): The blog post content
            num_suggestions (int): Number of title suggestions to generate
            
        Returns:
            list: A list of suggested titles
        """
        try:
            # Check cache first
            service_name = "huggingface"
            cached_titles = TitleSuggestionCache.get_cached_suggestions(content, service_name)
            if cached_titles:
                logger.info("Using cached HuggingFace title suggestions")
                return cached_titles

            if self.api_mode:
                titles = self._generate_via_api(content, num_suggestions)
            else:
                if not self.summarizer:
                    raise ModelLoadError("Local model not available")
                titles = self._generate_locally(content, num_suggestions)
                
            # Clean and format titles
            titles = [self._clean_title(title) for title in titles if title]
            
            if not titles:
                logger.warning("No titles generated")
                return []

            # Cache the results
            if TitleSuggestionCache.cache_suggestions(content, service_name, titles):
                logger.debug(f"Cached {len(titles)} HuggingFace title suggestions")
            
            logger.info(f"Generated {len(titles)} title suggestions using HuggingFace")
            return titles
            
        except Exception as e:
            logger.error(f"Error in HuggingFace title generation: {str(e)}")
            if isinstance(e, HuggingFaceServiceError):
                raise
            raise HuggingFaceServiceError(f"Title generation failed: {str(e)}")
    
    def _generate_via_api(self, content, num_suggestions):
        """
        Generate titles using Hugging Face Inference API
        
        Args:
            content (str): The blog post content
            num_suggestions (int): Number of title suggestions to generate
            
        Returns:
            list: A list of suggested titles
        """
        try:
            API_URL = f"https://api-inference.huggingface.co/models/{self.model_name}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # Truncate content if it's too long
            max_content_length = 1000  # Adjust based on model constraints
            truncated_content = content[:max_content_length] + "..." if len(content) > max_content_length else content
            
            # Prepare the payload
            payload = {
                "inputs": truncated_content,
                "parameters": {
                    "max_length": 30,
                    "min_length": 5,
                    "do_sample": True,
                    "top_k": 50,
                    "top_p": 0.95,
                    "num_return_sequences": num_suggestions
                }
            }
            
            # Call the API
            try:
                response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()
            except requests.exceptions.Timeout:
                logger.error("HuggingFace API request timed out")
                raise APIError("Request timed out. Please try again.")
            except requests.exceptions.RequestException as e:
                logger.error(f"HuggingFace API request failed: {str(e)}")
                raise APIError(f"API request failed: {str(e)}")
            
            # Process the response
            titles = []
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict) and "generated_text" in item:
                        titles.append(item["generated_text"].strip())
                    elif isinstance(item, str):
                        titles.append(item.strip())
            elif isinstance(result, dict) and "generated_text" in result:
                titles.append(result["generated_text"].strip())
            
            if not titles:
                logger.warning("No titles extracted from API response")
            
            return titles
            
        except Exception as e:
            logger.error(f"Error in API title generation: {str(e)}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to generate titles via API: {str(e)}")
    
    def _generate_locally(self, content, num_suggestions):
        """
        Generate titles using local Hugging Face model
        
        Args:
            content (str): The blog post content
            num_suggestions (int): Number of title suggestions to generate
            
        Returns:
            list: A list of suggested titles
        """
        try:
            if not self.summarizer:
                raise ModelLoadError("Summarizer not initialized")
            
            # Truncate content if it's too long
            max_content_length = 1000  # Adjust based on model constraints
            truncated_content = content[:max_content_length] + "..." if len(content) > max_content_length else content
            
            # Generate summaries as title suggestions
            try:
                summaries = self.summarizer(
                    truncated_content, 
                    max_length=30, 
                    min_length=5,
                    do_sample=True,
                    top_k=50,
                    top_p=0.95,
                    num_return_sequences=num_suggestions
                )
            except Exception as e:
                logger.error(f"Error during local title generation: {str(e)}")
                raise ModelLoadError(f"Failed to generate titles locally: {str(e)}")
            
            # Extract the generated titles
            titles = [summary["summary_text"].strip() for summary in summaries]
            
            if not titles:
                logger.warning("No titles generated locally")
            
            return titles
            
        except Exception as e:
            logger.error(f"Error in local title generation: {str(e)}")
            if isinstance(e, ModelLoadError):
                raise
            raise HuggingFaceServiceError(f"Failed to generate titles locally: {str(e)}")
    
    def _clean_title(self, title):
        """
        Clean and format the generated title
        
        Args:
            title (str): The raw generated title
            
        Returns:
            str: The cleaned title
        """
        try:
            # Remove unnecessary punctuation and formatting
            title = title.strip()
            
            # Remove trailing periods
            if title.endswith('.'):
                title = title[:-1]
            
            # Capitalize the first letter
            if title:
                title = title[0].upper() + title[1:]
            
            return title
        except Exception as e:
            logger.warning(f"Error cleaning title '{title}': {str(e)}")
            return title  # Return original title if cleaning fails