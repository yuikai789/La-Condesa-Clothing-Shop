from datetime import datetime
from extensions import db

class Category(db.Model):
    """Product category model"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    """Product model with sizes, colors, and images"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    base_price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sizes = db.relationship('ProductSize', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    colors = db.relationship('ProductColor', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    images = db.relationship('ProductImage', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', back_populates='product', lazy='dynamic')
    # Removed backref for movements to avoid conflict with InventoryMovement.product
    
    def get_total_stock(self):
        """Calculate total stock across all sizes"""
        return sum(size.stock_quantity for size in self.sizes)
    
    def get_total_stock_by_size(self, size):
        """Get stock for specific size"""
        size_obj = self.sizes.filter_by(size=size).first()
        return size_obj.stock_quantity if size_obj else 0
    
    def is_available(self, size=None, color=None):
        """Check if product is available in specified size/color"""
        if not self.is_active:
            return False
        
        if size:
            stock = self.get_total_stock_by_size(size)
            return stock > 0
        
        return self.get_total_stock() > 0
    
    def to_dict(self, include_stock=True):
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'base_price': self.base_price,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sizes': [s.to_dict() for s in self.sizes],
            'colors': [c.to_dict() for c in self.colors],
            'images': [i.to_dict() for i in self.images]
        }
        
        if include_stock:
            result['total_stock'] = self.get_total_stock()
        
        return result
    
    def __repr__(self):
        return f'<Product {self.name}>'

class ProductSize(db.Model):
    """Product size and stock tracking"""
    __tablename__ = 'product_sizes'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('product_id', 'size', name='uq_product_size'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'size': self.size,
            'stock_quantity': self.stock_quantity
        }
    
    def __repr__(self):
        return f'<ProductSize {self.product.name} - {self.size}>'

class ProductColor(db.Model):
    """Product color options"""
    __tablename__ = 'product_colors'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('product_id', 'color', name='uq_product_color'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'color': self.color
        }
    
    def __repr__(self):
        return f'<ProductColor {self.product.name} - {self.color}>'

class ProductImage(db.Model):
    """Product image storage"""
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'image_path': self.image_path,
            'is_primary': self.is_primary
        }
    
    def __repr__(self):
        return f'<ProductImage {self.product.name}>'
