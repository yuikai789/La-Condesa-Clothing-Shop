from .public import public_bp
from .auth import auth_bp
from .customer import customer_bp
from .employee import employee_bp
from .admin import admin_bp

__all__ = ['public_bp', 'auth_bp', 'customer_bp', 'employee_bp', 'admin_bp']
