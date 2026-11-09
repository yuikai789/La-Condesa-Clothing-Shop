import io
import os

from flask import current_app


def remote_enabled():
    return (current_app.config.get('STORAGE_BACKEND') or 'local').lower() == 's3'


def _s3_client():
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError(
            'El almacenamiento S3 requiere el paquete boto3. Instálalo con "pip install boto3".'
        ) from exc

    client_kwargs = {}
    region = current_app.config.get('S3_REGION')
    endpoint = current_app.config.get('S3_ENDPOINT_URL')
    access_key = current_app.config.get('S3_ACCESS_KEY_ID')
    secret_key = current_app.config.get('S3_SECRET_ACCESS_KEY')

    if region:
        client_kwargs['region_name'] = region
    if endpoint:
        client_kwargs['endpoint_url'] = endpoint
    if access_key and secret_key:
        client_kwargs['aws_access_key_id'] = access_key
        client_kwargs['aws_secret_access_key'] = secret_key

    return boto3.client('s3', **client_kwargs)


def _bucket():
    bucket = current_app.config.get('S3_BUCKET')
    if not bucket:
        raise RuntimeError('S3_BUCKET debe configurarse cuando STORAGE_BACKEND=s3')
    return bucket


def _object_key(path):
    prefix = (current_app.config.get('S3_PREFIX') or '').strip('/')
    key = (path or '').lstrip('/')
    return f'{prefix}/{key}' if prefix else key


def local_path(path):
    return os.path.join(current_app.config['RECEIPTS_FOLDER'], os.path.basename(path or ''))


def upload_file(local_file_path, path):
    if not remote_enabled():
        return path
    _s3_client().upload_file(local_file_path, _bucket(), _object_key(path))
    return path


def open_receipt(path):
    if not path:
        return None
    if remote_enabled():
        response = _s3_client().get_object(Bucket=_bucket(), Key=_object_key(path))
        return io.BytesIO(response['Body'].read())
    return local_path(path)


def receipt_exists(path):
    if not path:
        return False
    if remote_enabled():
        try:
            _s3_client().head_object(Bucket=_bucket(), Key=_object_key(path))
            return True
        except Exception:
            return False
    return os.path.isfile(local_path(path))


def delete_receipt(path):
    if not path:
        return False
    try:
        if remote_enabled():
            _s3_client().delete_object(Bucket=_bucket(), Key=_object_key(path))
            return True
        filepath = local_path(path)
        if os.path.isfile(filepath):
            os.remove(filepath)
            return True
    except Exception:
        current_app.logger.exception('No se pudo eliminar el comprobante %s', path)
    return False
