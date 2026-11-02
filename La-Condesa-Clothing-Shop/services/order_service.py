import logging
from datetime import datetime
from random import randint
from extensions import db
from models import Order, OrderItem, InventoryMovement, ProductSize
from utils.qr_generator import generate_qr_code
from utils.validators import validate_order
from services.email_service import email_service

logger = logging.getLogger(__name__)


class OrderService:

    def create_order(self, user_id, items, pickup_location=None):
        errors = validate_order({'pickup_location': pickup_location})
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
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=item['product_id'],
                size=item['size'],
                color=item['color'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
            ))
            total += item['quantity'] * item['unit_price']

        order.subtotal = total
        order.tax = total * 0.16
        order.total = order.subtotal + order.tax
        db.session.commit()

        self._safe_email(
            email_service.send_order_confirmation,
            f'la confirmación del pedido {order.order_number}',
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

    def mark_as_preparing(self, order_id):
        order = Order.query.get(order_id)
        if not order:
            return None, 'Pedido no encontrado'

        if not order.update_status('preparing'):
            return None, 'No se puede preparar este pedido'

        db.session.commit()
        return order, None

    def mark_as_ready(self, order_id):
        order = Order.query.get(order_id)
        if not order:
            return None, 'Pedido no encontrado'

        if not order.update_status('ready_for_pickup'):
            return None, 'No se puede marcar como listo - transición de estado inválida'

        order.receipt_path = generate_qr_code(order.order_number)
        db.session.commit()

        self._safe_email(
            email_service.send_order_ready,
            f"el aviso 'listo' del pedido {order.order_number}",
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
            db.session.add(InventoryMovement(
                user_id=order.user_id,
                product_id=item.product_id,
                movement_type='sale',
                reason='Vendido',
                quantity=item.quantity
            ))
            size = ProductSize.query.filter_by(
                product_id=item.product_id,
                size=item.size
            ).first()
            if size:
                size.stock_quantity = max(0, size.stock_quantity - item.quantity)

        db.session.commit()
        return order, None

    def list_orders(self, status=None):
        query = Order.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Order.created_at.desc()).all()

    def _safe_email(self, sender, description, **kwargs):
        try:
            sender(**kwargs)
        except Exception as e:
            logger.warning(f"No se pudo enviar {description}: {e}")

    def _generate_order_number(self):
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"ORD-{timestamp}-{randint(1000, 9999)}"


order_service = OrderService()
