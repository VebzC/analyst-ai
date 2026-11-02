#!/usr/bin/env python3
"""
Example script demonstrating how to use the SEC MD Parser tools.

This script shows:
1. How to parse a local HTML file
2. How to extract XBRL data
3. How to generate financial analysis
4. How to access specific financial metrics
"""

import os
from sec_md_parser import SECParser
from real_sec_parser import SECFilingParser

def example_parse_local_file():
    """Example of parsing a local file."""
    print("\n===== Example: Parsing Local File =====")
    
    # Path to sample file (created by test_sec_enhanced.py)
    sample_path = "output/enhanced-sample.html"
    
    # Check if sample file exists, run test_sec_enhanced.py if not
    if not os.path.exists(sample_path):
        print(f"Sample file not found at {sample_path}")
        print("Please run test_sec_enhanced.py first to generate the sample file.")
        return
    
    # Initialize parser
    parser = SECFilingParser()
    
    # Load HTML from file
    html_content = parser.load_filing_from_file(sample_path)
    
    # Parse the filing
    document, metadata, enhanced_markdown = parser.parse_filing(html_content)
    
    # Print metadata
    print("\nMetadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    # Print XBRL facts
    if document.xbrl_facts:
        print(f"\nExtracted {len(document.xbrl_facts)} XBRL facts")
        
        # Group facts by name
        fact_by_name = {}
        for fact in document.xbrl_facts:
            if fact.name not in fact_by_name:
                fact_by_name[fact.name] = []
            fact_by_name[fact.name].append(fact)
        
        print("\nXBRL fact types:")
        for name, facts in fact_by_name.items():
            print(f"  {name}: {len(facts)} facts")
    
    # Save outputs with custom prefix
    output_files = parser.save_outputs(
        document, 
        metadata, 
        enhanced_markdown, 
        prefix="example_output"
    )
    
    print("\nOutput files:")
    for output_type, file_path in output_files.items():
        print(f"  {output_type}: {file_path}")

def example_extract_financial_metrics():
    """Example of extracting and analyzing specific financial metrics."""
    print("\n===== Example: Extracting Financial Metrics =====")
    
    # Path to sample file
    sample_path = "output/enhanced-sample.html"
    
    # Check if sample file exists
    if not os.path.exists(sample_path):
        print(f"Sample file not found at {sample_path}")
        return
    
    # Initialize SEC parser directly for more control
    parser = SECParser()
    
    # Load and parse HTML
    with open(sample_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    document = parser.parse_from_html(html_content)
    
    # Find specific metrics
    revenue_facts = [fact for fact in document.xbrl_facts if fact.name == "us-gaap:Revenue"]
    net_income_facts = [fact for fact in document.xbrl_facts if fact.name == "us-gaap:NetIncome"]
    
    print("\nRevenue data:")
    for fact in revenue_facts:
        print(f"  {fact.context_ref}: ${format_value(fact.value)}")
    
    print("\nNet Income data:")
    for fact in net_income_facts:
        print(f"  {fact.context_ref}: ${format_value(fact.value)}")
    
    # Calculate growth and margins
    try:
        # Find Q3 2024 and Q3 2023 revenue
        q3_2024_revenue = next(
            (fact for fact in revenue_facts if fact.context_ref == "duration_2024-07-01_2024-09-30"), 
            None
        )
        
        q3_2023_revenue = next(
            (fact for fact in revenue_facts if fact.context_ref == "duration_2023-07-01_2023-09-30"), 
            None
        )
        
        # Find Q3 2024 net income
        q3_2024_income = next(
            (fact for fact in net_income_facts if fact.context_ref == "duration_2024-07-01_2024-09-30"), 
            None
        )
        
        if q3_2024_revenue and q3_2023_revenue and q3_2024_income:
            # Parse values
            current_rev = float(q3_2024_revenue.value.replace(",", ""))
            prev_rev = float(q3_2023_revenue.value.replace(",", ""))
            current_inc = float(q3_2024_income.value.replace(",", ""))
            
            # Calculate growth and margin
            revenue_growth = ((current_rev - prev_rev) / prev_rev) * 100
            profit_margin = (current_inc / current_rev) * 100
            
            print("\nFinancial Analysis:")
            print(f"  Revenue Growth (Q3 YoY): {revenue_growth:.2f}%")
            print(f"  Profit Margin (Q3): {profit_margin:.2f}%")
    
    except (ValueError, TypeError, StopIteration) as e:
        print(f"\nError in financial calculations: {e}")

def format_value(value_str):
    """Format a numerical string for display."""
    try:
        # Remove commas and convert to float
        value = float(value_str.replace(",", ""))
        
        # Format based on size
        if value >= 1e9:
            return f"{value/1e9:.2f} billion"
        elif value >= 1e6:
            return f"{value/1e6:.2f} million"
        else:
            return f"{value:,.2f}"
    except (ValueError, TypeError):
        return value_str

def main():
    """Run example functions."""
    print("SEC MD Parser Tools - Usage Examples")
    
    # Example 1: Parse a local file
    example_parse_local_file()
    
    # Example 2: Extract financial metrics
    example_extract_financial_metrics()
    
    print("\nExamples completed!")

if __name__ == "__main__":
    main() 