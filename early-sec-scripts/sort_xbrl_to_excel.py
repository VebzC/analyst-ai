import pandas as pd

# Load extracted XBRL financials
df = pd.read_csv("xbrl_financials_timeseries.csv")

# Extract the prefix (everything before ":") from the "Metric" column
df["Prefix"] = df["Metric"].apply(lambda x: x.split(":")[0] if ":" in x else "unknown")

# Create a dictionary to store dataframes for each prefix
prefix_groups = {}

# Separate metrics into different tabs based on their prefixes
for prefix in df["Prefix"].unique():
    subset = df[df["Prefix"] == prefix].copy()
    
    # Remove the prefix for better readability inside each tab
    subset["Metric"] = subset["Metric"].apply(lambda x: x.split(":")[-1])
    
    # Store the cleaned dataframe in the dictionary
    prefix_groups[prefix] = subset.drop(columns=["Prefix"])

# Save to an Excel file with each prefix in a different tab
output_file = "xbrl_financials_sorted.xlsx"
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    for prefix, df_subset in prefix_groups.items():
        df_subset.to_excel(writer, sheet_name=prefix[:31], index=False)  # Excel tab names are max 31 chars

print(f"✅ Sorted financial data saved to {output_file}")
