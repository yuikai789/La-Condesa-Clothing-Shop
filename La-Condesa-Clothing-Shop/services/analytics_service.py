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

    def get_financial_summary(self, days=30):
        start_date = datetime.utcnow() - timedelta(days=days)

        total_revenue = db.session.query(
            db.func.sum(Order.total)
        ).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).scalar() or 0

        total_orders = db.session.query(
            db.func.count(Order.id)
        ).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).scalar() or 0

        avg_order_value = (total_revenue / total_orders) if total_orders else 0

        total_tax = db.session.query(
            db.func.sum(Order.tax)
        ).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).scalar() or 0

        total_subtotal = db.session.query(
            db.func.sum(Order.subtotal)
        ).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).scalar() or 0

        total_discounts = db.session.query(
            db.func.sum(Order.discount)
        ).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).scalar() or 0

        total_items = db.session.query(
            db.func.sum(OrderItem.quantity)
        ).join(Order).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).scalar() or 0

        return {
            'total_revenue': float(total_revenue),
            'total_subtotal': float(total_subtotal),
            'total_tax': float(total_tax),
            'total_discounts': float(total_discounts),
            'total_orders': total_orders,
            'total_items': total_items,
            'avg_order_value': float(avg_order_value),
            'period_days': days
        }

    def get_monthly_sales(self, months=6):
        results = []
        now = datetime.utcnow()
        for i in range(months - 1, -1, -1):
            raw_month = now.month - i
            year_offset = 0
            if raw_month <= 0:
                year_offset = -((raw_month - 1) // 12) + 1
            m = ((raw_month - 1) % 12) + 1
            y = now.year - (i // 12) if raw_month > 0 else now.year - ((abs(raw_month) // 12) + 1)
            if raw_month <= 0:
                y = now.year + year_offset
            month_start = datetime(y, m, 1)
            if m == 12:
                month_end = datetime(y + 1, 1, 1)
            else:
                month_end = datetime(y, m + 1, 1)

            revenue = db.session.query(
                db.func.sum(Order.total)
            ).filter(
                Order.status == 'delivered',
                Order.created_at >= month_start,
                Order.created_at < month_end
            ).scalar() or 0

            count = db.session.query(
                db.func.count(Order.id)
            ).filter(
                Order.status == 'delivered',
                Order.created_at >= month_start,
                Order.created_at < month_end
            ).scalar() or 0

            month_name = month_start.strftime('%Y-%m')
            results.append({
                'month': month_name,
                'revenue': float(revenue),
                'orders': count
            })

        return results

    def get_profit_by_product(self, days=30):
        start_date = datetime.utcnow() - timedelta(days=days)

        results = db.session.query(
            Product.id,
            Product.name,
            Product.base_price,
            db.func.sum(OrderItem.quantity).label('total_sold'),
            db.func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_revenue')
        ).join(
            OrderItem
        ).join(
            Order
        ).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).group_by(Product.id).order_by(
            db.desc('total_revenue')
        ).all()

        total_revenue = sum(float(r.total_revenue or 0) for r in results) if results else 0

        return [
            {
                'id': r.id,
                'name': r.name,
                'base_price': float(r.base_price),
                'total_sold': r.total_sold,
                'total_revenue': float(r.total_revenue or 0),
                'percentage': round((float(r.total_revenue or 0) / total_revenue * 100), 2) if total_revenue else 0
            }
            for r in results
        ], float(total_revenue)

    def get_order_status_breakdown(self):
        from models import Order
        statuses = ['pending_payment', 'paid', 'preparing', 'ready_for_pickup', 'delivered']
        breakdown = {}
        for status in statuses:
            count = Order.query.filter_by(status=status).count()
            total = Order.query.filter_by(status=status).with_entities(
                db.func.sum(Order.total)
            ).scalar() or 0
            breakdown[status] = {'count': count, 'total': float(total)}
        return breakdown

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
