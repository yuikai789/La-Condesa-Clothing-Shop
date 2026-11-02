from flask import Blueprint, request, render_template
from flask_login import login_required
from models import Order
from utils.decorators import employee_required
from services.order_service import order_service
from services.inventory_service import inventory_service
from services.analytics_service import analytics_service
from routes.order_actions import run_order_action

employee_bp = Blueprint('employee', __name__)


@employee_bp.route('/dashboard')
@login_required
@employee_required
def dashboard():
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    pending_payment = Order.query.filter_by(payment_status='pending').count()
    low_stock = inventory_service.get_low_stock_products()
    daily_sales = analytics_service.get_daily_sales(days=7)
    monthly_sales = analytics_service.get_sales_summary(days=30)
    top_products = analytics_service.get_top_selling_products(limit=5, days=7)

    return render_template('employee/dashboard.html',
                         recent_orders=recent_orders,
                         pending_payment=pending_payment,
                         low_stock=low_stock,
                         daily_sales=daily_sales,
                         daily_sales_total=sum(sale['total'] for sale in daily_sales),
                         daily_orders_count=sum(sale['orders'] for sale in daily_sales),
                         monthly_sales=monthly_sales,
                         top_products=top_products)


@employee_bp.route('/orders')
@login_required
@employee_required
def orders():
    return render_template('employee/orders.html', orders=order_service.list_orders(request.args.get('status')))


@employee_bp.route('/orders/<int:order_id>/confirm-payment', methods=['POST'])
@login_required
@employee_required
def confirm_payment(order_id):
    return run_order_action(order_id, 'confirm_payment', 'employee.orders', request.form.get('payment_reference'))


@employee_bp.route('/orders/<int:order_id>/prepare', methods=['POST'])
@login_required
@employee_required
def prepare_order(order_id):
    return run_order_action(order_id, 'prepare', 'employee.orders')


@employee_bp.route('/orders/<int:order_id>/ready', methods=['POST'])
@login_required
@employee_required
def mark_order_ready(order_id):
    return run_order_action(order_id, 'ready', 'employee.orders')


@employee_bp.route('/orders/<int:order_id>/deliver', methods=['POST'])
@login_required
@employee_required
def mark_order_delivered(order_id):
    return run_order_action(order_id, 'deliver', 'employee.orders')


@employee_bp.route('/sales')
@login_required
@employee_required
def sales():
    summary = analytics_service.get_sales_summary(days=30)
    top_products = analytics_service.get_top_selling_products(limit=10)

    return render_template('employee/sales.html', summary=summary, top_products=top_products)
