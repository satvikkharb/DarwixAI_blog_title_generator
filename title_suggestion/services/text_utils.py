import re
import logging
import string
from collections import Counter

logger = logging.getLogger(__name__)

class TextAnalysisError(Exception):
    """Custom exception for text analysis errors"""
    pass

class TextAnalyzer:
    """
    Utility class for text analysis and processing
    """
    
    @staticmethod
    def extract_keywords(text, top_n=10):
        """
        Extract the most common keywords from text
        
        Args:
            text (str): The input text
            top_n (int): Number of top keywords to return
            
        Returns:
            list: A list of (keyword, count) tuples
        """
        try:
            if not isinstance(text, str):
                raise ValueError("Input text must be a string")
            
            if not text.strip():
                raise ValueError("Input text cannot be empty")
                
            if not isinstance(top_n, int) or top_n < 1:
                raise ValueError("top_n must be a positive integer")
            
            # Convert to lowercase
            text = text.lower()
            
            # Remove punctuation
            try:
                text = re.sub(f'[{re.escape(string.punctuation)}]', ' ', text)
            except re.error as e:
                logger.error(f"Regex error during punctuation removal: {str(e)}")
                raise TextAnalysisError("Failed to process text punctuation")
            
            # Tokenize into words
            words = text.split()
            if not words:
                logger.warning("No words found after tokenization")
                return []
            
            # Remove common stop words
            stop_words = {
                'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 
                'which', 'this', 'that', 'these', 'those', 'then', 'just', 'so', 'than', 
                'such', 'both', 'through', 'about', 'for', 'is', 'of', 'while', 'during', 
                'to', 'in', 'at', 'by', 'on', 'with', 'from', 'be', 'been', 'being', 
                'have', 'has', 'had', 'do', 'does', 'did', 'i', 'you', 'he', 'she', 
                'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'who', 'whom', 
                'whose', 'where', 'when', 'why', 'how'
            }
            
            # Filter out stop words and words less than 3 characters
            filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
            
            if not filtered_words:
                logger.warning("No words remaining after filtering")
                return []
            
            # Count word frequencies
            try:
                word_counts = Counter(filtered_words)
                return word_counts.most_common(top_n)
            except Exception as e:
                logger.error(f"Error counting word frequencies: {str(e)}")
                raise TextAnalysisError("Failed to analyze word frequencies")
                
        except Exception as e:
            logger.error(f"Error in keyword extraction: {str(e)}")
            if isinstance(e, TextAnalysisError):
                raise
            raise TextAnalysisError(f"Keyword extraction failed: {str(e)}")
    
    @staticmethod
    def extract_sentences(text, max_sentences=5):
        """
        Extract key sentences from text
        
        Args:
            text (str): The input text
            max_sentences (int): Maximum number of sentences to extract
            
        Returns:
            list: A list of sentences
        """
        try:
            if not isinstance(text, str):
                raise ValueError("Input text must be a string")
            
            if not text.strip():
                raise ValueError("Input text cannot be empty")
                
            if not isinstance(max_sentences, int) or max_sentences < 1:
                raise ValueError("max_sentences must be a positive integer")
            
            # Simple sentence splitting using regex
            try:
                sentence_pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s'
                sentences = re.split(sentence_pattern, text)
            except re.error as e:
                logger.error(f"Regex error during sentence splitting: {str(e)}")
                raise TextAnalysisError("Failed to split text into sentences")
            
            # Remove empty sentences and trim whitespace
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                logger.warning("No sentences found in text")
                return []
            
            return sentences[:max_sentences]
            
        except Exception as e:
            logger.error(f"Error in sentence extraction: {str(e)}")
            if isinstance(e, TextAnalysisError):
                raise
            raise TextAnalysisError(f"Sentence extraction failed: {str(e)}")
    
    @staticmethod
    def get_content_summary(text, max_length=200):
        """
        Generate a simple summary of the content
        
        Args:
            text (str): The input text
            max_length (int): Maximum length of summary
            
        Returns:
            str: A summary of the text
        """
        try:
            if not isinstance(text, str):
                raise ValueError("Input text must be a string")
            
            if not text.strip():
                raise ValueError("Input text cannot be empty")
                
            if not isinstance(max_length, int) or max_length < 1:
                raise ValueError("max_length must be a positive integer")
            
            # Get first few sentences
            sentences = TextAnalyzer.extract_sentences(text, max_sentences=3)
            
            if not sentences:
                logger.warning("No sentences available for summary")
                return ""
            
            # Join sentences into a summary
            summary = ' '.join(sentences)
            
            # Truncate if too long
            if len(summary) > max_length:
                summary = summary[:max_length-3] + '...'
                
            return summary
            
        except Exception as e:
            logger.error(f"Error generating content summary: {str(e)}")
            if isinstance(e, TextAnalysisError):
                raise
            raise TextAnalysisError(f"Summary generation failed: {str(e)}")
    
    @staticmethod
    def clean_and_normalize_text(text):
        """
        Clean and normalize text for processing
        
        Args:
            text (str): The input text
            
        Returns:
            str: Cleaned text
        """
        try:
            if not isinstance(text, str):
                raise ValueError("Input text must be a string")
            
            # Convert to lowercase
            text = text.lower()
            
            try:
                # Replace multiple whitespace with single space
                text = re.sub(r'\s+', ' ', text)
                
                # Remove URLs
                text = re.sub(r'https?://\S+|www\.\S+', '', text)
                
                # Remove email addresses
                text = re.sub(r'\S+@\S+', '', text)
                
                # Remove HTML tags
                text = re.sub(r'<.*?>', '', text)
            except re.error as e:
                logger.error(f"Regex error during text cleaning: {str(e)}")
                raise TextAnalysisError("Failed to clean and normalize text")
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error in text cleaning: {str(e)}")
            if isinstance(e, TextAnalysisError):
                raise
            raise TextAnalysisError(f"Text cleaning failed: {str(e)}")