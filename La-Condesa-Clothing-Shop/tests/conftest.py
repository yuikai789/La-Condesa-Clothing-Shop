import os
import tempfile

import pytest

_TEST_DIR = tempfile.mkdtemp(prefix='la_condesa_tests_')
os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.join(_TEST_DIR, 'test.db').replace('\\', '/')
os.environ['FLASK_ENV'] = 'development'
os.environ.setdefault('SECRET_KEY', 'test-secret-key')

from app import app as flask_app
from extensions import db
from init_db import initialize_database


@pytest.fixture()
def app():
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY='test-secret-key',
    )
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        initialize_database(flask_app)
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_client(client):
    response = client.post('/auth/login', data={
        'email': 'admin@lacondesa.com',
        'password': 'Admin123!',
    })
    assert response.status_code == 302
    return client
