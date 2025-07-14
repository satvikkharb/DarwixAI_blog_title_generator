import os
import logging
from openai import OpenAI, APIError, RateLimitError, APIConnectionError, InternalServerError
from django.conf import settings
from .cache_service import TitleSuggestionCache

logger = logging.getLogger(__name__)

class OpenAIServiceError(Exception):
    """Custom exception for OpenAI service errors"""
    pass

class OpenAITitleGenerator:
    """
    Service class to generate blog post title suggestions using OpenAI API
    """
    
    def __init__(self):
        """
        Initialize the OpenAI client using the API key from settings
        """
        try:
            self.api_key = settings.OPENAI_API_KEY
            if not self.api_key:
                raise ValueError("OpenAI API key is not set")
            
            self.client = OpenAI(api_key=self.api_key)
            # Using GPT-4 Turbo as it's more cost-effective and newer
            self.model = "gpt-4-turbo-preview"
            logger.info("OpenAI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {str(e)}")
            raise OpenAIServiceError(f"Service initialization failed: {str(e)}")

    def generate_titles(self, content, num_suggestions=3):
        """
        Generate blog post title suggestions using OpenAI's API
        
        Args:
            content (str): The blog post content
            num_suggestions (int): Number of title suggestions to generate
            
        Returns:
            list: A list of suggested titles
        """
        try:
            # Check cache first
            service_name = "openai"
            cached_titles = TitleSuggestionCache.get_cached_suggestions(content, service_name)
            if cached_titles:
                logger.info("Using cached OpenAI title suggestions")
                return cached_titles

            # Prepare the prompt
            prompt = self._create_prompt(content, num_suggestions)
            
            # Call OpenAI API
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional blog title generator. Create engaging, SEO-friendly titles that accurately reflect the content while being catchy and memorable."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=150,
                    top_p=1,
                    frequency_penalty=0.5,
                    presence_penalty=0.3,
                    response_format={ "type": "text" }
                )
            except RateLimitError as e:
                logger.error(f"OpenAI rate limit exceeded: {str(e)}")
                raise OpenAIServiceError("Rate limit exceeded. Please try again later.")
            except APIConnectionError as e:
                logger.error(f"OpenAI API connection error: {str(e)}")
                raise OpenAIServiceError("Connection error. Please check your internet connection.")
            except InternalServerError as e:
                logger.error(f"OpenAI internal server error: {str(e)}")
                raise OpenAIServiceError("OpenAI service is currently experiencing issues.")
            except APIError as e:
                logger.error(f"OpenAI API error: {str(e)}")
                raise OpenAIServiceError("API error occurred. Please try again.")
            except Exception as e:
                logger.error(f"OpenAI request failed: {str(e)}")
                raise OpenAIServiceError(f"Failed to generate titles: {str(e)}")

            # Process the response
            titles = self._process_response(response)
            
            # Cache the results
            if not titles:
                logger.warning("No titles generated from OpenAI response")
                return []

            if TitleSuggestionCache.cache_suggestions(content, service_name, titles):
                logger.debug(f"Cached {len(titles)} OpenAI title suggestions")
            
            logger.info(f"Generated {len(titles)} title suggestions using OpenAI")
            return titles
            
        except Exception as e:
            logger.error(f"Error in OpenAI title generation: {str(e)}")
            if isinstance(e, OpenAIServiceError):
                raise
            raise OpenAIServiceError(f"Title generation failed: {str(e)}")
    
    def _create_prompt(self, content, num_suggestions):
        """
        Create a prompt for the OpenAI API
        
        Args:
            content (str): The blog post content
            num_suggestions (int): Number of title suggestions to generate
            
        Returns:
            str: The formatted prompt
        """
        try:
            # Truncate content if it's too long
            max_content_length = 4000  # Adjust based on token limits
            truncated_content = content[:max_content_length] + "..." if len(content) > max_content_length else content
            
            prompt = f"""Generate exactly {num_suggestions} unique and engaging blog post titles based on the following content.
            
Content:
{truncated_content}

Requirements:
1. Each title should be SEO-friendly and no longer than 60 characters
2. Titles should be catchy and engaging while accurately reflecting the content
3. Format the output as a numbered list (1., 2., etc.)
4. Do not include any additional text or explanations
5. Each title should be unique and different in structure

Generate {num_suggestions} titles now:"""
            
            return prompt
        except Exception as e:
            logger.error(f"Error creating prompt: {str(e)}")
            raise OpenAIServiceError(f"Failed to create prompt: {str(e)}")
    
    def _process_response(self, response):
        """
        Process the OpenAI API response to extract title suggestions
        
        Args:
            response: The OpenAI API response
            
        Returns:
            list: A list of suggested titles
        """
        try:
            # Extract the generated text
            generated_text = response.choices[0].message.content.strip()
            if not generated_text:
                logger.warning("Empty response from OpenAI")
                return []

            # Parse the numbered list of titles
            titles = []
            for line in generated_text.split('\n'):
                line = line.strip()
                # Skip empty lines
                if not line:
                    continue
                    
                try:
                    # Handle numbered format (e.g., "1. Title")
                    if '.' in line and line[0].isdigit():
                        title = line.split('.', 1)[1].strip()
                        if title and len(title) <= 60:  # Validate title length
                            titles.append(title)
                    # Handle dash format (e.g., "- Title")
                    elif line.startswith('-'):
                        title = line[1:].strip()
                        if title and len(title) <= 60:
                            titles.append(title)
                    # Handle plain text (if not starting with number or dash)
                    elif not any(line.startswith(prefix) for prefix in ['title', 'suggestion', 'here']):
                        if line and len(line) <= 60:
                            titles.append(line)
                except Exception as e:
                    logger.warning(f"Failed to process line '{line}': {str(e)}")
                    continue

            if not titles:
                logger.warning("No valid titles extracted from response")
            
            return titles
        except Exception as e:
            logger.error(f"Error processing OpenAI response: {str(e)}")
            raise OpenAIServiceError(f"Failed to process response: {str(e)}")