import math
import os

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.extensions import db
from app.models.users import Users
from app.models.vendors import Vendors


def assign_vendors_to_users():
    users = Users.query.all()
    vendors = Vendors.query.all()

    if not users:
        print("No users found.")
        return

    if not vendors:
        print("No vendors found.")
        return

    num_users = len(users)
    num_vendors = len(vendors)

    for i, vendor in enumerate(vendors):
        assigned_user = users[i % num_users]
        vendor.username = assigned_user.username

    db.session.commit()
    print(
        f"Done — {num_vendors} vendors assigned across {num_users} users "
        f"({math.ceil(num_vendors / num_users)} max per user)"
    )


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        assign_vendors_to_users()
