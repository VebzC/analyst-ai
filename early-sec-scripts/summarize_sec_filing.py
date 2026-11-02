import openai
import pdfplumber
import os
import re

# === Configuration: OpenAI API Key ===
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Set it using export OPENAI_API_KEY='your-api-key'")

client = openai.OpenAI(api_key=api_key)

# === Configuration: Define SEC Filing PDF ===
pdf_file_path = "sec_filing.pdf"
if not os.path.exists(pdf_file_path):
    raise FileNotFoundError(f"PDF filing not found: {pdf_file_path}")

# === Step 1: Extract Text from PDF ===
def extract_pdf_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

full_text = extract_pdf_text(pdf_file_path)
if not full_text.strip():
    raise ValueError("Extracted text is empty. Check the PDF content.")

# === Step 2: Locate the MD&A Section ===
def extract_mda_section(text):
    pattern = r"(?i)(management['’]s discussion and analysis|MD&A)(.*?)(?=item \d+|financial statements|conclusion)"
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        return "\n".join([match[1] for match in matches])
    else:
        return "MD&A section not found in the text."

mda_text = extract_mda_section(full_text)
if "MD&A section not found" in mda_text:
    raise ValueError("Could not locate MD&A section in the document.")

# === Step 3: Send Text to OpenAI for Financial Analyst-Style Summary ===
def summarize_mda(text):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a financial analyst summarizing the Management’s Discussion and Analysis (MD&A) section from an SEC 10-Q or 10-K filing. Your summary should highlight key financial metrics, revenue trends, net income drivers, risk factors, business segment performance, and forward guidance."},
            {"role": "user", "content": f"Extract and summarize the MD&A section from this text in bullet points with a financial analyst’s perspective:\n{text[:8000]}"}
        ]
    )
    return response.choices[0].message.content

summary = summarize_mda(mda_text)

# === Step 4: Save Summary to File ===
output_file = "sec_filing_mda_summary.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(summary)

print(f"✅ MD&A summary saved to {output_file}")

