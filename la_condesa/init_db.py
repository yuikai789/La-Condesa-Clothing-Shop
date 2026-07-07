"""Database initialization script"""
import os
from app import app
from extensions import db
from models import User, Category

def init_database():
    """Initialize the database with default data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default categories
        categories = [
            {'name': 'Mujeres', 'description': 'Ropa y accesorios para mujeres'},
            {'name': 'Hombres', 'description': 'Ropa y accesorios para hombres'},
            {'name': 'Niños', 'description': 'Ropa para niños'},
            {'name': 'Accesorios', 'description': 'Bolsos, zapatos y accesorios'},
            {'name': 'Especiales', 'description': 'Ropa para ocasiones especiales'}
        ]
        
        for cat_data in categories:
            if not Category.query.filter_by(name=cat_data['name']).first():
                category = Category(
                    name=cat_data['name'],
                    description=cat_data['description']
                )
                db.session.add(category)
        
        # Create default administrator
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@lacondesa.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin123!')
        
        if not User.query.filter_by(email=admin_email).first():
            admin = User(
                name='Administrador',
                email=admin_email,
                phone='5555555555',
                role='administrator',
                is_active=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
        
        db.session.commit()
        print('Database initialized successfully!')
        print(f'Admin credentials:')
        print(f'  Email: {admin_email}')
        print(f'  Password: {admin_password}')

if __name__ == '__main__':
    init_database()
