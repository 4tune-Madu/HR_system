from .base import *


DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "10.0.1.37",
]

CORS_ALLOWED_ORIGINS += [
    "http://10.0.1.37:5175",
]

CSRF_TRUSTED_ORIGINS += [
    "http://10.0.1.37:5175",
]
