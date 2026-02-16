from flask_seeder import Seeder, Faker, generator

import os
from reportlab.pdfgen import canvas

faker = Faker()

#initalize variables (these are based off of Lynda's invoice_seeder.py)

filename = 'sample.pdf'
document_title = 'Invoice Sample PDF'


# dummy data stuff we're generating for sake of demo
po_number = 'will use faker for this'
supplier = "will use faker for this"
amount = 'will use faker for this'
status = 'will use faker for this'

#formatted for text for pdf
textlines = [
    'PO Number: ' + po_number,
    'Supplier: ' + supplier,
    'Amount: ' + str(amount),
    'Status: ' + status
]

#pdf canvas
pdf = canvas.Canvas(filename)
pdf.setTitle(document_title)

pdf.setFont("Arial", 36)
pdf.drawCentredString(300, 770, document_title)

#hopefully printing out those details? :sob:
for lines in textlines:
    text.textline(lines)

pdf.drawText(text)

class InvoicePDFSeeder(Seeder):
    





if __name__ == "__main__":
    seeder = InvoicePDFSeeder()
    seeder.run()

"""
bruh i'm just trying to comment out
"""