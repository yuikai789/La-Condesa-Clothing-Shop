import pytest

from extensions import db
from models import User


def make_user(email, password='Clave123', role='customer', active=True):
    user = User(name='Usuario Auth', email=email, role=role, is_active=active)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def test_login_redirects_by_role(client, app):
    make_user('employee@test.com', role='employee')

    response = client.post('/auth/login', data={
        'email': 'employee@test.com', 'password': 'Clave123'})
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/employee/dashboard')
    client.post('/auth/logout')

    make_user('cliente-login@test.com')
    response = client.post('/auth/login', data={
        'email': 'cliente-login@test.com', 'password': 'Clave123'})
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/customer/dashboard')
    client.post('/auth/logout')

    response = client.post('/auth/login', data={
        'email': 'admin@lacondesa.com', 'password': 'Admin123!'})
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/dashboard')


def test_login_invalid_and_inactive(client, app):
    make_user('inactivo@test.com', active=False)

    response = client.post('/auth/login', data={
        'email': 'nadie@test.com', 'password': 'Clave123'})
    assert response.status_code == 200
    assert b'inv' in response.data.lower()

    response = client.post('/auth/login', data={
        'email': 'inactivo@test.com', 'password': 'Clave123'})
    assert response.status_code == 200
    assert b'deshabilitada' in response.data.lower()


def test_login_with_overlong_password_does_not_crash(client, app):
    make_user('larga@test.com')
    response = client.post('/auth/login', data={
        'email': 'larga@test.com', 'password': 'a' * 200})
    assert response.status_code == 200


def test_register_success_duplicate_and_normalization(client, app):
    response = client.post('/auth/register', data={
        'name': 'Cliente Nuevo',
        'email': 'Nuevo@Example.COM',
        'password': 'Clave123',
        'phone': '5551234567',
    })
    assert response.status_code == 302

    user = User.query.filter_by(email='nuevo@example.com').first()
    assert user is not None
    assert user.role == 'customer'
    assert user.check_password('Clave123') is True

    client.post('/auth/logout')
    response = client.post('/auth/register', data={
        'name': 'Cliente Nuevo',
        'email': 'nuevo@example.com',
        'password': 'Clave123',
        'phone': '5551234567',
    })
    assert response.status_code == 200
    assert b'ya est' in response.data.lower()


@pytest.mark.parametrize('data', [
    {'name': 'A', 'email': 'bien@test.com', 'password': 'Clave123', 'phone': ''},
    {'name': 'Bien', 'email': 'mal', 'password': 'Clave123', 'phone': ''},
    {'name': 'Bien', 'email': 'bien2@test.com', 'password': 'corta', 'phone': ''},
    {'name': 'Bien', 'email': 'bien3@test.com', 'password': 'Clave123', 'phone': 'abc'},
])
def test_register_validation_errors(client, data):
    response = client.post('/auth/register', data=data)
    assert response.status_code == 200
    assert User.query.filter_by(email=data['email'].lower()).first() is None


def test_logout_clears_session(client, app):
    make_user('logout@test.com')
    client.post('/auth/login', data={'email': 'logout@test.com', 'password': 'Clave123'})
    assert client.get('/customer/dashboard').status_code == 200

    assert client.get('/auth/logout').status_code == 405
    assert client.post('/auth/logout').status_code == 302
    assert client.get('/customer/dashboard').status_code == 302


def test_csrf_blocks_post_without_token(client, app, monkeypatch):
    monkeypatch.setitem(app.config, 'WTF_CSRF_ENABLED', True)
    response = client.post('/auth/login', data={
        'email': 'admin@lacondesa.com', 'password': 'Admin123!'})
    assert response.status_code == 400
    assert client.get('/auth/login').status_code == 200


def test_not_found_and_forbidden_pages(client, app):
    assert client.get('/ruta-que-no-existe').status_code == 404

    make_user('sin-permiso@test.com')
    client.post('/auth/login', data={'email': 'sin-permiso@test.com',
                                     'password': 'Clave123'})
    response = client.get('/admin/dashboard')
    assert response.status_code == 403
    assert b'403' in response.data or b'denegado' in response.data.lower()


def test_production_requires_secret_key(monkeypatch):
    from flask import Flask
    from config import ProductionConfig

    monkeypatch.delenv('SECRET_KEY', raising=False)
    dummy = Flask(__name__)
    dummy.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    with pytest.raises(RuntimeError):
        ProductionConfig.init_app(dummy)
