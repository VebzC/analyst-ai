# SEC MD Parser - Technical Documentation

## Overview

SEC MD Parser is a Python library for parsing SEC filings from HTML/XBRL documents into structured formats including Markdown. The library extracts both textual content and XBRL (eXtensible Business Reporting Language) data, allowing users to analyze financial reports comprehensively.

## Key Components

### Parser

**File: `sec_md_parser/__init__.py`**
- Purpose: Main entry point for the library
- Key components:
  - `SECParser`: Main parser class for SEC filings
    - `parse_from_html()`: Parses HTML content into a structured `SECDocument`
    - `document_to_markdown()`: Converts a `SECDocument` to Markdown
    - `html_to_markdown()`: One-step conversion from HTML to Markdown

### Models

**File: `sec_md_parser/models/document.py`**
- Purpose: Defines the core data models for representing SEC documents
- Key components:
  - `XBRLFact`: Represents a single XBRL fact (financial data point)
  - `FinancialMetric`: Represents a processed financial metric
  - `DocumentNode`: Represents a node in the document tree (section, paragraph, table, etc.)
  - `DocumentTree`: Represents the hierarchical structure of a document
  - `SECDocument`: Represents a complete SEC filing with metadata, document tree, and XBRL facts

### XBRL Metadata Extraction

**File: `sec_md_parser/parser/metadata/xbrl_extractor.py`**
- Purpose: Extracts detailed XBRL metadata from HTML/XBRL documents
- Key components:
  - `XbrlMetadataExtractor`: Extracts XBRL metadata including:
    - Namespaces and taxonomy references
    - Context definitions (entities, periods, segments)
    - Unit definitions
    - Facts (financial data points)
    - Calculation and presentation relationships
    - Custom taxonomy extensions

### Table Analysis

**File: `sec_md_parser/analyzer/table_analyzer.py`**
- Purpose: Analyzes tables in SEC filings, extracting structure and linking XBRL facts
- Key components:
  - `TableAnalyzer`: Analyzes tables in the document
    - `analyze_table()`: Analyzes a table element, extracting its structure and XBRL facts
    - `_extract_table_structure()`: Extracts the structure of a table (rows, cells, etc.)
    - `_find_xbrl_facts_for_cell()`: Associates XBRL facts with table cells

### Document Building

**File: `sec_md_parser/builder/document_builder.py`**
- Purpose: Builds a structured document tree from HTML content
- Key components:
  - `DocumentTreeBuilder`: Builds a document tree from HTML content
    - `build_from_html()`: Builds a document tree from HTML content
    - `_process_table()`: Processes a table element into a structured node
    - `_associate_xbrl_facts_with_sections()`: Associates XBRL facts with document sections

### Markdown Conversion

**File: `sec_md_parser/converter/markdown_converter.py`**
- Purpose: Converts document trees to Markdown
- Key components:
  - `MarkdownConverter`: Converts document trees to Markdown
    - `convert()`: Converts a document tree to Markdown
    - `_convert_table()`: Converts a table node to Markdown
    - `_convert_structured_table()`: Converts a structured table to Markdown
    - `_format_xbrl_facts()`: Formats XBRL facts as Markdown tables

### Enhanced Markdown Generation

**File: `sec_md_parser/converter/markdown_generator.py`**
- Purpose: Provides standalone functions for generating enhanced Markdown from document trees
- Key components:
  - `generate_markdown_from_tree()`: Recursively generates Markdown from a document tree node
  - `generate_markdown_table()`: Generates a Markdown table from table structure data
  - `generate_markdown_document()`: Creates a complete Markdown document with summaries and metadata

### LLM Integration

**File: `sec_md_parser/llm/llm_integration.py`**
- Purpose: Provides functions for optimizing SEC filing data for language model consumption
- Key components:
  - `generate_llm_optimized_output()`: Creates an optimized data structure for LLM processing
  - `simplify_tree_for_llm()`: Simplifies the document tree for efficient LLM consumption
  - `extract_key_metrics()`: Extracts key financial metrics from financial statements
  - `generate_table_of_contents()`: Creates a structured table of contents
  - `generate_section_summaries()`: Generates summaries for document sections
  - `convert_to_qa_format()`: Converts document content to question-answer pairs for LLM fine-tuning

### Financial Detection

**File: `sec_md_parser/analyzer/financial_detector.py`**
- Purpose: Detects financial sections in documents (balance sheet, income statement, etc.)
- Key components:
  - `FinancialDetector`: Detects financial sections in documents
    - `detect_financial_sections()`: Identifies financial sections in a document tree
    - `_is_financial_section()`: Determines if a section contains financial data

### Financial Statement Identification

**File: `sec_md_parser/analyzer/financial_statement_identifier.py`**
- Purpose: Identifies and categorizes specific financial statements in SEC filings
- Key components:
  - `FinancialStatementIdentifier`: System for identifying and categorizing financial statements
    - `identify_statement_type()`: Identifies the type of financial statement for a given table node
    - `_identify_by_table_content()`: Analyzes table content to determine statement type
    - `process_document_tree()`: Processes entire document tree to categorize all financial tables

### Calculation Relationship Handling

**File: `sec_md_parser/analyzer/calculation_handler.py`**
- Purpose: Detects and preserves calculation relationships in financial statements
- Key components:
  - `CalculationRelationshipHandler`: Handles calculation relationships in financial statements
    - `analyze_financial_statement()`: Analyzes a financial statement to detect calculations
    - `_extract_from_calculation_linkbase()`: Extracts calculations from XBRL metadata
    - `_detect_from_table_structure()`: Detects calculations by analyzing table structure
    - `_apply_statement_rules()`: Applies financial statement-specific calculation rules
    - `get_calculation_hierarchy()`: Builds a hierarchy of calculations showing parent-child relationships

### CLI Interface

**File: `sec_md_parser/cli.py`**
- Purpose: Command-line interface for the library
- Key components:
  - `main()`: Entry point for the CLI
  - Commands:
    - `parse`: Parse a SEC filing into a structured document
    - `convert`: Convert a SEC filing to Markdown
    - `analyze`: Analyze a SEC filing and extract key information
  - Options:
    - `--no-xbrl`: Exclude XBRL metadata from Markdown output
    - `--no-financial-metadata`: Exclude financial metadata from Markdown output

## XBRL Data Handling

The SEC MD Parser handles XBRL data through several steps:

1. **Extraction**: The `XbrlMetadataExtractor` extracts XBRL facts from the HTML/XBRL document.
2. **Association**: XBRL facts are associated with relevant sections and tables in the document.
3. **Presentation**: When converting to Markdown, XBRL facts can be included in collapsible sections.

### XBRL Fact Structure

XBRL facts are represented as objects with the following attributes:
- `name`: The name of the fact (e.g., "us-gaap:Revenue")
- `value`: The value of the fact
- `context_ref`: Reference to the context (period, entity, etc.)
- `unit_ref`: Reference to the unit (USD, shares, etc.)
- `decimals`: Decimal precision of the value
- `period`: The period the fact applies to
- Additional attributes: precision, ID, etc.

## Table Handling

Tables are processed through several steps:

1. **Extraction**: The HTML table structure is extracted from the document.
2. **Analysis**: The `TableAnalyzer` analyzes the table structure, identifying headers, rows, cells, etc.
3. **XBRL Association**: XBRL facts are associated with table cells based on content matching.
4. **Conversion**: Tables are converted to Markdown format, preserving structure and XBRL associations.

### Table Structure

Tables are represented as nodes with the following structure:
- `table`: The root table node
  - `table_caption`: Table caption
  - `table_header`: Table header section
    - `table_header_row`: Header row
      - `table_header_cell`: Header cell
  - `table_body`: Table body section
    - `table_body_row`: Body row
      - `table_body_cell`: Body cell

## Usage Examples

### Basic Usage

```python
from sec_md_parser import SECParser

# Initialize parser
parser = SECParser()

# Parse from HTML
with open("10-k.html", "r") as f:
    html_content = f.read()

document = parser.parse_from_html(html_content)

# Convert to Markdown
markdown = document.to_markdown(include_xbrl=True, include_financial_metadata=True)

# Save to file
with open("10-k.md", "w") as f:
    f.write(markdown)
```

### Using the CLI

```bash
# Convert a filing to Markdown with XBRL data
python -m sec_md_parser convert 10-k.html -o 10-k.md

# Convert a filing to Markdown without XBRL data
python -m sec_md_parser convert 10-k.html -o 10-k-no-xbrl.md --no-xbrl

# Analyze a filing
python -m sec_md_parser analyze 10-k.html -o analysis.json

# Extract tables only
python -m sec_md_parser analyze 10-k.html -o tables.json --tables-only
```

## Advanced Features

### Financial Section Detection

The library can detect financial sections in SEC filings, such as:
- Balance sheets
- Income statements
- Cash flow statements
- Notes to financial statements

For each section, relevant XBRL facts are associated, allowing for analysis of financial data in context.

### Financial Statement Identification

The library includes a sophisticated financial statement identification system that can categorize tables as specific financial statement types:

- **Income statements**: Also known as statements of operations or earnings
- **Balance sheets**: Also known as statements of financial position
- **Cash flow statements**: Detailing operating, investing, and financing activities
- **Equity statements**: Showing changes in stockholders' equity

The identification is performed using multiple strategies:
1. Title/caption matching using common naming patterns
2. XBRL concept matching using typical concepts found in each statement type
3. Content analysis of table headers and first column to identify financial indicators

This enables automated extraction and analysis of specific financial statements from complex SEC filings.

### Calculation Relationship Handling

The library includes a sophisticated system for detecting and preserving calculation relationships in financial statements:

- **XBRL calculation linkbase**: Extracts calculation relationships from the XBRL calculation linkbase when available
- **Table structure analysis**: Detects calculations by analyzing the structure of financial statement tables
- **Statement-specific rules**: Applies financial statement-specific rules to enhance detected calculations
- **Calculation hierarchy**: Builds hierarchical structures showing parent-child relationships among calculations

The system supports different financial statement types with specialized calculation patterns:
- **Income statements**: Revenue - Cost of Sales = Gross Profit, etc.
- **Balance sheets**: Total Assets = Current Assets + Non-Current Assets, etc.
- **Cash flow statements**: Net Cash Change = Operating + Investing + Financing, etc.

Calculations detected are stored in the document metadata and can be used for:
- Validating financial data consistency
- Cross-checking XBRL and table data
- Generating financial models and analytics
- Enhancing financial statement visualization

### Enhanced Markdown Generation

The library includes a powerful markdown generation system with enhanced features:

- **Document tree traversal**: Recursively processes document nodes to generate structured Markdown
- **Metadata handling**: Includes document metadata in YAML or JSON format
- **Table formatting**: Converts complex table structures to Markdown tables with proper alignment
- **Financial metadata integration**: Includes financial statement types and calculation relationships
- **XBRL fact annotations**: Associates XBRL facts with corresponding text using custom annotations
- **Collapsible sections**: Creates collapsible details/summary sections for complex metadata

The enhanced Markdown generator supports several output formats and options:
- **Full document**: Complete document with all metadata and content
- **Financial focus**: Emphasis on financial statements with calculation relationships
- **XBRL integration**: Embedding XBRL facts directly with the content they apply to

This functionality can be used to generate documentation, reports, and analysis from SEC filings.

### LLM Integration Features

The library includes specialized features for optimizing SEC filings for consumption by language models:

- **Data restructuring**: Transforms complex document trees into simplified formats better suited for LLMs
- **Key metric extraction**: Automatically identifies and extracts important financial metrics from statements
- **Table of contents generation**: Creates structured navigation for large documents
- **Section summarization**: Generates concise summaries of document sections
- **QA pair generation**: Converts document content into question-answer pairs for fine-tuning LLMs

The LLM integration supports several use cases:
- **Document summarization**: Extracting the most important information from lengthy filings
- **Financial analysis**: Identifying key metrics and relationships for model-based analysis
- **Information retrieval**: Enabling precise querying of financial information
- **LLM fine-tuning**: Creating training data for specialized financial LLMs

Example format:
```json
{
  "document_metadata": {
    "title": "Annual Report",
    "filing_type": "10-K",
    "entity": "Example Corp",
    "filing_date": "2023-03-15"
  },
  "key_metrics": {
    "income_statement": {
      "revenue": 1000000000,
      "net_income": 100000000
    }
  },
  "table_of_contents": [
    {"title": "Business Description", "id": "section_1", "level": 1},
    {"title": "Financial Statements", "id": "section_2", "level": 1}
  ]
}
```

### Table Structure Analysis

Tables are analyzed to extract structured data, including:
- Captions and headers
- Row and column structures
- Cell content and formatting
- XBRL facts associated with cells

## Implementation Details

### XBRL Fact Matching

XBRL facts are matched to document sections and table cells through several techniques:
1. **Direct matching**: Finding inline XBRL tags within the content
2. **Content matching**: Matching fact names or values to text content
3. **Context matching**: Using context information to associate facts with relevant sections
4. **Structural analysis**: Using document structure to infer relationships

### Table Processing

Tables are processed using the following steps:
1. **Structure extraction**: Extracting rows, cells, headers, etc.
2. **Cell content parsing**: Extracting text, numeric values, and formatting
3. **XBRL association**: Linking XBRL facts to table cells
4. **Structured representation**: Creating a structured representation of the table

## Future Enhancements

1. **Improved XBRL context matching**: Better handling of complex XBRL contexts and dimensions
2. **Enhanced financial analysis**: Calculating financial ratios and metrics from XBRL data
3. **Document comparison**: Comparing multiple SEC filings to identify changes over time
4. **Interactive visualization**: Generating interactive visualizations of financial data 