from datetime import datetime, timedelta
from extensions import db

class Order(db.Model):
    """Order model with status tracking"""
    __tablename__ = 'orders'
    
    STATUSES = ['pending_payment', 'paid', 'preparing', 'ready_for_pickup', 'delivered']
    PAYMENT_STATUS = ['pending', 'verified', 'cancelled']
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    tax = db.Column(db.Float, nullable=False, default=0.0)
    discount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), default='pending_payment', nullable=False)
    pickup_location = db.Column(db.String(100), nullable=True)
    payment_status = db.Column(db.String(20), default='pending', nullable=False)
    payment_reference = db.Column(db.String(50), nullable=True)
    receipt_path = db.Column(db.String(255), nullable=True)
    payment_receipt_path = db.Column(db.String(255), nullable=True)
    confirmed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    customer = db.relationship('User', foreign_keys=[user_id], back_populates='orders', lazy='select')
    confirmed_by = db.relationship('User', foreign_keys=[confirmed_by_id], lazy='select', overlaps="orders")
    
    def can_be_delivered(self):
        """Check if order can be marked as delivered"""
        return self.status == 'ready_for_pickup'
    
    def is_overdue(self):
        """Check if order is overdue (payment not confirmed within 7 days)"""
        if self.payment_status != 'pending':
            return False
        return datetime.utcnow() > self.created_at + timedelta(days=7)
    
    def calculate_totals(self):
        """Recalculate order totals"""
        self.subtotal = sum(item.subtotal for item in self.items)
        self.tax = self.subtotal * 0.16  # 16% tax
        self.total = self.subtotal + self.tax - self.discount
        return self.subtotal, self.tax, self.total
    
    def update_status(self, new_status):
        """Update order status with validation"""
        if new_status not in self.STATUSES:
            return False
        
        # Validate status transition
        valid_transitions = {
            'pending_payment': ['paid', 'cancelled'],
            'paid': ['preparing', 'cancelled'],
            'preparing': ['ready_for_pickup'],
            'ready_for_pickup': ['delivered'],
            'delivered': [],
            'cancelled': []
        }
        
        if new_status in valid_transitions.get(self.status, []):
            self.status = new_status
            if new_status == 'paid':
                self.paid_at = datetime.utcnow()
            elif new_status == 'delivered':
                self.delivered_at = datetime.utcnow()
            return True
        return False
    
    def to_dict(self, include_items=True):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'order_number': self.order_number,
            'subtotal': self.subtotal,
            'tax': self.tax,
            'discount': self.discount,
            'total': self.total,
            'status': self.status,
            'pickup_location': self.pickup_location,
            'payment_status': self.payment_status,
            'payment_reference': self.payment_reference,
            'receipt_path': self.receipt_path,
            'payment_receipt_path': self.payment_receipt_path,
            'confirmed_by_id': self.confirmed_by_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'customer': self.customer.to_dict() if self.customer else None
        }
        
        if include_items:
            result['items'] = [i.to_dict() for i in self.items]
        
        return result
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    """Order item model"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    
    # Relationship
    product = db.relationship('Product', back_populates='order_items', lazy='select')
    
    @property
    def subtotal(self):
        return self.quantity * self.unit_price
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'size': self.size,
            'color': self.color,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.subtotal
        }
    
    def __repr__(self):
        return f'<OrderItem {self.product_id} x{self.quantity}>'
