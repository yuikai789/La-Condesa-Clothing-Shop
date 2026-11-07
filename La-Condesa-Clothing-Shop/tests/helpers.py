import io

from PIL import Image


def login(client, email, password):
    response = client.post('/auth/login', data={'email': email, 'password': password})
    assert response.status_code == 302
    return response


def create_product(client, name='Producto Test', price='100', size='M', stock='10', color='Rojo',
                   category_id='1'):
    response = client.post('/admin/products', data={
        'name': name,
        'description': 'Producto de prueba',
        'base_price': price,
        'category_id': category_id,
        'sizes[]': size,
        'stocks[]': stock,
        'colors[]': color,
    })
    assert response.status_code == 302
    return response


def create_customer(client, name='Cliente Test', email='cliente@test.com', password='Cliente123',
                    phone='5551234567'):
    response = client.post('/admin/users', data={
        'name': name,
        'email': email,
        'password': password,
        'phone': phone,
        'role': 'customer',
    })
    assert response.status_code == 302
    return response


def add_to_cart(client, product_id, size='M', color='Rojo', quantity=1):
    return client.post('/customer/cart', data={
        'action': 'add',
        'product_id': str(product_id),
        'size': size,
        'color': color,
        'quantity': str(quantity),
    })


def checkout(client, pickup_location='Tienda'):
    return client.post('/customer/checkout', data={'pickup_location': pickup_location})


def png_bytes():
    image = Image.new('RGB', (10, 10), 'white')
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer
