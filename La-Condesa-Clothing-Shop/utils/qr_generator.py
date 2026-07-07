import qrcode
import os
from datetime import datetime

def generate_qr_code(data, filename=None, folder='static/images/qrcodes'):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(base_dir, '..', folder)
    os.makedirs(folder_path, exist_ok=True)

    if not filename:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'qr_{timestamp}.png'

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')

    filepath = os.path.join(folder_path, filename)
    img.save(filepath)

    return os.path.join(folder, filename)
