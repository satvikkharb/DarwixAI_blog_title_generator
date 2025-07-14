from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from .models import TitleSuggestionRequest


class TitleSuggestionTests(TestCase):
    """
    Test cases for the title suggestion API
    """
    
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('suggest-titles')
        self.valid_content = """
        This is a sample blog post about machine learning and artificial intelligence.
        It covers various topics including neural networks, deep learning, and natural
        language processing. The post discusses how these technologies are being used in
        different industries and what the future might hold for AI development.
        """
        
    def test_empty_content(self):
        """Test that the API rejects empty content"""
        response = self.client.post(self.url, {'content': ''}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_short_content(self):
        """Test that the API rejects very short content"""
        response = self.client.post(self.url, {'content': 'Too short'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    @patch('title_suggestion.services.openai_service.OpenAITitleGenerator.generate_titles')
    @patch('title_suggestion.services.huggingface_service.HuggingFaceTitleGenerator.generate_titles')
    def test_successful_title_generation(self, mock_hf_generate, mock_openai_generate):
        """Test successful title generation with mocked services"""
        # Mock the results from the services
        mock_openai_generate.return_value = [
            "The Future of AI: Transforming Industries",
            "Machine Learning Revolution: What's Next?"
        ]
        mock_hf_generate.return_value = [
            "Understanding Neural Networks and Deep Learning"
        ]
        
        response = self.client.post(self.url, {'content': self.valid_content}, format='json')
        
        # Check that the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains titles
        self.assertIn('suggestions', response.data)
        self.assertEqual(len(response.data['suggestions']), 3)
        
        # Check that a new request was created in the database
        self.assertEqual(TitleSuggestionRequest.objects.count(), 1)
        
        # Check that the titles were stored in the database
        request = TitleSuggestionRequest.objects.first()
        self.assertEqual(len(request.get_suggested_titles_list()), 3)
        
    @patch('title_suggestion.services.openai_service.OpenAITitleGenerator.generate_titles')
    @patch('title_suggestion.services.huggingface_service.HuggingFaceTitleGenerator.generate_titles')
    def test_partial_service_failure(self, mock_hf_generate, mock_openai_generate):
        """Test that the API works even if one service fails"""
        # Mock OpenAI service success but HuggingFace failure
        mock_openai_generate.return_value = [
            "The Future of AI: Transforming Industries",
            "Machine Learning Revolution: What's Next?",
            "Neural Networks Explained: A Beginner's Guide"
        ]
        mock_hf_generate.return_value = []  # Service failure
        
        response = self.client.post(self.url, {'content': self.valid_content}, format='json')
        
        # Check that the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that we still got titles from the working service
        self.assertIn('suggestions', response.data)
        self.assertEqual(len(response.data['suggestions']), 3)
        
    @patch('title_suggestion.services.openai_service.OpenAITitleGenerator.generate_titles')
    @patch('title_suggestion.services.huggingface_service.HuggingFaceTitleGenerator.generate_titles')
    def test_complete_service_failure(self, mock_hf_generate, mock_openai_generate):
        """Test API behavior when all services fail"""
        # Mock both services failing
        mock_openai_generate.side_effect = Exception("Service unavailable")
        mock_hf_generate.side_effect = Exception("Service unavailable")
        
        response = self.client.post(self.url, {'content': self.valid_content}, format='json')
        
        # Check that we get an error response
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Check that a request was still created (but without suggestions)
        self.assertEqual(TitleSuggestionRequest.objects.count(), 1)
        request = TitleSuggestionRequest.objects.first()
        self.assertEqual(len(request.get_suggested_titles_list()), 0)