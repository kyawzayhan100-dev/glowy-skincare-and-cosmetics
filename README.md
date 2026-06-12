# Glowy Skincare and Cosmetics

A simple e-commerce website built with Flask and SQLite for product browsing, cart management, and checkout.

## Features

- Product catalog with skincare and cosmetics items
- Product details page
- Shopping cart stored in session
- SQLite database for product and order data
- Checkout form and order confirmation
- Admin product editing for name, price, category, and image
- Product image upload support for store listings

## Setup Instructions

1. Install Python 3.11+.
2. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

3. Activate the environment if allowed:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks script execution, run the next steps directly with the venv executables:

   ```powershell
   .\.venv\Scripts\pip.exe install -r requirements.txt
   .\.venv\Scripts\python.exe init_db.py
   .\.venv\Scripts\python.exe app.py
   ```

4. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Initialize the database:

   ```powershell
   python init_db.py
   ```

6. Run the app:

   ```powershell
   python app.py
   ```

7. Open `http://127.0.0.1:5000` in your browser.

## Project Files

- `app.py` - Flask web application
- `init_db.py` - SQLite schema and seed data setup
- `templates/` - HTML templates for the site
- `static/css/style.css` - Styling for the site
- `glowy.db` - Generated SQLite database file after initialization

## Adding More Products

### Option 1: Add products from the site

Visit `http://127.0.0.1:5000/admin/products` and use the `Add Product` button to create new products or edit existing product name, price, category, and image.

### Option 2: Add products by editing the database seed data

Open `init_db.py` and add new items to the `products` list, then run:

```powershell
.\.venv\Scripts\python.exe init_db.py
```

### Option 3: Insert directly into SQLite

```powershell
sqlite3 glowy.db
INSERT INTO products (name, description, price, category) VALUES ('New Cream', 'Hydrating cream', 22.50, 'Skincare');
.exit
```

## Deploying to the Internet

1. Initialize Git in the project folder:

   ```powershell
   "C:\Program Files\Git\cmd\git.exe" init
   "C:\Program Files\Git\cmd\git.exe" add .
   "C:\Program Files\Git\cmd\git.exe" commit -m "Initial Glowy Skincare and Cosmetics site"
   ```

2. Create a GitHub repository and push your code.
3. Choose a deployment service like Railway, Render, or PythonAnywhere.
4. Configure the service to run your app with:

   ```bash
   python app.py
   ```

5. If your host provides a dashboard, set `PORT` automatically or leave it to the platform.

### Recommended deploy platforms

- Railway: connect GitHub repo, set start command `python app.py`
- Render: connect GitHub repo, use Python service and `python app.py`
- PythonAnywhere: upload files and set the web app entry point to `app.py`

### Notes

- The app now binds to `0.0.0.0` and uses `PORT` from the environment, which hosts require.
- Keep `glowy.db` local during development; deployment platforms may use their own persistent storage.
git push -u origin master