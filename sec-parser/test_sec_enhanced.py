#!/usr/bin/env python3
"""
Enhanced test script to parse a sample SEC filing using the sec_md_parser library.
This script creates a sample HTML file with XBRL tags and converts it to markdown
with a focus on preserving and displaying the XBRL data.
"""

import os
import json
from pathlib import Path
from bs4 import BeautifulSoup
from sec_md_parser import SECParser
from sec_md_parser.models.base import XBRLFact

# Create a sample HTML file with XBRL tags
SAMPLE_HTML = """
<html>
<head>
    <title>JPMorgan Chase & Co. - Form 10-Q</title>
</head>
<body>
    <div class="filing-header">
        <h1>FORM 10-Q</h1>
        <p>Quarterly Report Pursuant to Section 13 or 15(d) of the Securities Exchange Act of 1934</p>
        <p>Filed: September 30, 2024</p>
        <p>Company: JPMorgan Chase & Co.</p>
        <p>CIK: 0000019617</p>
    </div>
    
    <div class="section">
        <h2>Item 1. Financial Statements</h2>
        <p>The following consolidated financial statements and notes should be read in conjunction with JPMorgan Chase's Annual Report.</p>
        
        <table class="financial-table">
            <caption>CONSOLIDATED STATEMENTS OF INCOME (Unaudited)</caption>
            <thead>
                <tr>
                    <th rowspan="2">Line Item</th>
                    <th colspan="2">Three months ended September 30</th>
                    <th colspan="2">Nine months ended September 30</th>
                </tr>
                <tr>
                    <th>2024</th>
                    <th>2023</th>
                    <th>2024</th>
                    <th>2023</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Total Revenue</td>
                    <td>
                        <ix:nonfraction name="us-gaap:Revenue" contextref="duration_2024-07-01_2024-09-30" 
                        unitref="usd" decimals="-6">42,515,000,000</ix:nonfraction>
                    </td>
                    <td>
                        <ix:nonfraction name="us-gaap:Revenue" contextref="duration_2023-07-01_2023-09-30" 
                        unitref="usd" decimals="-6">39,874,000,000</ix:nonfraction>
                    </td>
                    <td>
                        <ix:nonfraction name="us-gaap:Revenue" contextref="duration_2024-01-01_2024-09-30" 
                        unitref="usd" decimals="-6">125,782,000,000</ix:nonfraction>
                    </td>
                    <td>
                        <ix:nonfraction name="us-gaap:Revenue" contextref="duration_2023-01-01_2023-09-30" 
                        unitref="usd" decimals="-6">116,352,000,000</ix:nonfraction>
                    </td>
                </tr>
                <tr>
                    <td>Net Income</td>
                    <td>
                        <ix:nonfraction name="us-gaap:NetIncome" contextref="duration_2024-07-01_2024-09-30" 
                        unitref="usd" decimals="-6">13,245,000,000</ix:nonfraction>
                    </td>
                    <td>
                        <ix:nonfraction name="us-gaap:NetIncome" contextref="duration_2023-07-01_2023-09-30" 
                        unitref="usd" decimals="-6">12,756,000,000</ix:nonfraction>
                    </td>
                    <td>
                        <ix:nonfraction name="us-gaap:NetIncome" contextref="duration_2024-01-01_2024-09-30" 
                        unitref="usd" decimals="-6">41,562,000,000</ix:nonfraction>
                    </td>
                    <td>
                        <ix:nonfraction name="us-gaap:NetIncome" contextref="duration_2023-01-01_2023-09-30" 
                        unitref="usd" decimals="-6">38,853,000,000</ix:nonfraction>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</body>
</html>
"""

def generate_enhanced_markdown(document, original_markdown):
    """Generate enhanced markdown with XBRL data."""
    # Create a new markdown document with the original content
    enhanced_md = original_markdown
    
    # Add a section for XBRL data
    enhanced_md += "\n\n## XBRL Data Analysis\n\n"
    
    # Group XBRL facts by type
    fact_by_type = {}
    for fact in document.xbrl_facts:
        if fact.name not in fact_by_type:
            fact_by_type[fact.name] = []
        fact_by_type[fact.name].append(fact)
    
    # Add sections for each fact type
    for fact_name, facts in fact_by_type.items():
        enhanced_md += f"### {fact_name}\n\n"
        enhanced_md += "| Value | Context | Unit | Decimals |\n"
        enhanced_md += "| --- | --- | --- | --- |\n"
        
        for fact in facts:
            enhanced_md += f"| {fact.value} | {fact.context_ref} | {fact.unit_ref} | {fact.decimals} |\n"
        
        enhanced_md += "\n"
    
    # Add a section for financial analysis
    enhanced_md += "\n## Financial Analysis\n\n"
    
    # Get Revenue facts
    revenue_facts = fact_by_type.get("us-gaap:Revenue", [])
    
    # Get most recent quarterly revenue
    q3_2024_revenue = next(
        (fact for fact in revenue_facts if fact.context_ref == "duration_2024-07-01_2024-09-30"), 
        None
    )
    
    q3_2023_revenue = next(
        (fact for fact in revenue_facts if fact.context_ref == "duration_2023-07-01_2023-09-30"), 
        None
    )
    
    if q3_2024_revenue and q3_2023_revenue:
        try:
            current_rev = float(q3_2024_revenue.value.replace(",", ""))
            prev_rev = float(q3_2023_revenue.value.replace(",", ""))
            growth = ((current_rev - prev_rev) / prev_rev) * 100
            
            enhanced_md += f"### Revenue Growth Analysis\n\n"
            enhanced_md += f"* Q3 2024 Revenue: ${format_number(current_rev)}\n"
            enhanced_md += f"* Q3 2023 Revenue: ${format_number(prev_rev)}\n"
            enhanced_md += f"* Year-over-Year Growth: {growth:.2f}%\n\n"
        except (ValueError, TypeError):
            enhanced_md += "Could not perform revenue analysis due to data format issues.\n\n"
    
    # Get Net Income facts
    net_income_facts = fact_by_type.get("us-gaap:NetIncome", [])
    
    # Get most recent quarterly net income
    q3_2024_income = next(
        (fact for fact in net_income_facts if fact.context_ref == "duration_2024-07-01_2024-09-30"), 
        None
    )
    
    q3_2023_income = next(
        (fact for fact in net_income_facts if fact.context_ref == "duration_2023-07-01_2023-09-30"), 
        None
    )
    
    if q3_2024_income and q3_2023_income and q3_2024_revenue:
        try:
            current_inc = float(q3_2024_income.value.replace(",", ""))
            prev_inc = float(q3_2023_income.value.replace(",", ""))
            current_rev = float(q3_2024_revenue.value.replace(",", ""))
            
            growth = ((current_inc - prev_inc) / prev_inc) * 100
            margin = (current_inc / current_rev) * 100
            
            enhanced_md += f"### Profitability Analysis\n\n"
            enhanced_md += f"* Q3 2024 Net Income: ${format_number(current_inc)}\n"
            enhanced_md += f"* Q3 2023 Net Income: ${format_number(prev_inc)}\n"
            enhanced_md += f"* Year-over-Year Growth: {growth:.2f}%\n"
            enhanced_md += f"* Q3 2024 Profit Margin: {margin:.2f}%\n\n"
        except (ValueError, TypeError):
            enhanced_md += "Could not perform profitability analysis due to data format issues.\n\n"
    
    return enhanced_md

def format_number(num):
    """Format a number for display."""
    if num >= 1e9:
        return f"{num/1e9:.2f} billion"
    elif num >= 1e6:
        return f"{num/1e6:.2f} million"
    else:
        return f"{num:,.2f}"

def parse_sec_filing(html_content, output_dir="output"):
    """Parse an SEC filing using sec_md_parser and save the result."""
    print("Parsing sample SEC filing...")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the sample HTML content
    html_path = os.path.join(output_dir, "enhanced-sample.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Sample HTML saved to {html_path}")
    
    # Initialize the parser
    parser = SECParser()
    
    # Parse the HTML content
    document = parser.parse_from_html(html_content)
    
    # Extract metadata
    print("\nMetadata:")
    for key, value in document.metadata.items():
        print(f"  {key}: {value}")
    
    # Convert to markdown
    standard_markdown = parser.document_to_markdown(document)
    
    # Generate enhanced markdown with XBRL data
    enhanced_markdown = generate_enhanced_markdown(document, standard_markdown)
    
    # Save the markdown content
    markdown_path = os.path.join(output_dir, "enhanced-output.md")
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(enhanced_markdown)
    
    print(f"\nEnhanced markdown output saved to {markdown_path}")
    
    # Save XBRL facts to JSON for reference
    xbrl_facts = [fact.to_dict() for fact in document.xbrl_facts]
    json_path = os.path.join(output_dir, "xbrl-facts.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(xbrl_facts, f, indent=2)
    
    print(f"XBRL facts saved to {json_path}")
    
    # Print XBRL facts statistics
    if document.xbrl_facts:
        print(f"\nExtracted {len(document.xbrl_facts)} XBRL facts")
        
        # Group facts by name
        fact_counts = {}
        for fact in document.xbrl_facts:
            if fact.name not in fact_counts:
                fact_counts[fact.name] = 0
            fact_counts[fact.name] += 1
        
        print("\nXBRL fact types:")
        for name, count in sorted(fact_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {name}: {count}")
    
    return document, enhanced_markdown

def main():
    """Main function to parse a sample SEC filing."""
    try:
        # Parse the sample SEC filing
        document, markdown = parse_sec_filing(SAMPLE_HTML)
        
        # Print a sample of the markdown
        print("\nSample of enhanced markdown output (first 500 characters):")
        print(markdown[:500] + "...")
        
        print("\nProcessing complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 