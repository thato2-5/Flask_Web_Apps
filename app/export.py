from flask import make_response
from io import BytesIO
import csv
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from models import Product, Order

def export_products_to_csv():
    products = Product.query.all()
    si = BytesIO()
    cw = csv.writer(si)
    
    # Write header
    cw.writerow(['ID', 'Name', 'Description', 'Price', 'Inventory'])
    
    # Write data
    for product in products:
        cw.writerow([
            product.id,
            product.name,
            product.description,
            product.price,
            product.inventory.quantity if product.inventory else 0
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=products.csv"
    output.headers["Content-type"] = "text/csv"
    return output

def export_products_to_excel():
    products = Product.query.all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"
    
    # Write header
    ws.append(['ID', 'Name', 'Description', 'Price', 'Inventory'])
    
    # Write data
    for product in products:
        ws.append([
            product.id,
            product.name,
            product.description,
            product.price,
            product.inventory.quantity if product.inventory else 0
        ])
    
    si = BytesIO()
    wb.save(si)
    si.seek(0)
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=products.xlsx"
    output.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return output

def export_products_to_pdf():
    products = Product.query.all()
    si = BytesIO()
    p = canvas.Canvas(si)
    
    # Set up PDF
    p.setFont("Helvetica", 12)
    y = 800  # Start position
    
    # Write header
    p.drawString(50, y, "Product Inventory Report")
    y -= 30
    
    # Write column headers
    p.drawString(50, y, "ID")
    p.drawString(100, y, "Name")
    p.drawString(300, y, "Price")
    p.drawString(400, y, "Inventory")
    y -= 20
    
    # Write data
    for product in products:
        p.drawString(50, y, str(product.id))
        p.drawString(100, y, product.name[:30])  # Limit name length
        p.drawString(300, y, f"${product.price:.2f}")
        p.drawString(400, y, str(product.inventory.quantity if product.inventory else 0))
        y -= 20
        
        if y < 50:  # New page if we're at the bottom
            p.showPage()
            y = 800
            p.setFont("Helvetica", 12)
    
    p.save()
    si.seek(0)
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=products.pdf"
    output.headers["Content-type"] = "application/pdf"
    return output

