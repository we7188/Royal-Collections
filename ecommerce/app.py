from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from models import db, User, CartItem, Order, Contact

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db.init_app(app)

# Load products from static images folder with categories and prices
def load_products():
    products = []
    categories = {
        'Electronics': ['galaxy 05.jpeg', 'hp laptop.jpeg', 'laptop.jpeg', 'redmi 15c.webp', 'bluetooth speaker.jpeg', 'jbl system.jpeg', 'earpods.jpeg'],
        'Kitchen': ['electric kettle.jpeg', 'dispenser.jpeg'],
        'Appliances': ['fridge.jpeg'],
        'Shoes': ['air force shoe.jpeg'],
        'Beauty': ['blow dry.jpeg'],
        'Toys': ['rubix cube.jpeg'],
        'Accessories': ['water bottle.jpeg']
    }
    # Prices in KES based on real market values
    prices = {
        'galaxy 05.jpeg': 20000,
        'hp laptop.jpeg': 50000,
        'laptop.jpeg': 40000,
        'redmi 15c.webp': 15000,
        'bluetooth speaker.jpeg': 3000,
        'jbl system.jpeg': 8000,
        'earpods.jpeg': 2000,
        'electric kettle.jpeg': 3500,
        'dispenser.jpeg': 2500,
        'fridge.jpeg': 25000,
        'air force shoe.jpeg': 1500,
        'blow dry.jpeg': 5000,
        'rubix cube.jpeg': 200,
        'water bottle.jpeg': 1000
    }
    images_dir = os.path.join(app.static_folder, 'images')
    if os.path.exists(images_dir):
        for filename in os.listdir(images_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                product_name = os.path.splitext(filename)[0].replace('_', ' ').title()
                category = 'Other'
                for cat, files in categories.items():
                    if filename in files:
                        category = cat
                        break
                price = prices.get(filename, 1000)  # Default price if not found
                products.append({
                    'name': product_name,
                    'image': filename,
                    'category': category,
                    'price': price
                })
    return products

@app.route('/')
def index():
    products = load_products()
    cart_count = 0
    if 'user_id' in session:
        cart_count = CartItem.query.filter_by(user_id=session['user_id']).count()
    return render_template('index.html', products=products, cart_count=cart_count)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user = User(username=username, email=email, password=password)
        try:
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            flash('Registration successful!')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                flash('Email already registered. Please use a different email.')
            else:
                flash('Registration failed. Please try again.')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('register'))
    cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
    return render_template('cart.html', cart_items=cart_items)

@app.route('/add_to_cart/<product_name>')
def add_to_cart(product_name):
    if 'user_id' not in session:
        return redirect(url_for('register'))
    products = load_products()
    product = next((p for p in products if p['name'] == product_name), None)
    if not product:
        flash('Product not found.')
        return redirect(url_for('index'))
    cart_item = CartItem.query.filter_by(user_id=session['user_id'], product_name=product_name).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=session['user_id'], product_name=product_name, price=product['price'])
        db.session.add(cart_item)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.')
    return redirect(url_for('index'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('register'))
    cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
    if request.method == 'POST':
        # Create orders from cart items
        for item in cart_items:
            order = Order(user_id=item.user_id, product_name=item.product_name, price=item.price, quantity=item.quantity)
            db.session.add(order)
        # Clear cart
        CartItem.query.filter_by(user_id=session['user_id']).delete()
        db.session.commit()
        flash('Payment successful via M-PESA! Order placed.')
        return redirect(url_for('index'))
    return render_template('checkout.html', cart_items=cart_items)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        problem_type = request.form['problem_type']
        message = request.form['message']
        contact_entry = Contact(name=name, email=email, problem_type=problem_type, message=message)
        db.session.add(contact_entry)
        db.session.commit()
        flash('Thank you for contacting us! We will get back to you soon.')
        return redirect(url_for('index'))
    cart_count = 0
    if 'user_id' in session:
        cart_count = CartItem.query.filter_by(user_id=session['user_id']).count()
    return render_template('contact.html', cart_count=cart_count)

@app.route('/delete_from_cart/<int:item_id>')
def delete_from_cart(item_id):
    if 'user_id' not in session:
        return redirect(url_for('register'))
    item = CartItem.query.filter_by(id=item_id, user_id=session['user_id']).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Item removed from cart.')
    return redirect(url_for('cart'))

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('register'))
    orders = Order.query.filter_by(user_id=session['user_id']).all()
    cart_count = CartItem.query.filter_by(user_id=session['user_id']).count()
    return render_template('orders.html', orders=orders, cart_count=cart_count)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
