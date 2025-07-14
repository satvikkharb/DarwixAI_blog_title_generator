"""
WSGI config for blog_title_generator project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_title_generator.settings')

application = get_wsgi_application()