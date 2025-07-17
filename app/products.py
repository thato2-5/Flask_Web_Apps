@app.route('/products/bulk_add', methods=['GET', 'POST'])
@login_required
@admin_required
def bulk_add_products():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                if file.filename.endswith('.csv'):
                    import csv
                    reader = csv.DictReader(file.read().decode('utf-8').splitlines())
                    products = [row for row in reader]
                elif file.filename.endswith('.json'):
                    import json
                    products = json.load(file)
                
                count = 0
                for product_data in products:
                    product = Product(
                        name=product_data['name'],
                        description=product_data.get('description', ''),
                        price=float(product_data['price'])
                    )
                    db.session.add(product)
                    db.session.flush()  # To get the ID
                    
                    inventory = Inventory(
                        product_id=product.id,
                        quantity=int(product_data.get('quantity', 0))
                    db.session.add(inventory)
                    count += 1
                
                db.session.commit()
                flash(f'Successfully added {count} products', 'success')
                return redirect(url_for('list_products'))
            
            except Exception as e:
                db.session.rollback()
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(request.url)

    return render_template('products/bulk_add.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['csv', 'json']

