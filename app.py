import os
import sys
import psycopg2
import time
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, usd, time_format, fetch_form_data, update_data
from crawl import car_info

# Configure application
app = Flask(__name__)

app.secret_key = os.urandom(24)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Custom filters
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["time_format"] = time_format

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')

car_list_length = 7
car_list = None
insert_id = None

@app.route("/")
@login_required
def index():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    with conn:
        with conn.cursor() as cursor:

            user_id = session["user_id"]

            cursor.execute("SELECT car, link, six_day_price, five_day_price, four_day_price,  \
                    three_day_price, two_day_price, one_day_price, sell_price FROM \
                    purchases JOIN cars ON purchases.car_id = cars.id \
                    JOIN prices ON prices.car_id = cars.id WHERE user_id = %s AND purchases.insert_id = %s", (user_id, insert_id))

            info = cursor.fetchall()

            n_selected = len(info)

            if n_selected not in [car_list_length, 0]:
                cursor.execute("DELETE FROM purchases WHERE user_id = %s AND insert_id = %s", (user_id, insert_id))

                return f"Error completing purchase: {n_selected} cars were purchased."

            days = ("Six Day Price", "Five Day Price", "Four Day Price", "Three Day Price", "Two Day Price", "One Day Price", "Sell Price")

    return render_template("index.html", info=info, days=days)

@app.route("/selection", methods=["GET", "POST"])
@login_required
def selection():
    if request.method == "POST":

        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM purchases WHERE user_id = %s AND insert_id = %s", (user_id, insert_id))

                if len(cursor.fetchall()) > 0:
                    return "You can only purchase cars once per round."
                    
        else:
            try:
                checked_cars = [car_id for car_id in car_list if request.form.get(str(car_id))]
            except:
                checked_cars = []

            if 'complete-purchase' in request.form:
                with conn:
                    with conn.cursor() as cursor:

                        user_id = session["user_id"]

                        data = zip([user_id] * car_list_length, [insert_id] * car_list_length, checked_cars)

                        for datum in data:
                            cursor.execute("INSERT INTO purchases (user_id, insert_id, car_id) VALUES (%s, %s, %s)", datum)

                return redirect("/")
                    
            else:
                with conn:
                    with conn.cursor() as cursor:
                        # Add server-side validation

                        checked_cars_tuple = (tuple(checked_cars),)

                        cursor.execute("SELECT six_day_price FROM prices WHERE car_id IN %s", checked_cars_tuple)

                        checked_cars_prices = [price[0] for price in cursor.fetchall()]

                        checked_cars = {car_id: car_price for (car_id, car_price) in zip(checked_cars, checked_cars_prices)}

                        try:
                            info = fetch_form_data()

                            if info == -1:
                                return 'Error fetching data: a new round has begun.'
                        except:
                            e = sys.exc_info()[0]
                            return str(e)

                return render_template('selection.html', info=info, checked_cars=checked_cars)

    else:
        try:
            info = fetch_form_data()

            if info == -1:
                update_data()
                info = fetch_form_data()
        except:
            e = sys.exc_info()[0]
            return str(e)

        return render_template('selection.html', info=info, checked_cars={})


@app.route("/review", methods=["POST"])
@login_required
def review():
    global car_list

    if request.method == "POST":
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        with conn:
            with conn.cursor() as cursor:

                cursor.execute("SELECT id FROM cars WHERE insert_id = %s", (insert_id,))
                car_ids = list(map(lambda x: str(x[0]), cursor.fetchall()))

                car_list = [int(car_id) for car_id in car_ids if request.form.get(car_id)]
                
                if len(car_list) != car_list_length:
                    return f"Somehow, you selected {len(car_list)} cars."

                car_list_tuple = (tuple(car_list),)

                cursor.execute("SELECT six_day_price FROM prices WHERE car_id IN %s", car_list_tuple)

                car_prices = [price[0] for price in cursor.fetchall()]

                total = sum(car_prices)

                if total > 100000:
                    return "Somehow, you spent more than 100,000 dollars."

                cursor.execute("SELECT car, link, six_day_price, id FROM \
                            cars JOIN prices ON cars.id = prices.car_id \
                            WHERE id in %s", car_list_tuple)

                info = cursor.fetchall()

        return render_template('review.html', info=info)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    global insert_id

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return "must provide username"

        # Ensure password was submitted
        elif not request.form.get("password"):
            return "must provide password"

        # Query database for username
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username = %s", (request.form.get("username"),))
                row = cursor.fetchone()

            # Ensure username exists and password is correct
            if row is None or not check_password_hash(row[2], request.form.get("password")):
                return "invalid username and/or password"

            # Remember which user has logged in
            session["user_id"] = row[0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM car_inserts")
                insert_id = cursor.fetchall()[-1][0]

        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        with conn:
            with conn.cursor() as cursor:
                username = request.form.get("username")
                password = request.form.get("password")
                confirmation = request.form.get("confirmation")


                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                row = cursor.fetchone()

                """Register user"""
                # Ensure username was submitted
                if not username:
                    return "must provide username"

                # Checks to see if username has already been used
                elif row is not None:
                    return "username has already been used"

                # Ensure password was submitted
                elif not password:
                    return "must provide password"

                # makes sure that there was a password confirmation
                elif not confirmation:
                    return "must provide confirmation"

                # makes sure that the password equals the confirmation
                elif password != confirmation:
                    return "password and confirmation do not match"

                # Generates a hash for the password
                password_hash = generate_password_hash(password)

                # Inserts the user into the users table, saving the autogenerated id in the variable user_id
                cursor.execute("INSERT INTO users (username, hash) VALUES (%s, %s)", (username, password_hash))
                cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
                user_id = cursor.fetchone()[0]

                # Remember which user has logged in
                session["user_id"] = user_id

        return redirect("/")
    else:
        return render_template('register.html')

conn.close()