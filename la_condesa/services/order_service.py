from datetime import datetime, timedelta
from extensions import db
from models import Order, OrderItem, InventoryMovement
from utils.qr_generator import generate_qr_code
from utils.validators import validate_order
from services.email_service import email_service

class OrderService:

    def create_order(self, user_id, items, pickup_location=None):
        data = {'pickup_location': pickup_location}
        errors = validate_order(data)
        if errors:
            return None, errors

        order = Order(
            user_id=user_id,
            order_number=self._generate_order_number(),
            pickup_location=pickup_location
        )
        db.session.add(order)
        db.session.flush()

        total = 0
        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product_id'],
                size=item['size'],
                color=item['color'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
            )
            db.session.add(order_item)
            total += item['quantity'] * item['unit_price']

        order.subtotal = total
        order.tax = total * 0.16
        order.total = order.subtotal + order.tax

        db.session.commit()

        email_service.send_order_confirmation(
            order=order,
            customer_email=order.customer.email,
            customer_name=order.customer.name,
            order_items=order.items
        )

        return order, None

    def upload_receipt(self, order_id, receipt_path):
        order = Order.query.get(order_id)
        if not order:
            return None, 'Pedido no encontrado'

        if order.payment_status != 'pending':
            return None, 'El pago ya ha sido procesado'

        order.payment_receipt_path = receipt_path
        db.session.commit()
        return order, None

    def confirm_payment(self, order_id, confirmed_by_id, payment_reference=None):
        order = Order.query.get(order_id)
        if not order:
            return None, 'Pedido no encontrado'

        if not order.payment_receipt_path:
            return None, 'El cliente aún no ha subido su comprobante de pago'

        if order.payment_status != 'pending':
            return None, 'El pago ya ha sido procesado'

        order.payment_status = 'verified'
        order.payment_reference = payment_reference or f"CONF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        order.confirmed_by_id = confirmed_by_id
        order.update_status('paid')

        db.session.commit()
        return order, None

    def mark_as_ready(self, order_id):
        order = Order.query.get(order_id)
        if not order:
            return None, 'Pedido no encontrado'

        if not order.update_status('ready_for_pickup'):
            return None, 'No se puede marcar como listo - transición de estado inválida'

        qr_path = generate_qr_code(order.order_number)
        order.receipt_path = qr_path

        db.session.commit()

        email_service.send_order_ready(
            order=order,
            customer_email=order.customer.email,
            customer_name=order.customer.name
        )

        return order, None

    def mark_as_delivered(self, order_id):
        order = Order.query.get(order_id)
        if not order:
            return None, 'Pedido no encontrado'

        if not order.update_status('delivered'):
            return None, 'No se puede marcar como entregado - transición de estado inválida'

        for item in order.items:
            movement = InventoryMovement(
                user_id=order.user_id,
                product_id=item.product_id,
                movement_type='sale',
                reason='Vendido',
                quantity=item.quantity
            )
            db.session.add(movement)
            from models import ProductSize
            size = ProductSize.query.filter_by(
                product_id=item.product_id,
                size=item.size
            ).first()
            if size:
                size.stock_quantity = max(0, size.stock_quantity - item.quantity)

        db.session.commit()
        return order, None

    def _generate_order_number(self):
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        from random import randint
        return f"ORD-{timestamp}-{randint(1000, 9999)}"

order_service = OrderService()
