import barcode
from barcode.writer import ImageWriter
import os
from flask import send_from_directory
from models import Product

def generate_barcode(product_id):
    # Create barcode
    code = barcode.get('code128', str(product_id), writer=ImageWriter())
    
    # Save to static/barcodes directory
    if not os.path.exists('static/barcodes'):
        os.makedirs('static/barcodes')
    
    filename = code.save(f'static/barcodes/{product_id}')
    return filename

def get_barcode_path(product_id):
    return f'barcodes/{product_id}.png'

def setup_barcode_routes(app):
    @app.route('/barcode/<int:product_id>')
    @login_required
    def get_product_barcode(product_id):
        product = Product.query.get_or_404(product_id)
        barcode_path = f'static/barcodes/{product_id}.png'
        
        if not os.path.exists(barcode_path):
            generate_barcode(product_id)
        
        return send_from_directory('static/barcodes', f'{product_id}.png')

