import os
from datetime import datetime
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
DATABASE = os.path.join(os.path.dirname(__file__), 'glowy.db')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'glowyadmin123')
_db_initialized = False
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

PRODUCTS = [
    {
        'name': 'Glow Serum',
        'description': 'Hydrating vitamin C face serum for radiant skin.',
        'price': 29.99,
        'category': 'Skincare'
    },
    {
        'name': 'Luminous Lip Tint',
        'description': 'Sheer, long-lasting lip tint with a glossy finish.',
        'price': 18.50,
        'category': 'Cosmetics'
    },
    {
        'name': 'Silk Night Cream',
        'description': 'Nourishing overnight moisturizer for soft skin.',
        'price': 34.99,
        'category': 'Skincare'
    },
    {
        'name': 'Velvet Matte Eyeshadow',
        'description': 'Palette of natural, blendable shades for everyday looks.',
        'price': 24.00,
        'category': 'Cosmetics'
    },
    {
        'name': 'Radiant Facial Oil',
        'description': 'Lightweight oil to restore brightness and glow.',
        'price': 27.50,
        'category': 'Skincare'
    }
]

CREATE_PRODUCTS_SQL = '''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    image TEXT DEFAULT ''
);
'''

CREATE_ORDERS_SQL = '''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    shipping_address TEXT NOT NULL,
    shipping_city TEXT NOT NULL,
    shipping_postal_code TEXT NOT NULL,
    total REAL NOT NULL,
    created_at TEXT NOT NULL
);
'''

CREATE_ORDER_ITEMS_SQL = '''
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);
'''


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(CREATE_PRODUCTS_SQL)
        cursor.execute(CREATE_ORDERS_SQL)
        cursor.execute(CREATE_ORDER_ITEMS_SQL)
        cursor.execute('SELECT count(*) FROM products')
        product_count = cursor.fetchone()[0]
        if product_count == 0:
            for product in PRODUCTS:
                cursor.execute(
                    'INSERT INTO products (name, description, price, category, image) VALUES (?, ?, ?, ?, ?);',
                    (product['name'], product['description'], product['price'], product['category'], product.get('image', ''))
                )
        conn.commit()


def ensure_db():
    global _db_initialized
    if _db_initialized:
        return

    if not os.path.exists(DATABASE):
        init_db()
    else:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='products'")
        has_products = cursor.fetchone()[0] > 0
        if has_products:
            cursor.execute("PRAGMA table_info(products)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'image' not in columns:
                cursor.execute('ALTER TABLE products ADD COLUMN image TEXT DEFAULT ""')

        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='orders'")
        has_orders = cursor.fetchone()[0] > 0
        if has_orders:
            cursor.execute("PRAGMA table_info(orders)")
            order_columns = [row[1] for row in cursor.fetchall()]
            missing_order_columns = {
                'customer_phone': 'TEXT DEFAULT ""',
                'shipping_city': 'TEXT DEFAULT ""',
                'shipping_postal_code': 'TEXT DEFAULT ""'
            }
            for column, ddl in missing_order_columns.items():
                if column not in order_columns:
                    cursor.execute(f'ALTER TABLE orders ADD COLUMN {column} {ddl}')

        conn.commit()
        conn.close()
        if not has_products:
            init_db()

    _db_initialized = True

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db_connection():
    ensure_db()
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin panel.')
            return redirect(url_for('admin_login'))
        return view_func(*args, **kwargs)
    return wrapped_view


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Logged in successfully.')
            return redirect(url_for('admin_products'))
        flash('Invalid admin credentials.')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have logged out.')
    return redirect(url_for('home'))


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
@admin_required
def admin_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('admin_products.html', products=products)


@app.route('/admin/orders')
@admin_required
def admin_orders():
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin_orders.html', orders=orders)


@app.route('/admin/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    order_items = conn.execute(
        'SELECT oi.quantity, oi.price, p.name FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = ?',
        (order_id,)
    ).fetchall()
    conn.close()
    if not order:
        flash('Order not found.')
        return redirect(url_for('admin_orders'))
    return render_template('admin_order_detail.html', order=order, items=order_items)


@app.route('/admin/add-product', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price_raw = request.form.get('price', '0').strip()
        category = request.form.get('category', '').strip() or 'Uncategorized'
        image_name = ''

        try:
            price = float(price_raw)
        except ValueError:
            price = 0.0

        image_file = request.files.get('image')
        if image_file and image_file.filename and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            image_name = f"{timestamp}_{filename}"
            image_path = os.path.join(UPLOAD_FOLDER, image_name)
            image_file.save(image_path)
        elif image_file and image_file.filename:
            flash('Only PNG, JPG, JPEG, and GIF images are allowed.')
            return redirect(url_for('add_product'))

        if name and description and price > 0:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO products (name, description, price, category, image) VALUES (?, ?, ?, ?, ?)',
                (name, description, price, category, image_name)
            )
            conn.commit()
            conn.close()
            flash('Product added successfully!')
            return redirect(url_for('admin_products'))

        flash('Please enter a complete product name, description, and price.')

    return render_template('add_product.html')


@app.route('/admin/edit-product/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        conn.close()
        flash('Product not found.')
        return redirect(url_for('admin_products'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price_raw = request.form.get('price', '0').strip()
        category = request.form.get('category', '').strip() or 'Uncategorized'
        image_name = product['image']

        try:
            price = float(price_raw)
        except ValueError:
            price = product['price']

        image_file = request.files.get('image')
        if image_file and image_file.filename and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            image_name = f"{timestamp}_{filename}"
            image_path = os.path.join(UPLOAD_FOLDER, image_name)
            image_file.save(image_path)
        elif image_file and image_file.filename:
            flash('Only PNG, JPG, JPEG, and GIF images are allowed.')
            conn.close()
            return redirect(url_for('edit_product', product_id=product_id))

        if name and description and price > 0:
            conn.execute(
                'UPDATE products SET name = ?, description = ?, price = ?, category = ?, image = ? WHERE id = ?',
                (name, description, price, category, image_name, product_id)
            )
            conn.commit()
            conn.close()
            flash('Product updated successfully!')
            return redirect(url_for('admin_products'))

        flash('Please enter valid product information.')

    conn.close()
    return render_template('edit_product.html', product=product)


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
        phone = request.form['phone']
        address = request.form['address']
        city = request.form['city']
        postal_code = request.form['postal_code']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO orders (customer_name, customer_email, customer_phone, shipping_address, shipping_city, shipping_postal_code, total, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (name, email, phone, address, city, postal_code, total, datetime.utcnow().isoformat())
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
        return render_template(
            'checkout_success.html',
            order_id=order_id,
            items=items,
            total=total,
            name=name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            postal_code=postal_code
        )

    return render_template('checkout.html', items=items, total=total)


if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )
