import os
import pandas as pd
from bs4 import BeautifulSoup

# === Configuration: Define iXBRL Filing Path ===
xbrl_file_path = "primary-document.html"

if not os.path.exists(xbrl_file_path):
    raise FileNotFoundError(f"XBRL filing not found: {xbrl_file_path}")

# === Step 1: Parse iXBRL File Using BeautifulSoup (Proper XML Parsing) ===
def parse_ixbrl(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "xml")  # Using XML parser for iXBRL
    return soup

# === Step 2: Extract Time Context from XBRL ===
def extract_time_contexts(soup):
    contexts = {}
    for context in soup.find_all("xbrli:context"):
        context_id = context.get("id")
        period = context.find("xbrli:period")

        if period:
            start_date = period.find("xbrli:startDate")
            end_date = period.find("xbrli:endDate")
            instant = period.find("xbrli:instant")

            if instant:
                contexts[context_id] = instant.text  # For point-in-time values
            elif start_date and end_date:
                contexts[context_id] = f"{start_date.text} to {end_date.text}"  # For period values

    return contexts

# === Step 3: Extract All XBRL Facts & Link to Context ===
def extract_all_xbrl_data(soup, contexts):
    financial_data = []

    for fact in soup.find_all(["ix:nonFraction", "ix:nonNumeric"]):
        concept = fact.get("name")
        value = fact.text.strip()
        context_ref = fact.get("contextRef")

        # Find the period for this fact
        time_period = contexts.get(context_ref, "Unknown")

        if concept and value:
            financial_data.append({"Metric": concept, "Value": value, "Period": time_period})

    return financial_data

# Parse the iXBRL file
soup = parse_ixbrl(xbrl_file_path)
contexts = extract_time_contexts(soup)
financials = extract_all_xbrl_data(soup, contexts)

# Convert to DataFrame
df = pd.DataFrame(financials)

# Save to CSV for Review
df.to_csv("xbrl_financials_with_time.csv", index=False)

print("✅ All XBRL Financial Data saved to xbrl_financials_with_time.csv")
