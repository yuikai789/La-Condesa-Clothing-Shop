import os

from extensions import db
from models import Order, Product, ProductSize
from tests.helpers import (add_to_cart, checkout, create_customer, create_product,
                           login, png_bytes)


def setup_store(admin_client, app, product_name='Producto Cliente', stock='10',
                customer_email='cliente@test.com'):
    create_product(admin_client, name=product_name, stock=stock)
    create_customer(admin_client, email=customer_email)
    product_id = Product.query.filter_by(name=product_name).first().id
    admin_client.post('/auth/logout')
    login(admin_client, customer_email, 'Cliente123')
    return product_id


def cart_post(client, **data):
    return client.post('/customer/cart', data=data)


def test_cart_requires_customer(client):
    assert client.get('/customer/cart').status_code == 302
    assert client.post('/customer/cart', data={'action': 'clear'}).status_code == 302


def test_cart_add_validations(admin_client, app):
    product_id = setup_store(admin_client, app)

    assert cart_post(admin_client, action='add', product_id='abc', quantity='1',
                     size='M', color='Rojo').status_code == 400
    assert cart_post(admin_client, action='add', product_id=str(product_id), quantity='0',
                     size='M', color='Rojo').status_code == 400
    assert cart_post(admin_client, action='add', product_id='9999', quantity='1',
                     size='M', color='Rojo').status_code == 404
    assert cart_post(admin_client, action='add', product_id=str(product_id), quantity='1',
                     size='XL', color='Rojo').status_code == 400
    assert cart_post(admin_client, action='add', product_id=str(product_id), quantity='1',
                     size='M', color='Azul').status_code == 400
    assert cart_post(admin_client, action='add', product_id=str(product_id), quantity='99',
                     size='M', color='Rojo').status_code == 400

    product = db.session.get(Product, product_id)
    product.is_active = False
    db.session.commit()
    assert cart_post(admin_client, action='add', product_id=str(product_id), quantity='1',
                     size='M', color='Rojo').status_code == 400


def test_cart_add_update_remove_clear(admin_client, app):
    product_id = setup_store(admin_client, app)

    response = add_to_cart(admin_client, product_id, quantity=1)
    assert response.status_code == 200
    assert response.get_json()['cart_key'] == f'{product_id}_M_Rojo'

    response = add_to_cart(admin_client, product_id, quantity=2)
    assert response.status_code == 200
    with admin_client.session_transaction() as session:
        assert session['cart'][f'{product_id}_M_Rojo']['quantity'] == 2

    key = f'{product_id}_M_Rojo'
    assert cart_post(admin_client, action='update', cart_key=key,
                     quantity='abc').status_code == 400
    assert cart_post(admin_client, action='update', cart_key=key,
                     quantity='0').status_code == 400
    assert cart_post(admin_client, action='update', cart_key=key,
                     quantity='99').status_code == 400
    assert cart_post(admin_client, action='update', cart_key=key,
                     quantity='3').status_code == 200
    assert cart_post(admin_client, action='update', cart_key='no-existe',
                     quantity='1').status_code == 200

    assert cart_post(admin_client, action='remove', cart_key=key).status_code == 200
    assert cart_post(admin_client, action='remove', cart_key='no-existe').status_code == 200
    assert cart_post(admin_client, action='clear').status_code == 200
    assert admin_client.get('/customer/cart').status_code == 200


def test_checkout_empty_cart(admin_client, app):
    create_customer(admin_client, email='vacio@test.com')
    admin_client.post('/auth/logout')
    login(admin_client, 'vacio@test.com', 'Cliente123')

    response = checkout(admin_client)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/customer/cart')
    assert Order.query.count() == 0


def test_checkout_removes_unavailable_items(admin_client, app):
    product_id = setup_store(admin_client, app, product_name='Producto No Disponible',
                             customer_email='nodisponible@test.com')
    add_to_cart(admin_client, product_id, quantity=2)

    size = ProductSize.query.filter_by(product_id=product_id, size='M').first()
    size.stock_quantity = 1
    db.session.commit()

    response = checkout(admin_client)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/customer/cart')
    assert Order.query.count() == 0
    with admin_client.session_transaction() as session:
        assert session['cart'] == {}


def test_checkout_success_and_order_detail(admin_client, app):
    product_id = setup_store(admin_client, app, product_name='Producto Checkout',
                             customer_email='checkout@test.com')
    add_to_cart(admin_client, product_id, quantity=2)

    response = checkout(admin_client, pickup_location='Tienda Centro')
    assert response.status_code == 302
    order = Order.query.order_by(Order.id.desc()).first()
    assert response.headers['Location'].endswith(f'/customer/orders/{order.id}')
    assert order.total == 232.0
    assert order.pickup_location == 'Tienda Centro'
    with admin_client.session_transaction() as session:
        assert session['cart'] == {}

    assert admin_client.get(f'/customer/orders/{order.id}').status_code == 200
    assert admin_client.get('/customer/orders').status_code == 200
    assert admin_client.get('/customer/dashboard').status_code == 200


def test_checkout_rejects_long_pickup_location(admin_client, app):
    product_id = setup_store(admin_client, app, product_name='Producto Ubicacion',
                             customer_email='ubicacion@test.com')
    add_to_cart(admin_client, product_id)

    response = checkout(admin_client, pickup_location='x' * 101)
    assert response.status_code == 400
    assert 'pickup_location' in response.get_json()['error']


def test_order_detail_ownership_and_missing(admin_client, app):
    product_id = setup_store(admin_client, app, product_name='Producto Propiedad',
                             customer_email='dueno@test.com')
    add_to_cart(admin_client, product_id)
    checkout(admin_client)
    order_id = Order.query.order_by(Order.id.desc()).first().id
    admin_client.post('/auth/logout')

    login(admin_client, 'admin@lacondesa.com', 'Admin123!')
    create_customer(admin_client, email='intruso@test.com')
    admin_client.post('/auth/logout')
    login(admin_client, 'intruso@test.com', 'Cliente123')
    response = admin_client.get(f'/customer/orders/{order_id}')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')
    assert admin_client.get('/customer/orders/9999').status_code == 404


def test_receipt_access_control(admin_client, app):
    product_id = setup_store(admin_client, app, product_name='Producto Recibo',
                             customer_email='recibo@test.com')
    add_to_cart(admin_client, product_id)
    checkout(admin_client)
    order = Order.query.order_by(Order.id.desc()).first()

    response = admin_client.post(
        f'/customer/orders/{order.id}/upload-receipt',
        data={'receipt': (png_bytes(), 'recibo.png')},
        content_type='multipart/form-data',
    )
    assert response.status_code == 302
    db.session.refresh(order)
    assert order.payment_receipt_path.startswith('receipts/')

    receipt_file = os.path.join(app.config['RECEIPTS_FOLDER'],
                                os.path.basename(order.payment_receipt_path))
    try:
        assert os.path.isfile(receipt_file)
        assert admin_client.get(f'/customer/orders/{order.id}/receipt').status_code == 200
        assert admin_client.get(
            '/static/receipts/' + os.path.basename(order.payment_receipt_path)
        ).status_code == 404

        admin_client.post('/auth/logout')
        login(admin_client, 'admin@lacondesa.com', 'Admin123!')
        create_customer(admin_client, email='otro-recibo@test.com')
        admin_client.post('/auth/logout')
        login(admin_client, 'otro-recibo@test.com', 'Cliente123')
        assert admin_client.get(f'/customer/orders/{order.id}/receipt').status_code == 403

        admin_client.post('/auth/logout')
        response = admin_client.get(f'/customer/orders/{order.id}/receipt')
        assert response.status_code == 302

        login(admin_client, 'admin@lacondesa.com', 'Admin123!')
        assert admin_client.get(f'/customer/orders/{order.id}/receipt').status_code == 200
        assert admin_client.get('/customer/orders/9999/receipt').status_code == 404
    finally:
        if os.path.isfile(receipt_file):
            os.remove(receipt_file)


def test_upload_receipt_validations(admin_client, app):
    product_id = setup_store(admin_client, app, product_name='Producto Subida',
                             customer_email='subida@test.com')
    add_to_cart(admin_client, product_id)
    checkout(admin_client)
    order = Order.query.order_by(Order.id.desc()).first()

    response = admin_client.post(f'/customer/orders/{order.id}/upload-receipt',
                                 data={}, content_type='multipart/form-data')
    assert response.status_code == 302
    db.session.refresh(order)
    assert order.payment_receipt_path is None

    response = admin_client.post(
        f'/customer/orders/{order.id}/upload-receipt',
        data={'receipt': (png_bytes(), 'archivo.txt')},
        content_type='multipart/form-data',
    )
    assert response.status_code == 302
    db.session.refresh(order)
    assert order.payment_receipt_path is None

    order.status = 'cancelled'
    db.session.commit()
    response = admin_client.post(
        f'/customer/orders/{order.id}/upload-receipt',
        data={'receipt': (png_bytes(), 'recibo.png')},
        content_type='multipart/form-data',
    )
    assert response.status_code == 302
    db.session.refresh(order)
    assert order.payment_receipt_path is None

    order.status = 'pending_payment'
    order.payment_status = 'verified'
    db.session.commit()
    response = admin_client.post(
        f'/customer/orders/{order.id}/upload-receipt',
        data={'receipt': (png_bytes(), 'recibo.png')},
        content_type='multipart/form-data',
    )
    assert response.status_code == 302
    db.session.refresh(order)
    assert order.payment_receipt_path is None


def test_upload_receipt_rejects_other_customer(admin_client, app):
    product_id = setup_store(admin_client, app, product_name='Producto Ajeno',
                             customer_email='propietario@test.com')
    add_to_cart(admin_client, product_id)
    checkout(admin_client)
    order_id = Order.query.order_by(Order.id.desc()).first().id
    admin_client.post('/auth/logout')

    login(admin_client, 'admin@lacondesa.com', 'Admin123!')
    create_customer(admin_client, email='ajeno@test.com')
    admin_client.post('/auth/logout')
    login(admin_client, 'ajeno@test.com', 'Cliente123')
    response = admin_client.post(
        f'/customer/orders/{order_id}/upload-receipt',
        data={'receipt': (png_bytes(), 'recibo.png')},
        content_type='multipart/form-data',
    )
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')
