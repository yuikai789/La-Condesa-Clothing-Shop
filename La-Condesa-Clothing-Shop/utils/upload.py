import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_payment_receipt(file, order_id):
    if not file or not allowed_file(file.filename):
        return None, 'Invalid file type'

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"receipt_{order_id}_{uuid.uuid4().hex[:8]}.{ext}"

    upload_folder = os.path.join(current_app.root_path, 'static', 'receipts')
    os.makedirs(upload_folder, exist_ok=True)

    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    return f"receipts/{filename}", None

def save_image(file, product_id):
    """Save uploaded image file"""
    if not file or not allowed_file(file.filename):
        return None, 'Invalid file type'
    
    # Create filename with UUID
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"product_{product_id}_{uuid.uuid4().hex[:8]}.{ext}"
    
    # Ensure upload directory exists
    upload_folder = os.path.join(current_app.root_path, 'static', 'images')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    return f"images/{filename}", None

def delete_image(image_path):
    """Delete image file"""
    if not image_path:
        return False
    
    filepath = os.path.join(current_app.root_path, 'static', image_path)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    
    return False

def get_image_url(image_path):
    """Get full URL for image"""
    if not image_path:
        return None
    return f"/static/{image_path}"
