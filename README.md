```markdown
# Документація системи інвентаризації

## Зміст
1. [Опис проекту](#опис-проекту)
2. [Структура проекту](#структура-проекту)
3. [Налаштування](#налаштування)
4. [Основні компоненти](#основні-компоненти)
5. [API Endpoints](#api-endpoints)
6. [Приклади використання](#приклади-використання)

## Опис проекту
Система інвентаризації - це веб-додаток для управління складським обліком товарів. Система дозволяє вести облік товарів, відслідковувати їх кількість, здійснювати операції приходу та витрати, а також формувати звіти.

## Структура проекту
```
inventory-system/
├── app.py # Головний файл додатку
├── static/ # Статичні файли
│   ├── css/
│   │   └── style.css # Стилі
│   └── js/
│       └── main.js # JavaScript функції
├── templates/ # HTML шаблони
│   ├── base.html # Базовий шаблон
│   ├── catalog.html # Сторінка каталогу
│   ├── dashboard.html # Головна сторінка
│   ├── inventory.html # Сторінка обліку
│   ├── login.html # Сторінка входу
│   ├── register.html # Сторінка реєстрації
│   └── reports.html # Сторінка звітів
└── requirements.txt # Залежності проекту
```

## Налаштування

### Змінні середовища
Створіть файл `.env` з наступними змінними:
```
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_DATABASE=inventory_db
```

### Встановлення залежностей
```bash
pip install -r requirements.txt
```

## Основні компоненти

### Моделі даних

#### Product (Товар)
```python
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, nullable=False)
    min_quantity = db.Column(db.Integer, default=0)
```

Приклад створення товару:
```python
new_product = Product(
    name="Ноутбук Lenovo",
    code="LEN-001",
    quantity=10,
    price=25000.00,
    min_quantity=2
)
```

#### Operation (Операція)
```python
class Operation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
```

Приклад створення операції:
```python
new_operation = Operation(
    date=datetime.now(UTC),
    type='incoming',
    product_id=1,
    quantity=5,
    price=24000.00
)
```

### API Endpoints

#### Товари

##### Додавання товару
```python
@app.route('/add_product', methods=['POST'])
@login_required
def add_product():
    # Приклад запиту:
    # POST /add_product
    # {
    #     "name": "Ноутбук Lenovo",
    #     "code": "LEN-001",
    #     "quantity": 10,
    #     "price": 25000.00,
    #     "min_quantity": 2
    # }
```

##### Оновлення товару
```python
@app.route('/update_product/<int:id>', methods=['POST'])
@login_required
def update_product(id):
    # Приклад запиту:
    # POST /update_product/1
    # {
    #     "name": "Ноутбук Lenovo ThinkPad",
    #     "quantity": 15,
    #     "price": 26000.00
    # }
```

#### Операції

##### Додавання приходу
```python
@app.route('/add_incoming', methods=['POST'])
@login_required
def add_incoming():
    # Приклад запиту:
    # POST /add_incoming
    # {
    #     "product_id": 1,
    #     "quantity": 5,
    #     "price": 24000.00,
    #     "datetime": "2024-03-20T14:30"
    # }
```

### JavaScript функції

#### Додавання товару
```javascript
function addProduct(event) {
    // Приклад виклику:
    // const form = document.querySelector('form');
    // form.addEventListener('submit', addProduct);
}
```

#### Редагування товару
```javascript
function editProduct(id) {
    // Приклад виклику:
    // <button onclick="editProduct(1)">Редагувати</button>
}
```

## Приклади використання

### Реєстрація користувача
```python
POST /register
{
    "username": "admin",
    "email": "admin@example.com",
    "password": "secure_password"
}
```

### Додавання товару
```python
POST /add_product
{
    "name": "Ноутбук Lenovo",
    "code": "LEN-001",
    "quantity": 10,
    "price": 25000.00,
    "min_quantity": 2
}
```

### Додавання операції приходу
```python
POST /add_incoming
{
    "product_id": 1,
    "quantity": 5,
    "price": 24000.00,
    "datetime": "2024-03-20T14:30"
}
```
```