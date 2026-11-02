import requests
import pandas as pd
import os
import json

# === Configuration: SEC API Details ===
SEC_BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts"
CIK = "0000019617"  # JPMorgan Chase's CIK
HEADERS = {"User-Agent": "AnalystAI/1.0 (your_email@example.com)"}
QUARTER = "CY2024Q1"  # Adjust this dynamically based on the filing date later

# === Function to Fetch All Available Line Items from SEC API ===
def fetch_all_sec_quarterly_data(cik, quarter):
    url = f"{SEC_BASE_URL}/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"❌ Error fetching data: {response.status_code}")
        return None
    
    data = response.json()
    financial_data = {}
    
    # Loop through all available financial concepts
    for concept, details in data.get("facts", {}).get("us-gaap", {}).items():
        if "units" in details and "USD" in details["units"]:
            for entry in details["units"]["USD"]:
                if "frame" in entry and entry["frame"] == quarter:
                    financial_data[concept] = entry["val"]
                elif "instant" in entry:  # Fallback for balance sheet items
                    financial_data[concept] = entry["val"]
    
    return financial_data

# === Fetch All Available Data ===
financial_data = fetch_all_sec_quarterly_data(CIK, QUARTER)

if financial_data:
    # Convert to DataFrame
    df = pd.DataFrame(list(financial_data.items()), columns=["Metric", "Value"])
    
    # Save to CSV for Review
    df.to_csv("sec_quarterly_financials.csv", index=False)
    print("✅ SEC Quarterly Financials saved to sec_quarterly_financials.csv")
else:
    print("⚠️ No financial data found for the specified quarter.")

