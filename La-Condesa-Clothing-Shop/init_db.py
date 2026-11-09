"""Database initialization script"""
import os
from extensions import db
from models import User, Category


def initialize_database(app):
    """Create tables and seed default data (idempotent)."""
    with app.app_context():
        db.create_all()

        categories = [
            {'name': 'Mujeres', 'description': 'Ropa y accesorios para mujeres'},
            {'name': 'Hombres', 'description': 'Ropa y accesorios para hombres'},
            {'name': 'Niños', 'description': 'Ropa para niños'},
            {'name': 'Accesorios', 'description': 'Bolsos, zapatos y accesorios'},
            {'name': 'Especiales', 'description': 'Ropa para ocasiones especiales'}
        ]

        for cat_data in categories:
            if not Category.query.filter_by(name=cat_data['name']).first():
                db.session.add(Category(
                    name=cat_data['name'],
                    description=cat_data['description']
                ))

        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@lacondesa.com')
        admin_password = os.environ.get('ADMIN_PASSWORD')

        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                name='Administrador',
                email=admin_email,
                phone='5555555555',
                role='administrator',
                is_active=True,
                email_verified=True
            )
            admin.set_password(admin_password or 'Admin123!')
            db.session.add(admin)
        elif admin_password:
            admin.set_password(admin_password)

        db.session.commit()
        return admin_email


def init_database():
    from app import app
    admin_email = initialize_database(app)
    print('Database initialized successfully!')
    print('Admin credentials:')
    print(f'  Email: {admin_email}')


if __name__ == '__main__':
    init_database()
