from flask import Blueprint, request, redirect, url_for, render_template, flash, jsonify, session
from flask_login import current_user, login_required
from models import Product, ProductSize, ProductColor, Order
from services.order_service import order_service
from utils.upload import save_payment_receipt

customer_bp = Blueprint('customer', __name__)


def get_cart():
    if 'cart' not in session:
        session['cart'] = {}
    return session['cart']


def get_cart_items():
    cart = get_cart()
    if not cart:
        return [], 0, 0

    product_ids = {item.get('product_id') for item in cart.values()}
    products = {p.id: p for p in Product.query.filter(Product.id.in_(product_ids)).all()}
    sizes = {
        (s.product_id, s.size): s
        for s in ProductSize.query.filter(ProductSize.product_id.in_(product_ids)).all()
    }

    cart_items = []
    total = 0
    item_count = 0

    for key, item in cart.items():
        product = products.get(item.get('product_id'))
        if not product:
            continue

        quantity = item.get('quantity', 0)
        item_total = quantity * item.get('unit_price', 0)
        total += item_total
        item_count += quantity

        size_obj = sizes.get((product.id, item.get('size')))
        is_available = True
        unavailable_reason = None

        if not product.is_active:
            is_available = False
            unavailable_reason = 'Producto no disponible'
        elif size_obj and size_obj.stock_quantity < quantity:
            is_available = False
            unavailable_reason = f'Stock insuficiente. Disponible: {size_obj.stock_quantity}'

        cart_items.append({
            'key': key,
            'product': product.to_dict(),
            'size': item.get('size'),
            'color': item.get('color'),
            'quantity': quantity,
            'unit_price': item.get('unit_price', 0),
            'subtotal': item_total,
            'is_available': is_available,
            'unavailable_reason': unavailable_reason
        })

    return cart_items, total, item_count


@customer_bp.route('/dashboard')
@login_required
def dashboard():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(10).all()
    return render_template('customer/dashboard.html', orders=orders)


@customer_bp.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    cart = get_cart()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            if current_user.role != 'customer':
                return jsonify({'error': 'Solo los clientes pueden añadir productos al carrito'}), 403

            product_id = int(request.form.get('product_id'))
            size = request.form.get('size')
            color = request.form.get('color')
            quantity = int(request.form.get('quantity', 1))

            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Producto no encontrado'}), 404
            if not product.is_active:
                return jsonify({'error': 'Producto no disponible'}), 400

            size_obj = ProductSize.query.filter_by(product_id=product_id, size=size).first()
            if not size_obj:
                return jsonify({'error': 'Talla no disponible'}), 400
            if size_obj.stock_quantity < quantity:
                return jsonify({'error': f'Stock insuficiente. Disponible: {size_obj.stock_quantity}'}), 400

            color_obj = ProductColor.query.filter_by(product_id=product_id, color=color).first()
            if not color_obj:
                return jsonify({'error': 'Color no disponible'}), 400

            cart_key = f"{product_id}_{size}_{color}"
            cart[cart_key] = {
                'product_id': product_id,
                'size': size,
                'color': color,
                'quantity': quantity,
                'unit_price': product.base_price
            }
            session['cart'] = cart
            return jsonify({'success': 'Producto añadido al carrito', 'cart_key': cart_key})

        elif action == 'update':
            cart_key = request.form.get('cart_key')
            quantity = int(request.form.get('quantity', 1))

            if cart_key in cart:
                item = cart[cart_key]
                size_obj = ProductSize.query.filter_by(
                    product_id=item['product_id'],
                    size=item['size']
                ).first()
                if size_obj and size_obj.stock_quantity < quantity:
                    return jsonify({'error': f'Stock insuficiente. Disponible: {size_obj.stock_quantity}'}), 400
                cart[cart_key]['quantity'] = quantity

            session['cart'] = cart
            return jsonify({'success': 'Carrito actualizado'})

        elif action == 'remove':
            cart_key = request.form.get('cart_key')
            if cart_key in cart:
                del cart[cart_key]
            session['cart'] = cart
            return jsonify({'success': 'Producto eliminado'})

        elif action == 'clear':
            session['cart'] = {}
            return jsonify({'success': 'Carrito limpiado'})

    cart_items, total, item_count = get_cart_items()
    return render_template('customer/cart.html', cart_items=cart_items, total=total, item_count=item_count)


@customer_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = get_cart()

    if not cart:
        flash('Tu carrito está vacío', 'warning')
        return redirect(url_for('customer.cart'))

    cart_items, total, _ = get_cart_items()
    unavailable_items = [item for item in cart_items if not item['is_available']]

    if unavailable_items:
        for item in unavailable_items:
            del cart[item['key']]
        session['cart'] = cart
        flash(f'Se eliminaron {len(unavailable_items)} producto(s) no disponible(s)', 'warning')
        return redirect(url_for('customer.cart'))

    if request.method == 'POST':
        pickup_location = request.form.get('pickup_location')
        items = [
            {
                'product_id': item['product_id'],
                'size': item['size'],
                'color': item['color'],
                'quantity': item['quantity'],
                'unit_price': item['unit_price']
            }
            for item in cart.values()
        ]

        order, error = order_service.create_order(current_user.id, items, pickup_location)
        if error:
            return jsonify({'error': str(error)}), 400

        session['cart'] = {}
        flash('¡Pedido realizado exitosamente!', 'success')
        return redirect(url_for('customer.order_detail', order_id=order.id))

    return render_template('customer/checkout.html', cart_items=cart_items, total=total)


@customer_bp.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('customer/orders.html', orders=user_orders)


@customer_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash('Acceso denegado', 'error')
        return redirect(url_for('public.index'))

    return render_template('customer/order_detail.html', order=order)


@customer_bp.route('/orders/<int:order_id>/upload-receipt', methods=['POST'])
@login_required
def upload_receipt(order_id):
    order = Order.query.get_or_404(order_id)
    detail_url = url_for('customer.order_detail', order_id=order_id)

    if order.user_id != current_user.id:
        flash('Acceso denegado', 'error')
        return redirect(url_for('public.index'))

    if order.payment_status != 'pending':
        flash('El pago ya ha sido procesado', 'warning')
        return redirect(detail_url)

    file = request.files.get('receipt')
    if not file or not file.filename:
        flash('Debes seleccionar un archivo', 'error')
        return redirect(detail_url)

    receipt_path, error = save_payment_receipt(file, order_id)
    if error:
        flash(f'Error al subir comprobante: {error}', 'error')
        return redirect(detail_url)

    order, error = order_service.upload_receipt(order_id, receipt_path)
    if error:
        flash(f'Error: {error}', 'error')
    else:
        flash('Comprobante de pago subido exitosamente. Espera la confirmación.', 'success')

    return redirect(detail_url)
