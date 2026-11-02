import os
import requests
import json

# ======================================================
# IMPORTANT: You need to replace this with a valid token
# Sign up at https://sec-api.io and generate a new API key
# from your dashboard, then replace it below
# ======================================================
API_KEY = os.environ.get("SEC_API_KEY", "")  # set SEC_API_KEY in your environment
TICKER = "AAPL"  # Replace with your ticker

# Define the endpoint
url = "https://api.sec-api.io/full-text-search"

# Query structure
payload = {
    "query": f"ticker:{TICKER} AND formType:\"10-Q\"",
    "from": 0,
    "size": 10,
    "sort": [{"filedAt": {"order": "desc"}}]
}

# Use Authorization header with Bearer prefix
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Make the POST request to the API
print(f"Querying {TICKER} 10-Q filings...")
response = requests.post(url, headers=headers, json=payload)

# Print request details for debugging
print(f"Request URL: {url}")
print(f"Request Headers: {headers}")
print(f"Request Payload: {json.dumps(payload, indent=2)}")

# Check the response and process the data
if response.status_code == 200:
    filings_data = response.json()
    # Depending on the API's structure, filings might be in a key like "filings" or "hits".
    # For example, if filings are in a key called "filings":
    filings = filings_data.get("filings", filings_data.get("hits", []))
    if filings:
        print(f"Found {len(filings)} filings:")
        for filing in filings:
            print("Accession Number:", filing.get("accessionNumber"))
            print("Filing Date:", filing.get("filedAt"))
            print("Form Type:", filing.get("formType"))
            print("-" * 40)
    else:
        print("No filings found matching the criteria.")
        print("Response data:", json.dumps(filings_data, indent=2))
else:
    print(f"Error: {response.status_code} {response.text}")
    print("\nPossible issues:")
    print("1. The API token might be invalid or expired")
    print("2. The API endpoint might have changed")
    print("3. The request format might be incorrect")
    print("\nVisit https://sec-api.io/docs for current documentation")