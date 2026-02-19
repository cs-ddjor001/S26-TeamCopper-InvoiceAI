import os, csv
from faker import Faker

faker = Faker()

def generate_purchase_orders(n = 51):
    os.makedirs("data", exist_ok=True)

    purchase_orders = []

    for _ in range(n):
        purchase_orders.append({
            "po_number": faker.bothify("PO-####-??"),
            "vendor": faker.company(),
            "amount": faker.pyfloat(left_digits=5, right_digits=2, positive=True),
            "date_issued": faker.date_this_year()
        })

        with open("data/purchase_orders.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=purchase_orders[0].keys())
            writer.writeheader()
            writer.writerows(purchase_orders)

    print("Purchase order listed can be found under data/ folder.")
    return purchase_orders
    
if __name__== "__main__":
    generate_purchase_orders(5050)