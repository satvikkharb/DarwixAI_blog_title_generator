import hashlib
import json
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

class CacheServiceError(Exception):
    """Custom exception for cache service errors"""
    pass

class TitleSuggestionCache:
    """
    Service class to handle caching of title suggestions
    """
    
    # Cache timeout in seconds (default: 24 hours)
    CACHE_TIMEOUT = 86400
    
    @staticmethod
    def get_cache_key(content, service_name):
        """
        Generate a cache key for the given content and service
        
        Args:
            content (str): The blog post content
            service_name (str): The name of the service (e.g., 'openai', 'huggingface')
            
        Returns:
            str: A cache key
        """
        try:
            if not content or not service_name:
                raise ValueError("Content and service_name are required")
                
            # Create a deterministic hash of the content
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            return f"title_suggestion:{service_name}:{content_hash}"
        except Exception as e:
            logger.error(f"Error generating cache key: {str(e)}")
            raise CacheServiceError(f"Failed to generate cache key: {str(e)}")
    
    @staticmethod
    def get_cached_suggestions(content, service_name):
        """
        Retrieve cached title suggestions if available
        
        Args:
            content (str): The blog post content
            service_name (str): The name of the service (e.g., 'openai', 'huggingface')
            
        Returns:
            list or None: A list of suggested titles if cached, None otherwise
        """
        try:
            if not content or not service_name:
                logger.warning("Missing required parameters for cache lookup")
                return None
                
            cache_key = TitleSuggestionCache.get_cache_key(content, service_name)
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Cache hit for {service_name} title suggestions")
                return cached_result
            
            logger.info(f"Cache miss for {service_name} title suggestions")
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached suggestions: {str(e)}")
            return None
    
    @staticmethod
    def cache_suggestions(content, service_name, suggestions):
        """
        Cache title suggestions for future use
        
        Args:
            content (str): The blog post content
            service_name (str): The name of the service (e.g., 'openai', 'huggingface')
            suggestions (list): A list of suggested titles
            
        Returns:
            bool: True if caching was successful, False otherwise
        """
        try:
            if not suggestions:
                logger.warning("No suggestions provided for caching")
                return False
                
            if not content or not service_name:
                logger.warning("Missing required parameters for caching")
                return False
                
            cache_key = TitleSuggestionCache.get_cache_key(content, service_name)
            
            try:
                cache.set(cache_key, suggestions, TitleSuggestionCache.CACHE_TIMEOUT)
                logger.info(f"Cached {len(suggestions)} title suggestions for {service_name}")
                return True
            except Exception as e:
                logger.error(f"Cache operation failed: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error caching title suggestions: {str(e)}")
            return False