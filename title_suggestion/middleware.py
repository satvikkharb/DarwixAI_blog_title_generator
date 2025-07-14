import logging
import json
import traceback
from django.http import JsonResponse
from rest_framework import status

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_exception(e)

    def handle_exception(self, exc):
        error_id = logger.error(f"Unhandled exception: {str(exc)}\n{''.join(traceback.format_tb(exc.__traceback__))}")
        
        # Prepare error response
        error_data = {
            'error': 'An unexpected error occurred',
            'detail': str(exc) if settings.DEBUG else 'Please try again later',
            'error_id': error_id
        }
        
        return JsonResponse(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details
        logger.info(f"Request: {request.method} {request.path}")
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = request.body.decode('utf-8')
                if body:
                    logger.debug(f"Request body: {body}")
            except Exception as e:
                logger.warning(f"Could not log request body: {str(e)}")

        response = self.get_response(request)

        # Log response status
        logger.info(f"Response status: {response.status_code}")
        return response