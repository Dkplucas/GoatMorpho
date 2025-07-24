"""
WSGI config for goat_measure project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goat_measure.settings')

application = get_wsgi_application()