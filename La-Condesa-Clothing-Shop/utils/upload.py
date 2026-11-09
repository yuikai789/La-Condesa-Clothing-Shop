import os
import shutil
import tempfile
import uuid

from flask import current_app
from PIL import Image

from utils import storage


def allowed_file(filename):
    allowed = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def _verify_image(file):
    try:
        Image.open(file.stream).verify()
    except Exception:
        return False
    finally:
        try:
            file.stream.seek(0)
        except (AttributeError, OSError):
            pass
    return True


def _save_file(file, prefix, subfolder):
    if not file or not allowed_file(file.filename):
        return None, 'Invalid file type'

    if not _verify_image(file):
        return None, 'El archivo no es una imagen válida'

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}"
    relative_path = f"{subfolder}/{filename}"

    if subfolder == 'receipts':
        if storage.remote_enabled():
            folder = tempfile.mkdtemp(prefix='la_condesa_receipt_')
        else:
            folder = current_app.config['RECEIPTS_FOLDER']
    else:
        folder = os.path.join(current_app.root_path, 'static', subfolder)

    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    file.save(filepath)

    if subfolder == 'receipts' and storage.remote_enabled():
        try:
            storage.upload_file(filepath, relative_path)
        except Exception:
            current_app.logger.exception('No se pudo subir el comprobante al almacenamiento externo')
            return None, 'No se pudo almacenar el comprobante de forma persistente'
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    return relative_path, None


def save_payment_receipt(file, order_id):
    return _save_file(file, f"receipt_{order_id}", 'receipts')


def save_image(file, product_id):
    return _save_file(file, f"product_{product_id}", 'images')


def delete_image(image_path):
    if not image_path:
        return False

    static_root = os.path.abspath(os.path.join(current_app.root_path, 'static'))
    filepath = os.path.abspath(os.path.join(static_root, image_path))
    try:
        if os.path.commonpath([static_root, filepath]) != static_root:
            return False
    except ValueError:
        return False

    if os.path.isfile(filepath):
        os.remove(filepath)
        return True

    return False
