from flask_seeder import Seeder
from faker import Faker
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

faker = Faker()

class InvoicePDFSeeder(Seeder):
    def run(self, count=50):
        out_dir = os.path.join("data", "pdfs")
        os.makedirs(out_dir, exist_ok=True)

        for i in range(count):
            po = faker.bothify("PO-####-??")
            supplier = faker.company()
            amount = round(faker.pyfloat(left_digits=5, right_digits=2, positive=True), 2)
            status = faker.random_element(elements=("pending", "complete", "in progress"))
            date = faker.date_between(start_date='-2y', end_date='today').strftime("%Y-%m-%d")

            safe_po = po.replace('/', '_').replace(' ', '_')
            filename = f"invoice_{i+1}_{safe_po}.pdf"
            path = os.path.join(out_dir, filename)

            c = canvas.Canvas(path, pagesize=letter)
            width, height = letter

            x = 36
            y = height - 36
            c.setFont("Helvetica-Bold", 16)
            c.drawString(x, y, "Invoice")
            y -= 24
            c.setFont("Helvetica", 12)
            c.drawString(x, y, f"PO Number: {po}")
            y -= 16
            c.drawString(x, y, f"Supplier: {supplier}")
            y -= 16
            c.drawString(x, y, f"Date: {date}")
            y -= 16
            c.drawString(x, y, f"Amount: ${amount:,.2f}")
            y -= 16
            c.drawString(x, y, f"Status: {status}")
            y -= 28

            c.setFont("Helvetica-Bold", 12)
            c.drawString(x, y, "Items")
            y -= 18
            c.setFont("Helvetica", 10)
            num_items = faker.random_int(min=1, max=5)
            for j in range(num_items):
                desc = faker.sentence(nb_words=4)
                qty = faker.random_int(min=1, max=10)
                unit = round(faker.pyfloat(left_digits=3, right_digits=2, positive=True), 2)
                line_total = round(qty * unit, 2)
                c.drawString(x, y, f"- {desc}  Qty:{qty}  Unit:${unit:.2f}  Total:${line_total:.2f}")
                y -= 14
                if y < 72:
                    c.showPage()
                    y = height - 36
                    c.setFont("Helvetica", 10)

            c.showPage()
            c.save()

        print(f"Generated {count} PDF invoices in {out_dir}")


if __name__ == "__main__":
    seeder = InvoicePDFSeeder()
    seeder.run()
