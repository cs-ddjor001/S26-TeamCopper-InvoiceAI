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
- pip install setuptools 
- Important Note: Check that setuptools is showing up when you run: pip show setuptools. If it is not showing, run: pip install --upgrade pip setuptools wheel
If still not showing, run the following to force install it:
  .\.venv\Scripts\python.exe -m pip install setuptools==68.0.0

## How to run seeder:
There are two options: 
1. For PDFs: python seeders\invoice_pdf_seeder.py
2. For CSVs: python -m seeders.invoice_csv_seeder