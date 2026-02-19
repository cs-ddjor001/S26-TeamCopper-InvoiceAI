Team Copper - Spring 2026

# Members

  - cs-ddjor001 - Dusan Djordjevic - ddjor001@odu.edu
  - cmjgrubb - Craig Grubb - cgrub002@odu.edu
  - juuliannd41 - Julian Diaz - jdiaz037@odu.edu
  - MichaelNimitz1995 - Michael Nimitza - mnimi001@odu.edu
  - MinMin5843 - Lynda Salinas Ascanova - lsali002@odu.edu
  - qelson - Quin Elson - qelso001@odu.edu
  - stodd009 - Savannah Todd - stodd009@odu.edu
  - tfull013 - Tommy Fuller - tfull013@odu.edu

## Install the following first before running any seeders:
- in .venv (virtual environment)
- pip install Flask-Seeder
- pip install Faker
- pip install reportlab (pdf gen.)
- .\.venv\Scripts\python.exe -m pip install setuptools==68.0.0

## How to run seeders:
There are two options for invoices: 
1. For PDFs: python seeders\invoice_pdf_seeder.py
2. For CSVs: python -m seeders.invoice_csv_seeder

## PDF Parsing Pipeline

Parses a generated invoice PDF and saves the data to the database.

### New dependency
pip install pdfplumber

### How to run
1. Generate a PDF:
   python seeders/invoice_pdf_seeder.py

2. Parse it into the database:
   python parse_pdf.py

This creates a Vendor (if one with that name doesn't exist), a Purchase_Order,
and an Invoice row in app.db. Run python app.py first if app.db doesn't exist yet.

Note: The parser reads field labels exactly as written by the seeder
("PO Number:", "Supplier:", "Amount:", "Status:"). If those labels change
in the seeder, parser.py must be updated to match.

Now, for the purchase orders: python -m seeders.purchase_order_seeder

## PDF Parsing Pipeline

Parses a generated invoice PDF and saves the data to the database.

### New dependency
pip install pdfplumber

### How to run
1. Generate a PDF:
   python seeders/invoice_pdf_seeder.py

2. Parse it into the database:
   python parse_pdf.py

This creates a Vendor (if one with that name doesn't exist), a Purchase_Order,
and an Invoice row in app.db. Run python app.py first if app.db doesn't exist yet.

Note: The parser reads field labels exactly as written by the seeder
("PO Number:", "Supplier:", "Amount:", "Status:"). If those labels change
in the seeder, parser.py must be updated to match.