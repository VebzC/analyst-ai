import os
from weasyprint import HTML

# === Configuration: Select Filing ===
company_ticker = "JPM"
filing_type = "10-Q"
latest_filing_folder = "0000019617-24-000326"
html_file = f"sec-edgar-filings/{company_ticker}/{filing_type}/{latest_filing_folder}/primary-document.html"
pdf_output = "sec_filing.pdf"

# ✅ Ensure the file exists
if not os.path.exists(html_file):
    raise FileNotFoundError(f"Filing not found: {html_file}")

# ✅ Convert HTML to PDF using WeasyPrint
try:
    HTML(filename=html_file).write_pdf(pdf_output)
    print(f"✅ SEC filing converted to PDF: {pdf_output}")
except Exception as e:
    print(f"❌ Error converting HTML to PDF: {e}")

