from datetime import datetime, timedelta
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)  
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            image TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()
@app.route('/product/<int:product_id>')
def product_page(product_id):
    
    product_tuple = get_product_by_id(product_id)  
    product_dict = {
        'id': product_tuple[0],
        'name': product_tuple[1],
        'image': product_tuple[2],
        'description': product_tuple[3],
        'price': product_tuple[4]
    }
    return render_template('product_description.html', product=product_dict)
@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    
    if 'cart' in session:
        
        session['cart'] = [item for item in session['cart'] if item['product_id'] != product_id]
        session.modified = True  

    return redirect(url_for('view_cart'))  
@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, name, description, price, image FROM products")
    products = [{'id': row[0], 'name': row[1], 'description': row[2], 'price': row[3], 'image': row[4]} for row in c.fetchall()]
    conn.close()
    username = session.get('username')
    return render_template('index.html', products=products, username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = username
            session['cart'] = []  # Initialize an empty cart
            return redirect(url_for('index'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return 'Username already exists. Please choose a different one.'
        finally:
            conn.close()
    return render_template('signup.html')

@app.route('/add_to_cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    if 'username' not in session:
        return redirect(url_for('login')) 

    product = get_product_by_id(product_id)
    if not product:
        return "Product not found", 404

    if 'cart' not in session:
        session['cart'] = []
        session['cart_add_time'] = datetime.now() 

    cart = session['cart']
    existing_item = next((item for item in cart if item['product_id'] == product_id), None)
    if existing_item:
        existing_item['quantity'] += 1
    else:
        cart.append({'product_id': product[0], 'name': product[1], 'price': product[3], 'quantity': 1, 'image': product[4]})

    session['cart'] = cart
    session['cart_add_time'] = datetime.now() 
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'username' not in session:
        return redirect(url_for('login')) 

    cart_items = session.get('cart', [])
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    cart_add_time = session.get('cart_add_time', datetime.now())
    if cart_add_time.tzinfo is not None:
        cart_add_time = cart_add_time.replace(tzinfo=None) 
    
    current_time = datetime.now() 
    
    time_diff = current_time - cart_add_time 

    discount = 0
    if time_diff <= timedelta(minutes=1): 
        discount = total_price * 0.20 
    elif time_diff <= timedelta(minutes=2):  
        discount = total_price * 0.10  
    elif time_diff <= timedelta(minutes=3): 
        discount = total_price * 0.05 

    final_price = total_price - discount

    if request.method == 'POST':
        session['cart'] = [] 
        return redirect(url_for('thank_you'))

    return render_template('checkout.html', total_price=total_price, discount=discount, final_price=final_price, discount_percentage=(20 if discount == total_price * 0.20 else 10 if discount == total_price * 0.10 else 5 if discount == total_price * 0.05 else 0))

# Get product by ID
def get_product_by_id(product_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()
    return product

from flask import Flask, render_template, request, jsonify


@app.route('/voice_search')
def voice_search():
    query = request.args.get('query')
    if query:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, name, description, price, image FROM products WHERE name LIKE ?", ('%' + query + '%',))
        products = [{'id': row[0], 'name': row[1], 'description': row[2], 'price': row[3], 'image': row[4]} for row in c.fetchall()]
        conn.close()

        return jsonify(products=products)
    else:
        return jsonify({'error': 'No query provided'}), 400

@app.route('/view_cart')
def view_cart():
    cart_items = session.get('cart', [])
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('view_cart.html', cart_items=cart_items, total_price=total_price)


@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/offers')
def offers():
    offers_data = [
        {"title": "10% off on your next purchase!", "description": "Get 10% off on your next order."},
        {"title": "Free shipping on orders above $50!", "description": "Enjoy free shipping on orders above $50."},
        {"title": "Buy 1, get 1 free on selected items!", "description": "Limited time offer on selected items."}
    ]
    return jsonify(offers_data)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)