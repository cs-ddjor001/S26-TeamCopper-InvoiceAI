import csv
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models.users import Users

CSV_FILE = "data/sample_team_members.csv"


def parse_time(value):
    if not value or not value.strip():
        return None
    try:
        return datetime.strptime(value.strip(), "%H:%M:%S").time()
    except ValueError:
        return None


def parse_bool(value):
    if not value or not value.strip():
        return None
    return value.strip().lower() == "true"


def load_users(filepath=None):
    if filepath is None:
        filepath = CSV_FILE

    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    user_cache = {user.username for user in Users.query.all()}

    loaded_users = 0
    skipped_rows = 0

    print(f"Loading: {filepath}")

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get("username", "").strip()
            if not username:
                skipped_rows += 1
                continue

            if username in user_cache:
                skipped_rows += 1
                continue

            user = Users(
                username=username,
                email=row.get("email", "").strip() or None,
                display_name=row.get("display_name", "").strip() or None,
                active=parse_bool(row.get("active", "")),
                creation_time=parse_time(row.get("creation_time", "")),
                deactivation_time=parse_time(row.get("deactivation_time", "")),
                enabled_in_queue=parse_bool(row.get("enabled_in_queue", "")),
            )
            db.session.add(user)
            user_cache.add(username)
            loaded_users += 1

    db.session.commit()
    print(f"Done — users loaded: {loaded_users}, rows skipped: {skipped_rows}")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        load_users()