"""CLI interface for SEC MD Parser."""

import os
import sys
import argparse
from pathlib import Path
import logging

from sec_md_parser import SECParser
from sec_md_parser.converter.markdown_converter import MarkdownConverter


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert SEC filings to Markdown or analyze their structure."
    )
    
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging output"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Parser command
    parser_cmd = subparsers.add_parser(
        "parse", help="Parse a SEC filing HTML file into a structured document"
    )
    parser_cmd.add_argument(
        "input_file", type=str, help="Path to the SEC filing HTML file"
    )
    parser_cmd.add_argument(
        "-o", "--output", type=str, help="Output file path for the parsed document (JSON)"
    )
    
    # Convert command
    convert_cmd = subparsers.add_parser(
        "convert", help="Convert a SEC filing HTML file to Markdown"
    )
    convert_cmd.add_argument(
        "input_file", type=str, help="Path to the SEC filing HTML file"
    )
    convert_cmd.add_argument(
        "-o", "--output", type=str, help="Output Markdown file path"
    )
    convert_cmd.add_argument(
        "--no-xbrl", action="store_true", 
        help="Exclude XBRL metadata from the Markdown output"
    )
    convert_cmd.add_argument(
        "--no-financial-metadata", action="store_true", 
        help="Exclude financial metadata from the Markdown output"
    )
    
    # Analyze command
    analyze_cmd = subparsers.add_parser(
        "analyze", help="Analyze a SEC filing HTML file and extract key information"
    )
    analyze_cmd.add_argument(
        "input_file", type=str, help="Path to the SEC filing HTML file"
    )
    analyze_cmd.add_argument(
        "-o", "--output", type=str, help="Output file path for analysis results (JSON)"
    )
    analyze_cmd.add_argument(
        "--tables-only", action="store_true", 
        help="Extract only tables from the document"
    )
    
    return parser.parse_args()


def main() -> int:
    """Run the CLI application."""
    args = parse_arguments()
    setup_logging(args.verbose)
    
    # Get the logger
    logger = logging.getLogger(__name__)
    
    if not args.command:
        logger.error("No command specified. Use --help for usage information.")
        return 1
    
    # Check if input file exists
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input_file}")
        return 1
    
    try:
        # Initialize parser
        parser = SECParser()
        
        if args.command == "parse":
            # Parse the document
            with open(input_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            document = parser.parse_from_html(html_content)
            
            # Output the document
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(document.to_json())
                
                logger.info(f"Parsed document saved to {args.output}")
            else:
                # Print to stdout
                print(document.to_json())
            
        elif args.command == "convert":
            # Parse the document
            with open(input_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            document = parser.parse_from_html(html_content)
            
            # Convert to Markdown
            converter = MarkdownConverter()
            markdown = converter.convert(
                document.document_tree,
                include_xbrl=not args.no_xbrl,
                include_financial_metadata=not args.no_financial_metadata
            )
            
            # Output the Markdown
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown)
                
                logger.info(f"Markdown document saved to {args.output}")
            else:
                # Print to stdout
                print(markdown)
        
        elif args.command == "analyze":
            # Parse the document
            with open(input_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            document = parser.parse_from_html(html_content)
            
            # Analyze the document
            if args.tables_only:
                # Extract only tables
                tables = document.extract_tables()
                
                # Output the tables
                if args.output:
                    output_path = Path(args.output)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    import json
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(tables, f, indent=2)
                    
                    logger.info(f"Table analysis saved to {args.output}")
                else:
                    # Print to stdout
                    import json
                    print(json.dumps(tables, indent=2))
            else:
                # General analysis
                analysis = document.analyze()
                
                # Output the analysis
                if args.output:
                    output_path = Path(args.output)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    import json
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(analysis, f, indent=2)
                    
                    logger.info(f"Document analysis saved to {args.output}")
                else:
                    # Print to stdout
                    import json
                    print(json.dumps(analysis, indent=2))
    
    except Exception as e:
        logger.error(f"Error processing file {args.input_file}: {str(e)}")
        if args.verbose:
            import traceback
            logger.error(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 