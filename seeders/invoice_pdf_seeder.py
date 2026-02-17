import os
from faker import Faker
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

faker = Faker()

"""
to make sure i'm not an idiot, i will generate the dummy data first
and then print that onto the pdf
"""

def generate_invoice_pdf(filename): 
    # dummy data stuff we're generating for sake of demo
    po_number = faker.bothify("PO-####-??"),        
    supplier = faker.company(),
    amount = faker.pyfloat(left_digits=5, right_digits=2, positive=True),
    status = faker.random_element(elements=("pending", "complete", "in progress"))
       
    #pdf stuff
    filename = 'sample.pdf'
    document_title = 'Invoice Sample PDF'
    
    #pdf canvas setup
    pdf = canvas.Canvas(filename,document_title)
    pdf.setTitle(document_title)
    
    #font + title
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString   (300, 770, document_title)

    text_object = pdf.beginText(100, 700)
    text_object.setFont("Helvetica", 12)

    #formatted for text for pdf
    textlines = [
        f"PO Number:    {po_number}",
        f"Supplier:     {supplier}",
        f"Amount:      ${amount}",
        f"Status:       {status}" 
    ]
    
    #hopefully printing out those details? :sob:
    for lines in textlines:
        text_object.textLine(lines)

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
    
    
if __name__ == "__main__":
    generate_invoice_pdf("sample.pdf")
    #seeder.run()

"""
bruh i'm just trying to comment out
"""