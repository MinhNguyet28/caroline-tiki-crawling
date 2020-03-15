from bs4 import BeautifulSoup
import requests
import sqlite3
from collections import deque

TIKI_URL = 'https://tiki.vn'
THRESHOLD_CATEGORIES = 1
PAGES = 10

conn = sqlite3.connect('tiki_products.db')
cur = conn.cursor()


def drop_table():
    try:
        cur.execute('DROP TABLE products;')
    except Exception as err:
        print('ERROR DROP TABLE:', err)


def delete_all():
    return cur.execute('DELETE FROM products;')


def get_url(url):
    # time.sleep(1)
    try:
        response = requests.get(url).text
        response = BeautifulSoup(response, 'html.parser')
        return response
    except Exception as err:
            print('ERROR BY REQUEST:', err)


class Category:
    def __init__(self, cat_id, name, url, parent_id):
        self.cat_id = cat_id
        self.name = name
        self.url = url
        self.parent_id = parent_id

    def __repr__(self):
        return "ID: {}, Name: {}, URL: {}, Parent_id: {}".format(self.cat_id, self.name, self.url, self.parent_id)

    def save_into_db(self):
        query = """
            INSERT INTO categories (name, url, parent_id)
            VALUES (?, ?, ?);
        """
        val = (self.name, self.url, self.parent_id)
        try:
            cur.execute(query, val)
            self.cat_id = cur.lastrowid
        except Exception as err:
            print('ERROR BY INSERT:', err)


class Products:
    def __init__(self, product_id, title, price, category):
        self.product_id = product_id
        self.title = title
        self.price = price
        self.category = category

    def save_into_db(self):
        query = """
            INSERT INTO products (product_id, title, price, category)
            VALUES (?, ?, ?, ?);
        """
        val = (self.product_id, self.title, self.price, self.category)
        try:
            cur.execute(query, val)
            self.id = cur.lastrowid
        except Exception as err:
            print('ERROR BY INSERT:', err)


def create_products_table():
    query = """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            title TEXT,
            price INT, 
            category TEXT 
        )
    """
    try:
        cur.execute(query)
    except Exception as err:
        print('ERROR BY CREATE TABLE', err)


drop_table()
create_products_table()


def get_main_categories(save_db=False):
    soup = get_url(TIKI_URL)

    result = []
    for a in soup.findAll('a', {'class': 'MenuItem__MenuLink-tii3xq-1 efuIbv'}):
        cat_id = None
        name = a.find('span', {'class': 'text'}).text
        url = a['href']
        parent_id = None

        cat = Category(cat_id, name, url, parent_id)
        if save_db:
            cat.save_into_db()
        result.append(cat)
    return result


def get_sub_categories(category, save_db=False):
    name = category.name
    url = category.url
    result = []

    try:
        soup = get_url(url)
        div_containers = soup.findAll(
            'div', {'class': 'list-group-item is-child'})
        for div in div_containers:
            sub_id = None
            sub_name = div.a.text
            sub_url = 'http://tiki.vn' + div.a['href']
            sub_parent_id = category.cat_id

            sub = Category(sub_id, sub_name, sub_url, sub_parent_id)
            if save_db:
                sub.save_into_db()
            result.append(sub)
    except Exception as err:
        print('ERROR BY GET SUB CATEGORIES:', err)
    return result

def get_all_categories(main_categories):
    de = deque(main_categories)

    while len(de) < THRESHOLD_CATEGORIES:
        parent_cat = de.popleft()
        sub_cats = get_sub_categories(parent_cat)
        de.extend(sub_cats)

      
    return de

def get_products(cat, pages=PAGES, save_db=False):
    for j in cat:
        for i in range(1, pages + 1):
            print(j.url + '&page={}'.format(i))
            soup = get_url(j.url + '&page={}'.format(i))
            for a in soup.findAll('div', {'class': 'product-item'}):
                product_id = a.attrs['data-seller-product-id']
                title = a.attrs['data-title']
                price = a.attrs['data-price']
                category = a.attrs['data-category']

                pro = Products(product_id, title, price, category)
                if save_db:
                    pro.save_into_db()

get_products(get_all_categories(get_main_categories()), 10, True)

conn.commit()
cur.close()
conn.close()
