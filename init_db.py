import sqlite3

import os

DATABASE = os.path.join(os.path.dirname(__file__), 'glowy.db')

products = [
    {
        'name': 'Glow Serum',
        'description': 'Hydrating vitamin C face serum for radiant skin.',
        'price': 29.99,
        'category': 'Skincare',
        'image': ''
    },
    {
        'name': 'Luminous Lip Tint',
        'description': 'Sheer, long-lasting lip tint with a glossy finish.',
        'price': 18.50,
        'category': 'Cosmetics',
        'image': ''
    },
    {
        'name': 'Silk Night Cream',
        'description': 'Nourishing overnight moisturizer for soft skin.',
        'price': 34.99,
        'category': 'Skincare',
        'image': ''
    },
    {
        'name': 'Velvet Matte Eyeshadow',
        'description': 'Palette of natural, blendable shades for everyday looks.',
        'price': 24.00,
        'category': 'Cosmetics',
        'image': ''
    },
    {
        'name': 'Radiant Facial Oil',
        'description': 'Lightweight oil to restore brightness and glow.',
        'price': 27.50,
        'category': 'Skincare',
        'image': ''
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
    shipping_address TEXT NOT NULL,
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
        cursor.execute('DELETE FROM products;')
        for product in products:
            cursor.execute(
                'INSERT INTO products (name, description, price, category, image) VALUES (?, ?, ?, ?, ?);',
                (product['name'], product['description'], product['price'], product['category'], product.get('image', ''))
            )
        conn.commit()


if __name__ == '__main__':
    init_db()
    print('Initialized SQLite database and seeded product data in glowy.db.')
