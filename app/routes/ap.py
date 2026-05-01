from flask import Blueprint, redirect, render_template, session, url_for
from app.models import Invoice, Purchase_Order, Users, Vendors

ap_bp = Blueprint("ap", __name__)


@ap_bp.route("/ap")
@ap_bp.route("/ap/<username>")
def ap(username=None):
    session_user = session.get("username")
    if not session_user:
        return redirect(url_for("auth.home"))
    if username and username != session_user:
        return redirect(f"/ap/{session_user}")

    user = Users.query.filter_by(username=session_user).first()
    invoices = Invoice.query.filter_by(uploaded_by=session_user).all()
    purchase_orders = Purchase_Order.query.all()
    vendors = Vendors.query.filter_by(username=session_user).all()

    return render_template(
        "ap.html",
        invoices=invoices,
        purchase_orders=purchase_orders,
        user=user,
        vendors=vendors,
    )
