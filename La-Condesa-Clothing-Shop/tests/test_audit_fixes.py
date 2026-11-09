from datetime import timedelta
from decimal import Decimal

from werkzeug.datastructures import FileStorage

from extensions import db
from models import Product, ProductColor, ProductSize, User
from services.order_service import order_service
from utils import storage
from utils.datetime_utils import utcnow
from utils.tokens import generate_email_token, generate_password_reset_token
from utils.upload import save_payment_receipt
from tests.helpers import png_bytes


def make_user(email='auditoria-fix@test.com', role='customer', verified=True):
    user = User(name='Usuario Fix', email=email, role=role, email_verified=verified)
    user.set_password('Clave123')
    db.session.add(user)
    db.session.commit()
    return user


def make_product(name='Producto Fix', price=100, stock=10):
    product = Product(name=name, description='Descripcion', base_price=Decimal(str(price)),
                      category_id=1, is_active=True)
    db.session.add(product)
    db.session.flush()
    db.session.add(ProductSize(product_id=product.id, size='M', stock_quantity=stock))
    db.session.add(ProductColor(product_id=product.id, color='Rojo'))
    db.session.commit()
    return product


def items(product_id, quantity=1):
    return [{'product_id': product_id, 'size': 'M', 'color': 'Rojo', 'quantity': quantity}]


def test_create_order_reserves_stock_and_prevents_oversell(app):
    user = make_user()
    product = make_product(stock=1)

    first, error = order_service.create_order(user.id, items(product.id), 'Tienda')
    assert error is None

    size = ProductSize.query.filter_by(product_id=product.id, size='M').first()
    db.session.refresh(size)
    assert size.reserved_quantity == 1
    assert size.available_quantity == 0

    _, error = order_service.create_order(user.id, items(product.id), 'Tienda')
    assert error == 'Stock insuficiente para Producto Fix (talla M)'

    _, error = order_service.cancel_order(first.id)
    assert error is None
    db.session.refresh(size)
    assert size.reserved_quantity == 0
    assert size.available_quantity == 1


def test_tax_rate_is_configurable(app, monkeypatch):
    monkeypatch.setitem(app.config, 'TAX_RATE', Decimal('0.10'))
    user = make_user(email='iva@test.com')
    product = make_product(name='Producto IVA', price=50)

    order, error = order_service.create_order(user.id, items(product.id, 2), 'Tienda')

    assert error is None
    assert order.subtotal == Decimal('100.00')
    assert order.tax == Decimal('10.00')
    assert order.total == Decimal('110.00')


def test_register_and_verify_email(client, app):
    response = client.post('/auth/register', data={
        'name': 'Cliente Verifica',
        'email': 'verifica@test.com',
        'password': 'Clave123',
        'phone': '',
    })
    assert response.status_code == 302

    user = User.query.filter_by(email='verifica@test.com').first()
    assert user is not None
    assert user.email_verified is False

    token = generate_email_token(user)
    response = client.get(f'/auth/verify-email/{token}')
    assert response.status_code == 302
    db.session.refresh(user)
    assert user.email_verified is True

    assert client.get('/auth/verify-email/token-invalido').status_code == 302


def test_register_requires_verification_before_login(client, app, monkeypatch):
    monkeypatch.setitem(app.config, 'REQUIRE_EMAIL_VERIFICATION', True)

    response = client.post('/auth/register', data={
        'name': 'Cliente Pendiente',
        'email': 'pendiente@test.com',
        'password': 'Clave123',
        'phone': '',
    })

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')
    assert client.get('/customer/dashboard').status_code == 302


def test_password_reset_flow_and_token_invalidation(client, app):
    user = make_user(email='reset@test.com')
    token = generate_password_reset_token(user)

    response = client.post(f'/auth/reset-password/{token}', data={
        'password': 'NuevaClave1',
        'confirm_password': 'NuevaClave1',
    })
    assert response.status_code == 302

    db.session.refresh(user)
    assert user.check_password('NuevaClave1') is True

    response = client.get(f'/auth/reset-password/{token}')
    assert response.status_code == 302


def test_forgot_password_always_redirects(client, app):
    response = client.post('/auth/forgot-password', data={'email': 'no-existe@test.com'})
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')


def test_cart_expires_after_ttl(admin_client, app):
    from tests.helpers import add_to_cart, create_customer, create_product, login

    create_product(admin_client, name='Producto Carrito TTL')
    create_customer(admin_client, email='ttl@test.com')
    product_id = Product.query.filter_by(name='Producto Carrito TTL').first().id

    admin_client.post('/auth/logout')
    login(admin_client, 'ttl@test.com', 'Cliente123')
    add_to_cart(admin_client, product_id)

    with admin_client.session_transaction() as session:
        session['cart_updated_at'] = (utcnow() - timedelta(hours=2)).isoformat()

    assert admin_client.get('/customer/cart').status_code == 200
    with admin_client.session_transaction() as session:
        assert session['cart'] == {}


def test_receipt_storage_helpers(app):
    path, error = save_payment_receipt(FileStorage(png_bytes(), filename='pago.png'), 42)
    assert error is None
    try:
        assert storage.receipt_exists(path) is True
        assert storage.open_receipt(path).endswith(path.split('/')[-1])
    finally:
        assert storage.delete_receipt(path) is True
    assert storage.receipt_exists(path) is False


def test_s3_storage_helpers(app, monkeypatch, tmp_path):
    monkeypatch.setitem(app.config, 'STORAGE_BACKEND', 's3')
    monkeypatch.setitem(app.config, 'S3_BUCKET', 'bucket-pruebas')
    monkeypatch.setitem(app.config, 'S3_PREFIX', 'recibos')

    calls = {}

    class FakeBody:
        def read(self):
            return b'contenido'

    class FakeClient:
        def upload_file(self, local_path, bucket, key):
            calls['upload'] = (local_path, bucket, key)

        def head_object(self, Bucket, Key):
            calls['head'] = (Bucket, Key)
            return {}

        def get_object(self, Bucket, Key):
            calls['get'] = (Bucket, Key)
            return {'Body': FakeBody()}

        def delete_object(self, Bucket, Key):
            calls['delete'] = (Bucket, Key)

    monkeypatch.setattr(storage, '_s3_client', lambda: FakeClient())

    local_file = tmp_path / 'recibo.png'
    local_file.write_bytes(b'contenido')

    assert storage.upload_file(str(local_file), 'receipts/recibo.png') == 'receipts/recibo.png'
    assert calls['upload'] == (str(local_file), 'bucket-pruebas', 'recibos/receipts/recibo.png')
    assert storage.receipt_exists('receipts/recibo.png') is True
    assert storage.open_receipt('receipts/recibo.png').read() == b'contenido'
    assert storage.delete_receipt('receipts/recibo.png') is True
    assert calls['delete'] == ('bucket-pruebas', 'recibos/receipts/recibo.png')
