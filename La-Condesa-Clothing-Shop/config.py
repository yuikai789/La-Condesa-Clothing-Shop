import os
import secrets
from datetime import timedelta
from decimal import Decimal, InvalidOperation


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _env_int(name, default):
    raw = os.environ.get(name)
    if raw is None:
        raw = str(default)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _env_decimal(name, default):
    raw = os.environ.get(name)
    if raw is None:
        raw = str(default)
    try:
        return Decimal(raw)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _database_uri():
    uri = os.environ.get('DATABASE_URL') or 'sqlite:///la_condesa.db'
    if uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql://', 1)
    if uri.startswith('postgresql://'):
        uri = uri.replace('postgresql://', 'postgresql+psycopg://', 1)
    return uri


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or None
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
    }

    SESSION_PERMANENT = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = _env_int('MAIL_PORT', 1025)
    MAIL_USE_TLS = _env_bool('MAIL_USE_TLS', False)
    MAIL_USE_SSL = _env_bool('MAIL_USE_SSL', False)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@lacondesa.com')

    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images')
    RECEIPTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'receipts')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # External object storage for payment receipts (local by default)
    STORAGE_BACKEND = os.environ.get('STORAGE_BACKEND', 'local').strip().lower()
    S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_REGION = os.environ.get('S3_REGION')
    S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL')
    S3_ACCESS_KEY_ID = os.environ.get('S3_ACCESS_KEY_ID') or os.environ.get('AWS_ACCESS_KEY_ID')
    S3_SECRET_ACCESS_KEY = os.environ.get('S3_SECRET_ACCESS_KEY') or os.environ.get('AWS_SECRET_ACCESS_KEY')
    S3_PREFIX = os.environ.get('S3_PREFIX', 'receipts')

    # Fiscal configuration
    TAX_RATE = _env_decimal('TAX_RATE', '0.16')

    # Cart
    CART_TTL_MINUTES = _env_int('CART_TTL_MINUTES', 60)

    # Account verification / recovery
    REQUIRE_EMAIL_VERIFICATION = _env_bool('REQUIRE_EMAIL_VERIFICATION', False)
    EMAIL_VERIFICATION_MAX_AGE = _env_int('EMAIL_VERIFICATION_MAX_AGE', 86400)
    PASSWORD_RESET_MAX_AGE = _env_int('PASSWORD_RESET_MAX_AGE', 3600)

    BCRYPT_LOG_ROUNDS = 12
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # Rate limiting
    RATELIMIT_ENABLED = _env_bool('RATELIMIT_ENABLED', True)
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per hour')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025

    @staticmethod
    def init_app(app):
        if not app.config.get('SECRET_KEY'):
            app.config['SECRET_KEY'] = secrets.token_hex(32)
            app.logger.warning(
                'SECRET_KEY no configurada: se generó una clave efímera para desarrollo. '
                'Define SECRET_KEY en el entorno para mantener sesiones entre reinicios.'
            )


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_SAMESITE = 'Strict'

    @staticmethod
    def init_app(app):
        secret = os.environ.get('SECRET_KEY') or app.config.get('SECRET_KEY')
        if not secret or secret in ('dev-secret-key-change-in-production', 'your-secret-key-here-change-in-production'):
            raise RuntimeError('SECRET_KEY debe configurarse con un valor seguro en producción')

        database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if database_uri.startswith('sqlite'):
            app.logger.warning(
                'Producción con SQLite: usa DATABASE_URL de PostgreSQL para evitar pérdida de datos '
                'en entornos con sistema de archivos efímero.'
            )
        if app.config.get('STORAGE_BACKEND') != 's3':
            app.logger.warning(
                'Producción con recibos locales: configura STORAGE_BACKEND=s3 para persistir los '
                'comprobantes fuera del disco efímero.'
            )


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
