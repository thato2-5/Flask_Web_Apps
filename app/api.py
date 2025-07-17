from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Product, Order, Inventory
from functools import wraps

api_bp = Blueprint('api', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.role == 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/products', methods=['GET'])
@login_required
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': p.price,
        'inventory': p.inventory.quantity if p.inventory else 0
    } for p in products])

@api_bp.route('/products/<int:id>', methods=['GET'])
@login_required
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'inventory': product.inventory.quantity if product.inventory else 0
    })

@api_bp.route('/products', methods=['POST'])
@login_required
@admin_required
def create_product():
    data = request.get_json()
    product = Product(
        name=data['name'],
        description=data.get('description', ''),
        price=data['price']
    )
    db.session.add(product)
    db.session.commit()
    
    # Create inventory record
    inventory = Inventory(
        product_id=product.id,
        quantity=data.get('quantity', 0)
    )
    db.session.add(inventory)
    db.session.commit()
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'message': 'Product created successfully'
    }), 201

