from flask import current_app, has_app_context
from flask_login import UserMixin
import bcrypt
from extensions import db
from utils.datetime_utils import utcnow

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    ROLES = ['administrator', 'employee', 'customer']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default='customer', nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    orders = db.relationship('Order', foreign_keys='Order.user_id', back_populates='customer', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role not in self.ROLES:
            self.role = 'customer'

    def set_password(self, password):
        rounds = current_app.config.get('BCRYPT_LOG_ROUNDS', 12) if has_app_context() else 12
        salt = bcrypt.gensalt(rounds=rounds)
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        if not self.password_hash or not password:
            return False
        encoded = password.encode('utf-8')
        if len(encoded) > 72:
            return False
        try:
            return bcrypt.checkpw(encoded, self.password_hash.encode('utf-8'))
        except (ValueError, TypeError):
            return False

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.name} ({self.role})>'
