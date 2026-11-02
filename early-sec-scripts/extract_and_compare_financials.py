import openai
import pdfplumber
import pandas as pd
import os
import json
import requests

# === Configuration: OpenAI API Key ===
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Set it using export OPENAI_API_KEY='your-api-key'")

client = openai.OpenAI(api_key=api_key)

# === Configuration: Define SEC Filing PDF ===
pdf_file_path = "sec_filing.pdf"
if not os.path.exists(pdf_file_path):
    raise FileNotFoundError(f"PDF filing not found: {pdf_file_path}")

# === Step 1: Extract Tables from PDF ===
def extract_tables_from_pdf(pdf_path):
    extracted_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                df = pd.DataFrame(table)
                extracted_tables.append(df)
    return extracted_tables

tables = extract_tables_from_pdf(pdf_file_path)

if not tables:
    raise ValueError("No financial tables found in the PDF.")

# === Step 2: Save Tables to CSV for Review ===
for i, df in enumerate(tables):
    df.to_csv(f"financial_table_{i+1}.csv", index=False)

print("✅ Financial tables extracted and saved as CSV files.")

# === Step 3: Fetch Financial Data from SEC’s XBRL API ===
SEC_BASE_URL = "https://data.sec.gov/api/xbrl/companyconcept"
CIK = "0000019617"  # JPMorgan Chase's CIK

def fetch_sec_financials(cik, concept):
    url = f"{SEC_BASE_URL}/CIK{cik}/us-gaap/{concept}.json"
    headers = {"User-Agent": "AnalystAI/1.0 (your_email@example.com)"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error fetching {concept}: {response.status_code}")
        return None

# Fetch Revenue, Net Income, and Assets
revenue_data = fetch_sec_financials(CIK, "Revenues")
net_income_data = fetch_sec_financials(CIK, "NetIncomeLoss")
assets_data = fetch_sec_financials(CIK, "Assets")

print("✅ SEC Financial Data Retrieved.")

# === Step 4: Compare Extracted vs. Standardized Data ===
def get_latest_value(data):
    if data and "units" in data and "USD" in data["units"]:
        return data["units"]["USD"][-1]["val"]  # Most recent value
    return None

sec_revenue = get_latest_value(revenue_data)
sec_net_income = get_latest_value(net_income_data)
sec_assets = get_latest_value(assets_data)

# Placeholder for manually extracted values (to be automated later)
pdf_revenue = 13340000000  # Placeholder (Extract from CSV)
pdf_net_income = 41900000000  # Placeholder (Extract from CSV)

# Compare Values
comparison = {
    "Revenue (PDF Extracted)": pdf_revenue,
    "Revenue (SEC API)": sec_revenue,
    "Net Income (PDF Extracted)": pdf_net_income,
    "Net Income (SEC API)": sec_net_income,
    "Total Assets (SEC API)": sec_assets
}

# Save Comparison as JSON
with open("financial_comparison.json", "w") as f:
    json.dump(comparison, f, indent=4)

print("✅ Financial data comparison saved to financial_comparison.json")

# === Step 5: Generate AI-Powered Financial Report ===
def analyze_financial_comparison(comparison):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a financial analyst analyzing discrepancies between SEC XBRL data and as-reported financials."},
            {"role": "user", "content": f"Compare and explain key financial differences:\n{json.dumps(comparison, indent=4)}"}
        ]
    )
    return response.choices[0].message.content

summary = analyze_financial_comparison(comparison)

# Save AI-Generated Report
with open("financial_analysis.txt", "w", encoding="utf-8") as f:
    f.write(summary)

print("✅ AI-powered financial analysis saved to financial_analysis.txt.")
