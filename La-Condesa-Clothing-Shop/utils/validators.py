import re

EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_RE = re.compile(r'^\+?1?\d{9,15}$')


def validate_email(email):
    email = (email or '').strip()
    if not email:
        return 'Se requiere un correo electrónico válido'
    if not EMAIL_RE.match(email):
        return 'Formato de correo electrónico inválido'
    return None


def validate_password(password):
    password = password or ''
    if len(password) < 8:
        return 'La contraseña debe tener al menos 8 caracteres'
    if len(password.encode('utf-8')) > 72:
        return 'La contraseña no puede superar los 72 bytes'
    if not re.search(r'[A-Z]', password):
        return 'La contraseña debe contener al menos una letra mayúscula'
    if not re.search(r'[a-z]', password):
        return 'La contraseña debe contener al menos una letra minúscula'
    if not re.search(r'\d', password):
        return 'La contraseña debe contener al menos un número'
    return None


def validate_phone(phone):
    phone = (phone or '').strip()
    if phone and not PHONE_RE.match(phone):
        return 'Formato de número telefónico inválido'
    return None


def validate_registration(data):
    errors = {}

    name = data.get('name', '').strip()
    if not name or len(name) < 2:
        errors['name'] = 'El nombre debe tener al menos 2 caracteres'

    email_error = validate_email(data.get('email', '').lower())
    if email_error:
        errors['email'] = email_error

    password_error = validate_password(data.get('password', ''))
    if password_error:
        errors['password'] = password_error

    phone_error = validate_phone(data.get('phone', ''))
    if phone_error:
        errors['phone'] = phone_error

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
    else:
        try:
            int(category_id)
        except (ValueError, TypeError):
            errors['category_id'] = 'Categoría inválida'

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
