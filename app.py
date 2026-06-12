import os
from datetime import datetime
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
DATABASE = 'glowy.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def home():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('index.html', products=products)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product is None:
        return redirect(url_for('home'))
    return render_template('product.html', product=product)


@app.route('/admin/products')
def admin_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('admin_products.html', products=products)


@app.route('/admin/add-product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price_raw = request.form.get('price', '0').strip()
        category = request.form.get('category', '').strip() or 'Uncategorized'
        try:
            price = float(price_raw)
        except ValueError:
            price = 0.0

        if name and description and price > 0:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO products (name, description, price, category) VALUES (?, ?, ?, ?)',
                (name, description, price, category)
            )
            conn.commit()
            conn.close()
            flash('Product added successfully!')
            return redirect(url_for('admin_products'))

        flash('Please enter a complete product name, description, and price.')

    return render_template('add_product.html')


@app.route('/cart')
def cart():
    items = []
    total = 0.0
    cart_data = session.get('cart', {})
    if cart_data:
        conn = get_db_connection()
        for product_id, quantity in cart_data.items():
            product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
            if product:
                subtotal = product['price'] * quantity
                total += subtotal
                items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
        conn.close()
    return render_template('cart.html', items=items, total=total)


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    cart_data = session.get('cart', {})
    cart_data[str(product_id)] = cart_data.get(str(product_id), 0) + quantity
    session['cart'] = cart_data
    flash('Added to cart successfully!')
    return redirect(url_for('cart'))


@app.route('/update_cart', methods=['POST'])
def update_cart():
    cart_data = session.get('cart', {})
    for product_id, quantity in request.form.items():
        if product_id.startswith('quantity_'):
            pid = product_id.split('_', 1)[1]
            try:
                qty = int(quantity)
            except ValueError:
                qty = 0
            if qty > 0:
                cart_data[pid] = qty
            else:
                cart_data.pop(pid, None)
    session['cart'] = cart_data
    flash('Cart updated successfully.')
    return redirect(url_for('cart'))


@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart_data = session.get('cart', {})
    cart_data.pop(str(product_id), None)
    session['cart'] = cart_data
    flash('Item removed from cart.')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_data = session.get('cart', {})
    if not cart_data:
        flash('Your cart is empty.')
        return redirect(url_for('home'))

    conn = get_db_connection()
    items = []
    total = 0.0
    for product_id, quantity in cart_data.items():
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if product:
            subtotal = product['price'] * quantity
            total += subtotal
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
    conn.close()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        address = request.form['address']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO orders (customer_name, customer_email, shipping_address, total, created_at) VALUES (?, ?, ?, ?, ?)',
            (name, email, address, total, datetime.utcnow().isoformat())
        )
        order_id = cursor.lastrowid
        for item in items:
            cursor.execute(
                'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                (order_id, item['product']['id'], item['quantity'], item['product']['price'])
            )
        conn.commit()
        conn.close()

        session.pop('cart', None)
        return render_template('checkout_success.html', order_id=order_id, items=items, total=total, name=name)

    return render_template('checkout.html', items=items, total=total)


if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )
