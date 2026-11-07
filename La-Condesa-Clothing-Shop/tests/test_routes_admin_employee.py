import os
from datetime import date

import pytest

from extensions import db
from models import (EmployeeProfile, InventoryMovement, Order, OrderItem,
                    Product, ProductColor, ProductImage, ProductSize, User)
from routes.order_actions import run_order_action
from services.order_service import order_service
from tests.helpers import (add_to_cart, checkout, create_customer, create_product,
                           login, png_bytes)


def make_user(email, role='employee'):
    user = User(name='Usuario Admin Test', email=email, role=role)
    user.set_password('Clave123')
    db.session.add(user)
    db.session.commit()
    return user


def product_by_name(name):
    return Product.query.filter_by(name=name).first()


def test_admin_user_crud_and_audit(admin_client, app):
    response = admin_client.post('/admin/users', data={
        'name': 'A', 'email': 'mal', 'password': 'corta',
        'phone': 'abc', 'role': 'customer',
    })
    assert response.status_code == 200
    assert User.query.filter_by(email='mal').first() is None

    response = admin_client.post('/admin/users', data={
        'name': 'Rol Malo', 'email': 'rolmalo@test.com', 'password': 'Clave123',
        'phone': '5551234567', 'role': 'superadmin',
    })
    assert response.status_code == 200
    assert User.query.filter_by(email='rolmalo@test.com').first() is None

    response = admin_client.post('/admin/users', data={
        'name': 'Empleado Nuevo', 'email': 'empleado-nuevo@test.com',
        'password': 'Clave123', 'phone': '5551234567', 'role': 'employee',
    })
    assert response.status_code == 302
    employee = User.query.filter_by(email='empleado-nuevo@test.com').first()
    assert employee is not None
    employee_id = employee.id

    response = admin_client.post('/admin/users', data={
        'name': 'Empleado Nuevo', 'email': 'empleado-nuevo@test.com',
        'password': 'Clave123', 'phone': '5551234567', 'role': 'employee',
    })
    assert response.status_code == 200
    assert User.query.filter_by(email='empleado-nuevo@test.com').count() == 1

    for data in (
        {'name': 'A', 'email': 'empleado-nuevo@test.com', 'role': 'employee'},
        {'name': 'Valido', 'email': 'mal', 'role': 'employee'},
        {'name': 'Valido', 'email': 'empleado-nuevo@test.com', 'phone': 'abc', 'role': 'employee'},
        {'name': 'Valido', 'email': 'empleado-nuevo@test.com', 'role': 'root'},
    ):
        response = admin_client.post(f'/admin/users/{employee_id}', data=data)
        assert response.status_code == 302

    db.session.expire_all()
    employee = db.session.get(User, employee_id)
    assert employee.name == 'Empleado Nuevo'
    assert employee.role == 'employee'

    make_user('duplicado@test.com', role='customer')
    response = admin_client.post(f'/admin/users/{employee_id}', data={
        'name': 'Duplicado', 'email': 'duplicado@test.com',
        'phone': '5551234567', 'role': 'employee', 'password': '',
    })
    assert response.status_code == 302
    db.session.expire_all()
    assert db.session.get(User, employee_id).email == 'empleado-nuevo@test.com'

    response = admin_client.post(f'/admin/users/{employee_id}', data={
        'name': 'Empleado Actualizado', 'email': 'actualizado@test.com',
        'phone': '5550001111', 'role': 'employee', 'password': 'Nueva123',
    })
    assert response.status_code == 302
    db.session.expire_all()
    employee = db.session.get(User, employee_id)
    assert employee.name == 'Empleado Actualizado'
    assert employee.email == 'actualizado@test.com'
    assert employee.phone == '5550001111'
    assert employee.check_password('Nueva123') is True

    assert admin_client.get('/admin/users?page=1').status_code == 200
    assert admin_client.get('/admin/audit-logs').status_code == 200
    assert admin_client.get(
        '/admin/audit-logs?entity_type=user&action=create').status_code == 200


@pytest.mark.parametrize('role', ['customer', 'employee', 'administrator'])
def test_admin_creates_user_with_each_role(admin_client, app, role):
    email = f'creado-{role}@test.com'
    response = admin_client.post('/admin/users', data={
        'name': 'Usuario Creado', 'email': email, 'password': 'Clave123',
        'phone': '5551234567', 'role': role,
    })
    assert response.status_code == 302

    created = User.query.filter_by(email=email).first()
    assert created is not None
    assert created.role == role

    first_page = admin_client.get('/admin/users').get_data(as_text=True)
    assert email in first_page


def test_admin_create_user_allows_weak_password(admin_client, app):
    response = admin_client.post('/admin/users', data={
        'name': 'Clave Simple', 'email': 'clave-simple@test.com', 'password': '1234',
        'phone': '', 'role': 'employee',
    })
    assert response.status_code == 302
    created = User.query.filter_by(email='clave-simple@test.com').first()
    assert created is not None
    assert created.check_password('1234') is True


def test_admin_create_user_requires_password(admin_client, app):
    response = admin_client.post('/admin/users', data={
        'name': 'Sin Clave', 'email': 'sin-clave@test.com', 'password': '',
        'phone': '', 'role': 'employee',
    })
    assert response.status_code == 200
    assert 'La contraseña es obligatoria' in response.get_data(as_text=True)
    assert User.query.filter_by(email='sin-clave@test.com').first() is None


def test_admin_delete_user_rules(admin_client, app):
    admin_id = User.query.filter_by(email='admin@lacondesa.com').first().id
    response = admin_client.post(f'/admin/users/{admin_id}/delete')
    assert response.status_code == 302
    assert db.session.get(User, admin_id) is not None

    with_order = make_user('con-pedido@test.com', role='customer')
    db.session.add(Order(user_id=with_order.id, order_number='ORD-DEL-1',
                         status='pending_payment'))
    db.session.commit()
    admin_client.post(f'/admin/users/{with_order.id}/delete')
    assert db.session.get(User, with_order.id) is not None

    employee = make_user('borrar-perfil@test.com', role='employee')
    profile = EmployeeProfile(user_id=employee.id, position='Ventas')
    db.session.add(profile)
    db.session.commit()
    profile_id = profile.id
    admin_client.post(f'/admin/users/{employee.id}/delete')
    db.session.expire_all()
    assert db.session.get(User, employee.id) is None
    assert db.session.get(EmployeeProfile, profile_id) is None


def test_admin_product_crud_with_images(admin_client, app):
    created_files = []
    response = admin_client.post('/admin/products', data={
        'name': 'Producto Imagen',
        'description': 'Con imagen',
        'base_price': '100',
        'category_id': '1',
        'sizes[]': 'S,M',
        'stocks[]': '1,2',
        'colors[]': 'Rojo,Azul',
        'image': (png_bytes(), 'producto.png'),
    }, content_type='multipart/form-data')
    assert response.status_code == 302

    product = product_by_name('Producto Imagen')
    assert product is not None
    assert product.sizes.count() == 2
    assert product.colors.count() == 2
    image = ProductImage.query.filter_by(product_id=product.id).first()
    assert image is not None
    first_image = image.image_path
    created_files.append(os.path.join(app.root_path, 'static', first_image))
    assert os.path.isfile(created_files[-1])

    product_id = product.id
    response = admin_client.post(f'/admin/products/{product_id}', data={
        'name': 'Producto Imagen Actualizado',
        'description': 'Nueva',
        'base_price': '120',
        'category_id': '2',
        'is_active': 'on',
        'image': (png_bytes(), 'nueva.png'),
    }, content_type='multipart/form-data')
    assert response.status_code == 302
    db.session.expire_all()
    product = db.session.get(Product, product_id)
    assert product.name == 'Producto Imagen Actualizado'
    assert product.base_price == 120.0
    assert product.category_id == 2
    assert first_image not in [i.image_path for i in product.images]
    second_image = product.images.first().image_path
    created_files.append(os.path.join(app.root_path, 'static', second_image))
    assert not os.path.isfile(created_files[0])
    assert os.path.isfile(created_files[1])

    for data in (
        {'name': '', 'base_price': '10', 'category_id': '1'},
        {'name': 'Producto Imagen Actualizado', 'base_price': 'abc', 'category_id': '1'},
        {'name': 'Producto Imagen Actualizado', 'base_price': '10', 'category_id': '999'},
    ):
        response = admin_client.post(f'/admin/products/{product_id}', data=data)
        assert response.status_code == 302

    response = admin_client.post(f'/admin/products/{product_id}', data={
        'name': 'Producto Desactivado',
        'base_price': '120',
        'category_id': '2',
    })
    assert response.status_code == 302
    db.session.expire_all()
    product = db.session.get(Product, product_id)
    assert product.is_active is False

    response = admin_client.post(f'/admin/products/{product_id}/delete')
    assert response.status_code == 302
    db.session.expire_all()
    assert db.session.get(Product, product_id) is None
    assert not os.path.isfile(created_files[1])
    assert admin_client.get('/admin/products').status_code == 200


def test_product_delete_blocked_with_orders(admin_client, app):
    create_product(admin_client, name='Producto Con Pedido')
    product = product_by_name('Producto Con Pedido')
    admin_id = User.query.filter_by(email='admin@lacondesa.com').first().id
    order = Order(user_id=admin_id, order_number='ORD-DEL-2', status='pending_payment')
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderItem(order_id=order.id, product_id=product.id, size='M',
                             color='Rojo', quantity=1, unit_price=100))
    db.session.commit()
    product_id = product.id

    admin_client.post(f'/admin/products/{product_id}/delete')
    db.session.expire_all()
    assert db.session.get(Product, product_id) is not None


def test_admin_inventory_movement_flow(admin_client, app):
    create_product(admin_client, name='Producto Movimiento Admin', stock='5')
    product = product_by_name('Producto Movimiento Admin')

    invalid_posts = [
        {'product_id': 'abc', 'movement_type': 'purchase', 'quantity': '1'},
        {'product_id': str(product.id), 'movement_type': 'invalido', 'quantity': '1'},
        {'product_id': str(product.id), 'movement_type': 'purchase', 'quantity': 'abc'},
        {'product_id': str(product.id), 'movement_type': 'purchase', 'quantity': '0'},
        {'product_id': '9999', 'movement_type': 'purchase', 'quantity': '1'},
        {'product_id': str(product.id), 'size': 'XL', 'movement_type': 'purchase',
         'quantity': '1'},
        {'product_id': str(product.id), 'movement_type': 'loss', 'quantity': '100'},
    ]
    for data in invalid_posts:
        response = admin_client.post('/admin/inventory/movements', data=data)
        assert response.status_code == 302

    for movement_type, quantity, expected in (
        ('purchase', '3', 8),
        ('return', '2', 10),
        ('loss', '1', 9),
        ('correction', '2', 7),
    ):
        response = admin_client.post('/admin/inventory/movements', data={
            'product_id': str(product.id),
            'movement_type': movement_type,
            'quantity': quantity,
            'reason': 'Prueba',
        })
        assert response.status_code == 302
        db.session.expire_all()
        size = ProductSize.query.filter_by(product_id=product.id, size='M').first()
        assert size.stock_quantity == expected

    movements = InventoryMovement.query.filter_by(product_id=product.id).all()
    assert len(movements) == 4
    assert all(movement.user_id == 1 for movement in movements)
    assert admin_client.get('/admin/inventory').status_code == 200

    no_sizes = Product(name='Sin Tallas', base_price=10, category_id=1)
    db.session.add(no_sizes)
    db.session.commit()
    response = admin_client.post('/admin/inventory/movements', data={
        'product_id': str(no_sizes.id),
        'movement_type': 'purchase',
        'quantity': '1',
    })
    assert response.status_code == 302


def test_admin_exports(admin_client, app):
    for export_type in ('summary', 'sales', 'products', 'desconocido'):
        response = admin_client.get(f'/admin/analytics/export?type={export_type}')
        assert response.status_code == 200
        assert response.headers['Content-Type'].startswith('text/csv')
        assert 'attachment' in response.headers['Content-Disposition']

    for export_type in ('financial', 'monthly', 'profit', 'status', 'otro'):
        response = admin_client.get(
            f'/admin/financial-reports/export?type={export_type}&days=7')
        assert response.status_code == 200
        assert response.headers['Content-Type'].startswith('text/csv')
        assert 'attachment' in response.headers['Content-Disposition']

    response = admin_client.get('/admin/financial-reports/export?type=financial&days=99')
    assert response.status_code == 200
    assert '30d' in response.headers['Content-Disposition']
    assert admin_client.get('/admin/financial-reports?days=7').status_code == 200
    assert admin_client.get('/admin/financial-reports?days=99').status_code == 200


def test_admin_employee_profiles(admin_client, app):
    customer = make_user('cliente-perfil@test.com', role='customer')
    response = admin_client.post(f'/admin/employees/{customer.id}/profile', data={
        'position': 'No permitido'})
    assert response.status_code == 302
    assert customer.employee_profile is None

    employee = make_user('empleado-perfil@test.com', role='employee')
    response = admin_client.post(f'/admin/employees/{employee.id}/profile', data={
        'position': 'Ventas',
        'hire_date': '2024-01-15',
        'salary': '5000',
        'emergency_contact': 'Contacto',
        'emergency_phone': '5551234567',
        'notes': 'Notas',
    })
    assert response.status_code == 302
    db.session.expire_all()
    employee = db.session.get(User, employee.id)
    profile = employee.employee_profile
    assert profile.position == 'Ventas'
    assert profile.hire_date == date(2024, 1, 15)
    assert profile.salary == 5000.0

    response = admin_client.post(f'/admin/employees/{employee.id}/profile', data={
        'position': 'Caja',
        'hire_date': 'fecha-invalida',
        'salary': 'no-numero',
    })
    assert response.status_code == 302
    db.session.expire_all()
    profile = db.session.get(User, employee.id).employee_profile
    assert profile.position == 'Caja'
    assert profile.hire_date == date(2024, 1, 15)
    assert profile.salary == 5000.0
    assert admin_client.get('/admin/employees').status_code == 200


def test_employee_pages_and_order_actions(admin_client, app):
    create_product(admin_client, name='Producto Empleado', stock='10')
    create_customer(admin_client, email='cliente-empleado@test.com')
    product = product_by_name('Producto Empleado')
    customer = User.query.filter_by(email='cliente-empleado@test.com').first()
    order, error = order_service.create_order(
        customer.id,
        [{'product_id': product.id, 'size': 'M', 'color': 'Rojo', 'quantity': 2}],
        'Tienda',
    )
    assert error is None
    order.payment_receipt_path = 'receipts/pago.png'
    db.session.commit()
    order_id = order.id

    employee = make_user('empleado-acciones@test.com')
    admin_client.post('/auth/logout')
    login(admin_client, employee.email, 'Clave123')

    for path in ('/employee/dashboard', '/employee/orders', '/employee/sales'):
        assert admin_client.get(path).status_code == 200
    assert admin_client.get('/admin/dashboard').status_code == 403

    for action in ('confirm-payment', 'prepare', 'ready', 'deliver'):
        response = admin_client.post(f'/employee/orders/{order_id}/{action}')
        assert response.status_code == 302

    db.session.expire_all()
    order = db.session.get(Order, order_id)
    assert order.status == 'delivered'
    size = ProductSize.query.filter_by(product_id=product.id, size='M').first()
    assert size.stock_quantity == 8

    qr_path = order.receipt_path
    if qr_path:
        full_path = os.path.join(app.root_path, 'static', qr_path)
        if os.path.isfile(full_path):
            os.remove(full_path)


def test_unknown_order_action_raises(app):
    with pytest.raises(ValueError):
        run_order_action(1, 'accion-desconocida', 'admin.orders')
