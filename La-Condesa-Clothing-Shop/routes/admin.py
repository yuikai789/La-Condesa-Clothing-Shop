import json
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, render_template, flash, jsonify, make_response
from flask_login import login_required, current_user
from extensions import db
from models import User, Product, Category, ProductSize, ProductColor, ProductImage, Order, InventoryMovement, AuditLog, EmployeeProfile
from utils.validators import validate_registration, validate_product
from utils.decorators import admin_required
from utils.pagination import paginate_query
from services.inventory_service import inventory_service
from services.analytics_service import analytics_service
from services.order_service import order_service
from services.audit_service import audit_service
from utils.upload import save_image, delete_image

admin_bp = Blueprint('admin', __name__)


def _audit(action, entity_type, entity_id, description, old_value=None, new_value=None):
    audit_service.log(
        user_id=current_user.id,
        username=current_user.name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        old_value=old_value,
        new_value=new_value,
        ip_address=request.remote_addr
    )


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    summary = analytics_service.get_sales_summary(days=30)

    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         recent_orders=recent_orders,
                         summary=summary)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    pagination = paginate_query(User.query, page)
    return render_template('admin/users.html', users=pagination.items, users_json=[u.to_dict() for u in pagination.items], pagination=pagination)


@admin_bp.route('/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    data = {
        'name': request.form.get('name', ''),
        'email': request.form.get('email', ''),
        'password': request.form.get('password', ''),
        'phone': request.form.get('phone', ''),
        'role': request.form.get('role', 'customer')
    }

    errors = validate_registration(data)
    if errors:
        flash('Errores de validación', 'error')
        return redirect(url_for('admin.users'))

    if User.query.filter_by(email=data['email'].strip().lower()).first():
        flash('El correo ya está registrado', 'error')
        return redirect(url_for('admin.users'))

    user = User(
        name=data['name'].strip(),
        email=data['email'].strip().lower(),
        phone=data['phone'].strip() if data['phone'] else None,
        role=data['role']
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    _audit('create', 'user', user.id, f'Usuario creado: {user.name} ({user.email}, rol: {user.role})',
           new_value={'name': user.name, 'email': user.email, 'role': user.role, 'phone': user.phone})

    flash('Usuario creado exitosamente', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)

    old_data = user.to_dict()

    user.name = request.form.get('name', user.name)
    user.email = request.form.get('email', user.email).lower()
    user.phone = request.form.get('phone', user.phone)
    user.role = request.form.get('role', user.role)

    if request.form.get('password'):
        user.set_password(request.form.get('password'))

    db.session.commit()

    _audit('update', 'user', user.id, f'Usuario actualizado: {user.name}',
           old_value=old_data, new_value=user.to_dict())

    flash('Usuario actualizado exitosamente', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user_id == current_user.id:
        flash('No puedes eliminar tu propia cuenta', 'error')
        return redirect(url_for('admin.users'))

    user_data = user.to_dict()

    db.session.delete(user)
    db.session.commit()

    _audit('delete', 'user', user_id, f'Usuario eliminado: {user_data["name"]} ({user_data["email"]})',
           old_value=user_data)

    flash('Usuario eliminado exitosamente', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/products')
@login_required
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    pagination = paginate_query(Product.query, page)
    categories = Category.query.all()
    return render_template('admin/products.html', products=pagination.items, categories=categories, products_json=[p.to_dict() for p in pagination.items], pagination=pagination)


@admin_bp.route('/products', methods=['POST'])
@login_required
@admin_required
def create_product():
    sizes_raw = request.form.getlist('sizes[]')
    stocks_raw = request.form.getlist('stocks[]')
    colors_raw = request.form.getlist('colors[]')

    if len(sizes_raw) == 1 and ',' in sizes_raw[0]:
        sizes_raw = [s.strip() for s in sizes_raw[0].split(',') if s.strip()]
    if len(stocks_raw) == 1 and ',' in stocks_raw[0]:
        stocks_raw = [s.strip() for s in stocks_raw[0].split(',') if s.strip()]
    if len(colors_raw) == 1 and ',' in colors_raw[0]:
        colors_raw = [c.strip() for c in colors_raw[0].split(',') if c.strip()]

    data = {
        'name': request.form.get('name', ''),
        'description': request.form.get('description', ''),
        'base_price': request.form.get('base_price', 0),
        'category_id': request.form.get('category_id'),
        'sizes': [
            {'size': s.strip(), 'stock_quantity': stocks_raw[i] if i < len(stocks_raw) else 0}
            for i, s in enumerate(sizes_raw)
        ],
        'colors': [{'color': c.strip()} for c in colors_raw]
    }

    errors = validate_product(data)
    if errors:
        flash('Errores de validación', 'error')
        return redirect(url_for('admin.products'))

    product = Product(
        name=data['name'].strip(),
        description=data['description'].strip() if data['description'] else None,
        base_price=float(data['base_price']),
        category_id=int(data['category_id'])
    )
    db.session.add(product)
    db.session.flush()
    product_id = product.id

    for i, size in enumerate(sizes_raw):
        product_size = ProductSize(
            product_id=product.id,
            size=size.strip(),
            stock_quantity=int(stocks_raw[i]) if i < len(stocks_raw) else 0
        )
        db.session.add(product_size)

    for color in colors_raw:
        product_color = ProductColor(
            product_id=product.id,
            color=color.strip()
        )
        db.session.add(product_color)

    db.session.commit()

    _audit('create', 'product', product.id, f'Producto creado: {product.name} (${product.base_price})',
           new_value={'name': product.name, 'base_price': product.base_price, 'category_id': product.category_id,
                      'sizes': sizes_raw, 'colors': colors_raw})

    if 'image' in request.files:
        file = request.files['image']
        if file.filename and file.filename != '':
            image_path, error = save_image(file, product.id)
            if error:
                flash(f'Error al subir la imagen: {error}', 'warning')
            else:
                product_image = ProductImage(
                    product_id=product.id,
                    image_path=image_path,
                    is_primary=True
                )
                db.session.add(product_image)
                db.session.commit()
                flash('Producto creado exitosamente con imagen', 'success')
                return redirect(url_for('admin.products'))

    db.session.commit()
    flash('Producto creado exitosamente', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    old_data = {'name': product.name, 'description': product.description,
                'base_price': product.base_price, 'category_id': product.category_id,
                'is_active': product.is_active}

    product.name = request.form.get('name', product.name)
    product.description = request.form.get('description', product.description)

    price = request.form.get('base_price')
    if price:
        product.base_price = float(price)

    cat_id = request.form.get('category_id')
    if cat_id:
        product.category_id = int(cat_id)

    product.is_active = 'is_active' in request.form

    if 'image' in request.files:
        file = request.files['image']
        if file.filename and file.filename != '':
            image_path, error = save_image(file, product.id)
            if error:
                flash(f'Error al subir la imagen: {error}', 'warning')
            else:
                old_image = ProductImage.query.filter_by(product_id=product.id, is_primary=True).first()
                if old_image:
                    delete_image(old_image.image_path)
                    db.session.delete(old_image)

                product_image = ProductImage(
                    product_id=product.id,
                    image_path=image_path,
                    is_primary=True
                )
                db.session.add(product_image)

    db.session.commit()

    _audit('update', 'product', product.id, f'Producto actualizado: {product.name}',
           old_value=old_data, new_value={'name': product.name, 'description': product.description,
                                          'base_price': product.base_price, 'category_id': product.category_id,
                                          'is_active': product.is_active})

    flash('Producto actualizado exitosamente', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    product_data = {'name': product.name, 'base_price': product.base_price, 'category_id': product.category_id}
    db.session.delete(product)
    db.session.commit()
    _audit('delete', 'product', product_id, f'Producto eliminado: {product_data["name"]}',
           old_value=product_data)
    flash('Producto eliminado exitosamente', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    status = request.args.get('status')
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    all_orders = query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=all_orders)


@admin_bp.route('/orders/<int:order_id>/confirm-payment', methods=['POST'])
@login_required
@admin_required
def confirm_payment(order_id):
    order = Order.query.get(order_id)
    if not order:
        flash('Pedido no encontrado', 'error')
        return redirect(url_for('admin.orders'))

    payment_reference = request.form.get('payment_reference')

    order, error = order_service.confirm_payment(
        order_id, current_user.id, payment_reference
    )

    if error:
        flash(f'Error: {error}', 'error')
    else:
        _audit('confirm_payment', 'order', order_id,
               f'Pago confirmado para orden {order.order_number}', new_value={'status': 'paid'})
        flash('Pago confirmado exitosamente', 'success')

    return redirect(url_for('admin.orders'))


@admin_bp.route('/orders/<int:order_id>/prepare', methods=['POST'])
@login_required
@admin_required
def prepare_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        flash('Pedido no encontrado', 'error')
        return redirect(url_for('admin.orders'))

    if order.update_status('preparing'):
        db.session.commit()
        _audit('update_status', 'order', order_id,
               f'Orden {order.order_number} marcada como preparando', new_value={'status': 'preparing'})
        flash('Pedido marcado como preparando', 'success')
    else:
        flash('No se puede preparar este pedido', 'error')

    return redirect(url_for('admin.orders'))


@admin_bp.route('/orders/<int:order_id>/ready', methods=['POST'])
@login_required
@admin_required
def mark_order_ready(order_id):
    order = Order.query.get(order_id)
    if not order:
        flash('Pedido no encontrado', 'error')
        return redirect(url_for('admin.orders'))

    order, error = order_service.mark_as_ready(order_id)

    if error:
        flash(f'Error: {error}', 'error')
    else:
        _audit('update_status', 'order', order_id,
               f'Orden {order.order_number} marcada como lista para recoger', new_value={'status': 'ready_for_pickup'})
        flash('Pedido marcado como listo para recoger', 'success')

    return redirect(url_for('admin.orders'))


@admin_bp.route('/orders/<int:order_id>/deliver', methods=['POST'])
@login_required
@admin_required
def mark_order_delivered(order_id):
    order = Order.query.get(order_id)
    if not order:
        flash('Pedido no encontrado', 'error')
        return redirect(url_for('admin.orders'))

    order, error = order_service.mark_as_delivered(order_id)

    if error:
        flash(f'Error: {error}', 'error')
    else:
        _audit('update_status', 'order', order_id,
               f'Orden {order.order_number} marcada como entregada', new_value={'status': 'delivered'})
        flash('Pedido marcado como entregado', 'success')

    return redirect(url_for('admin.orders'))


@admin_bp.route('/inventory')
@login_required
@admin_required
def inventory():
    movements = inventory_service.get_inventory_movements(limit=50)
    low_stock = inventory_service.get_low_stock_products()
    products = Product.query.filter_by(is_active=True).all()
    products_data = [{'id': p.id, 'sizes': [s.to_dict() for s in p.sizes]} for p in products]
    return render_template('admin/inventory.html',
                         movements=movements,
                         low_stock=low_stock,
                         products=products,
                         products_json=products_data)


@admin_bp.route('/inventory/movements', methods=['POST'])
@login_required
@admin_required
def add_movement():
    product_id = request.form.get('product_id')
    size = request.form.get('size', '')
    movement_type = request.form.get('movement_type')
    quantity = int(request.form.get('quantity', 0))
    reason = request.form.get('reason', '')

    # If no size specified, use first available size
    if not size:
        first_size = ProductSize.query.filter_by(product_id=product_id).first()
        if not first_size:
            flash('El producto no tiene tallas configuradas', 'error')
            return redirect(url_for('admin.inventory'))
        size = first_size.size

    result, error = inventory_service.update_stock(
        product_id=product_id,
        size=size,
        quantity_change=quantity if movement_type == 'purchase' else -quantity,
        movement_type=movement_type,
        reason=reason,
        user_id=current_user.id
    )

    if error:
        flash(f'Error: {error}', 'error')
    else:
        from models import Product as Prod
        prod = Prod.query.get(product_id)
        _audit('inventory_movement', 'inventory', int(product_id),
               f'Movimiento {movement_type} x{quantity} de {prod.name if prod else "desconocido"} ({size})',
               new_value={'product_id': product_id, 'size': size, 'movement_type': movement_type,
                          'quantity': quantity, 'reason': reason})
        flash('Movimiento registrado exitosamente', 'success')

    return redirect(url_for('admin.inventory'))


@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    summary = analytics_service.get_sales_summary(days=30)
    daily_sales = analytics_service.get_daily_sales(days=30)
    top_products = analytics_service.get_top_selling_products(limit=10)
    low_stock = inventory_service.get_low_stock_products()

    return render_template('admin/analytics.html',
                         summary=summary,
                         daily_sales=daily_sales,
                         top_products=top_products,
                         low_stock=low_stock)


@admin_bp.route('/analytics/export')
@login_required
@admin_required
def export_analytics():
    export_type = request.args.get('type', 'summary')

    if export_type == 'sales':
        data = analytics_service.get_daily_sales(days=30)
    elif export_type == 'products':
        data = analytics_service.get_top_selling_products(limit=100)
    else:
        data = analytics_service.get_sales_summary(days=30)

    csv_data = analytics_service.export_to_csv(data, 'export.csv')

    response = make_response(csv_data)
    response.headers['Content-Disposition'] = f'attachment; filename={export_type}_export.csv'
    response.headers['Content-Type'] = 'text/csv'

    return response


@admin_bp.route('/employees')
@login_required
@admin_required
def employees():
    page = request.args.get('page', 1, type=int)
    employee_users = User.query.filter(User.role.in_(['employee', 'administrator']))
    pagination = paginate_query(employee_users, page, per_page=20)
    employees_list = []
    for u in pagination.items:
        emp_data = u.to_dict()
        if u.employee_profile:
            emp_data['profile'] = u.employee_profile.to_dict()
        else:
            emp_data['profile'] = None
        employees_list.append(emp_data)
    return render_template('admin/employees.html',
                         employees=pagination.items,
                         employees_json=employees_list,
                         pagination=pagination)


@admin_bp.route('/employees/<int:user_id>/profile', methods=['POST'])
@login_required
@admin_required
def update_employee_profile(user_id):
    user = User.query.get_or_404(user_id)
    if user.role not in ('employee', 'administrator'):
        flash('Solo se pueden gestionar perfiles de empleados y administradores', 'error')
        return redirect(url_for('admin.employees'))

    profile = user.employee_profile
    if not profile:
        profile = EmployeeProfile(user_id=user_id)
        db.session.add(profile)
        db.session.flush()

    old_data = profile.to_dict() if profile.id else None

    position = request.form.get('position')
    if position:
        profile.position = position.strip()

    hire_date_str = request.form.get('hire_date')
    if hire_date_str:
        try:
            profile.hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass

    salary = request.form.get('salary')
    if salary:
        try:
            profile.salary = float(salary)
        except (ValueError, TypeError):
            pass

    profile.emergency_contact = request.form.get('emergency_contact', profile.emergency_contact)
    profile.emergency_phone = request.form.get('emergency_phone', profile.emergency_phone)
    profile.notes = request.form.get('notes', profile.notes)

    db.session.commit()

    _audit('update', 'employee_profile', user_id,
           f'Perfil de empleado actualizado: {user.name}',
           old_value=old_data, new_value=profile.to_dict())

    flash('Perfil de empleado actualizado exitosamente', 'success')
    return redirect(url_for('admin.employees'))


@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    entity_type = request.args.get('entity_type')
    action = request.args.get('action')
    logs = audit_service.get_recent_activity(limit=100)
    total = audit_service.count_logs(entity_type=entity_type, action=action)
    return render_template('admin/audit_logs.html',
                         logs=logs,
                         total=total,
                         current_entity_type=entity_type,
                         current_action=action,
                         entity_types=['user', 'product', 'order', 'inventory', 'employee_profile'],
                         actions=['create', 'update', 'delete', 'confirm_payment', 'update_status', 'inventory_movement'])


@admin_bp.route('/financial-reports')
@login_required
@admin_required
def financial_reports():
    days = request.args.get('days', 30, type=int)
    if days not in (7, 15, 30, 90, 365):
        days = 30

    summary = analytics_service.get_financial_summary(days=days)
    monthly = analytics_service.get_monthly_sales(months=6)
    profit_data, total_revenue = analytics_service.get_profit_by_product(days=days)
    top_products = analytics_service.get_top_selling_products(limit=10, days=days)
    status_breakdown = analytics_service.get_order_status_breakdown()
    low_stock = inventory_service.get_low_stock_products()

    return render_template('admin/financial_reports.html',
                         summary=summary,
                         monthly=monthly,
                         profit_data=profit_data,
                         total_revenue=total_revenue,
                         top_products=top_products,
                         status_breakdown=status_breakdown,
                         low_stock=low_stock,
                         selected_days=days)


@admin_bp.route('/financial-reports/export')
@login_required
@admin_required
def export_financial():
    export_type = request.args.get('type', 'financial')
    days = request.args.get('days', 30, type=int)
    if days not in (7, 15, 30, 90, 365):
        days = 30

    if export_type == 'financial':
        data = [analytics_service.get_financial_summary(days=days)]
    elif export_type == 'monthly':
        data = analytics_service.get_monthly_sales(months=12)
    elif export_type == 'profit':
        data, _ = analytics_service.get_profit_by_product(days=days)
    elif export_type == 'status':
        breakdown = analytics_service.get_order_status_breakdown()
        data = [{'status': k, 'count': v['count'], 'total': v['total']} for k, v in breakdown.items()]
    else:
        data = [analytics_service.get_sales_summary(days=days)]

    csv_data = analytics_service.export_to_csv(data, 'export.csv')
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = f'attachment; filename={export_type}_report_{days}d.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response
