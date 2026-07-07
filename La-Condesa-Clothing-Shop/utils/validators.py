import re

def validate_registration(data):
    errors = {}

    name = data.get('name', '').strip()
    if not name or len(name) < 2:
        errors['name'] = 'El nombre debe tener al menos 2 caracteres'

    email = data.get('email', '').strip().lower()
    if not email or '@' not in email:
        errors['email'] = 'Se requiere un correo electrónico válido'
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors['email'] = 'Formato de correo electrónico inválido'

    password = data.get('password', '')
    if not password or len(password) < 8:
        errors['password'] = 'La contraseña debe tener al menos 8 caracteres'
    elif not re.search(r'[A-Z]', password):
        errors['password'] = 'La contraseña debe contener al menos una letra mayúscula'
    elif not re.search(r'[a-z]', password):
        errors['password'] = 'La contraseña debe contener al menos una letra minúscula'
    elif not re.search(r'\d', password):
        errors['password'] = 'La contraseña debe contener al menos un número'

    phone = data.get('phone', '').strip()
    if phone and not re.match(r'^\+?1?\d{9,15}$', phone):
        errors['phone'] = 'Formato de número telefónico inválido'

    return errors

def validate_product(data):
    errors = {}

    name = data.get('name', '').strip()
    if not name or len(name) > 100:
        errors['name'] = 'El nombre debe tener entre 1 y 100 caracteres'

    description = data.get('description', '')
    if description and len(description) > 1000:
        errors['description'] = 'La descripción debe tener menos de 1000 caracteres'

    base_price = data.get('base_price', 0)
    try:
        base_price = float(base_price)
        if base_price < 0:
            errors['base_price'] = 'El precio no puede ser negativo'
    except (ValueError, TypeError):
        errors['base_price'] = 'Formato de precio inválido'

    category_id = data.get('category_id')
    if not category_id:
        errors['category_id'] = 'Se requiere una categoría'

    sizes = data.get('sizes', [])
    if not sizes:
        errors['sizes'] = 'Se requiere al menos una talla'
    else:
        for i, size in enumerate(sizes):
            if not size.get('size'):
                errors[f'sizes_{i}_size'] = 'Se requiere el nombre de la talla'
            try:
                stock = int(size.get('stock_quantity', 0))
                if stock < 0:
                    errors[f'sizes_{i}_stock'] = 'El stock no puede ser negativo'
            except (ValueError, TypeError):
                errors[f'sizes_{i}_stock'] = 'Formato de stock inválido'

    colors = data.get('colors', [])
    for i, color in enumerate(colors):
        if not color.get('color'):
            errors[f'colors_{i}'] = 'Se requiere el nombre del color'

    return errors

def validate_order(data):
    errors = {}

    pickup_location = data.get('pickup_location', '').strip()
    if pickup_location and len(pickup_location) > 100:
        errors['pickup_location'] = 'La ubicación de recogida debe tener menos de 100 caracteres'

    payment_reference = data.get('payment_reference', '').strip()
    if payment_reference and len(payment_reference) > 50:
        errors['payment_reference'] = 'La referencia de pago debe tener menos de 50 caracteres'

    return errors
