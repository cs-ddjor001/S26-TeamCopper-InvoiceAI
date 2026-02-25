# Exit immediately if any command fails
$ErrorActionPreference = "Stop"

Write-Host "=== InvoiceAI Setup ==="

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Uncomment to wipe and recreate the database (needed after schema changes)
# Remove-Item -Force app.db -ErrorAction SilentlyContinue

Write-Host "[1/4] Generating purchase orders CSV..."
python seeders/purchase_order_seeder.py

Write-Host "[2/4] Loading purchase orders into database..."
python seeders/load_po_csv.py

Write-Host "[3/4] Generating invoice PDFs..."
python seeders/invoice_pdf_seeder.py

Write-Host "[4/4] Parsing invoice PDFs..."
foreach ($pdf in Get-ChildItem -Path data -Filter "sample_*.pdf") {
    python parse_pdf.py $pdf.FullName
}

Write-Host ""
Write-Host "Done. Start the app with: python app.py"
