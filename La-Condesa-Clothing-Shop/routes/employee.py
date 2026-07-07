from flask import Blueprint, request, redirect, url_for, render_template, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Order, Product, AuditLog
from utils.decorators import employee_required
from services.order_service import order_service
from services.inventory_service import inventory_service
from services.analytics_service import analytics_service
from services.audit_service import audit_service

employee_bp = Blueprint('employee', __name__)


@employee_bp.route('/dashboard')
@login_required
@employee_required
def dashboard():
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    pending_payment = Order.query.filter_by(payment_status='pending').count()

    low_stock = inventory_service.get_low_stock_products()

    daily_sales = analytics_service.get_daily_sales(days=7)
    daily_sales_total = sum(sale['total'] for sale in daily_sales)
    daily_orders_count = sum(sale['orders'] for sale in daily_sales)

    monthly_sales = analytics_service.get_sales_summary(days=30)

    top_products = analytics_service.get_top_selling_products(limit=5, days=7)

    return render_template('employee/dashboard.html',
                         recent_orders=recent_orders,
                         pending_payment=pending_payment,
                         low_stock=low_stock,
                         daily_sales=daily_sales,
                         daily_sales_total=daily_sales_total,
                         daily_orders_count=daily_orders_count,
                         monthly_sales=monthly_sales,
                         top_products=top_products)


@employee_bp.route('/orders')
@login_required
@employee_required
def orders():
    status = request.args.get('status')

    query = Order.query
    if status:
        query = query.filter_by(status=status)

    all_orders = query.order_by(Order.created_at.desc()).all()
    return render_template('employee/orders.html', orders=all_orders)


@employee_bp.route('/orders/<int:order_id>/confirm-payment', methods=['POST'])
@login_required
@employee_required
def confirm_payment(order_id):
    order = Order.query.get(order_id)
    if not order:
        flash('Pedido no encontrado', 'error')
        return redirect(url_for('employee.orders'))

    payment_reference = request.form.get('payment_reference')

    order, error = order_service.confirm_payment(
        order_id, current_user.id, payment_reference
    )

    if error:
        flash(f'Error: {error}', 'error')
    else:
        audit_service.log(
            user_id=current_user.id, username=current_user.name,
            action='confirm_payment', entity_type='order', entity_id=order_id,
            description=f'Pago confirmado para orden {order.order_number}',
            new_value={'status': 'paid'}, ip_address=request.remote_addr
        )
        flash('Pago confirmado exitosamente', 'success')

    return redirect(url_for('employee.orders'))


@employee_bp.route('/orders/<int:order_id>/prepare', methods=['POST'])
@login_required
@employee_required
def prepare_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        flash('Pedido no encontrado', 'error')
        return redirect(url_for('employee.orders'))

    if order.update_status('preparing'):
        db.session.commit()
        audit_service.log(
            user_id=current_user.id, username=current_user.name,
            action='update_status', entity_type='order', entity_id=order_id,
            description=f'Orden {order.order_number} marcada como preparando',
            new_value={'status': 'preparing'}, ip_address=request.remote_addr
        )
        flash('Pedido marcado como preparando', 'success')
    else:
        flash('No se puede preparar este pedido', 'error')

    return redirect(url_for('employee.orders'))


@employee_bp.route('/orders/<int:order_id>/ready', methods=['POST'])
@login_required
@employee_required
def mark_order_ready(order_id):
    order = Order.query.get(order_id)
    if not order:
        flash('Pedido no encontrado', 'error')
        return redirect(url_for('employee.orders'))

    order, error = order_service.mark_as_ready(order_id)

    if error:
        flash(f'Error: {error}', 'error')
    else:
        audit_service.log(
            user_id=current_user.id, username=current_user.name,
            action='update_status', entity_type='order', entity_id=order_id,
            description=f'Orden {order.order_number} marcada como lista para recoger',
            new_value={'status': 'ready_for_pickup'}, ip_address=request.remote_addr
        )
        flash('Pedido marcado como listo para recoger', 'success')

    return redirect(url_for('employee.orders'))


@employee_bp.route('/orders/<int:order_id>/deliver', methods=['POST'])
@login_required
@employee_required
def mark_order_delivered(order_id):
    order = Order.query.get(order_id)
    if not order:
        flash('Pedido no encontrado', 'error')
        return redirect(url_for('employee.orders'))

    order, error = order_service.mark_as_delivered(order_id)

    if error:
        flash(f'Error: {error}', 'error')
    else:
        audit_service.log(
            user_id=current_user.id, username=current_user.name,
            action='update_status', entity_type='order', entity_id=order_id,
            description=f'Orden {order.order_number} marcada como entregada',
            new_value={'status': 'delivered'}, ip_address=request.remote_addr
        )
        flash('Pedido marcado como entregado', 'success')

    return redirect(url_for('employee.orders'))


@employee_bp.route('/sales')
@login_required
@employee_required
def sales():
    summary = analytics_service.get_sales_summary(days=30)
    top_products = analytics_service.get_top_selling_products(limit=10)

    return render_template('employee/sales.html',
                         summary=summary,
                         top_products=top_products)
