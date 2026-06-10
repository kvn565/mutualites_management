"""
Django settings for mutualite project — Gestion des Mutualités de Santé.
"""

from pathlib import Path
import os

# ═══════════════════════════════════════════════════════════════
#  CHEMINS
# ═══════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent.parent

LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════
#  SÉCURITÉ DE BASE
# ═══════════════════════════════════════════════════════════════

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-changez-en-production-2024!')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',')


# ═══════════════════════════════════════════════════════════════
#  APPLICATIONS INSTALLÉES
# ═══════════════════════════════════════════════════════════════

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',

    # ── Modules socle ─────────────────────────────────────────────
    'core',           # Utilisateur custom, middleware, audit
    'dashboard',      # Tableau de bord
    'superadmin',     # Super administration

    # ── Modules métier ────────────────────────────────────────────
    'affilies',
    'ayants_droit',
    'services_sante',
    'partenaires',
    'origines',
    'factures',
    'cotisations',
    'pharmacie',
    'comptabilite',
    'utilisateurs',
    'ventilations',
    'corbeille',
    'groupe',
    'aide',
]


# ═══════════════════════════════════════════════════════════════
#  MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.MutualiteMiddleware',
    'core.middleware.LicenseMiddleware',
    'core.middleware.AuditLogMiddleware',
    'core.middleware.RateLimitMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ═══════════════════════════════════════════════════════════════
#  URLS & AUTH
# ═══════════════════════════════════════════════════════════════

ROOT_URLCONF = 'mutualite.urls'

AUTH_USER_MODEL    = 'core.Utilisateur'
LOGIN_URL          = '/connexion/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/connexion/'


# ═══════════════════════════════════════════════════════════════
#  TEMPLATES
# ═══════════════════════════════════════════════════════════════

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.mutualite_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'mutualite.wsgi.application'


# ═══════════════════════════════════════════════════════════════
#  DJANGO REST FRAMEWORK
# ═══════════════════════════════════════════════════════════════

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}


# ═══════════════════════════════════════════════════════════════
#  BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── PostgreSQL pour la production ──────────────────────────────
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'mutualite_db',
#         'USER': 'mutualite_user',
#         'PASSWORD': 'votre_mot_de_passe',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }


# ═══════════════════════════════════════════════════════════════
#  CACHE
# ═══════════════════════════════════════════════════════════════

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "mutualite-cache",
    }
}


# ═══════════════════════════════════════════════════════════════
#  RATE LIMITING
# ═══════════════════════════════════════════════════════════════

RATELIMIT_LOGIN_MAX    = 10
RATELIMIT_LOGIN_WINDOW = 300


# ═══════════════════════════════════════════════════════════════
#  SESSIONS
# ═══════════════════════════════════════════════════════════════

SESSION_COOKIE_HTTPONLY         = True
SESSION_COOKIE_SAMESITE         = 'Lax'
SESSION_COOKIE_AGE              = 28800   # 8 heures
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


# ═══════════════════════════════════════════════════════════════
#  SÉCURITÉ
# ═══════════════════════════════════════════════════════════════

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS             = 'SAMEORIGIN'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# ═══════════════════════════════════════════════════════════════
#  VALIDATION MOTS DE PASSE
# ═══════════════════════════════════════════════════════════════

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ═══════════════════════════════════════════════════════════════
#  INTERNATIONALISATION
# ═══════════════════════════════════════════════════════════════

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Bujumbura'

USE_I18N = True
USE_L10N = False
USE_TZ = True

DEFAULT_CURRENCY = 'BIF'

DATE_FORMAT = 'd/m/Y'
TIME_FORMAT = 'H:i'
DATETIME_FORMAT = 'd/m/Y H:i'

DATE_INPUT_FORMATS = [
    '%d/%m/%Y',
    '%d-%m-%Y',
    '%Y-%m-%d',
]

SHORT_DATE_FORMAT = 'd/m/Y'
SHORT_DATETIME_FORMAT = 'd/m/Y H:i'


# ═══════════════════════════════════════════════════════════════
#  FICHIERS STATIQUES & MEDIA
# ═══════════════════════════════════════════════════════════════

STATIC_URL  = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL   = '/media/'
MEDIA_ROOT  = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ═══════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '[{asctime}] [{levelname}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'security.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'security',
            'encoding': 'utf-8',
        },
        'app_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'app.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'security',
        },
    },
    'loggers': {
        'core.security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'app_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}


# ═══════════════════════════════════════════════════════════════
#  PARAMÈTRES MÉTIER — Mutualité
# ═══════════════════════════════════════════════════════════════

MUTUALITE_NOM = "Mutualité de Santé"
MUTUALITE_DEVISE = "BIF"
MUTUALITE_PAYS = "Burundi"
