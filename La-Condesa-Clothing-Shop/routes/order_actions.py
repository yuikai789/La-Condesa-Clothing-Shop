from flask import flash, redirect, url_for
from flask_login import current_user
from services.order_service import order_service
from services.audit_service import log_action


def run_order_action(order_id, action, redirect_endpoint, payment_reference=None):
    if action == 'confirm_payment':
        order, error = order_service.confirm_payment(order_id, current_user.id, payment_reference)
        success = 'Pago confirmado exitosamente'
        description = 'Pago confirmado para orden {}'
        status = 'paid'
    elif action == 'prepare':
        order, error = order_service.mark_as_preparing(order_id)
        success = 'Pedido marcado como preparando'
        description = 'Orden {} marcada como preparando'
        status = 'preparing'
    elif action == 'ready':
        order, error = order_service.mark_as_ready(order_id)
        success = 'Pedido marcado como listo para recoger'
        description = 'Orden {} marcada como lista para recoger'
        status = 'ready_for_pickup'
    elif action == 'cancel':
        order, error = order_service.cancel_order(order_id)
        success = 'Pedido cancelado exitosamente'
        description = 'Orden {} cancelada'
        status = 'cancelled'
    elif action == 'deliver':
        order, error = order_service.mark_as_delivered(order_id)
        success = 'Pedido marcado como entregado'
        description = 'Orden {} marcada como entregada'
        status = 'delivered'
    else:
        raise ValueError(f'Acción de pedido desconocida: {action}')

    if error:
        flash(f'Error: {error}', 'error')
    else:
        log_action(
            'confirm_payment' if action == 'confirm_payment' else 'update_status',
            'order',
            order_id,
            description.format(order.order_number),
            new_value={'status': status}
        )
        flash(success, 'success')

    return redirect(url_for(redirect_endpoint))
