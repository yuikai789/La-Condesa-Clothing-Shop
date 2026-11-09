import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, redirect, url_for, render_template, flash, make_response, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from extensions import db
from models import (User, Product, Category, ProductSize, ProductColor, ProductImage,
                    Order, OrderItem, EmployeeProfile, InventoryMovement)
from utils.validators import (validate_registration, validate_product, validate_email,
                              validate_phone)
from utils.decorators import admin_required
from utils.pagination import paginate_query
from services.inventory_service import inventory_service
from services.analytics_service import analytics_service
from services.order_service import order_service
from services.audit_service import audit_service, log_action
from routes.order_actions import run_order_action
from utils.upload import save_image, delete_image

admin_bp = Blueprint('admin', __name__)


def _apply_product_image(product, file):
    if not file or not file.filename:
        return False, None

    image_path, error = save_image(file, product.id)
    if error:
        return False, error

    old_image = ProductImage.query.filter_by(product_id=product.id, is_primary=True).first()
    if old_image:
        delete_image(old_image.image_path)
        db.session.delete(old_image)

    db.session.add(ProductImage(product_id=product.id, image_path=image_path, is_primary=True))
    return True, None


def _csv_response(data, filename):
    safe_filename = re.sub(r'[^A-Za-z0-9_.-]', '_', filename) or 'export.csv'
    response = make_response(analytics_service.export_to_csv(data, safe_filename))
    response.headers['Content-Disposition'] = f'attachment; filename={safe_filename}'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response


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


def _validate_admin_password(password):
    if not password:
        return 'La contraseña es obligatoria'
    if len(password.encode('utf-8')) > 72:
        return 'La contraseña no puede superar los 72 bytes'
    return None


def _render_users_page(page=1, form_errors=None, form_data=None):
    user_query = User.query.order_by(User.created_at.desc(), User.id.desc())
    pagination = paginate_query(user_query, page)
    return render_template('admin/users.html',
                           users=pagination.items,
                           users_json=[u.to_dict() for u in pagination.items],
                           pagination=pagination,
                           form_errors=form_errors or {},
                           form_data=form_data or {})


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    return _render_users_page(page)


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
    errors.pop('password', None)

    password_error = _validate_admin_password(data['password'])
    if password_error:
        errors['password'] = password_error

    if data['role'] not in User.ROLES:
        errors['role'] = 'Rol inválido'

    if not errors and User.query.filter_by(email=data['email'].strip().lower()).first():
        errors['email'] = 'El correo ya está registrado'

    if errors:
        for message in errors.values():
            flash(message, 'error')
        return _render_users_page(form_errors=errors, form_data=data)

    user = User(
        name=data['name'].strip(),
        email=data['email'].strip().lower(),
        phone=data['phone'].strip() if data['phone'] else None,
        role=data['role'],
        email_verified=True
    )
    user.set_password(data['password'])

    try:
        db.session.add(user)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('No se pudo crear el usuario')
        flash('No se pudo crear el usuario. Revisa los datos e inténtalo de nuevo.', 'error')
        return _render_users_page(form_data=data)

    try:
        log_action('create', 'user', user.id, f'Usuario creado: {user.name} ({user.email}, rol: {user.role})',
                   new_value={'name': user.name, 'email': user.email, 'role': user.role, 'phone': user.phone})
    except Exception:
        db.session.rollback()
        current_app.logger.exception('No se pudo registrar la auditoría de creación de usuario')

    flash('Usuario creado exitosamente', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user(user_id):
    user = db.get_or_404(User, user_id)

    old_data = user.to_dict()

    name = request.form.get('name', user.name).strip()
    email = request.form.get('email', user.email).strip().lower()
    phone = request.form.get('phone', user.phone)
    role = request.form.get('role', user.role)
    password = request.form.get('password', '')

    if not name or len(name) < 2:
        flash('El nombre debe tener al menos 2 caracteres', 'error')
        return redirect(url_for('admin.users'))

    email_error = validate_email(email)
    if email_error:
        flash(email_error, 'error')
        return redirect(url_for('admin.users'))

    phone_error = validate_phone(phone)
    if phone_error:
        flash(phone_error, 'error')
        return redirect(url_for('admin.users'))

    if role not in User.ROLES:
        flash('Rol inválido', 'error')
        return redirect(url_for('admin.users'))

    existing = User.query.filter(User.email == email, User.id != user_id).first()
    if existing:
        flash('El correo ya está registrado por otro usuario', 'error')
        return redirect(url_for('admin.users'))

    if password:
        password_error = _validate_admin_password(password)
        if password_error:
            flash(password_error, 'error')
            return redirect(url_for('admin.users'))
        user.set_password(password)

    user.name = name
    user.email = email
    user.phone = phone.strip() if phone else None
    user.role = role

    db.session.commit()

    log_action('update', 'user', user.id, f'Usuario actualizado: {user.name}',
           old_value=old_data, new_value=user.to_dict())

    flash('Usuario actualizado exitosamente', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = db.get_or_404(User, user_id)

    if user_id == current_user.id:
        flash('No puedes eliminar tu propia cuenta', 'error')
        return redirect(url_for('admin.users'))

    if Order.query.filter_by(user_id=user_id).first():
        flash('No se puede eliminar un usuario con pedidos registrados. Desactívalo en su lugar.', 'error')
        return redirect(url_for('admin.users'))

    user_data = user.to_dict()

    if user.employee_profile:
        db.session.delete(user.employee_profile)

    db.session.delete(user)
    db.session.commit()

    log_action('delete', 'user', user_id, f'Usuario eliminado: {user_data["name"]} ({user_data["email"]})',
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

    if not db.session.get(Category, int(data['category_id'])):
        flash('La categoría seleccionada no existe', 'error')
        return redirect(url_for('admin.products'))

    product = Product(
        name=data['name'].strip(),
        description=data['description'].strip() if data['description'] else None,
        base_price=Decimal(str(data['base_price'])),
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

    log_action('create', 'product', product.id, f'Producto creado: {product.name} (${product.base_price})',
           new_value={'name': product.name, 'base_price': product.base_price, 'category_id': product.category_id,
                      'sizes': sizes_raw, 'colors': colors_raw})

    if 'image' in request.files:
        saved, error = _apply_product_image(product, request.files['image'])
        if error:
            flash(f'Error al subir la imagen: {error}', 'warning')
        elif saved:
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
    product = db.get_or_404(Product, product_id)
    old_data = {'name': product.name, 'description': product.description,
                'base_price': product.base_price, 'category_id': product.category_id,
                'is_active': product.is_active}

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name or len(name) > 100:
        flash('El nombre debe tener entre 1 y 100 caracteres', 'error')
        return redirect(url_for('admin.products'))
    if description and len(description) > 1000:
        flash('La descripción debe tener menos de 1000 caracteres', 'error')
        return redirect(url_for('admin.products'))

    try:
        price = Decimal(str(request.form.get('base_price', '')))
        if price < 0:
            raise ValueError
    except (InvalidOperation, ValueError, TypeError):
        flash('Formato de precio inválido', 'error')
        return redirect(url_for('admin.products'))

    try:
        cat_id = int(request.form.get('category_id', ''))
    except (ValueError, TypeError):
        flash('Categoría inválida', 'error')
        return redirect(url_for('admin.products'))

    if not db.session.get(Category, cat_id):
        flash('La categoría seleccionada no existe', 'error')
        return redirect(url_for('admin.products'))

    product.name = name
    product.description = description or None
    product.base_price = price
    product.category_id = cat_id
    product.is_active = 'is_active' in request.form

    if 'image' in request.files:
        saved, error = _apply_product_image(product, request.files['image'])
        if error:
            flash(f'Error al subir la imagen: {error}', 'warning')

    db.session.commit()

    log_action('update', 'product', product.id, f'Producto actualizado: {product.name}',
           old_value=old_data, new_value={'name': product.name, 'description': product.description,
                                          'base_price': product.base_price, 'category_id': product.category_id,
                                          'is_active': product.is_active})

    flash('Producto actualizado exitosamente', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = db.get_or_404(Product, product_id)

    if OrderItem.query.filter_by(product_id=product_id).first():
        flash('No se puede eliminar un producto con pedidos registrados. Desactívalo en su lugar.', 'error')
        return redirect(url_for('admin.products'))

    product_data = {'name': product.name, 'base_price': product.base_price, 'category_id': product.category_id}
    for image in product.images:
        delete_image(image.image_path)
    db.session.delete(product)
    db.session.commit()
    log_action('delete', 'product', product_id, f'Producto eliminado: {product_data["name"]}',
           old_value=product_data)
    flash('Producto eliminado exitosamente', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    return render_template('admin/orders.html', orders=order_service.list_orders(request.args.get('status')))


@admin_bp.route('/orders/<int:order_id>/confirm-payment', methods=['POST'])
@login_required
@admin_required
def confirm_payment(order_id):
    return run_order_action(order_id, 'confirm_payment', 'admin.orders', request.form.get('payment_reference'))


@admin_bp.route('/orders/<int:order_id>/prepare', methods=['POST'])
@login_required
@admin_required
def prepare_order(order_id):
    return run_order_action(order_id, 'prepare', 'admin.orders')


@admin_bp.route('/orders/<int:order_id>/ready', methods=['POST'])
@login_required
@admin_required
def mark_order_ready(order_id):
    return run_order_action(order_id, 'ready', 'admin.orders')


@admin_bp.route('/orders/<int:order_id>/deliver', methods=['POST'])
@login_required
@admin_required
def mark_order_delivered(order_id):
    return run_order_action(order_id, 'deliver', 'admin.orders')


@admin_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_order(order_id):
    return run_order_action(order_id, 'cancel', 'admin.orders')


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
    try:
        product_id = int(request.form.get('product_id', ''))
    except (ValueError, TypeError):
        flash('Producto inválido', 'error')
        return redirect(url_for('admin.inventory'))

    size = request.form.get('size', '')
    movement_type = request.form.get('movement_type')
    reason = request.form.get('reason', '')

    try:
        quantity = int(request.form.get('quantity', 0))
    except (ValueError, TypeError):
        flash('Cantidad inválida', 'error')
        return redirect(url_for('admin.inventory'))

    if movement_type not in InventoryMovement.TYPES:
        flash('Tipo de movimiento inválido', 'error')
        return redirect(url_for('admin.inventory'))
    if quantity <= 0:
        flash('La cantidad debe ser mayor a cero', 'error')
        return redirect(url_for('admin.inventory'))
    if not db.session.get(Product, product_id):
        flash('El producto no existe', 'error')
        return redirect(url_for('admin.inventory'))

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
        quantity_change=quantity if movement_type in ('purchase', 'return') else -quantity,
        movement_type=movement_type,
        reason=reason,
        user_id=current_user.id
    )

    if error:
        flash(f'Error: {error}', 'error')
    else:
        prod = db.session.get(Product, product_id)
        log_action('inventory_movement', 'inventory', product_id,
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
        data = [analytics_service.get_sales_summary(days=30)]

    return _csv_response(data, f'{export_type}_export.csv')


@admin_bp.route('/employees')
@login_required
@admin_required
def employees():
    page = request.args.get('page', 1, type=int)
    employee_users = User.query.filter(User.role.in_(['employee', 'administrator']))
    pagination = paginate_query(employee_users, page, per_page=20)
    employees_list = [
        {**u.to_dict(), 'profile': u.employee_profile.to_dict() if u.employee_profile else None}
        for u in pagination.items
    ]
    return render_template('admin/employees.html',
                         employees=pagination.items,
                         employees_json=employees_list,
                         pagination=pagination)


@admin_bp.route('/employees/<int:user_id>/profile', methods=['POST'])
@login_required
@admin_required
def update_employee_profile(user_id):
    user = db.get_or_404(User, user_id)
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
            profile.salary = Decimal(str(salary))
        except (InvalidOperation, ValueError, TypeError):
            pass

    profile.emergency_contact = request.form.get('emergency_contact', profile.emergency_contact)
    profile.emergency_phone = request.form.get('emergency_phone', profile.emergency_phone)
    profile.notes = request.form.get('notes', profile.notes)

    db.session.commit()

    log_action('update', 'employee_profile', user_id,
           f'Perfil de empleado actualizado: {user.name}',
           old_value=old_data, new_value=profile.to_dict())

    flash('Perfil de empleado actualizado exitosamente', 'success')
    return redirect(url_for('admin.employees'))


@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    entity_type = request.args.get('entity_type')
    action = request.args.get('action')
    logs = audit_service.get_logs(limit=100, entity_type=entity_type, action=action)
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

    return _csv_response(data, f'{export_type}_report_{days}d.csv')
