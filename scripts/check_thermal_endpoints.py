import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geglca.settings')

import django
django.setup()

from django.test import Client
from django.conf import settings

settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

client = Client()

urls = [
    '/api/ekobaudat-material/8/thermal_u/',
    '/api/ekobaudat-material/1312/thermal_u/',
    '/api/ekobaudat-material/352/thermal_u/',
    '/api/ekobaudat-material/603/thermal_u/',
]

for url in urls:
    response = client.get(url)
    print(url, response.status_code, response.content.decode())
