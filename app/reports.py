from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from models import db, Order, Product, Inventory
from datetime import datetime, timedelta
from sqlalchemy import func

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def reports_dashboard():
    return render_template('reports/dashboard.html')

@reports_bp.route('/reports/sales')
@login_required
def sales_report():
    # Default to last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Get filter parameters
    start_date_param = request.args.get('start_date')
    end_date_param = request.args.get('end_date')
    
    if start_date_param:
        start_date = datetime.strptime(start_date_param, '%Y-%m-%d')
    if end_date_param:
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d')
    
    # Query orders in date range
    orders = Order.query.filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date
    ).all()
    
    # Calculate total sales
    total_sales = sum(
        sum(item.quantity * item.price_at_time for item in order.items)
        for order in orders
    )
    
    # Sales by product
    sales_by_product = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity * OrderItem.price_at_time).label('total_sales'),
        func.sum(OrderItem.quantity).label('total_quantity')
    ).join(OrderItem, OrderItem.product_id == Product.id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date
     ).group_by(Product.name).all()
    
    return render_template('reports/sales.html',
                         orders=orders,
                         total_sales=total_sales,
                         sales_by_product=sales_by_product,
                         start_date=start_date.date(),
                         end_date=end_date.date())

@reports_bp.route('/reports/inventory')
@login_required
def inventory_report():
    # Get low stock items
    low_stock = db.session.query(Inventory, Product)\
        .join(Product, Inventory.product_id == Product.id)\
        .filter(Inventory.quantity < Inventory.low_stock_threshold)\
        .all()
    
    # Get inventory value
    inventory_value = db.session.query(
        func.sum(Inventory.quantity * Product.price)
    ).join(Product, Inventory.product_id == Product.id).scalar()
    
    return render_template('reports/inventory.html',
                         low_stock=low_stock,
                         inventory_value=inventory_value)

