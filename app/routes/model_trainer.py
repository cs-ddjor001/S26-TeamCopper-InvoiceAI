from flask import Blueprint, render_template
from app.models import Invoice

model_trainer_bp = Blueprint("model_trainer", __name__)


@model_trainer_bp.route("/model-trainer")
def model_trainer():
    invoices = Invoice.query.all()
    invoice_count = len(invoices)
    completed_count = sum(1 for i in invoices if i.status == "complete")
    match_rate = (completed_count / invoice_count * 100) if invoice_count else 0
    scored = [i for i in invoices if i.confidence_score is not None]
    low_confidence = sum(1 for i in scored if i.confidence_score < 50)
    med_confidence = sum(1 for i in scored if 50 <= i.confidence_score < 80)
    high_confidence = sum(1 for i in scored if i.confidence_score >= 80)
    unscored = invoice_count - len(scored)
    avg_confidence = (
        int(sum(i.confidence_score for i in scored) / len(scored)) if scored else 0
    )
    return render_template(
        "model-trainer.html",
        invoice_count=invoice_count,
        match_rate=match_rate,
        low_confidence=low_confidence,
        med_confidence=med_confidence,
        high_confidence=high_confidence,
        unscored=unscored,
        avg_confidence=avg_confidence,
    )
