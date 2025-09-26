import requests
from bs4 import BeautifulSoup
import json
import logging
import re
from typing import List, Dict

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Базовий URL для McDonald's
BASE_URL = "https://www.mcdonalds.com"
MENU_URL = "https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html"
API_URL = "https://www.mcdonalds.com/dnaapp/itemDetails?country=UA&language=uk&showLiveData=true&item={item_id}"

# Моделі даних для продукту
class Product:
    def __init__(self, name: str, link: str, image: str, description: str = "", calories: str = "", fats: str = "",
                 carbs: str = "", proteins: str = "", unsaturated_fats: str = "", sugar: str = "", salt: str = "",
                 portion: str = ""):
        self.name = name
        self.link = link
        self.image = image
        self.description = description
        self.calories = calories
        self.fats = fats
        self.carbs = carbs
        self.proteins = proteins
        self.unsaturated_fats = unsaturated_fats
        self.sugar = sugar
        self.salt = salt
        self.portion = portion

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "link": self.link,
            "image": self.image,
            "description": self.description,
            "calories": self.calories,
            "fats": self.fats,
            "carbs": self.carbs,
            "proteins": self.proteins,
            "unsaturated_fats": self.unsaturated_fats,
            "sugar": self.sugar,
            "salt": self.salt,
            "portion": self.portion
        }

# Функція для отримання HTML контенту
def get_html(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка при отриманні HTML: {e}")
        return ""

# Функція для отримання нутріціологічної цінності з API
def get_nutrition_from_api(item_id: str) -> Dict:
    """Запит до API для отримання нутріціологічної цінності."""
    url = API_URL.format(item_id=item_id)
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Шукаємо потрібні елементи в списку 'nutrient_facts'
        nutrients = data.get('item', {}).get('nutrient_facts', {}).get('nutrient', [])

        # Збираємо всю потрібну інформацію
        nutrition_info = {
            'portion': None,
            'calories': None,
            'fats': None,
            'unsaturated_fats': None,
            'carbs': None,
            'sugar': None,
            'proteins': None,
            'salt': None
        }

        # Перебираємо всі нутрієнти і витягуємо необхідні дані
        for nutrient in nutrients:
            name = nutrient.get('name')
            value = nutrient.get('value')
            if name == 'Вага порції':
                nutrition_info['portion'] = value
            elif name == 'Калорійність':
                nutrition_info['calories'] = value
            elif name == 'Жири':
                nutrition_info['fats'] = value
            elif name == 'НЖК':
                nutrition_info['unsaturated_fats'] = value
            elif name == 'Вуглеводи':
                nutrition_info['carbs'] = value
            elif name == 'Цукор':
                nutrition_info['sugar'] = value
            elif name == 'Білки':
                nutrition_info['proteins'] = value
            elif name == 'Сіль':
                nutrition_info['salt'] = value

        return nutrition_info
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка при отриманні даних з API для продукту {item_id}: {e}")
        return {
            'portion': "",
            'calories': "",
            'fats': "",
            'unsaturated_fats': "",
            'carbs': "",
            'sugar': "",
            'proteins': "",
            'salt': ""
        }

# Функція для парсингу сторінки продукту
def parse_product_details(product_url: str) -> Dict:
    full_url = BASE_URL + product_url
    html_content = get_html(full_url)
    soup = BeautifulSoup(html_content, 'html.parser')

    # Парсимо опис
    description = soup.find('div', class_='cmp-product-details-main__description').text.strip() if soup.find('div',
                                                                                                          class_='cmp-product-details-main__description') else ''

    # Витягуємо item_id з URL (наприклад, /product/200153/)
    item_id = re.search(r'product/(\d+)', product_url).group(1) if re.search(r'product/(\d+)', product_url) else ''

    # Якщо item_id не знайдено в URL, намагаємося знайти в HTML
    if not item_id:
        item_id = soup.find('div', class_='cmp-product-details-main').get('data-item-id', '') if soup.find('div', class_='cmp-product-details-main') else ''
        if item_id:
            logger.info(f"Знайдено item_id в HTML: {item_id}")
        else:
            logger.warning(f"Не вдалося знайти item_id для продукту {product_url}")

    # Отримуємо нутріціологічну цінність через API
    nutrition_data = get_nutrition_from_api(item_id) if item_id else {}

    return {
        "description": description,
        "calories": nutrition_data.get("calories", ""),
        "fats": nutrition_data.get("fats", ""),
        "carbs": nutrition_data.get("carbs", ""),
        "proteins": nutrition_data.get("proteins", ""),
        "unsaturated_fats": nutrition_data.get("unsaturated_fats", ""),
        "sugar": nutrition_data.get("sugar", ""),
        "salt": nutrition_data.get("salt", ""),
        "portion": nutrition_data.get("portion", "")
    }

# Функція для парсингу головної сторінки меню
def parse_menu(html: str) -> List[Product]:
    soup = BeautifulSoup(html, 'html.parser')
    products = []

    product_items = soup.find_all('li', class_='cmp-category__item')
    if not product_items:
        logger.warning("Не вдалося знайти елементи продуктів на сторінці.")

    for item in product_items:
        try:
            product_name = item.find('div', class_='cmp-category__item-name').text.strip()
            product_link = item.find('a', class_='cmp-category__item-link')['href']
            product_image = item.find('img', class_='categories-item-img')['src']

            # Парсимо додаткові дані зі сторінки продукту
            product_details = parse_product_details(product_link)

            # Створюємо об'єкт продукту
            product = Product(
                product_name,
                product_link,
                product_image,
                product_details['description'],
                product_details['calories'],
                product_details['fats'],
                product_details['carbs'],
                product_details['proteins'],
                product_details['unsaturated_fats'],
                product_details['sugar'],
                product_details['salt'],
                product_details['portion']
            )
            products.append(product)

        except AttributeError as e:
            logger.warning(f"Пропущено продукт через відсутність необхідних даних: {e}")

    return products

# Функція для збереження даних у JSON файл
def save_to_json(data: List[Product], filename: str = 'menu_data.json') -> None:
    try:
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump([product.to_dict() for product in data], json_file, ensure_ascii=False, indent=4)
        logger.info(f"Дані успішно збережено у файл {filename}")
    except IOError as e:
        logger.error(f"Помилка при збереженні даних у файл: {e}")
        raise

# Основна частина програми
def main():
    try:
        # Отримуємо HTML контент
        logger.info(f"Отримуємо HTML з {MENU_URL}")
        html_content = get_html(MENU_URL)

        # Парсимо дані про продукти
        logger.info("Парсимо дані з HTML контенту...")
        products = parse_menu(html_content)

        # Перевірка на наявність продуктів
        if not products:
            logger.warning("Не було знайдено жодного продукту.")

        # Зберігаємо дані в JSON файл
        save_to_json(products)

        logger.info(f"Зібрано {len(products)} продуктів.")

    except Exception as e:
        logger.error(f"Помилка в основній частині програми: {e}")

if __name__ == "__main__":
    main()