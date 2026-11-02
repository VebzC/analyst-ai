# SEC Markdown Parser Tools

A collection of tools for parsing SEC EDGAR filings, extracting XBRL data, and converting to markdown with financial analysis.

## Overview

This project provides tools to:

1. Parse SEC EDGAR HTML filings
2. Extract XBRL financial data
3. Convert to clean, structured markdown
4. Generate financial analysis based on XBRL data
5. Handle SEC.gov connection issues with robust caching

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/sec-md-parser-tools.git
cd sec-md-parser-tools
pip install -r requirements.txt
```

## Quick Start

### Process a SEC filing from URL:

```bash
python real_sec_parser.py --url https://www.sec.gov/Archives/edgar/data/...
```

### Process a local HTML file:

```bash
python real_sec_parser.py --file path/to/filing.html
```

### Generate enhanced analysis:

```bash
python test_sec_enhanced.py
```

## Tools

### 1. real_sec_parser.py

A robust tool for parsing SEC filings that can:
- Download filings from SEC.gov with proper user agent
- Cache downloaded filings to prevent repeated downloads
- Extract XBRL data and metadata
- Generate enhanced markdown with financial analysis
- Handle connection issues gracefully

**Options:**
```
--url URL               URL of SEC filing to parse
--file FILE             Local HTML file to parse
--no-cache              Disable caching of SEC filings
--output-prefix PREFIX  Prefix for output files
--verbose               Enable verbose logging
```

### 2. test_sec_enhanced.py

A test script that demonstrates enhanced markdown generation with:
- Detailed XBRL data tables
- Financial analysis including:
  - Revenue growth
  - Profit margin
  - Year-over-year comparisons

### 3. test_sec_sample.py

A simple test script using a sample SEC filing to demonstrate basic functionality.

## Output Files

The tools generate several output files:

1. **Enhanced Markdown** - A markdown file containing the structured SEC filing with XBRL data and financial analysis
2. **XBRL JSON** - A JSON file containing all extracted XBRL facts
3. **Metadata JSON** - A JSON file with filing metadata

## XBRL Data Analysis

The parser extracts XBRL facts from SEC filings, which include:

- Financial metrics (Revenue, Net Income, EPS, etc.)
- Context references (time periods)
- Units and precision information

## Financial Analysis

The enhanced output includes automatic financial analysis:

- Revenue growth calculations
- Profit margin analysis
- Quarter-over-quarter comparisons
- Year-over-year growth rates

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- sec_md_parser

## Handling SEC.gov Restrictions

SEC.gov restricts automated access, so the tools include:

1. Proper user agent headers with contact information
2. Robust caching to minimize requests
3. Fallback to local files when SEC.gov is unavailable

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 