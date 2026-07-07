from extensions import db
from models import ProductSize, InventoryMovement, OrderItem
from datetime import datetime

class InventoryService:

    LOW_STOCK_THRESHOLD = 5

    def update_stock(self, product_id, size, quantity_change, movement_type, reason=None, user_id=None):
        size_obj = ProductSize.query.filter_by(
            product_id=product_id,
            size=size
        ).first()

        if not size_obj:
            return None, 'Talla de producto no encontrada'

        new_stock = size_obj.stock_quantity + quantity_change
        if new_stock < 0:
            return None, 'Stock insuficiente'

        size_obj.stock_quantity = new_stock

        movement = InventoryMovement(
            user_id=user_id,
            product_id=product_id,
            movement_type=movement_type,
            reason=reason,
            quantity=abs(quantity_change)
        )
        db.session.add(movement)

        db.session.commit()
        return size_obj, None

    def get_low_stock_products(self):
        from models import Product
        products = Product.query.filter(Product.is_active == True).all()
        low_stock = []

        for product in products:
            total_stock = sum(s.stock_quantity for s in product.sizes)
            if total_stock <= self.LOW_STOCK_THRESHOLD:
                low_stock.append(product)

        return low_stock

    def get_inventory_movements(self, product_id=None, limit=100):
        query = InventoryMovement.query

        if product_id:
            query = query.filter_by(product_id=product_id)

        return query.order_by(InventoryMovement.created_at.desc()).limit(limit).all()

    def check_availability(self, product_id, size, quantity):
        size_obj = ProductSize.query.filter_by(
            product_id=product_id,
            size=size
        ).first()

        if not size_obj:
            return False, 'Talla no encontrada'

        if size_obj.stock_quantity < quantity:
            return False, 'Stock insuficiente'

        return True, None

inventory_service = InventoryService()
