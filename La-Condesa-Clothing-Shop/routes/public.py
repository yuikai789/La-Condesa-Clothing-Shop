from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models import Product, Category

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    categories = Category.query.all()
    featured_products = Product.query.filter_by(is_active=True).limit(6).all()
    return render_template('public/index.html',
                         categories=categories,
                         featured_products=featured_products)


@public_bp.route('/about')
def about():
    return render_template('public/about.html')


@public_bp.route('/contact')
def contact():
    return render_template('public/contact.html')


@public_bp.route('/catalog')
def catalog():
    category_id = request.args.get('category')
    size = request.args.get('size')
    min_price = request.args.get('min_price', 0, type=float)
    max_price = request.args.get('max_price', 999999, type=float)

    query = Product.query.filter_by(is_active=True)

    if category_id:
        query = query.filter_by(category_id=category_id)

    products = query.all()

    filtered_products = []
    for product in products:
        if size:
            has_size = any(s.size == size and s.stock_quantity > 0 for s in product.sizes)
            if not has_size:
                continue

        if not (min_price <= product.base_price <= max_price):
            continue

        filtered_products.append(product)

    categories = Category.query.all()
    return render_template('public/catalog.html',
                         products=filtered_products,
                         categories=categories,
                         selected_category=category_id,
                         selected_size=size,
                         min_price=min_price,
                         max_price=max_price)


@public_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)

    total_stock = product.get_total_stock()

    available_sizes = [s for s in product.sizes if s.stock_quantity > 0]

    return render_template('public/product_detail.html',
                         product=product,
                         total_stock=total_stock,
                         available_sizes=available_sizes)
