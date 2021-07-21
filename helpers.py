from functools import wraps
from flask import redirect, render_template, request, session
import scrapy
import datetime
import os
import psycopg2
from crawl import car_info

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def usd(value):
    """Format value as USD."""
    return f"${int(value):,}"


def time_format(value):
    days = int(value)

    return f"{days} Days" if days > 0 else f"{int((value - days) * 24)} Hours"


# https://stackoverflow.com/questions/12686991/how-to-get-last-friday
def last_friday_datetime():
    current_time = datetime.datetime.now()

    # get friday, one week ago, at 6 o'clock EST
    last_friday = (current_time.date()
        - datetime.timedelta(days=current_time.weekday())
        + datetime.timedelta(days=4, weeks=-1))
    last_friday_at_14 = datetime.datetime.combine(last_friday, datetime.time(14))

    # if today is also friday, and after 2 o'clock UTC, change to the current date
    one_week = datetime.timedelta(weeks=1)
    if current_time - last_friday_at_14 >= one_week:
        last_friday_at_14 += one_week

    return last_friday_at_14


def fetch_form_data():
    DATABASE_URL = os.environ['DATABASE_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')

    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM car_inserts where timestamp >= %s", (last_friday_datetime(),))

            if cursor.fetchone() is None:
                return -1

            cursor.execute("SELECT car, link, six_day_price, id FROM \
                            cars JOIN prices ON cars.id = prices.car_id")

            return cursor.fetchall()


def update_data():
    DATABASE_URL = os.environ['DATABASE_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')

    with conn:
        with conn.cursor() as cursor:

            all_info = car_info()

            info = all_info[0]
            timestamp = all_info[1]

            cursor.execute("INSERT INTO car_inserts (timestamp) VALUES (%s)", (timestamp,))
            cursor.execute("SELECT id FROM car_inserts WHERE timestamp = %s", (timestamp,))
            car_insert_id = cursor.fetchone()[0]

            for datum in info:
                cursor.execute("INSERT INTO cars (car, link, time_remaining, insert_id) VALUES (%s, %s, %s, %s)", (datum[0], datum[1], datum[3], car_insert_id))

                cursor.execute("SELECT id FROM cars")
                car_id = cursor.fetchall()[-1][0]

                cursor.execute("INSERT INTO prices (car_id, six_day_price) values (%s, %s)", (car_id, datum[2]))