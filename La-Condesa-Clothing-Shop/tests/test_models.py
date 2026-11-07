from datetime import date

from extensions import db
from init_db import initialize_database
from models import (AuditLog, Category, EmployeeProfile, InventoryMovement,
                    Order, OrderItem, Product, ProductColor, ProductImage,
                    ProductSize, User)


def make_user(email='modelo@test.com', role='customer'):
    user = User(name='Usuario Modelo', email=email, role=role)
    user.set_password('Clave123')
    db.session.add(user)
    db.session.commit()
    return user


def make_product(name='Producto Modelo', price=100.0, stock=10, active=True):
    product = Product(name=name, description='Descripcion', base_price=price,
                      category_id=1, is_active=active)
    db.session.add(product)
    db.session.flush()
    db.session.add(ProductSize(product_id=product.id, size='M', stock_quantity=stock))
    db.session.add(ProductColor(product_id=product.id, color='Rojo'))
    db.session.add(ProductImage(product_id=product.id, image_path='images/modelo.png', is_primary=True))
    db.session.commit()
    return product


def test_user_password_roles_and_dict(app):
    user = User(name='Invalido', email='invalido@test.com', role='superadmin')
    user.set_password('Clave123')
    assert user.role == 'customer'
    assert user.check_password('Clave123') is True
    assert user.check_password('Incorrecta1') is False
    assert user.check_password('') is False
    assert user.check_password('a' * 100) is False

    data = user.to_dict()
    assert data['email'] == 'invalido@test.com'
    assert 'password_hash' not in data
    assert data['role'] == 'customer'


def test_password_hashes_are_unique(app):
    first = User(name='Uno', email='uno@test.com')
    second = User(name='Dos', email='dos@test.com')
    first.set_password('Clave123')
    second.set_password('Clave123')
    assert first.password_hash != second.password_hash


def test_order_status_transitions(app):
    user = make_user()
    order = Order(user_id=user.id, order_number='ORD-MODEL-1', status='pending_payment')
    db.session.add(order)
    db.session.commit()

    assert order.update_status('preparing') is False
    assert order.update_status('estado_invalido') is False
    assert order.update_status('paid') is True
    assert order.paid_at is not None
    assert order.update_status('delivered') is False
    assert order.update_status('preparing') is True
    assert order.update_status('ready_for_pickup') is True
    assert order.update_status('delivered') is True
    assert order.delivered_at is not None
    assert order.update_status('cancelled') is False

    data = order.to_dict()
    assert data['order_number'] == 'ORD-MODEL-1'
    assert data['customer']['id'] == user.id
    assert data['items'] == []


def test_order_can_be_cancelled_from_pending_or_paid(app):
    user = make_user(email='cancel@test.com')
    pending = Order(user_id=user.id, order_number='ORD-MODEL-2', status='pending_payment')
    paid = Order(user_id=user.id, order_number='ORD-MODEL-3', status='paid')
    db.session.add_all([pending, paid])
    db.session.commit()

    assert pending.update_status('cancelled') is True
    assert paid.update_status('cancelled') is True


def test_order_item_and_product_dicts(app):
    user = make_user(email='item@test.com')
    product = make_product()
    order = Order(user_id=user.id, order_number='ORD-MODEL-4', subtotal=200,
                  tax=32, total=232, status='delivered', payment_status='verified')
    db.session.add(order)
    db.session.flush()
    item = OrderItem(order_id=order.id, product_id=product.id, size='M',
                     color='Rojo', quantity=2, unit_price=100)
    db.session.add(item)
    db.session.commit()

    assert item.subtotal == 200
    assert item.to_dict()['product_name'] == 'Producto Modelo'
    assert product.get_total_stock() == 10
    product_data = product.to_dict()
    assert product_data['total_stock'] == 10
    assert product_data['sizes'][0]['size'] == 'M'
    assert product_data['colors'][0]['color'] == 'Rojo'
    assert product_data['images'][0]['is_primary'] is True
    assert product_data['category_name'] == 'Mujeres'
    assert product.to_dict(include_stock=False).get('total_stock') is None
    assert db.session.get(Category, 1).to_dict()['name'] == 'Mujeres'


def test_employee_audit_and_movement_dicts(app):
    user = make_user(email='empleado@test.com', role='employee')
    product = make_product(name='Producto Movimiento')

    profile = EmployeeProfile(user_id=user.id, position='Ventas', hire_date=date(2024, 1, 15),
                              salary=5000, emergency_contact='Contacto',
                              emergency_phone='5551234567', notes='Nota')
    movement = InventoryMovement(user_id=user.id, product_id=product.id,
                                 movement_type='purchase', quantity=3, reason='Compra')
    log = AuditLog(user_id=user.id, username=user.name, action='create',
                   entity_type='user', entity_id=user.id, description='Creacion',
                   old_value='{}', new_value='{"a": 1}', ip_address='127.0.0.1')
    db.session.add_all([profile, movement, log])
    db.session.commit()

    assert profile.to_dict()['hire_date'] == '2024-01-15'
    assert movement.to_dict()['product_name'] == 'Producto Movimiento'
    assert movement.to_dict()['user_name'] == user.name
    assert log.to_dict()['action'] == 'create'
    assert log.to_dict()['ip_address'] == '127.0.0.1'


def test_initialize_database_is_idempotent(app):
    with app.app_context():
        initialize_database(app)
        initialize_database(app)
        assert Category.query.count() == 5
        assert User.query.filter_by(email='admin@lacondesa.com').count() == 1
