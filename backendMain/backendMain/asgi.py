"""
ASGI config for backendMain project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from django.core.asgi import get_asgi_application

# Load .env from project root if present
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
	load_dotenv(env_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')

application = get_asgi_application()
