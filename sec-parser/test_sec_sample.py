#!/usr/bin/env python3
"""
Test script to parse a sample SEC filing using the sec_md_parser library.
This script creates a sample HTML file with XBRL tags and converts it to markdown.
"""

import os
from sec_md_parser import SECParser

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
                <tr>
                    <td>Earnings Per Share (Basic)</td>
                    <td>
                        <ix:nonfraction name="us-gaap:EarningsPerShareBasic" contextref="duration_2024-07-01_2024-09-30" 
                        unitref="usd/shares" decimals="2">4.55</ix:nonfraction>
                    </td>
                    <td>
                        <ix:nonfraction name="us-gaap:EarningsPerShareBasic" contextref="duration_2023-07-01_2023-09-30" 
                        unitref="usd/shares" decimals="2">4.32</ix:nonfraction>
                    </td>
                    <td>
                        <ix:nonfraction name="us-gaap:EarningsPerShareBasic" contextref="duration_2024-01-01_2024-09-30" 
                        unitref="usd/shares" decimals="2">14.25</ix:nonfraction>
                    </td>
                    <td>
                        <ix:nonfraction name="us-gaap:EarningsPerShareBasic" contextref="duration_2023-01-01_2023-09-30" 
                        unitref="usd/shares" decimals="2">13.15</ix:nonfraction>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>Item 2. Management's Discussion and Analysis</h2>
        <p>The firm's revenue<sup id="fnref1"><a href="#fn1">[1]</a></sup> for the three months ended September 30, 2024 was 
        <ix:nonfraction name="us-gaap:Revenue" contextref="duration_2024-07-01_2024-09-30" 
        unitref="usd" decimals="-6">42,515,000,000</ix:nonfraction>, an increase of 7% compared to 
        <ix:nonfraction name="us-gaap:Revenue" contextref="duration_2023-07-01_2023-09-30" 
        unitref="usd" decimals="-6">39,874,000,000</ix:nonfraction> for the same period in 2023.</p>
        
        <p>Net interest income was 
        <ix:nonfraction name="us-gaap:InterestAndDividendIncome" contextref="duration_2024-07-01_2024-09-30" 
        unitref="usd" decimals="-6">22,452,000,000</ix:nonfraction>, up from
        <ix:nonfraction name="us-gaap:InterestAndDividendIncome" contextref="duration_2023-07-01_2023-09-30" 
        unitref="usd" decimals="-6">21,875,000,000</ix:nonfraction> in the prior year period.</p>
    </div>
    
    <div class="footnotes">
        <ol>
            <li id="fn1">
                <p>Revenue includes net interest income and noninterest revenue.</p>
            </li>
        </ol>
    </div>
    
    <div style="display:none">
        <ix:header>
            <ix:references>
                <link:schemaRef xlink:href="http://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023-01-31.xsd" xlink:type="simple" />
            </ix:references>
            <ix:resources>
                <xbrl:context id="duration_2024-07-01_2024-09-30">
                    <xbrl:entity>
                        <xbrl:identifier scheme="http://www.sec.gov/CIK">0000019617</xbrl:identifier>
                    </xbrl:entity>
                    <xbrl:period>
                        <xbrl:startDate>2024-07-01</xbrl:startDate>
                        <xbrl:endDate>2024-09-30</xbrl:endDate>
                    </xbrl:period>
                </xbrl:context>
            </ix:resources>
        </ix:header>
    </div>
</body>
</html>
"""

def parse_sec_filing(html_content, output_dir="output"):
    """Parse an SEC filing using sec_md_parser and save the result."""
    print("Parsing sample SEC filing...")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the sample HTML content
    html_path = os.path.join(output_dir, "sample-filing.html")
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
    markdown = parser.document_to_markdown(document)
    
    # Save the markdown content
    markdown_path = os.path.join(output_dir, "sample-filing.md")
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    
    print(f"\nMarkdown output saved to {markdown_path}")
    
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
    
    return document, markdown

def main():
    """Main function to parse a sample SEC filing."""
    try:
        # Parse the sample SEC filing
        document, markdown = parse_sec_filing(SAMPLE_HTML)
        
        # Print a sample of the markdown
        print("\nSample of markdown output (first 500 characters):")
        print(markdown[:500] + "...")
        
        print("\nProcessing complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 