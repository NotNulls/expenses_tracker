from flask import Flask, render_template
import os
import psycopg2


base_dir = os.path.abspath(os.path.dirname(__name__))

app = Flask(__name__)
# app.config["DATABASE_URL"] = 'postgresql:///' + os.path.join(base_dir, 'money_db')
# app.config["TRACK_MODIFICATION"] = True
# app.config["DBUG"] = True

conn = psycopg2.connect(database="money_db",
                        user="postgres",
                        password="admin",
                        host="127.0.0.1", port="5432")


def postgres_test():
    try:
        cursor = conn.cursor()
        conn.commit()

        # in case we need to make a db and tables
        script = cursor.execute("select version()")
        rows = cursor.fetchall()
        print(f"Connected to:{rows}")

        cursor.close()
        conn.close()

    except Exception as error:
        print(error)


postgres_test()


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/other_page')
def other_page():
    return render_template('other_page.html')


if __name__ == "__main__":
    app.run()
