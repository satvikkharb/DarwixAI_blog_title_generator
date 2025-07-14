"""
ASGI config for blog_title_generator project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_title_generator.settings')

application = get_asgi_application()