import os

from extensions import db
from models import Order, Product, ProductSize
from services.order_service import order_service
from tests.helpers import (add_to_cart, checkout, create_customer, create_product, login,
                           png_bytes)


def test_public_pages(client):
    for path in ('/', '/catalog', '/about', '/contact', '/auth/login', '/auth/register'):
        response = client.get(path)
        assert response.status_code == 200, path


def test_full_access_requires_authentication(client):
    for path in ('/admin/dashboard', '/employee/dashboard', '/customer/dashboard'):
        response = client.get(path)
        assert response.status_code == 302, path


def test_admin_pages_load(admin_client):
    for path in ('/admin/dashboard', '/admin/users', '/admin/products', '/admin/orders',
                 '/admin/inventory', '/admin/analytics', '/admin/employees',
                 '/admin/audit-logs', '/admin/financial-reports'):
        response = admin_client.get(path)
        assert response.status_code == 200, path


def test_role_restrictions(admin_client):
    create_customer(admin_client)
    admin_client.post('/auth/logout')

    login(admin_client, 'cliente@test.com', 'Cliente123')
    assert admin_client.get('/customer/dashboard').status_code == 200
    assert admin_client.get('/admin/dashboard').status_code == 403
    assert admin_client.get('/employee/orders').status_code == 403

    admin_client.post('/auth/logout')
    login(admin_client, 'admin@lacondesa.com', 'Admin123!')
    assert admin_client.get('/customer/dashboard').status_code == 403


def test_product_validation(admin_client, app):
    create_product(admin_client, name='Categoria Invalida', category_id='999')
    create_product(admin_client, name='Stock Invalido', stock='no-numero')
    create_product(admin_client, name='Producto Valido')

    with app.app_context():
        assert Product.query.filter_by(name='Categoria Invalida').first() is None
        assert Product.query.filter_by(name='Stock Invalido').first() is None
        assert Product.query.filter_by(name='Producto Valido').first() is not None


def test_order_lifecycle_and_qr(admin_client, app):
    create_product(admin_client)
    create_customer(admin_client)

    with app.app_context():
        product = Product.query.filter_by(name='Producto Test').first()
        product_id = product.id

    admin_client.post('/auth/logout')
    login(admin_client, 'cliente@test.com', 'Cliente123')
    assert add_to_cart(admin_client, product_id, quantity=2).status_code == 200
    assert checkout(admin_client).status_code == 302

    with app.app_context():
        order = Order.query.order_by(Order.id.desc()).first()
        order_id = order.id
        assert order.status == 'pending_payment'
        assert order.total == 232.0

    response = admin_client.post(
        f'/customer/orders/{order_id}/upload-receipt',
        data={'receipt': (png_bytes(), 'receipt.png')},
        content_type='multipart/form-data',
    )
    assert response.status_code == 302
    assert admin_client.get(f'/customer/orders/{order_id}/receipt').status_code == 200

    admin_client.post('/auth/logout')
    login(admin_client, 'admin@lacondesa.com', 'Admin123!')
    for action in ('confirm-payment', 'prepare', 'ready', 'deliver'):
        response = admin_client.post(f'/admin/orders/{order_id}/{action}')
        assert response.status_code == 302, action

    with app.app_context():
        order = db.session.get(Order, order_id)
        size = ProductSize.query.filter_by(product_id=product_id, size='M').first()
        assert order.status == 'delivered'
        assert size.stock_quantity == 8
        assert order.receipt_path.startswith('images/qrcodes/')
        qr_path = order.receipt_path
        receipt_path = order.payment_receipt_path

    assert admin_client.get('/static/' + qr_path).status_code == 200

    qr_file = os.path.join(app.root_path, 'static', qr_path)
    if os.path.isfile(qr_file):
        os.remove(qr_file)
    receipt_file = os.path.join(app.config['RECEIPTS_FOLDER'], os.path.basename(receipt_path))
    if os.path.isfile(receipt_file):
        os.remove(receipt_file)


def test_cancel_order_updates_payment_status(admin_client, app):
    create_product(admin_client, name='Producto Cancelable')
    create_customer(admin_client, email='cancel@test.com')

    with app.app_context():
        product_id = Product.query.filter_by(name='Producto Cancelable').first().id

    admin_client.post('/auth/logout')
    login(admin_client, 'cancel@test.com', 'Cliente123')
    add_to_cart(admin_client, product_id)
    checkout(admin_client)

    with app.app_context():
        order_id = Order.query.order_by(Order.id.desc()).first().id
        size_before = ProductSize.query.filter_by(product_id=product_id, size='M').first().stock_quantity

    admin_client.post('/auth/logout')
    login(admin_client, 'admin@lacondesa.com', 'Admin123!')
    assert admin_client.post(f'/admin/orders/{order_id}/cancel').status_code == 302

    with app.app_context():
        order = db.session.get(Order, order_id)
        size_after = ProductSize.query.filter_by(product_id=product_id, size='M').first().stock_quantity
        assert order.status == 'cancelled'
        assert order.payment_status == 'cancelled'
        assert size_before == size_after


def test_inventory_returns_and_oversell(admin_client, app):
    create_product(admin_client, name='Producto Inventario', stock='5')

    with app.app_context():
        product_id = Product.query.filter_by(name='Producto Inventario').first().id

    admin_client.post('/admin/inventory/movements', data={
        'product_id': str(product_id),
        'size': 'M',
        'movement_type': 'return',
        'quantity': '3',
        'reason': 'Devolucion',
    })
    with app.app_context():
        assert ProductSize.query.filter_by(product_id=product_id, size='M').first().stock_quantity == 8

    admin_client.post('/admin/inventory/movements', data={
        'product_id': str(product_id),
        'size': 'M',
        'movement_type': 'loss',
        'quantity': '100',
        'reason': 'Prueba',
    })
    with app.app_context():
        assert ProductSize.query.filter_by(product_id=product_id, size='M').first().stock_quantity == 8


def test_logout_requires_post(client):
    assert client.get('/auth/logout').status_code == 405
    assert client.post('/auth/logout').status_code == 302


def test_order_service_rejects_invalid_quantity(app):
    with app.app_context():
        _, error = order_service.create_order(1, [{'product_id': 1, 'quantity': 0}], 'Tienda')
        assert error == 'La cantidad debe ser mayor a cero'
