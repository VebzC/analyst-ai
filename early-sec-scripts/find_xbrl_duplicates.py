import pandas as pd

# Load extracted XBRL financials
df = pd.read_csv("xbrl_financials_timeseries.csv")

# Count occurrences of each Metric + Period combination
duplicate_counts = df.groupby(["Metric", "Period"]).size().reset_index(name="Count")

# Filter only duplicate entries (Count > 1)
duplicates = duplicate_counts[duplicate_counts["Count"] > 1]

# Merge duplicates with original data for full details
duplicate_details = df.merge(duplicates[["Metric", "Period"]], on=["Metric", "Period"], how="inner")

# Save to CSV for inspection
duplicate_details.to_csv("xbrl_duplicates.csv", index=False)

# Print first few rows to console
print("✅ Duplicate Values Found. Check 'xbrl_duplicates.csv'")
print(duplicate_details.head())
