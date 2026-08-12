import os

# Flask configuration
DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() in {'1', 'true', 'yes'}
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')