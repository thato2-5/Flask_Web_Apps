from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from models import db, Product, Order, OrderItem, Inventory, User
from datetime import datetime
from flask_login import LoginManager, current_user, login_required
from auth import auth_bp
import os
#import LoginForm, RegistrationForm
from dotenv import load_dotenv
from api import api_bp
from reports import reports_bp
#from barcode import setup_barcode_routes
from export import export_products_to_csv, export_products_to_excel, export_products_to_pdf

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///warehouse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

load_dotenv()  # Load environment variables from .env file

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

app.register_blueprint(reports_bp, url_prefix='/reports')
app.register_blueprint(api_bp, url_prefix='/api/v1')
#setup_barcode_routes(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Product routes

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        
        product = Product(name=name, description=description, price=price)
        db.session.add(product)
        db.session.commit()
        
        # Create inventory record for the new product
        inventory = Inventory(product_id=product.id, quantity=0)
        db.session.add(inventory)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('list_products'))
    
    return render_template('add_product.html')

@app.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('list_products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/products/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    # First delete related inventory and order items
    Inventory.query.filter_by(product_id=id).delete()
    OrderItem.query.filter_by(product_id=id).delete()
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('list_products'))

# Order routes
@app.route('/orders')
@login_required
def list_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/orders/<int:id>')
@login_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('order_detail.html', order=order)

@app.route('/orders/add', methods=['GET', 'POST'])
@login_required
def create_order():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_email = request.form['customer_email']
        customer_phone = request.form['customer_phone']
        
        order = Order(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        
        flash('Order created successfully!', 'success')
        return redirect(url_for('order_detail', id=order.id))
    
    products = Product.query.all()
    return render_template('create_order.html', products=products)

@app.route('/orders/<int:id>/add_item', methods=['POST'])
@login_required
def add_order_item(id):
    order = Order.query.get_or_404(id)
    product_id = int(request.form['product_id'])
    quantity = int(request.form['quantity'])
    
    product = Product.query.get(product_id)
    
    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('order_detail', id=id))
    
    # Check inventory
    inventory = Inventory.query.filter_by(product_id=product_id).first()
    if inventory.quantity < quantity:
        flash(f'Not enough stock for {product.name}! Only {inventory.quantity} available.', 'danger')
        return redirect(url_for('order_detail', id=id))
    
    # Add item to order
    item = OrderItem(
        order_id=id,
        product_id=product_id,
        quantity=quantity,
        price_at_time=product.price
    )
    db.session.add(item)
    db.session.commit()
    
    flash('Item added to order!', 'success')
    return redirect(url_for('order_detail', id=id))

@app.route('/orders/<int:id>/update_status', methods=['POST'])
@login_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form['status']
    
    if new_status not in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
        flash('Invalid status!', 'danger')
        return redirect(url_for('order_detail', id=id))
    
    # If order is being completed, deduct inventory
    if new_status == 'shipped' and order.status != 'shipped':
        for item in order.items:
            inventory = Inventory.query.filter_by(product_id=item.product_id).first()
            inventory.quantity -= item.quantity
            db.session.add(inventory)
    
    order.status = new_status
    db.session.commit()
    
    flash('Order status updated!', 'success')
    return redirect(url_for('order_detail', id=id))

# Inventory routes
@app.route('/inventory')
@login_required
def view_inventory():
    inventory = db.session.query(Inventory, Product)\
        .join(Product, Inventory.product_id == Product.id)\
        .all()
    
    low_stock = [item for item in inventory if item.Inventory.quantity < item.Inventory.low_stock_threshold]
    
    return render_template('inventory.html', inventory=inventory, low_stock=low_stock)

@app.route('/inventory/<int:id>/update', methods=['POST'])
@login_required
def update_inventory(id):
    inventory = Inventory.query.get_or_404(id)
    action = request.form['action']
    quantity = int(request.form['quantity'])
    
    if action == 'add':
        inventory.quantity += quantity
    elif action == 'remove':
        if inventory.quantity < quantity:
            flash('Cannot remove more than available quantity!', 'danger')
            return redirect(url_for('view_inventory'))
        inventory.quantity -= quantity
    
    db.session.commit()
    flash('Inventory updated successfully!', 'success')
    return redirect(url_for('view_inventory'))

@app.route('/products')
@login_required
def list_products():
    query = Product.query
    
    # Search
    search_term = request.args.get('q')
    if search_term:
        query = query.filter(Product.name.ilike(f'%{search_term}%') | 
                         Product.description.ilike(f'%{search_term}%'))
    
    # Price filter
    min_price = request.args.get('min_price')
    if min_price:
        query = query.filter(Product.price >= float(min_price))
    
    max_price = request.args.get('max_price')
    if max_price:
        query = query.filter(Product.price <= float(max_price))
    
    # Sorting
    sort_option = request.args.get('sort', 'name_asc')
    if sort_option == 'name_asc':
        query = query.order_by(Product.name.asc())
    elif sort_option == 'name_desc':
        query = query.order_by(Product.name.desc())
    elif sort_option == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_option == 'price_desc':
        query = query.order_by(Product.price.desc())
    
    products = query.all()
    return render_template('products.html', products=products)

@app.route('/products/export/csv')
@login_required
def export_products_csv():
    return export_products_to_csv()

@app.route('/products/export/excel')
@login_required
def export_products_excel():
    return export_products_to_excel()

@app.route('/products/export/pdf')
@login_required
def export_products_pdf():
    return export_products_to_pdf()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)

