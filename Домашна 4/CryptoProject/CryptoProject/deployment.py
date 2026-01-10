import os
from .settings import *
from pathlib import Path  
from .settings import BASE_DIR

DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = [os.environ['WEBSITE_HOSTNAME']]
CSRF_TRUSTED_ORIGINS = ['https://' + os.environ['WEBSITE_HOSTNAME']]

# WhiteNoise
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware',
              'whitenoise.middleware.WhiteNoiseMiddleware'] + MIDDLEWARE
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ADD STATICFILES_DIRS (for collectstatic to find your CSS/JS)
STATICFILES_DIRS = [
    BASE_DIR / 'cryptoApp' / 'static',  # Your app static folder
    BASE_DIR / 'static',               # Global static (if exists)
]

# MySQL connection
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'crypto_db',
        'USER': 'dbadmin',
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': 'das-hw-db-2026.mysql.database.azure.com',
        'PORT': '3306',
    }
}
