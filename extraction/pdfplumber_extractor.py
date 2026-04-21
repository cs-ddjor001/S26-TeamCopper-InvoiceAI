import pdfplumber
import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    return text.strip()


def extract_tables(page):
    table_settings_list = [
        {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "intersection_tolerance": 5,
        },
        {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
        },
    ]

    tables = []

    for settings in table_settings_list:
        extracted = page.extract_tables(settings)
        if extracted:
            for table in extracted:
                cleaned_table = [
                    [cell.strip() if cell else "" for cell in row] for row in table
                ]
                tables.append(cleaned_table)

        if tables:
            break

    return tables


def extract_invoice_pdf(pdf_path: str) -> dict:
    result = {"file": pdf_path, "pages": []}

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=2, y_tolerance=2, layout=True)

            text = clean_text(text)

            tables = extract_tables(page)

            result["pages"].append(
                {"page_number": i + 1, "text": text, "tables": tables}
            )

    return result
