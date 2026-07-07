from flask_mail import Message
from flask import render_template
from extensions import mail
import logging
import os
from datetime import datetime

class EmailService:

    def __init__(self, app=None):
        if app:
            self.init_app(app)
        self.logger = logging.getLogger(__name__)

    def init_app(self, app):
        self.app = app

    def send_email(self, subject, recipients, html=None, text=None):
        try:
            msg = Message(
                subject=subject,
                recipients=recipients,
                html=html,
                body=text
            )
            mail.send(msg)
            return True
        except Exception as e:
            self.logger.error(f"Email falló: {e}")
            self._log_email_failure(subject, recipients, str(e))
            return False

    def send_order_confirmation(self, order, customer_email, customer_name, order_items):
        html = render_template(
            'emails/order_confirmation.html',
            order=order,
            customer_name=customer_name,
            items=order_items
        )
        return self.send_email(
            subject='Confirmación de Pedido - La Condesa',
            recipients=[customer_email],
            html=html
        )

    def send_order_ready(self, order, customer_email, customer_name):
        html = render_template(
            'emails/order_ready.html',
            order=order,
            customer_name=customer_name
        )
        return self.send_email(
            subject='Pedido Listo para Recoger - La Condesa',
            recipients=[customer_email],
            html=html
        )

    def send_order_delivered(self, order, customer_email, customer_name):
        html = render_template(
            'emails/order_delivered.html',
            order=order,
            customer_name=customer_name
        )
        return self.send_email(
            subject='Pedido Entregado - Gracias - La Condesa',
            recipients=[customer_email],
            html=html
        )

    def _log_email_failure(self, subject, recipients, error):
        errors_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'errors.txt')
        with open(errors_file, 'a') as f:
            f.write(f"[{datetime.utcnow().isoformat()}] EMAIL_ERROR: {error}\n")
            f.write(f"  Asunto: {subject}\n")
            f.write(f"  Destinatarios: {recipients}\n")
            f.write(f"  Fecha: {datetime.utcnow().isoformat()}\n\n")

email_service = EmailService()
