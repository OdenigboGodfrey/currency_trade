"""
Django settings for currency_trade project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'f6a%(0h*op+0@t%$x7^3p8%(k-s24u+q)^0+&50ct6xd6=if!i'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'pages',
    'Profile',
    'Transactions.apps.TransactionsConfig',
    'CTAdmin',
    'Authentication.apps.AuthenticationConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'storages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'currency_trade.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],

        },
    },
]

WSGI_APPLICATION = 'currency_trade.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'currency_trade',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# sendgrid mail settings
SENDGRID_API_KEY = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'XXXXXXXXXXXXXXXXX'
EMAIL_HOST_PASSWORD = 'XXXXXXXXXXXXXXXXX'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# Toggle sandbox mode (when running in DEBUG mode)
SENDGRID_SANDBOX_MODE_IN_DEBUG=False

# echo to stdout or any other file-like object that is passed to the backend via the stream kwarg.
SENDGRID_ECHO_TO_STDOUT=True

# EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
EMAIL_BACKEND = "sgbackend.SendGridBackend"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

AWS_DEFAULT_ACL = 'public-read'
AWS_ACCESS_KEY_ID = 'XXXXXXXXXXXX'
AWS_SECRET_ACCESS_KEY = 'XXXXXXXXXXXXXXXXXXXXXXX'
AWS_STORAGE_BUCKET_NAME = 'CT-fs'
AWS_S3_CUSTOM_DOMAIN = AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_LOCATION = 'static'
# STATIC_URL = '/static/'

STATIC_URL = 'https://' + AWS_S3_CUSTOM_DOMAIN + '/' + AWS_LOCATION + '/'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'Authentication/static'),
    # os.path.join(BASE_DIR, 'CTAdmin/static'),
]

# STATIC_URL = '/s/'
STATIC_URL_AUTH = 'Authentication/'
MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# STATIC_URL_AUTH +
SELFIEPATH = 'CTAdmin/Uploads/KYC/Selfie/'
ADDRESSPATH = 'CTAdmin/Uploads/KYC/Address/'
BACKIDPATH = 'CTAdmin/Uploads/KYC/BackId/'
FRONTIDPATH = 'CTAdmin/Uploads/KYC/FrontId/'
MEMAT = 'CTAdmin/Uploads/KYC/MEMAT/'
CAC = 'CTAdmin/Uploads/KYC/CAC/'
PROFILEPATH = 'Profile/Uploads/Display/'
TRANSACTIONPATH = 'CTAdmin/Uploads/Transactions/'
TRANSACTIONPATH_ADMIN = 'CTAdmin/Uploads/Transactions/Admin/'

KY_ADMIN = int(0)
T_ADMIN = int(1)
S_ADMIN = int(2)

# User Account Types
ACCOUNT_TYPES = [
    {'Name': 'Personal', 'val': int(1)},
    {'Name': 'Business', 'val': int(2)}
]

LOCAL_UPLOAD = False
ACCEPTED_IMAGE_TYPES = ['jpg', 'png', 'jpeg']



