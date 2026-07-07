from datetime import datetime
from extensions import db

class InventoryMovement(db.Model):
    __tablename__ = 'inventory_movements'

    TYPES = ['purchase', 'return', 'loss', 'correction', 'sale']

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', lazy='select')
    product = db.relationship('Product', lazy='select')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'movement_type': self.movement_type,
            'reason': self.reason,
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<InventoryMovement {self.movement_type} {self.product.name} x{self.quantity}>'
