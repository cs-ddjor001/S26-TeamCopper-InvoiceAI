from flask import Flask, render_template
from datetime import date, datetime
import os
from extensions import db

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "app.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def format_datetime(value, fmt="%m/%d/%Y"):
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime(fmt)

    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time()).strftime(fmt)

    if isinstance(value, str):
        for parse_fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, parse_fmt).strftime(fmt)
            except ValueError:
                continue

    return str(value)


app.jinja_env.filters["format_datetime"] = format_datetime

import models


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    invoices = models.Invoice.query.all()
    return render_template("dashboard.html", invoices=invoices)


@app.route("/ap")
def ap():
    invoices = models.Invoice.query.all()
    purchase_orders = models.Purchase_Order.query.all()
    return render_template(
        "ap.html", invoices=invoices, purchase_orders=purchase_orders
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
