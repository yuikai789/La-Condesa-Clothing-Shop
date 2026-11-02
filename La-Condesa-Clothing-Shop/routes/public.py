from flask import Blueprint, render_template, request
from models import Product, Category, ProductSize

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    featured_products = Product.query.filter_by(is_active=True).limit(6).all()
    return render_template('public/index.html', featured_products=featured_products)


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

    query = Product.query.filter(
        Product.is_active == True,
        Product.base_price >= min_price,
        Product.base_price <= max_price
    )

    if category_id:
        query = query.filter_by(category_id=category_id)

    if size:
        query = query.join(ProductSize).filter(
            ProductSize.size == size,
            ProductSize.stock_quantity > 0
        )

    return render_template('public/catalog.html',
                         products=query.all(),
                         categories=Category.query.all(),
                         selected_category=category_id,
                         selected_size=size,
                         min_price=min_price,
                         max_price=max_price)


@public_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('public/product_detail.html',
                         product=product,
                         total_stock=product.get_total_stock(),
                         available_sizes=[s for s in product.sizes if s.stock_quantity > 0])
