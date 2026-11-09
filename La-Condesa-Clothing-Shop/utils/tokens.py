import hashlib

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

EMAIL_SALT = 'la-condesa-email-verification'
PASSWORD_SALT = 'la-condesa-password-reset'


def _serializer(salt):
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=salt)


def password_fragment(password_hash):
    return hashlib.sha256((password_hash or '').encode('utf-8')).hexdigest()[:16]


def generate_email_token(user):
    return _serializer(EMAIL_SALT).dumps({'uid': user.id, 'email': user.email})


def load_email_token(token, max_age):
    try:
        return _serializer(EMAIL_SALT).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None


def generate_password_reset_token(user):
    return _serializer(PASSWORD_SALT).dumps({
        'uid': user.id,
        'ph': password_fragment(user.password_hash)
    })


def load_password_reset_token(token, max_age):
    try:
        return _serializer(PASSWORD_SALT).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
