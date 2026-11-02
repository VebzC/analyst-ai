# SEC MD Parser

A Python library for converting HTML SEC filings with XBRL data to Markdown format.

## Features

- Parses SEC filings containing HTML and XBRL data
- Converts complex financial documents to clean Markdown format
- Preserves semantic information and document structure
- Handles complex nested tables and financial statements
- Generates hierarchical document tree structure for LLM processing
- Preserves XBRL metadata for enhanced analysis

## Installation

```bash
pip install sec-md-parser
```

Or install from source:

```bash
git clone https://github.com/yourusername/sec-md-parser.git
cd sec-md-parser
pip install -e .
```

Development setup:

```bash
pip install -e ".[dev]"
```

## Usage

```python
from sec_md_parser import SECParser

# Parse a filing from a URL
parser = SECParser()
result = parser.parse_from_url("https://www.sec.gov/Archives/example-filing.htm")

# Convert to markdown
markdown_text = result.to_markdown()

# Get document hierarchical structure
document_tree = result.get_document_tree()

# Access XBRL data
xbrl_facts = result.get_xbrl_facts()
```

## Documentation

Full documentation is available at [docs/index.md](docs/index.md).

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Run linters
flake8 src tests
mypy src tests

# Format code
black src tests
isort src tests
```

## License

MIT
