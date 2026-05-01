from flask import Blueprint, jsonify, render_template, request, session
from app.models import Users

auth_bp = Blueprint("auth", __name__)

SPECIAL_ROUTES = {
    "sally.admin": "/dashboard",
    "tom.ap": "/ap",
    "jim.model": "/model-trainer",
}


@auth_bp.route("/")
def home():
    return render_template("index.html")


@auth_bp.route("/login")
def login():
    username = request.args.get("username", "").strip().lower()
    if not username:
        return jsonify({"error": "Please enter a username."}), 400

    session["username"] = username

    if username in SPECIAL_ROUTES:
        return jsonify({"redirect": SPECIAL_ROUTES[username]})

    user = Users.query.filter_by(username=username, active=True).first()
    if not user:
        return jsonify({"error": f"No active account found for '{username}'."}), 404

    return jsonify({"redirect": f"/ap/{username}"})
