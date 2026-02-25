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
- pip install pdfplumber


## Important to do before running anything!
1. Make sure to delete the app.db file if you have not done so already.
2. Run python app.py to create a new app.db with updated tables.
3. Proceed below to run the seeders.

## How to run seeders:

Run purchase order seeder first, as PO numberss generated on invoices depend on the PO seeder:
1. python -m seeders.purchase_order_seeder
2. seeders\load_po_csv.py to load it to db

Then there are two options for invoices: 
1. For PDFs: python seeders\invoice_pdf_seeder.py
2. For CSVs: python -m seeders.invoice_csv_seeder

## PDF Parsing Pipeline

Parses a generated invoice PDF and saves the data to the database.

## How to run
Manual Run:
1. Generate a PDF:
   python seeders/invoice_pdf_seeder.py

2. Parse it into the database:
   python parse_pdf.py data/sample_#.pdf (replace # with any number from 1-50).

3. Repeat until you are happy with how many pdfs are parsed and populated.

4. python run_matching.py to run the matching between invoices and purchase orders

5. Use Flask run to check the number of invoices counted on the website.

Auto Run:
1. Make sure database is empty (delete app.db, python app.py, exit app)
2. Run .\setup.ps1
3. flask run to start the app
4. Login with tom.ap, check out the invoice versus POs, then run matching, then go WOW!