from collections import defaultdict
from flask import Blueprint, render_template
from app.models import Invoice, Purchase_Order, Users, Vendors

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    invoices = Invoice.query.all()
    purchase_orders = Purchase_Order.query.all()
    pending_count = sum(1 for i in invoices if i.status != "complete")
    completed_count = sum(1 for i in invoices if i.status == "complete")
    total_value = sum(i.amount for i in invoices if i.amount)
    avg_value = total_value / len(invoices) if invoices else 0
    low_confidence = sum(
        1 for i in invoices
        if i.confidence_score is not None and i.confidence_score < 50
    )
    med_confidence = sum(
        1 for i in invoices
        if i.confidence_score is not None and 50 <= i.confidence_score < 80
    )
    high_confidence = sum(
        1 for i in invoices
        if i.confidence_score is not None and i.confidence_score >= 80
    )
    vendor_names = sorted(set(i.vendor_name for i in invoices if i.vendor_name))
    vendor_count = len(vendor_names)
    team_member = Users.query.all()
    vendors = Vendors.query.all()
    vendors_by_user = defaultdict(list)
    for v in vendors:
        if v.username:
            vendors_by_user[v.username].append(v)

    return render_template(
        "dashboard.html",
        invoices=invoices,
        purchase_orders=purchase_orders,
        pending_count=pending_count,
        completed_count=completed_count,
        total_value=total_value,
        avg_value=avg_value,
        low_confidence=low_confidence,
        med_confidence=med_confidence,
        high_confidence=high_confidence,
        vendor_names=vendor_names,
        vendor_count=vendor_count,
        team_member=team_member,
        vendors_by_user=vendors_by_user,
    )
