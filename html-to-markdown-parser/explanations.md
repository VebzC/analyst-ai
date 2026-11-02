## exhibit_handler.py

### Purpose
This module is responsible for handling and processing exhibits (financial documents) through the HTML to Markdown conversion pipeline.

### Functions and Classes

#### `process_exhibit(html_content: str, config: Config) -> str`
- **Inputs**: HTML content as string, configuration object
- **Outputs**: Markdown representation of the exhibit
- **Logic**: 
  - Cleans the HTML content
  - Builds a semantic tree using `build_semantic_tree` from parser.py
  - Renders the tree to Markdown using `render_tree_to_markdown` from parser.py

### Key Decisions
1. **Separation of Concerns**: This module focuses solely on the exhibit handling logic, delegating the parsing and rendering to the parser module.
2. **Configuration-based Processing**: Uses a configuration object to control aspects of the processing.

### Best Practices
- **Error Handling**: Robust error handling to deal with malformed HTML
- **Logging**: Comprehensive logging of the processing steps

## converter.py

### Purpose
This module provides the main interface for converting HTML documents to Markdown format.

### Functions and Classes

#### `convert_html_to_markdown(html_content: str, config: Config = None) -> str`
- **Inputs**: HTML content as string, optional configuration object
- **Outputs**: Markdown formatted string
- **Logic**: 
  - Creates a default config if none is provided
  - Delegates to the appropriate handler based on content type
  - Post-processes the output for consistency

#### `convert_file(input_path: str, output_path: str, config: Config = None) -> None`
- **Inputs**: Path to input HTML file, path to output Markdown file, optional configuration object
- **Outputs**: None (writes to file)
- **Logic**: 
  - Reads the HTML content from the input file
  - Converts it to Markdown using `convert_html_to_markdown`
  - Writes the result to the output file

### Key Decisions
1. **Handler Pattern**: Uses specialized handlers for different types of content.
2. **Default Configuration**: Provides sensible defaults while allowing custom configuration.

### Best Practices
- **Input Validation**: Checks for valid inputs before processing
- **Resource Management**: Ensures proper closing of file handles
- **Error Propagation**: Clear error messages when conversion fails

## http_utils.py

### Purpose
This module provides utilities for HTTP operations, particularly for fetching HTML content from URLs.

### Functions and Classes

#### `fetch_html(url: str, headers: dict = None, timeout: int = 10) -> str`
- **Inputs**: URL to fetch, optional headers dictionary, optional timeout in seconds
- **Outputs**: HTML content as string
- **Logic**: 
  - Makes an HTTP GET request to the specified URL
  - Handles various error cases (timeout, connection error, etc.)
  - Returns the response content as string

### Key Decisions
1. **Timeout Handling**: Implements a default timeout to prevent hanging on slow connections.
2. **Custom Headers**: Allows customization of request headers for compatibility with different sites.

### Best Practices
- **Exception Handling**: Specific exception handling for different network errors
- **User-Agent Rotation**: Optional rotation of user agents to prevent blocking
- **Response Validation**: Checks for valid HTML response before returning

## config.py

### Purpose
This module defines configuration options for the HTML to Markdown conversion process.

### Functions and Classes

#### `class Config`
- **Purpose**: Holds configuration options for the conversion process
- **Attributes**:
  - `table_max_rows`: Maximum number of rows to include in Markdown tables
  - `skip_noise_rows`: Whether to skip rows that likely contain noise
  - `normalize_tables`: Whether to normalize table cell counts
  - `line_break_preservation`: How to handle line breaks in cells
  - `heading_style`: Style for Markdown headings (e.g., '#' vs '==')
  - `log_level`: Logging level for the conversion process

#### `load_config(path: str) -> Config`
- **Inputs**: Path to a JSON configuration file
- **Outputs**: Config object
- **Logic**: 
  - Reads the JSON file
  - Validates the configuration values
  - Creates and returns a Config object

### Key Decisions
1. **Immutable Configuration**: Config objects are immutable after creation to prevent unexpected changes.
2. **Validation on Load**: Configuration values are validated when loaded to catch errors early.

### Best Practices
- **Defaults**: Sensible defaults for all configuration options
- **Validation**: Type and value validation for all options
- **Documentation**: Clear documentation of each option's purpose and valid values

## ingestor.py

### Purpose
This module handles the ingestion of HTML content from various sources (files, URLs, strings).

### Functions and Classes

#### `ingest_html(source: Union[str, Path, URL], config: Config = None) -> str`
- **Inputs**: Source (can be a file path, URL, or HTML string), optional configuration object
- **Outputs**: HTML content as string
- **Logic**: 
  - Detects the source type
  - Delegates to appropriate method for loading content
  - Returns the raw HTML

### Key Decisions
1. **Source Type Detection**: Automatically detects whether the source is a file, URL, or raw HTML.
2. **Unified Interface**: Provides a single entry point for all ingestion needs.

### Best Practices
- **Encoding Handling**: Properly handles different text encodings
- **Large File Support**: Efficiently processes large HTML files
- **Caching**: Optional caching of remote content to reduce network requests

## parser.py

### Purpose
This module provides functionality for parsing HTML documents and converting them to Markdown format. It handles document structure elements like headings, paragraphs, and tables, as well as inline formatting like bold and italic text.

### Functions and Classes

#### `class Node`
- **Purpose**: Represents a node in the semantic tree of the document.
- **Attributes**:
  - `tag`: The HTML tag name (e.g., 'h1', 'p', 'table')
  - `content`: Text content of the node
  - `children`: List of child nodes
  - `level`: Nesting level (useful for headings)
  - `metadata`: Additional information about the node

#### `clean_html(html: str) -> str`
- **Inputs**: Raw HTML string
- **Outputs**: Cleaned HTML with scripts, styles, noscript tags, and comments removed
- **Logic**: Uses BeautifulSoup to parse and clean the HTML

#### `build_semantic_tree(soup: BeautifulSoup) -> Node`
- **Inputs**: BeautifulSoup object of parsed HTML
- **Outputs**: Root Node containing a semantic tree representation
- **Logic**: 
  - Identifies headings, paragraphs, and tables in the HTML
  - Creates a corresponding Node structure
  - Preserves inline styling (bold, italic)

#### `render_tree_to_markdown(root: Node) -> str`
- **Inputs**: Root Node of a semantic tree
- **Outputs**: Markdown formatted string
- **Logic**:
  - Traverses the tree and renders each node type
  - Handles headings, paragraphs, and tables with specialized rendering

#### `_render_table_to_markdown(table_node: Node) -> str`
- **Inputs**: Table Node
- **Outputs**: Markdown formatted table string
- **Logic**:
  - Normalizes rows with inconsistent cell counts
  - Skips noise rows with only one non-empty cell
  - Always includes header separator row
  - Handles line breaks in cells using `<br>` tags
  - Truncates tables with more than 50 rows
  - Logs statistics about rows and columns processed

#### `_render_inline_formatting(nodes: List[Node]) -> str`
- **Inputs**: List of Node objects with formatting metadata
- **Outputs**: Markdown string with inline formatting applied
- **Logic**: Applies bold and italic formatting using Markdown syntax

### Key Decisions

1. **Table Rendering Improvements**:
   - **Row Normalization**: All rows are normalized to have the same number of cells as the longest row, filling empty cells with empty strings
   - **Noise Filtering**: Rows with only one non-empty cell are skipped as they're likely noise or formatting artifacts
   - **Header Handling**: If no `<th>` tags are present, the first row is treated as the header
   - **Line Break Preservation**: Newlines in table cells are converted to `<br>` tags for better readability
   - **Table Truncation**: Large tables (>50 rows) are truncated with a message indicating the number of hidden rows

2. **Semantic Tree Structure**: Uses a tree structure to represent the document semantics rather than directly converting HTML, which allows for better handling of document structure.

3. **Progressive Cleaning**: Cleans the HTML before parsing to remove irrelevant elements that might interfere with conversion.

### Best Practices
- **Strong Logging**: Comprehensive logging of table processing, including rows skipped, truncation, and final statistics
- **Error Tolerance**: Handles malformed tables gracefully (unbalanced rows, missing headers)
- **Output Readability**: Focuses on producing clean, readable Markdown that preserves the original content structure
- **Type Annotations**: Consistent use of type hints for better documentation and IDE support
- **Unit Testing**: Comprehensive test coverage for table rendering edge cases

## markdown_cleaner.py

### Purpose
This module provides functionality for cleaning and standardizing Markdown content after it has been generated. It addresses common issues in converted Markdown such as excess whitespace, malformed lists, and inconsistent table formatting.

### Functions and Classes

#### `clean_markdown(markdown: str) -> str`
- **Inputs**: Raw Markdown content as string
- **Outputs**: Cleaned and standardized Markdown string
- **Logic**: 
  - Removes trailing whitespace from each line
  - Replaces 3+ consecutive newlines with 2 newlines
  - Removes purely decorative lines (-, *, |) with no content
  - Collapses malformed list items (e.g., "- " followed by content on next line)
  - Ensures tables don't have trailing pipes unless they contain content
  - Inserts 2 newlines after headings for better readability
  - Removes repeated boilerplate lines (such as footers that appear multiple times)

### Key Decisions

1. **List Item Handling**:
   - Detects list items with markers (-, *, +) on a line by themselves
   - Combines them with the content on the next line to form proper list items
   - Preserves the original list marker character

2. **Table Formatting**:
   - Processes tables as coherent blocks rather than line by line
   - Identifies table start/end by looking for lines containing pipe characters
   - Removes trailing pipe characters only when they don't enclose actual content
   - Preserves table structure while improving readability

3. **Boilerplate Detection**:
   - Identifies lines that appear 3 or more times as potential boilerplate
   - Keeps only the first instance of each repeated line
   - Uses stripped line comparison to handle inconsistent indentation
   - Applies a minimum length threshold (>5 chars) to avoid treating short repeated lines as boilerplate

4. **Whitespace Normalization**:
   - Removes trailing whitespace while preserving indentation
   - Normalizes multiple consecutive blank lines to at most 2 blank lines
   - Ensures proper spacing around headings for improved readability

### Best Practices
- **Input Validation**: Handles empty or None input gracefully
- **Logging**: Provides debug logging for removed decorative lines
- **Regular Expressions**: Uses targeted regex patterns for specific transformations
- **Efficient Processing**: Processes the document in logical chunks (tables, list items) for better context-aware cleaning
- **Line-by-line Handling**: Processes most transformations line by line for memory efficiency
- **Comprehensive Testing**: Includes tests for all cleaning features, both individually and in combination

## HTML File to Markdown Conversion Utility

### Files

- **convert_file.py**: Implements the HTML file to Markdown conversion utility.

### Functions

- `convert_html_file_to_markdown(html_file_path, output_file_path=None)`: Takes an HTML file path, reads its content, converts it to Markdown using the existing `convert_html_to_markdown` function, and optionally saves the result to a file.

### Usage

The utility can be used both as a function import and as a command-line tool:

```python
# As a function import
from convert_file import convert_html_file_to_markdown

# Convert HTML file to Markdown
markdown = convert_html_file_to_markdown("path/to/file.html")

# Convert and save to a file
convert_html_file_to_markdown("path/to/file.html", "output.md")
```

**Command line usage**:
```bash
python convert_file.py path/to/file.html -o output.md
```

### Integration with Existing Codebase

This utility builds on the existing HTML to Markdown conversion pipeline, which includes:
- HTML cleaning and normalization
- Semantic tree building 
- Markdown rendering
- Table formatting and handling
- Markdown post-processing and cleaning

The conversion process handles tables, lists, headings, and other HTML elements, applying all the existing formatting rules and standards implemented in the core conversion functions.