import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.exceptions import ValidationError

from .services.openai_service import OpenAITitleGenerator, OpenAIServiceError
from .services.huggingface_service import HuggingFaceTitleGenerator, HuggingFaceServiceError
from .services.text_utils import TextAnalyzer
from .models import TitleSuggestionRequest

logger = logging.getLogger(__name__)

class TitleSuggestionError(Exception):
    """Base exception for title suggestion errors"""
    pass

class TitleSuggestionView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            # Validate request data
            content = request.data.get('content')
            if not content:
                return Response(
                    {'error': 'Blog post content is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not isinstance(content, str):
                return Response(
                    {'error': 'Content must be a string'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(content) < 50:
                return Response(
                    {'error': 'Blog post content must be at least 50 characters long'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            include_analysis = request.data.get('include_analysis', False)
            
            # Create request entry
            try:
                suggestion_request = TitleSuggestionRequest.objects.create(content=content)
            except Exception as e:
                logger.error(f"Failed to create request entry: {str(e)}")
                return Response(
                    {'error': 'Failed to process request'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            try:
                # Process content analysis if requested
                analysis_data = {}
                if include_analysis:
                    try:
                        keywords = TextAnalyzer.extract_keywords(content, top_n=5)
                        keywords = [word for word, count in keywords]
                        summary = TextAnalyzer.get_content_summary(content)
                        analysis_data = {
                            'keywords': keywords,
                            'summary': summary
                        }
                    except Exception as e:
                        logger.error(f"Content analysis failed: {str(e)}")
                        # Continue even if analysis fails
                        analysis_data = {
                            'error': 'Content analysis failed',
                            'keywords': [],
                            'summary': ''
                        }

                # Initialize title generators
                openai_titles = []
                hf_titles = []
                errors = []

                # Generate titles using OpenAI
                try:
                    openai_generator = OpenAITitleGenerator()
                    openai_titles = openai_generator.generate_titles(content)
                except OpenAIServiceError as e:
                    logger.error(f"OpenAI service error: {str(e)}")
                    errors.append(f"OpenAI service: {str(e)}")
                except Exception as e:
                    logger.error(f"Unexpected error in OpenAI service: {str(e)}")
                    errors.append("OpenAI service unavailable")

                # Generate titles using HuggingFace
                try:
                    hf_generator = HuggingFaceTitleGenerator()
                    hf_titles = hf_generator.generate_titles(content)
                except HuggingFaceServiceError as e:
                    logger.error(f"HuggingFace service error: {str(e)}")
                    errors.append(f"HuggingFace service: {str(e)}")
                except Exception as e:
                    logger.error(f"Unexpected error in HuggingFace service: {str(e)}")
                    errors.append("HuggingFace service unavailable")

                # Combine results
                combined_titles = []
                if openai_titles:
                    combined_titles.extend(openai_titles[:2])
                if hf_titles:
                    combined_titles.extend(hf_titles[:1])

                # Fill up remaining slots if needed
                if len(combined_titles) < 3:
                    if openai_titles and len(openai_titles) > 2:
                        combined_titles.extend(openai_titles[2:3])
                    if len(combined_titles) < 3 and hf_titles and len(hf_titles) > 1:
                        combined_titles.extend(hf_titles[1:3-len(combined_titles)])

                # Ensure we have at most 3 titles
                combined_titles = combined_titles[:3]

                # Check if we have any titles
                if not combined_titles:
                    if errors:
                        error_message = " | ".join(errors)
                        return Response(
                            {'error': f'Failed to generate titles: {error_message}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                    else:
                        return Response(
                            {'error': 'No titles could be generated'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                # Store suggestions
                try:
                    suggestion_request.set_suggested_titles_list(combined_titles)
                    suggestion_request.save()
                except Exception as e:
                    logger.error(f"Failed to save suggestions: {str(e)}")
                    # Continue since we can still return the titles to the user

                # Prepare response
                response_data = {
                    'id': suggestion_request.id,
                    'suggestions': combined_titles
                }

                # Add analysis if requested
                if include_analysis:
                    response_data['analysis'] = analysis_data

                # Add any non-fatal errors
                if errors:
                    response_data['warnings'] = errors

                return Response(response_data, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Unexpected error in title generation: {str(e)}")
                return Response(
                    {'error': 'An unexpected error occurred while processing your request'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Critical error in title suggestion view: {str(e)}")
            return Response(
                {'error': 'A critical error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
