import datetime
import json
from flask import Flask, render_template, redirect, flash, request, url_for, session, jsonify
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
        if 'jsonFile' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['jsonFile']

        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        try:
            posted_data = json.load(file)
        except Exception as e:
            flash(f'Error reading file: {e}', 'danger')
            return redirect(request.url)

        data = []
        try:
            for i in posted_data:
                expense_id = int(i['expense_id'])
                transaction_date = i['transaction_date']
                description = i['description']
                price = float(i['price'])
                category_id = int(i['category_id'])

                try:
                    cur.execute("SELECT EXISTS(SELECT 1 FROM expenses WHERE expenses_id=%s);", (expense_id,))
                    cond = cur.fetchone()[0]
                    if cond:
                        cur.execute(
                            "INSERT INTO expenses (transaction_date, description, price, category_id) VALUES (%s, %s, %s, %s);",
                            (transaction_date, description, price, category_id)
                        )
                        cur.execute("SELECT * FROM expenses ORDER BY expenses_id DESC LIMIT 1")
                        result = cur.fetchone()
                        data.append(result)

                except Exception as error:
                    flash(f"Database error: {error}", 'danger')
                    return redirect(url_for('expense_json_loader'))

            db_conn.commit()

            n = len(data)
            redirect_url = url_for('update_after_json_load', n=n)
            flash('Records added successfully.', 'success')

            return redirect(url_for('update_after_json_load', n=n))

        except Exception as e:
            flash(f'Error processing data: {e}', 'danger')
            return redirect(url_for('expense_json_loader'))

    return render_template('json_loader.html')


@app.route('/present_or_add_tag', methods=['GET', 'POST'])
def update_after_json_load():

    if request.method == 'GET':
        response = request.args.get('n', type=int)
        print(response)

        cur.execute(f"SELECT * FROM expenses ORDER BY expenses_id DESC LIMIT {response};")
        rows = cur.fetchall()
        columns = ['expense_id', 'transaction_date', 'description', 'price', 'category_id']
        result = [dict(zip(columns, row)) for row in rows]
        return render_template('added_json_or_tag.html', result=result)

    elif request.method == 'POST':

        print('request form:    ', request.form)
        expense_ids = request.form.getlist('expense_id')
        tags = request.form.getlist('tag')
        print(expense_ids, tags)

        if not expense_ids or not tags:
            flash('No tag added.', 'danger')
            return render_template('added_json_or_tag.html')

        for expense_id, tag in zip(expense_ids, tags):
            if tag:
                print(f"Expense ID: {expense_id}, Tag: {tag}")

    return render_template('added_json_or_tag.html')


if __name__ == "__main__":
    app.run()
