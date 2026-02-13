from flask_seeder import Seeder
from faker import Faker
from models.invoice import Invoice
import csv, os

faker = Faker()

class InvoiceFileSeeder(Seeder):
    def run(self):
        invoices = []

        for _ in range(50):
            invoice = {
                "po_number": faker.bothify("PO-####-??"),
                "supplier": faker.company(),
                "amount": faker.pyfloat(left_digits=5, right_digits=2, positive=True),
                "status": faker.random_element(elements=("pending", "complete", "in progress"))
            }
            invoices.append(invoice)
        
        os.makedirs("data", exist_ok=True)
        output_path = os.path.join("data", "dummy_invoices.csv")

        with open(output_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["po_number", "supplier", "amount", "status"])
            writer.writeheader()
            writer.writerows(invoices)
        
        print(f"Dummy data written to: {output_path}")

if __name__ == "__main__":
    seeder = InvoiceFileSeeder()
    seeder.run()