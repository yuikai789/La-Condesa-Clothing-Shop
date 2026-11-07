import os
from datetime import timedelta

import pytest

from extensions import db, mail
from models import (InventoryMovement, Order, OrderItem, Product, ProductColor,
                    ProductSize, User)
from services.analytics_service import analytics_service
from services.audit_service import audit_service
from services.email_service import email_service
from services.inventory_service import inventory_service
from services.order_service import order_service
from utils.datetime_utils import utcnow


def make_user(email='servicio@test.com', role='customer'):
    user = User(name='Usuario Servicio', email=email, role=role)
    user.set_password('Clave123')
    db.session.add(user)
    db.session.commit()
    return user


def make_product(name='Producto Servicio', price=100.0, stock=10, active=True):
    product = Product(name=name, description='Descripcion', base_price=price,
                      category_id=1, is_active=active)
    db.session.add(product)
    db.session.flush()
    db.session.add(ProductSize(product_id=product.id, size='M', stock_quantity=stock))
    db.session.add(ProductColor(product_id=product.id, color='Rojo'))
    db.session.commit()
    return product


def make_delivered_order(user_id, product_id, quantity=1, unit_price=100.0,
                         total=116.0, days_ago=0, status='delivered',
                         number=None):
    order = Order(
        user_id=user_id,
        order_number=number or f'ORD-AN-{utcnow().strftime("%H%M%S%f")}',
        subtotal=quantity * unit_price,
        tax=round(quantity * unit_price * 0.16, 2),
        total=total,
        status=status,
        payment_status='verified',
        created_at=utcnow() - timedelta(days=days_ago),
    )
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderItem(order_id=order.id, product_id=product_id, size='M',
                             color='Rojo', quantity=quantity, unit_price=unit_price))
    db.session.commit()
    return order


def order_items(product_id, quantity=1, size='M', color='Rojo'):
    return [{'product_id': product_id, 'size': size, 'color': color,
             'quantity': quantity, 'unit_price': 1}]


def test_create_order_calculates_totals_and_uses_server_price(app):
    user = make_user()
    product = make_product(price=100)

    order, error = order_service.create_order(user.id, order_items(product.id, 2), 'Tienda')

    assert error is None
    assert order.status == 'pending_payment'
    assert order.subtotal == 200.0
    assert order.tax == 32.0
    assert order.total == 232.0
    assert order.order_number.startswith('ORD-')
    item = order.items.first()
    assert item.unit_price == 100.0
    assert item.subtotal == 200.0


def test_create_order_accepts_missing_pickup_location(app):
    user = make_user(email='sin-pickup@test.com')
    product = make_product(name='Sin Pickup')

    order, error = order_service.create_order(user.id, order_items(product.id), None)

    assert error is None
    assert order.pickup_location is None


def test_create_order_validation_errors(app):
    user = make_user(email='errores@test.com')
    product = make_product(name='Producto Errores', stock=2)

    _, error = order_service.create_order(user.id, [], 'Tienda')
    assert error == 'El pedido no contiene productos'

    _, error = order_service.create_order(user.id, [{'product_id': 'x', 'quantity': 1}], 'Tienda')
    assert error == 'Datos de producto inválidos'

    _, error = order_service.create_order(user.id, order_items(product.id, 0), 'Tienda')
    assert error == 'La cantidad debe ser mayor a cero'

    _, error = order_service.create_order(user.id, order_items(9999), 'Tienda')
    assert error == 'Producto no disponible'

    _, error = order_service.create_order(user.id, order_items(product.id, 1, size='XL'), 'Tienda')
    assert error == 'Talla no disponible para Producto Errores'

    _, error = order_service.create_order(user.id, order_items(product.id, 3), 'Tienda')
    assert error == 'Stock insuficiente para Producto Errores (talla M)'

    _, error = order_service.create_order(user.id, order_items(product.id, 1, color='Azul'), 'Tienda')
    assert error == 'Color no disponible para Producto Errores'

    _, errors = order_service.create_order(user.id, order_items(product.id), 'x' * 101)
    assert 'pickup_location' in errors


def test_create_order_rejects_inactive_product(app):
    user = make_user(email='inactivo@test.com')
    product = make_product(name='Inactivo', active=False)

    _, error = order_service.create_order(user.id, order_items(product.id), 'Tienda')
    assert error == 'Producto no disponible'


def test_upload_receipt_and_confirm_payment(app):
    user = make_user(email='pago@test.com')
    product = make_product(name='Producto Pago')
    order, _ = order_service.create_order(user.id, order_items(product.id), 'Tienda')

    _, error = order_service.upload_receipt(9999, 'receipts/no.png')
    assert error == 'Pedido no encontrado'

    _, error = order_service.confirm_payment(order.id, user.id)
    assert error == 'El cliente aún no ha subido su comprobante de pago'

    updated, error = order_service.upload_receipt(order.id, 'receipts/pago.png')
    assert error is None
    assert updated.payment_receipt_path == 'receipts/pago.png'

    confirmed, error = order_service.confirm_payment(order.id, user.id, 'REF-MANUAL')
    assert error is None
    assert confirmed.status == 'paid'
    assert confirmed.payment_status == 'verified'
    assert confirmed.payment_reference == 'REF-MANUAL'
    assert confirmed.confirmed_by_id == user.id
    assert confirmed.paid_at is not None

    _, error = order_service.confirm_payment(order.id, user.id)
    assert error == 'El pago ya ha sido procesado'
    _, error = order_service.upload_receipt(order.id, 'receipts/otro.png')
    assert error == 'El pago ya ha sido procesado'


def test_confirm_payment_without_valid_transition(app):
    user = make_user(email='transicion@test.com')
    product = make_product(name='Producto Transicion')
    order, _ = order_service.create_order(user.id, order_items(product.id), 'Tienda')
    order.payment_receipt_path = 'receipts/pago.png'
    order.status = 'delivered'
    db.session.commit()

    _, error = order_service.confirm_payment(order.id, user.id)
    assert error == 'No se puede confirmar el pago de este pedido'


def test_upload_receipt_rejects_cancelled_order(app):
    user = make_user(email='cancelado@test.com')
    product = make_product(name='Producto Cancelado')
    order, _ = order_service.create_order(user.id, order_items(product.id), 'Tienda')
    order.status = 'cancelled'
    db.session.commit()

    _, error = order_service.upload_receipt(order.id, 'receipts/pago.png')
    assert error == 'No se puede subir un comprobante de un pedido cancelado'


def test_prepare_ready_deliver_flow(app):
    user = make_user(email='flujo@test.com')
    product = make_product(name='Producto Flujo', stock=10)
    order, _ = order_service.create_order(user.id, order_items(product.id, 2), 'Tienda')
    order.payment_receipt_path = 'receipts/pago.png'
    db.session.commit()

    _, error = order_service.mark_as_preparing(order.id)
    assert error == 'No se puede preparar este pedido'

    order_service.confirm_payment(order.id, user.id)
    _, error = order_service.mark_as_preparing(order.id)
    assert error is None
    _, error = order_service.mark_as_ready(order.id)
    assert error is None

    qr_path = order.receipt_path
    try:
        assert qr_path.startswith('images/qrcodes/')
        _, error = order_service.mark_as_delivered(order.id)
        assert error is None
        size = ProductSize.query.filter_by(product_id=product.id, size='M').first()
        assert size.stock_quantity == 8
        movement = InventoryMovement.query.filter_by(product_id=product.id,
                                                     movement_type='sale').first()
        assert movement.quantity == 2
        assert movement.user_id == user.id
    finally:
        if qr_path:
            path = os.path.join(app.root_path, 'static', qr_path)
            if os.path.isfile(path):
                os.remove(path)


def test_deliver_rolls_back_when_stock_is_insufficient(app):
    user = make_user(email='rollback@test.com')
    product = make_product(name='Producto Rollback', stock=10)
    order, _ = order_service.create_order(user.id, order_items(product.id, 3), 'Tienda')
    size = ProductSize.query.filter_by(product_id=product.id, size='M').first()
    size.stock_quantity = 1
    order.status = 'ready_for_pickup'
    db.session.commit()

    _, error = order_service.mark_as_delivered(order.id)

    assert error == 'Stock insuficiente para Producto Rollback (talla M)'
    db.session.refresh(size)
    db.session.refresh(order)
    assert size.stock_quantity == 1
    assert order.status == 'ready_for_pickup'
    assert InventoryMovement.query.filter_by(product_id=product.id,
                                             movement_type='sale').count() == 0


def test_cancel_order_and_list_orders(app):
    user = make_user(email='listar@test.com')
    product = make_product(name='Producto Listar')
    first, _ = order_service.create_order(user.id, order_items(product.id), 'Tienda')
    second, _ = order_service.create_order(user.id, order_items(product.id), 'Tienda')

    _, error = order_service.cancel_order(first.id)
    assert error is None
    assert first.status == 'cancelled'
    assert first.payment_status == 'cancelled'
    _, error = order_service.cancel_order(first.id)
    assert error == 'No se puede cancelar este pedido'

    assert len(order_service.list_orders()) == 2
    assert len(order_service.list_orders('pending_payment')) == 1
    assert len(order_service.list_orders('cancelled')) == 1
    assert second.status == 'pending_payment'


def test_missing_order_errors(app):
    assert order_service.upload_receipt(9999, 'x')[1] == 'Pedido no encontrado'
    assert order_service.confirm_payment(9999, 1)[1] == 'Pedido no encontrado'
    assert order_service.mark_as_preparing(9999)[1] == 'Pedido no encontrado'
    assert order_service.mark_as_ready(9999)[1] == 'Pedido no encontrado'
    assert order_service.mark_as_delivered(9999)[1] == 'Pedido no encontrado'
    assert order_service.cancel_order(9999)[1] == 'Pedido no encontrado'


def test_inventory_service_stock_and_movements(app):
    user = make_user(email='inventario@test.com', role='administrator')
    product = make_product(name='Producto Inventario', stock=5)

    _, error = inventory_service.update_stock(product.id, 'XL', 1, 'purchase', user_id=user.id)
    assert error == 'Talla de producto no encontrada'

    _, error = inventory_service.update_stock(product.id, 'M', -10, 'loss', user_id=user.id)
    assert error == 'Stock insuficiente'

    result, error = inventory_service.update_stock(product.id, 'M', 3, 'purchase',
                                                   reason='Compra', user_id=user.id)
    assert error is None
    assert result.stock_quantity == 8

    result, error = inventory_service.update_stock(product.id, 'M', 2, 'return',
                                                   reason='Devolucion', user_id=user.id)
    assert error is None
    assert result.stock_quantity == 10

    result, error = inventory_service.update_stock(product.id, 'M', -4, 'loss',
                                                   reason='Perdida', user_id=user.id)
    assert error is None
    assert result.stock_quantity == 6

    movements = inventory_service.get_inventory_movements(product_id=product.id)
    assert len(movements) == 3
    assert {m.movement_type for m in movements} == {'purchase', 'return', 'loss'}
    assert all(m.quantity > 0 for m in movements)
    assert len(inventory_service.get_inventory_movements(limit=1)) == 1

    low_stock = inventory_service.get_low_stock_products()
    assert product not in low_stock


def test_low_stock_excludes_inactive_and_high_stock(app):
    make_product(name='Stock Bajo', stock=2)
    make_product(name='Stock Alto', stock=50)
    make_product(name='Inactivo Bajo', stock=1, active=False)

    low_stock = inventory_service.get_low_stock_products()
    names = {product.name for product in low_stock}
    assert 'Stock Bajo' in names
    assert 'Stock Alto' not in names
    assert 'Inactivo Bajo' not in names


def test_analytics_summaries(app):
    user = make_user(email='analitica@test.com')
    product = make_product(name='Producto Analitica', price=100)
    make_delivered_order(user.id, product.id, quantity=2, unit_price=100,
                         total=232, number='ORD-AN-ACTUAL')
    make_delivered_order(user.id, product.id, quantity=1, unit_price=100,
                         total=116, days_ago=60, number='ORD-AN-VIEJO')
    make_delivered_order(user.id, product.id, quantity=1, unit_price=100,
                         total=116, days_ago=400, number='ORD-AN-MUY-VIEJO')
    make_delivered_order(user.id, product.id, quantity=1, unit_price=100,
                         total=116, status='pending_payment', number='ORD-AN-PENDIENTE')

    daily = analytics_service.get_daily_sales(days=30)
    assert len(daily) == 1
    assert daily[0]['orders'] == 1
    assert daily[0]['total'] == 232.0

    top = analytics_service.get_top_selling_products(days=30)
    assert top[0]['name'] == 'Producto Analitica'
    assert top[0]['total_sold'] == 2

    summary = analytics_service.get_financial_summary(days=30)
    assert summary['total_revenue'] == 232.0
    assert summary['total_orders'] == 1
    assert summary['total_items'] == 2
    assert summary['avg_order_value'] == 232.0
    assert summary['period_days'] == 30

    monthly = analytics_service.get_monthly_sales(months=6)
    assert len(monthly) == 6
    assert monthly[-1]['revenue'] == 232.0
    assert monthly[-1]['orders'] == 1

    profit, total_revenue = analytics_service.get_profit_by_product(days=30)
    assert total_revenue == 200.0
    assert profit[0]['percentage'] == 100.0

    breakdown = analytics_service.get_order_status_breakdown()
    assert breakdown['delivered']['count'] == 3
    assert breakdown['pending_payment']['count'] == 1
    assert breakdown['cancelled']['count'] == 0


def test_analytics_export_escapes_csv_injection():
    data = [{'name': '=1+1', 'value': '+cmd', 'safe': 'ok', 'empty': None}]
    output = analytics_service.export_to_csv(data, 'export.csv')
    assert "name,value,safe,empty" in output
    assert "'=1+1" in output
    assert "'+cmd" in output
    assert analytics_service.export_to_csv([], 'vacio.csv') == ''


def test_audit_service_logs_and_filters(app):
    user = make_user(email='auditoria@test.com', role='administrator')

    first = audit_service.log(user_id=user.id, username=user.name, action='create',
                              entity_type='product', entity_id=1,
                              old_value=None, new_value={'name': 'Producto'},
                              ip_address='127.0.0.1')
    audit_service.log(user_id=user.id, username=user.name, action='update',
                      entity_type='user', entity_id=2,
                      old_value={'x': 1}, new_value={'x': 2})

    assert first.new_value == '{"name": "Producto"}'
    assert audit_service.count_logs() == 2
    assert audit_service.count_logs(entity_type='product') == 1
    assert audit_service.count_logs(action='update') == 1
    assert audit_service.count_logs(user_id=user.id) == 2
    assert len(audit_service.get_logs(entity_type='product')) == 1


def test_email_service_success_and_failure(app, monkeypatch):
    assert email_service.app_debug() is True
    monkeypatch.setattr(mail, 'send', lambda message: None)
    assert email_service.send_email('Asunto', ['destino@test.com'], html='<p>Hola</p>') is True

    def fail_send(message):
        raise RuntimeError('sin servidor')

    recorded = {}
    monkeypatch.setattr(mail, 'send', fail_send)
    monkeypatch.setattr(email_service, '_log_email_failure',
                        lambda subject, recipients, error: recorded.update(
                            subject=subject, recipients=recipients, error=error))
    monkeypatch.setitem(app.config, 'DEBUG', False)

    assert email_service.send_email('Fallo', ['destino@test.com']) is False
    assert recorded['subject'] == 'Fallo'
    assert recorded['error'] == 'sin servidor'
