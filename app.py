import datetime
import json
import urllib.parse
from flask import Flask, render_template, redirect, flash, request, url_for, jsonify
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


@app.route('/select_by_date', methods=['GET', 'POST'])
def select_by_date():
    if request.method == 'GET':
        return render_template('date.html')
    elif request.method == 'POST':
        date_starts = request.form['start_date']
        date_ends = request.form['end_date']
        exact_date = request.form['exact_date']
        try:
            if date_starts and date_ends:
                cur.execute(
                    f"SELECT * FROM expenses WHERE transaction_date BETWEEN '{date_starts}' and '{date_ends}';"
                )
                date_range_query = cur.fetchall()
                return render_template('date.html', date_range_query=date_range_query)
            else:
                cur.execute(
                    f"SELECT * FROM expenses WHERE transaction_date = '{exact_date}';"
                )
                date_range_query = cur.fetchall()
                return render_template('date.html', date_range_query=date_range_query)
        except Exception as error:
            print(error)
    return render_template('date.html')


@app.route('/insert_json', methods=['GET', 'POST'])
def expense_json_loader():

    if request.method == 'GET':
        return render_template('json_loader.html')
    elif request.method == 'POST':
        posted_data = json.load(request.files['jsonFile'])
        data = []
        for i in posted_data:
            expense_id = int(i['expense_id'])
            transaction_date = i['transaction_date']
            description = i['description']
            price = float(i['price'])

            d = {'expense_id': expense_id, 'price': price, 'description': description,
                 'transaction_date': transaction_date}

            data.append(d)

            try:
                cur.execute(f"SELECT EXISTS(SELECT 1 FROM expenses WHERE expenses_id={expense_id});")
                cond = cur.fetchone()[0]
                if not cond:
                    cur.execute(
                        "INSERT INTO expenses (transaction_date, description, price) VALUES (%s, %s, %s)",
                        (transaction_date, description, price))
                    db_conn.commit()
                    flash('Records added successfully.','success')
                else:
                    flash('Record already exists', 'info')
            except Exception as error:
                flash(f"Database error: {error}")
        encoded_data = urllib.parse.quote(json.dumps(data))
        return redirect(url_for('update_after_json_load', data=encoded_data, flash=flash))
    else:
        return render_template('json_loader.html')


@app.route('/present_or_add_tag', methods=['GET', 'POST'])
def update_after_json_load():
    encoded_data = request.args.get('data')
    if request.method == 'GET':
        if encoded_data:
            data = json.loads(urllib.parse.unquote(encoded_data))
            return render_template('added_json_or_tag.html', data=data)
        else:
            flash('No data has been passed.',category='danger')
            return redirect('expense_json_loader')


if __name__ == "__main__":
    app.run()
