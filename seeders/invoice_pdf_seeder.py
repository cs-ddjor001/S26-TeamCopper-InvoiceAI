import csv
import os
from faker import Faker
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

faker = Faker()


def load_po_numbers(filepath="data/purchase_orders.csv"):
    po_numbers = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            po_numbers.append(int(row["po_number"]))
    return po_numbers


"""
to make sure i'm not an idiot, i will generate the dummy data first
and then print that onto the pdf
"""

def generate_invoice_pdf(filename, po_numbers):

    po_number = faker.random_element(po_numbers)
    supplier = faker.company()
    amount = faker.pyfloat(left_digits=5, right_digits=2, positive=True)
    status = faker.random_element(elements=("pending", "complete", "in progress"))
    date = faker.date_this_year()

    pdf = canvas.Canvas(filename, pagesize=letter)
    pdf.setTitle("Invoice Sample PDF")

    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(300, 770, "Invoice Sample PDF")

    text_object = pdf.beginText(100, 700)
    text_object.setFont("Helvetica", 12)

    textlines = [
        f"PO Number:    {po_number}",
        f"Supplier:     {supplier}",
        f"Amount:      ${amount}",
        f"Status:       {status}",
        f"Date Issued:  {date}"
    ]

    for line in textlines:
        text_object.textLine(line)

    pdf.drawText(text_object)
    pdf.showPage()
    pdf.save()

    """ lol i forget this is called a sanity check, BUT IT WORKS 
    print("dummy data generated:")
    print(f"PO Number:    {po_number}")
    print(f"Supplier:     {supplier}")
    print(f"Amount:      ${amount}")
    print(f"Status:       {status}")
    """
    print(f"Successfully generated {filename} with dummy invoice data. (hopefully)")
    
    
def generate_multiple(n=50):
    os.makedirs("data", exist_ok=True)
    po_numbers = load_po_numbers()
    for i in range(n):
        generate_invoice_pdf(f"data/sample_{i+1}.pdf", po_numbers)

    print(f"{n} PDF invoices generated.")

if __name__ == "__main__":
    generate_multiple(50)

"""
bruh i'm just trying to comment out
"""