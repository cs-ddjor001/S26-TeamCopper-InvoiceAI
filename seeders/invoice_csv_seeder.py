from flask_seeder import Seeder
from faker import Faker
import csv, os

faker = Faker()

class InvoiceCSVFileSeeder(Seeder):
    def run(self):
        os.makedirs("data", exist_ok=True)

        purchase_orders = []
        
        with open("data/purchase_orders.csv", "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                purchase_orders.append(row)

        for i in range(50):
            invoices = []

            for _ in range(100):
                po = faker.random_element(purchase_orders)
                invoices.append({
                    "po_number": po["po_number"],
                    "vendor": po["vendor"],
                    "amount": po["amount"],
                    "status": faker.random_element(elements=("pending", "complete", "in progress")),
                    "date": po["date_issued"]
                })
        
            filename = f"invoice_seed_{i+1}.csv"
            output_path = os.path.join("data", filename)

            with open(output_path, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["po_number", "vendor", "amount", "status", "date"])
                writer.writeheader()
                writer.writerows(invoices)
        
        print(f"Dummy invoices written to data/ folder")

if __name__ == "__main__":
    seeder = InvoiceCSVFileSeeder()
    seeder.run()