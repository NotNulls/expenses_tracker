import datetime
import os
from flask import Flask, render_template, redirect, flash, request
import psycopg2
from config import Configure


app = Flask(__name__)
app.config.from_object(Configure)
db_conn = psycopg2.connect(app.config['DATABASE_URL'])
cur = db_conn.cursor()


def get_categories():
    cur.execute("SELECT * FROM category")
    return cur.fetchall()


def search_by_category(category_id):
    script = cur.execute(f"SELECT * FROM expenses where category_id = {category_id};")
    return script


def get_json_expenses():
    cur.execute("select row_to_json(expenses) from expenses ORDER BY expenses_id DESC limit(5);")
    return cur.fetchall()


@app.route('/', methods=['GET', 'POST'])
@app.route('/add_expenses', methods=['GET', 'POST'])
def add_expenses():
    if request.method == "POST":
        price = request.form['price']
        description = request.form['description']
        transaction_date = request.form['transaction_date']
        category_id = request.form['category']

        try:
            price = float(price)
            if price <= 0:
                raise ValueError('Invalid input.')
        except ValueError:
            flash('Entry must be a positive number.', 'error')
            return redirect('/')

        try:
            transaction_date = datetime.datetime.strptime(transaction_date, '%d.%m.%Y').date()
        except ValueError:
            flash('Please enter a valid date in the format dd.mm.yyyy.', 'error')
            return redirect('/')

        cur.execute("""INSERT INTO expenses (category_id, price, description, transaction_date)
                            VALUES (%s,%s, %s, %s)""",
                    (category_id, price, description, transaction_date))
        db_conn.commit()
        flash('Transaction added.', 'success')
        return redirect('/')
    elif request.method == "GET":
        categories = get_categories()
        json_expenses = get_json_expenses()
        return render_template('add_expenses.html',
                               categories=categories,
                               json_expenses=json_expenses)


@app.route('/index', methods=['GET', 'POST'])
def index():
    searched_category = select_by_category()
    return render_template('index.html', searched_category=searched_category)


@app.route('/other_page')
def other_page():
    return render_template('other_page.html')


@app.route('/select_by_category', methods=['GET', 'POST'])
def select_by_category():
    categories = get_categories()
    if request.method == 'GET':
        return render_template('categories.html', categories=categories)
    elif request.method == 'POST':
        cat = int(request.form['category'])
        cur.execute(f"SELECT * FROM expenses where category_id = {cat} ORDER BY expenses_id DESC")
        results = cur.fetchall()
        return render_template('categories.html', categories=categories, results=results)
    else:
        return render_template('categories.html', categories=categories)



if __name__ == "__main__":
    app.run()
