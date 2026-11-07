import logging
from datetime import datetime
from random import randint
from uuid import uuid4

from flask import has_request_context
from flask_login import current_user
from sqlalchemy import update

from extensions import db
from models import Order, OrderItem, InventoryMovement, ProductSize, Product, ProductColor
from utils.qr_generator import generate_qr_code
from utils.validators import validate_order
from utils.datetime_utils import utcnow
from services.email_service import email_service

logger = logging.getLogger(__name__)


class OrderService:

    def create_order(self, user_id, items, pickup_location=None):
        errors = validate_order({'pickup_location': pickup_location})
        if errors:
            return None, errors

        if not items:
            return None, 'El pedido no contiene productos'

        normalized = []
        for item in items:
            try:
                product_id = int(item.get('product_id'))
                quantity = int(item.get('quantity', 0))
            except (TypeError, ValueError):
                return None, 'Datos de producto inválidos'

            if quantity <= 0:
                return None, 'La cantidad debe ser mayor a cero'

            product = db.session.get(Product, product_id)
            if not product or not product.is_active:
                return None, 'Producto no disponible'

            size_name = item.get('size')
            size_obj = ProductSize.query.filter_by(
                product_id=product_id,
                size=size_name
            ).first()
            if not size_obj:
                return None, f'Talla no disponible para {product.name}'
            if size_obj.stock_quantity < quantity:
                return None, f'Stock insuficiente para {product.name} (talla {size_name})'

            color_name = item.get('color')
            if not ProductColor.query.filter_by(product_id=product_id, color=color_name).first():
                return None, f'Color no disponible para {product.name}'

            normalized.append({
                'product_id': product_id,
                'size': size_name,
                'color': color_name,
                'quantity': quantity,
                'unit_price': float(product.base_price)
            })

        order = Order(
            user_id=user_id,
            order_number=self._generate_order_number(),
            pickup_location=pickup_location
        )
        db.session.add(order)
        db.session.flush()

        total = 0
        for item in normalized:
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=item['product_id'],
                size=item['size'],
                color=item['color'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
            ))
            total += item['quantity'] * item['unit_price']

        order.subtotal = round(total, 2)
        order.tax = round(order.subtotal * 0.16, 2)
        order.total = round(order.subtotal + order.tax, 2)
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
        order = db.session.get(Order, order_id)
        if not order:
            return None, 'Pedido no encontrado'

        if order.status == 'cancelled':
            return None, 'No se puede subir un comprobante de un pedido cancelado'

        if order.payment_status != 'pending':
            return None, 'El pago ya ha sido procesado'

        order.payment_receipt_path = receipt_path
        db.session.commit()
        return order, None

    def confirm_payment(self, order_id, confirmed_by_id, payment_reference=None):
        order = db.session.get(Order, order_id)
        if not order:
            return None, 'Pedido no encontrado'

        if not order.payment_receipt_path:
            return None, 'El cliente aún no ha subido su comprobante de pago'

        if order.payment_status != 'pending':
            return None, 'El pago ya ha sido procesado'

        if not order.update_status('paid'):
            return None, 'No se puede confirmar el pago de este pedido'

        order.payment_status = 'verified'
        order.payment_reference = payment_reference or f"CONF-{utcnow().strftime('%Y%m%d%H%M%S')}"
        order.confirmed_by_id = confirmed_by_id

        db.session.commit()
        return order, None

    def mark_as_preparing(self, order_id):
        order = db.session.get(Order, order_id)
        if not order:
            return None, 'Pedido no encontrado'

        if not order.update_status('preparing'):
            return None, 'No se puede preparar este pedido'

        db.session.commit()
        return order, None

    def mark_as_ready(self, order_id):
        order = db.session.get(Order, order_id)
        if not order:
            return None, 'Pedido no encontrado'

        if not order.update_status('ready_for_pickup'):
            return None, 'No se puede marcar como listo - transición de estado inválida'

        try:
            order.receipt_path = generate_qr_code(order.order_number)
        except Exception as e:
            logger.warning(f'No se pudo generar el QR del pedido {order.order_number}: {e}')
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
        order = db.session.get(Order, order_id)
        if not order:
            return None, 'Pedido no encontrado'

        if not order.update_status('delivered'):
            return None, 'No se puede marcar como entregado - transición de estado inválida'

        actor_id = self._actor_id(order.user_id)
        try:
            for item in order.items:
                result = db.session.execute(
                    update(ProductSize)
                    .where(
                        ProductSize.product_id == item.product_id,
                        ProductSize.size == item.size,
                        ProductSize.stock_quantity >= item.quantity
                    )
                    .values(stock_quantity=ProductSize.stock_quantity - item.quantity)
                )
                if result.rowcount == 0:
                    db.session.rollback()
                    return None, f'Stock insuficiente para {item.product.name} (talla {item.size})'

                db.session.add(InventoryMovement(
                    user_id=actor_id,
                    product_id=item.product_id,
                    movement_type='sale',
                    reason='Vendido',
                    quantity=item.quantity
                ))
        except Exception:
            db.session.rollback()
            logger.exception('Error al actualizar el inventario del pedido %s', order_id)
            return None, 'No se pudo actualizar el inventario'

        db.session.commit()
        return order, None

    def cancel_order(self, order_id):
        order = db.session.get(Order, order_id)
        if not order:
            return None, 'Pedido no encontrado'

        if not order.update_status('cancelled'):
            return None, 'No se puede cancelar este pedido'

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

    def _actor_id(self, fallback_user_id):
        if has_request_context() and getattr(current_user, 'is_authenticated', False):
            return current_user.id
        return fallback_user_id

    def _generate_order_number(self):
        for _ in range(10):
            timestamp = datetime.utcnow().strftime('%y%m%d%H%M')
            number = f"ORD-{timestamp}-{randint(1000, 9999)}"
            if not Order.query.filter_by(order_number=number).first():
                return number
        return f"ORD-{uuid4().hex[:12].upper()}"


order_service = OrderService()
