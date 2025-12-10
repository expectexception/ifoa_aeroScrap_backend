"""
WSGI config for backendMain project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from django.core.wsgi import get_wsgi_application

# Load .env from project root if present (helps when deploying with env file)
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
	load_dotenv(env_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')

application = get_wsgi_application()
