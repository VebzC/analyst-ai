import pandas as pd
from datetime import datetime

# Load the extracted XBRL financials
df = pd.read_csv("xbrl_financials_with_time.csv")

# Function to round months to nearest 3, 6, 9, or 12
def round_to_standard_months(months):
    if months <= 4:
        return 3
    elif months <= 7:
        return 6
    elif months <= 10:
        return 9
    else:
        return 12

# Function to format periods correctly
def format_period(period_str):
    # If there's a date range (e.g., "2024-01-01 to 2024-03-31")
    if " to " in period_str:
        start_date, end_date = period_str.split(" to ")
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Calculate number of months in the period
        num_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        
        # Round to nearest 3/6/9/12 months
        rounded_months = round_to_standard_months(num_months)
        
        return f"{rounded_months} months ended {end_date.strftime('%Y-%m-%d')}"
    
    # If it's a single date, return it as is (e.g., "2024-03-31")
    else:
        return period_str

# Apply the formatting function to the period column
df["Formatted_Period"] = df["Period"].apply(format_period)

# ✅ Step 1: Handle duplicate metric-period combinations by taking the **latest value**
df = df.groupby(["Metric", "Formatted_Period"], as_index=False).last()

# ✅ Step 2: Pivot the table so each Metric becomes a row, and each Period (Quarter) becomes a column
df_pivot = df.pivot(index="Metric", columns="Formatted_Period", values="Value")

# Save the new time-series formatted data
df_pivot.to_csv("xbrl_financials_timeseries.csv")

print("✅ Time-Series Financial Data saved to xbrl_financials_timeseries.csv")
