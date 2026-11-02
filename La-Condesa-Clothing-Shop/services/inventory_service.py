from extensions import db
from models import Product, ProductSize, InventoryMovement


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
        db.session.add(InventoryMovement(
            user_id=user_id,
            product_id=product_id,
            movement_type=movement_type,
            reason=reason,
            quantity=abs(quantity_change)
        ))

        db.session.commit()
        return size_obj, None

    def get_low_stock_products(self):
        stock = db.session.query(
            ProductSize.product_id,
            db.func.sum(ProductSize.stock_quantity).label('total')
        ).group_by(ProductSize.product_id).subquery()

        return Product.query.outerjoin(
            stock, Product.id == stock.c.product_id
        ).filter(
            Product.is_active == True,
            db.func.coalesce(stock.c.total, 0) <= self.LOW_STOCK_THRESHOLD
        ).all()

    def get_inventory_movements(self, product_id=None, limit=100):
        query = InventoryMovement.query

        if product_id:
            query = query.filter_by(product_id=product_id)

        return query.order_by(InventoryMovement.created_at.desc()).limit(limit).all()


inventory_service = InventoryService()
