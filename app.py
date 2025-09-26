from flask import Flask, jsonify, abort
import json
import os

app = Flask(__name__)

# Встановлення кодування JSON для підтримки UTF-8
app.config['JSON_AS_ASCII'] = False

# Шлях до JSON файлу
JSON_FILE = 'menu_data.json'

# Функція для завантаження даних з JSON файлу
def load_products():
    if not os.path.exists(JSON_FILE):
        return []
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Помилка при читанні JSON файлу: {e}")
        return []

# Ендпоінт для отримання всіх продуктів
@app.route('/all_products/', methods=['GET'])
def get_all_products():
    products = load_products()
    if not products:
        abort(404, description="Дані про продукти не знайдено")
    return jsonify(products)

# Ендпоінт для отримання інформації про конкретний продукт
@app.route('/products/<string:product_name>', methods=['GET'])
def get_product(product_name):
    products = load_products()
    product = next((p for p in products if p['name'].lower() == product_name.lower()), None)
    if not product:
        abort(404, description=f"Продукт {product_name} не знайдено")
    return jsonify(product)

# Ендпоінт для отримання конкретного поля продукту
@app.route('/products/<string:product_name>/<string:product_field>', methods=['GET'])
def get_product_field(product_name, product_field):
    products = load_products()
    product = next((p for p in products if p['name'].lower() == product_name.lower()), None)
    if not product:
        abort(404, description=f"Продукт {product_name} не знайдено")
    if product_field not in product:
        abort(404, description=f"Поле {product_field} не знайдено для продукту {product_name}")
    return jsonify({product_field: product[product_field]})

# Обробка помилок
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': str(error)}), 404

if __name__ == '__main__':
    app.run(debug=True)