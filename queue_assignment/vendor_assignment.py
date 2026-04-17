import math
from extensions import db
from models.users import Users
from models.vendors import Vendors


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

    # Split vendors evenly across users
    for i, vendor in enumerate(vendors):
        assigned_user = users[i % num_users]
        vendor.username = assigned_user.username

    db.session.commit()
    print(f"Done — {num_vendors} vendors assigned across {num_users} users "
          f"({math.ceil(num_vendors / num_users)} max per user)")


if __name__ == "__main__":
    from app import app
    with app.app_context():
        assign_vendors_to_users()