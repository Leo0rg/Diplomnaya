// Функція для показу/приховання форми додавання товару
function showAddProductForm() {
    const form = document.getElementById('productForm');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

// Функція для додавання нового товару через AJAX
function addProduct(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    fetch('/add_product', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json().then(data => ({
        ok: response.ok,
        data: data
    })))
    .then(result => {
        if (result.ok) {
            alert(result.data.message);
            window.location.reload();
        } else {
            alert(result.data.error || 'Сталася помилка при додаванні товару');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Сталася помилка при додаванні товару');
    });
}

// Функція для редагування овару
function editProduct(id) {
    // Отримуємо дані товару
    fetch(`/get_product/${id}`)
        .then(response => response.json())
        .then(product => {
            // Створюємо модальне вікно
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <h2>Редагування товару</h2>
                    <form onsubmit="updateProduct(event, ${id})" class="edit-form">
                        <div class="form-group">
                            <label for="edit-name">Назва:</label>
                            <input type="text" id="edit-name" name="name" value="${product.name}" required>
                        </div>
                        <div class="form-group">
                            <label for="edit-code">Артикул:</label>
                            <input type="text" id="edit-code" name="code" value="${product.code}" required>
                        </div>
                        <div class="form-group">
                            <label for="edit-quantity">Кількість:</label>
                            <input type="number" id="edit-quantity" name="quantity" value="${product.quantity}" required>
                        </div>
                        <div class="form-group">
                            <label for="edit-price">Ціна:</label>
                            <input type="number" step="0.01" id="edit-price" name="price" value="${product.price}" required>
                        </div>
                        <div class="form-group">
                            <label for="edit-min-quantity">Мінімальний залишок:</label>
                            <input type="number" id="edit-min-quantity" name="min_quantity" value="${product.min_quantity}" required>
                        </div>
                        <div class="modal-buttons">
                            <button type="submit">Зберегти</button>
                            <button type="button" onclick="closeModal(this)">Скасувати</button>
                        </div>
                    </form>
                </div>
            `;
            document.body.appendChild(modal);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Помилка при отриманні даних товару');
        });
}

// Функція для оновлення товару
function updateProduct(event, id) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    fetch(`/update_product/${id}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Помилка при оновленні товару');
    });
}

// Функція для закриття модального вікна
function closeModal(button) {
    const modal = button.closest('.modal');
    modal.remove();
}

// Функція для додавання операції приходу
function addIncoming(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    // Встановлюємо поточну дату та час, якщо поле пусте
    if (!formData.get('datetime')) {
        const now = new Date();
        const datetime = now.toISOString().slice(0, 16);
        formData.set('datetime', datetime);
    }
    
    fetch('/add_incoming', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Сталася помилка при додаванні приходу');
    });
}

// Функція для додавання операції витрати
function addOutgoing(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    // Встановлюємо поточну дату та час, якщо поле пусте
    if (!formData.get('datetime')) {
        const now = new Date();
        const datetime = now.toISOString().slice(0, 16);
        formData.set('datetime', datetime);
    }
    
    fetch('/add_outgoing', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Сталася помилка при додаванні витрати');
    });
}

// Функція для генерації звіту за період
function generateReport(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const startDate = formData.get('start_date');
    const endDate = formData.get('end_date');
    
    if (!startDate || !endDate) {
        alert('Будь ласка, виберіть початкову та кінцеву дати');
        return;
    }
    
    // Перенаправляємо на сторінку звітів з параметрами дат
    window.location.href = `/reports?start_date=${startDate}&end_date=${endDate}`;
}

// Функція для видалення товару
function deleteProduct(id) {
    if (confirm('Ви впевнені, що хочете видалити цей товар?')) {
        fetch(`/delete_product/${id}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                alert(data.message);
                window.location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Помилка при видаленні товару');
        });
    }
} 