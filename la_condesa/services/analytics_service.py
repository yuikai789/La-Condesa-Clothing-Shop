from extensions import db
from models import Order, OrderItem, Product
from datetime import datetime, timedelta

class AnalyticsService:

    def get_daily_sales(self, days=30):
        start_date = datetime.utcnow() - timedelta(days=days)

        results = db.session.query(
            db.func.date(Order.created_at).label('date'),
            db.func.sum(Order.total).label('total'),
            db.func.count(Order.id).label('orders')
        ).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).group_by(
            db.func.date(Order.created_at)
        ).order_by(
            Order.created_at.desc()
        ).all()

        return [
            {'date': str(r.date), 'total': float(r.total), 'orders': r.orders}
            for r in results
        ]

    def get_top_selling_products(self, limit=10, days=None):
        start_date = None
        if days:
            start_date = datetime.utcnow() - timedelta(days=days)

        query = db.session.query(
            Product.id,
            Product.name,
            Product.base_price,
            db.func.sum(OrderItem.quantity).label('total_sold')
        ).join(
            OrderItem
        ).join(
            Order
        ).filter(
            Order.status == 'delivered'
        )

        if start_date:
            query = query.filter(Order.created_at >= start_date)

        results = query.group_by(Product.id).order_by(
            db.desc('total_sold')
        ).limit(limit).all()

        return [
            {
                'id': r.id,
                'name': r.name,
                'base_price': float(r.base_price),
                'total_sold': r.total_sold
            }
            for r in results
        ]

    def get_sales_summary(self, days=30):
        start_date = datetime.utcnow() - timedelta(days=days)

        total_sales_result = db.session.query(
            db.func.sum(Order.total)
        ).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).scalar()

        total_orders_result = db.session.query(
            db.func.count(Order.id)
        ).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).scalar()

        avg_order_result = db.session.query(
            db.func.avg(Order.total)
        ).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).scalar()

        return {
            'total_sales': float(total_sales_result or 0),
            'total_orders': total_orders_result or 0,
            'avg_order_value': float(avg_order_result or 0),
            'period_days': days
        }

    def export_to_csv(self, data, filename):
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        if data:
            writer.writerow(data[0].keys())
            for row in data:
                writer.writerow(row.values())

        return output.getvalue()

analytics_service = AnalyticsService()
