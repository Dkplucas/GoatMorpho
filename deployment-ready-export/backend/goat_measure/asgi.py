"""
ASGI config for goat_measure project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goat_measure.settings')

application = get_asgi_application()