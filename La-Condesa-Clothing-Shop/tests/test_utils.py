import io
import os
from datetime import datetime, timedelta, timezone

import pytest
from werkzeug.datastructures import FileStorage

from extensions import db
from models import User
from utils.datetime_utils import utcnow
from utils.pagination import Pagination, paginate_query
from utils.qr_generator import generate_qr_code
from utils.upload import (allowed_file, delete_image, save_image,
                          save_payment_receipt)
from utils.validators import (validate_email, validate_order, validate_password,
                              validate_phone, validate_product,
                              validate_registration)
from tests.helpers import png_bytes


@pytest.mark.parametrize('email', ['a@b.com', 'nombre.apellido+tag@dominio.co'])
def test_validate_email_valid(email):
    assert validate_email(email) is None


@pytest.mark.parametrize('email', ['', None, 'sin-arroba', 'a@b', 'a b@c.com'])
def test_validate_email_invalid(email):
    assert validate_email(email) is not None


@pytest.mark.parametrize('password', ['Clave123', 'Abcdefg1', 'A' * 70 + 'b1'])
def test_validate_password_valid(password):
    assert validate_password(password) is None


@pytest.mark.parametrize('password,expected', [
    ('Ab1', 'al menos 8'),
    ('clave123', 'mayúscula'),
    ('CLAVE123', 'minúscula'),
    ('ClaveSinNumero', 'número'),
    ('Aa1' + 'a' * 70, '72 bytes'),
])
def test_validate_password_invalid(password, expected):
    error = validate_password(password)
    assert error is not None
    assert expected in error


@pytest.mark.parametrize('phone', ['', None, '5551234567', '+15551234567'])
def test_validate_phone_valid(phone):
    assert validate_phone(phone) is None


@pytest.mark.parametrize('phone', ['abc', '123', '555-123-4567'])
def test_validate_phone_invalid(phone):
    assert validate_phone(phone) is not None


def test_validate_registration():
    valid = {
        'name': 'Cliente Valido',
        'email': 'cliente@example.com',
        'password': 'Clave123',
        'phone': '5551234567',
    }
    assert validate_registration(valid) == {}

    errors = validate_registration({
        'name': 'A',
        'email': 'invalido',
        'password': 'corta',
        'phone': 'abc',
    })
    assert set(errors) == {'name', 'email', 'password', 'phone'}


def test_validate_product():
    valid = {
        'name': 'Producto',
        'description': 'Descripcion',
        'base_price': '99.90',
        'category_id': '1',
        'sizes': [{'size': 'M', 'stock_quantity': '3'}],
        'colors': [{'color': 'Rojo'}],
    }
    assert validate_product(valid) == {}

    errors = validate_product({
        'name': '',
        'description': 'x' * 1001,
        'base_price': 'abc',
        'category_id': 'x',
        'sizes': [{'size': '', 'stock_quantity': '-1'}],
        'colors': [{'color': ''}],
    })
    assert 'name' in errors
    assert 'description' in errors
    assert 'base_price' in errors
    assert 'category_id' in errors
    assert 'sizes_0_size' in errors
    assert 'sizes_0_stock' in errors
    assert 'colors_0' in errors

    assert 'sizes' in validate_product({'name': 'X', 'base_price': 1,
                                        'category_id': 1, 'sizes': [],
                                        'colors': []})


def test_validate_order_handles_none_and_lengths():
    assert validate_order({'pickup_location': None, 'payment_reference': None}) == {}
    assert 'pickup_location' in validate_order({'pickup_location': 'x' * 101})
    assert 'payment_reference' in validate_order({'payment_reference': 'x' * 51})
    assert validate_order({'pickup_location': 'Tienda', 'payment_reference': 'REF-1'}) == {}


def test_pagination(app):
    for index in range(4):
        db.session.add(User(name=f'Paginado {index}', email=f'pagina{index}@test.com',
                            password_hash='x'))
    db.session.commit()

    first = paginate_query(User.query.order_by(User.id), page=1, per_page=2)
    assert isinstance(first, Pagination)
    assert first.total == 5
    assert first.pages == 3
    assert first.has_prev is False
    assert first.has_next is True
    assert first.next_num == 2
    assert len(first.items) == 2

    clamped = paginate_query(User.query, page=0, per_page=2)
    assert clamped.page == 1

    last = paginate_query(User.query.order_by(User.id), page=3, per_page=2)
    assert last.has_prev is True
    assert last.has_next is False
    assert last.prev_num == 2
    assert len(last.items) == 1


def test_utcnow_is_naive_and_current():
    value = utcnow()
    assert value.tzinfo is None
    expected = datetime.now(timezone.utc).replace(tzinfo=None)
    assert abs(expected - value) < timedelta(seconds=5)


def test_qr_generation_creates_unique_files(app):
    first = generate_qr_code('ORD-UNO')
    second = generate_qr_code('ORD-DOS')
    try:
        assert first.startswith('images/qrcodes/')
        assert second.startswith('images/qrcodes/')
        assert first != second
        assert os.path.isfile(os.path.join(app.root_path, 'static', first))
        assert os.path.isfile(os.path.join(app.root_path, 'static', second))
    finally:
        for relative in (first, second):
            path = os.path.join(app.root_path, 'static', relative)
            if os.path.isfile(path):
                os.remove(path)


def test_upload_allowed_file(app):
    assert allowed_file('foto.PNG') is True
    assert allowed_file('foto.jpeg') is True
    assert allowed_file('foto.txt') is False
    assert allowed_file('sin_extension') is False


def test_save_and_delete_image(app):
    path, error = save_image(FileStorage(png_bytes(), filename='foto.png'), 99)
    try:
        assert error is None
        assert path.startswith('images/product_99_')
        assert os.path.isfile(os.path.join(app.root_path, 'static', path))
        assert delete_image(path) is True
        assert delete_image(path) is False
    finally:
        full_path = os.path.join(app.root_path, 'static', path or '')
        if path and os.path.isfile(full_path):
            os.remove(full_path)


def test_save_image_rejects_bad_extension_and_content(app):
    path, error = save_image(FileStorage(png_bytes(), filename='foto.txt'), 1)
    assert path is None
    assert error == 'Invalid file type'

    path, error = save_image(FileStorage(io.BytesIO(b'no-es-imagen'), filename='falso.png'), 1)
    assert path is None
    assert error == 'El archivo no es una imagen válida'


def test_save_payment_receipt(app):
    path, error = save_payment_receipt(FileStorage(png_bytes(), filename='pago.png'), 7)
    assert error is None
    assert path.startswith('receipts/receipt_7_')
    full_path = os.path.join(app.config['RECEIPTS_FOLDER'], os.path.basename(path))
    try:
        assert os.path.isfile(full_path)
    finally:
        if os.path.isfile(full_path):
            os.remove(full_path)


def test_delete_image_rejects_unsafe_paths(app):
    assert delete_image(None) is False
    assert delete_image('') is False
    assert delete_image('../config.py') is False
    assert delete_image('images/no-existe.png') is False
