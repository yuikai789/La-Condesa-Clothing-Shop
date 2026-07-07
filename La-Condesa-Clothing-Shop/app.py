from flask import Flask, render_template, session
from flask_login import current_user
import os

from config import config
from extensions import db, login_manager, migrate, mail, csrf

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)

    from routes.public import public_bp
    from routes.auth import auth_bp
    from routes.customer import customer_bp
    from routes.employee import employee_bp
    from routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(employee_bp, url_prefix='/employee')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from models import User
    from utils.sessions import track_session_activity

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_request
    def track_session():
        if current_user.is_authenticated:
            track_session_activity()

    @app.template_filter('status_es')
    def status_es(status):
        STATUS_MAP = {
            'pending_payment': 'Pendiente de pago',
            'paid': 'Pagado',
            'preparing': 'Preparando',
            'ready_for_pickup': 'Listo para recoger',
            'delivered': 'Entregado',
            'cancelled': 'Cancelado',
        }
        return STATUS_MAP.get(status, status)

    @app.template_filter('role_es')
    def role_es(role):
        ROLE_MAP = {
            'administrator': 'Administrador',
            'employee': 'Empleado',
            'customer': 'Cliente',
        }
        return ROLE_MAP.get(role, role)

    @app.template_filter('payment_status_es')
    def payment_status_es(status):
        PAYMENT_MAP = {
            'pending': 'Pendiente',
            'verified': 'Verificado',
            'cancelled': 'Cancelado',
        }
        return PAYMENT_MAP.get(status, status)

    @app.context_processor
    def inject_cart_count():
        cart = session.get('cart', {})
        count = sum(item.get('quantity', 0) for item in cart.values())
        return {'cart_count': count}

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
