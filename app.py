from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps  # Для створення декораторів
from flask_sqlalchemy import SQLAlchemy  # ORM для роботи з базою даних
from datetime import datetime, timedelta, UTC  # Для роботи з датою та часом
from werkzeug.security import generate_password_hash, check_password_hash  # Для шифрування паролів
import os
from dotenv import load_dotenv

# Завантажуємо змінні середовища
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Секретний ключ для сесій (замініть на власний)

# Налаштування підключення до SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модель товару в базі даних
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Унікальний ідентифікатор
    name = db.Column(db.String(100), nullable=False)  # Назва товару
    code = db.Column(db.String(50), unique=True, nullable=False)  # Унікальний артикул
    quantity = db.Column(db.Integer, default=0)  # Кількість на складі
    price = db.Column(db.Float, nullable=False)  # Ціна
    min_quantity = db.Column(db.Integer, default=0)  # Мінімальний залишок

# Модель операції (прихід/витрата)
class Operation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))  # Дата операції
    type = db.Column(db.String(20), nullable=False)  # Тип операції: 'incoming' (прихід) або 'outgoing' (витрата)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)  # Зв'язок з товаром
    quantity = db.Column(db.Integer, nullable=False)  # Кількість товару в операції
    price = db.Column(db.Float, nullable=False)  # Ціна за одиницю
    
    # Створюємо зв'язок з моделлю Product
    product = db.relationship('Product', backref=db.backref('operations', lazy=True))

# Модель користувача для авторизації
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)  # Логін
    password = db.Column(db.String(120), nullable=False)  # Хешований пароль
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email

# Модель для логування дій користувачів
class ActionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # Тип дії (додавання, редагування, видалення)
    description = db.Column(db.Text, nullable=False)  # Опис дії
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    # Зв'язок з користувачем
    user = db.relationship('User', backref=db.backref('actions', lazy=True))

# Декоратор для перевірки авторизації користувача
def login_required(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:  # Якщо користувач не авторизований
            return redirect(url_for('login'))  # Перенаправляємо на сторінку входу
        return view_function(*args, **kwargs)
    return decorated_function

# Головна сторінка (дашборд)
@app.route('/')
@login_required
def index():
    try:
        # Отримуємо дані для відображення на дашборді
        products = Product.query.all()  # Всі товари
        low_stock_products = Product.query.filter(Product.quantity <= Product.min_quantity).all()  # Товари з низьким залишком
        recent_operations = Operation.query.order_by(Operation.date.desc()).limit(5).all()  # Останні 5 операцій
        total_value = sum(product.quantity * product.price for product in products)  # Загальна вартість товарів
        
        return render_template('dashboard.html',
                             products=products,
                             low_stock_products=low_stock_products,
                             recent_operations=recent_operations,
                             total_value=total_value)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('dashboard.html', error="Помилка при завантаженні даних")

# Сторінка каталогу товарів
@app.route('/catalog')
@login_required
def catalog():
    try:
        products = Product.query.all()  # Отримуємо всі товари
        return render_template('catalog.html', products=products)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('catalog.html', products=[], error="Помилка при завантаженні товарів")

# Додавання нового товару
@app.route('/add_product', methods=['POST'])
@login_required
def add_product():
    try:
        if request.method == 'POST':
            # Отримуємо дані з форми
            name = request.form['name']
            code = request.form['code']
            quantity = int(request.form['quantity'])
            price = float(request.form['price'])
            min_quantity = int(request.form['min_quantity'])
            
            # Перевіряємо чи існує товар з таким артикулом
            existing_product = Product.query.filter_by(code=code).first()
            if existing_product:
                return jsonify({"error": "Товар з таким артикулом вже існує"}), 400
            
            # Створюємо новий товар
            product = Product(
                name=name,
                code=code,
                quantity=quantity, 
                price=price,
                min_quantity=min_quantity
            )
            db.session.add(product)
            db.session.commit()
            
            # Логуємо дію
            log_action(
                'add_product',
                f'Додано новий товар: {name} (артикул: {code})'
            )
            
            return jsonify({"message": "Товар успішно додано"})
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": "Некоректні дані. Перевірте правильність введених значень"}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error adding product: {str(e)}")
        return jsonify({"error": "Помилка при додаванні товару"}), 400

# Сторінка обліку товарів
@app.route('/inventory')
@login_required
def inventory():
    products = Product.query.all()
    operations = Operation.query.order_by(Operation.date.desc()).limit(10).all()  # Останні 10 операцій
    return render_template('inventory.html', products=products, operations=operations)

# Сторінка звітів
@app.route('/reports')
@login_required
def reports():
    try:
        # Отримуємо параметри дат з запиту
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Отримуємо товари з низьким залишком
        low_stock_products = Product.query.filter(Product.quantity <= Product.min_quantity).all()
        
        # Базовий запит операцій
        operations_query = Operation.query

        # Якщо вказані дати, фільтруємо операції за періодом
        if start_date and end_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # До кінця дня
            operations_query = operations_query.filter(Operation.date.between(start, end))
            
            # Логуємо формування звіту
            log_action(
                'generate_report',
                f'Сформовано звіт за період: {start_date} - {end_date}'
            )
        else:
            # Якщо дати не вказані, беремо операції за останній місяць
            month_ago = datetime.now(UTC) - timedelta(days=30)
            operations_query = operations_query.filter(Operation.date >= month_ago)

        operations = operations_query.order_by(Operation.date.desc()).all()
        
        # Рахуємо загальну вартість товарів
        total_value = sum(product.quantity * product.price for product in Product.query.all())
        
        # Рахуємо загальну кількість товарів
        total_items = sum(product.quantity for product in Product.query.all())
        
        return render_template('reports.html',
                             low_stock_products=low_stock_products,
                             operations=operations,
                             total_value=total_value,
                             total_items=total_items,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        print(f"Error generating report: {e}")
        return render_template('reports.html', error="Помилка при формуванні звіту")

# Додавання операції приходу товару
@app.route('/add_incoming', methods=['POST'])
@login_required
def add_incoming():
    try:
        # Отримуємо дані з форми
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        date = datetime.strptime(request.form['datetime'], '%Y-%m-%dT%H:%M')

        # Перевіряємо чи існує товар
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Товар не знайдено"}), 404

        # Створюємо нову операцію приходу
        operation = Operation(
            type='incoming',
            product_id=product_id,
            quantity=quantity,
            price=price,
            date=date
        )
        
        # Оновлюємо кількість товару на складі
        product.quantity += quantity

        db.session.add(operation)
        db.session.commit()

        # Логуємо дію
        log_action(
            'add_incoming',
            f'Додано прихід товару: {product.name}, кількість: {quantity}, ціна: {price}'
        )

        return jsonify({"message": "Прихід успішно додано"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/add_outgoing', methods=['POST'])
@login_required
def add_outgoing():
    try:
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        date = datetime.strptime(request.form['datetime'], '%Y-%m-%dT%H:%M')

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Товар не знайдено"}), 404

        if product.quantity < quantity:
            return jsonify({"error": "Недостатньо товару на складі"}), 400

        # Создаем новую операцию
        operation = Operation(
            type='outgoing',
            product_id=product_id,
            quantity=quantity,
            price=price,
            date=date
        )
        
        # Обновляем количество товара
        product.quantity -= quantity

        db.session.add(operation)
        db.session.commit()

        # Логуємо дію
        log_action(
            'add_outgoing',
            f'Додано витрату товару: {product.name}, кількість: {quantity}, ціна: {price}'
        )

        return jsonify({"message": "Витрату успішно додано"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# Маршрути аутентифікації
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            
            # Логуємо успішний вхід
            log_action(
                'user_login',
                f'Користувач {username} увійшов в систему'
            )
            
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Невірний логін або пароль')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Користувач вже існує')
        
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email вже використовується')
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, email=email)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Логуємо реєстрацію нового користувача
            log_action(
                'user_registration',
                f'Зареєстровано нового користувача: {username}'
            )
            
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error='Помилка при реєстрації')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            # Логуємо вихід з системи
            log_action(
                'user_logout',
                f'Користувач {user.username} вийшов з системи'
            )
    
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Додаємо новий маршрут для отримання даних товару
@app.route('/get_product/<int:id>', methods=['GET'])
@login_required
def get_product(id):
    try:
        product = Product.query.get(id)
        if product:
            return jsonify({
                "name": product.name,
                "code": product.code,
                "quantity": product.quantity,
                "price": product.price,
                "min_quantity": product.min_quantity
            })
        return jsonify({"error": "Товар не знайден"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Додаємо маршрут для оновлення товару
@app.route('/update_product/<int:id>', methods=['POST'])
@login_required
def update_product(id):
    try:
        product = Product.query.get(id)
        if not product:
            return jsonify({"error": "Товар не знайдено"}), 404

        # Зберігаємо старі значення для логу
        old_name = product.name
        old_quantity = product.quantity
        old_price = product.price

        # Отримуємо дані з форми
        product.name = request.form['name']
        product.code = request.form['code']
        product.quantity = int(request.form['quantity'])
        product.price = float(request.form['price'])
        product.min_quantity = int(request.form['min_quantity'])

        # Перевіряємо унікальність артикула
        existing_product = Product.query.filter_by(code=product.code).first()
        if existing_product and existing_product.id != id:
            return jsonify({"error": "Товар з таким артикулом вже існує"}), 400

        db.session.commit()

        # Логуємо зміни
        changes = []
        if old_name != product.name:
            changes.append(f"назву з '{old_name}' на '{product.name}'")
        if old_quantity != product.quantity:
            changes.append(f"кількість з {old_quantity} на {product.quantity}")
        if old_price != product.price:
            changes.append(f"ціну з {old_price} на {product.price}")

        if changes:
            log_action(
                'update_product',
                f"Оновлено товар (артикул: {id}): змінено " + ", ".join(changes)
            )

        return jsonify({"message": "Товар успішно оновлено"})
    except ValueError as e:
        return jsonify({"error": "Некоректні дані. Перевірте правильність введених значень"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

def log_action(action_type, description):
    """
    Функція для логування дій користувача
    """
    try:
        if 'user_id' in session:
            log = ActionLog(
                user_id=session['user_id'],
                action_type=action_type,
                description=description
            )
            db.session.add(log)
            db.session.commit()
    except Exception as e:
        print(f"Error logging action: {e}")
        db.session.rollback()

@app.route('/action_history')
@login_required
def action_history():
    try:
        # Отримуємо всі логи, відсортовані за часом (останні спочатку)
        logs = ActionLog.query.order_by(ActionLog.timestamp.desc()).all()
        return render_template('action_history.html', logs=logs)
    except Exception as e:
        print(f"Error getting action history: {e}")
        return render_template('action_history.html', logs=[], error="Помилка при завантаженні історії")

@app.route('/delete_product/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    try:
        product = Product.query.get(id)
        if not product:
            return jsonify({"error": "Товар не знайдено"}), 404

        product_name = product.name
        product_code = product.code

        # Видаляємо пов'язані операції
        Operation.query.filter_by(product_id=id).delete()
        
        # Видаляємо сам товар
        db.session.delete(product)
        db.session.commit()

        # Логуємо видалення
        log_action(
            'delete_product',
            f'Видалено товар: {product_name} (артикул: {product_code})'
        )

        return jsonify({"message": "Товар успішно видалено"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    with app.app_context():
        try:
            # Створюємо всі таблиці в базі даних
            db.create_all()
            print("База даних успішно створена")
        except Exception as e:
            print(f"Помилка при створенні бази даних: {e}")
    
    app.run(debug=True) 