from datetime import datetime, timedelta
from sqlalchemy import extract
from extensions import db
from models import Order, OrderItem, Product
from utils.datetime_utils import utcnow


class AnalyticsService:

    def _start_date(self, days):
        return utcnow() - timedelta(days=days)

    def _month_start(self, reference, offset):
        total = reference.year * 12 + reference.month - 1 - offset
        return datetime(total // 12, total % 12 + 1, 1)

    def get_daily_sales(self, days=30):
        start_date = self._start_date(days)

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

        if days:
            query = query.filter(Order.created_at >= self._start_date(days))

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

    def get_financial_summary(self, days=30):
        start_date = self._start_date(days)

        row = db.session.query(
            db.func.sum(Order.total),
            db.func.sum(Order.subtotal),
            db.func.sum(Order.tax),
            db.func.sum(Order.discount),
            db.func.count(Order.id),
            db.func.avg(Order.total)
        ).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).one()

        total_items = db.session.query(
            db.func.sum(OrderItem.quantity)
        ).join(Order).filter(
            Order.status == 'delivered',
            Order.created_at >= start_date
        ).scalar() or 0

        return {
            'total_revenue': float(row[0] or 0),
            'total_subtotal': float(row[1] or 0),
            'total_tax': float(row[2] or 0),
            'total_discounts': float(row[3] or 0),
            'total_orders': row[4] or 0,
            'total_items': total_items,
            'avg_order_value': float(row[5] or 0),
            'period_days': days
        }

    def get_sales_summary(self, days=30):
        summary = self.get_financial_summary(days)
        return {
            'total_sales': summary['total_revenue'],
            'total_orders': summary['total_orders'],
            'avg_order_value': summary['avg_order_value'],
            'period_days': days
        }

    def get_monthly_sales(self, months=6):
        now = utcnow()
        starts = [self._month_start(now, offset) for offset in range(months - 1, -1, -1)]
        year_col = extract('year', Order.created_at)
        month_col = extract('month', Order.created_at)

        results = db.session.query(
            year_col.label('year'),
            month_col.label('month'),
            db.func.sum(Order.total),
            db.func.count(Order.id)
        ).filter(
            Order.status == 'delivered',
            Order.created_at >= starts[0]
        ).group_by(year_col, month_col).all()

        data = {(int(y), int(m)): (float(total or 0), count) for y, m, total, count in results}
        return [
            {
                'month': start.strftime('%Y-%m'),
                'revenue': data.get((start.year, start.month), (0.0, 0))[0],
                'orders': data.get((start.year, start.month), (0.0, 0))[1]
            }
            for start in starts
        ]

    def get_profit_by_product(self, days=30):
        start_date = self._start_date(days)

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

        total_revenue = sum(float(r.total_revenue or 0) for r in results)

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
        results = db.session.query(
            Order.status,
            db.func.count(Order.id),
            db.func.sum(Order.total)
        ).group_by(Order.status).all()

        breakdown = {status: {'count': 0, 'total': 0.0} for status in Order.STATUSES}
        for status, count, total in results:
            breakdown[status] = {'count': count, 'total': float(total or 0)}
        return breakdown

    def export_to_csv(self, data, filename):
        import csv
        import io

        def safe_cell(value):
            if value is None:
                return ''
            text = str(value)
            if text and text[0] in ('=', '+', '-', '@'):
                return f"'{text}"
            return text

        output = io.StringIO()
        writer = csv.writer(output)

        if data:
            headers = list(data[0].keys())
            writer.writerow(headers)
            for row in data:
                writer.writerow([safe_cell(row.get(header)) for header in headers])

        return output.getvalue()


analytics_service = AnalyticsService()
