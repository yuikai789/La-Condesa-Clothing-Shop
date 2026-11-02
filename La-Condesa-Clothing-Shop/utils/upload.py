import os
import uuid
from flask import current_app


def allowed_file(filename):
    allowed = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def _save_file(file, prefix, subfolder):
    if not file or not allowed_file(file.filename):
        return None, 'Invalid file type'

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}"
    folder = os.path.join(current_app.root_path, 'static', subfolder)
    os.makedirs(folder, exist_ok=True)

    file.save(os.path.join(folder, filename))
    return f"{subfolder}/{filename}", None


def save_payment_receipt(file, order_id):
    return _save_file(file, f"receipt_{order_id}", 'receipts')


def save_image(file, product_id):
    return _save_file(file, f"product_{product_id}", 'images')


def delete_image(image_path):
    if not image_path:
        return False

    filepath = os.path.join(current_app.root_path, 'static', image_path)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True

    return False
