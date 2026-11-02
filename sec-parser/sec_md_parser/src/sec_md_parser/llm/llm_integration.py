"""LLM integration features for SEC filings."""

from typing import Dict, List, Optional, Any, Union
import re
import json
from collections import defaultdict

from sec_md_parser.models.document import DocumentNode, DocumentTree


def simplify_tree_for_llm(document_tree):
    """
    Create a simplified version of the document tree for LLM processing.
    
    Args:
        document_tree: The document tree to simplify
        
    Returns:
        Simplified tree structure optimized for LLM consumption
    """
    if not document_tree or not hasattr(document_tree, 'root'):
        return {"error": "Invalid document tree"}
    
    # Start with the root node
    return _simplify_node(document_tree.root)


def _simplify_node(node, max_depth=5, current_depth=0):
    """
    Recursively simplify a node and its children.
    
    Args:
        node: The node to simplify
        max_depth: Maximum depth to traverse
        current_depth: Current depth in the recursion
        
    Returns:
        Simplified node structure
    """
    if not node or current_depth > max_depth:
        return None
    
    # Create basic node info
    simplified = {
        "type": getattr(node, 'type', None) or getattr(node, 'node_type', 'unknown'),
        "id": getattr(node, 'id', None)
    }
    
    # Add content if available
    content = getattr(node, 'content', None)
    if content:
        # Truncate very long content to avoid overwhelming the LLM
        if len(content) > 1000:
            simplified["content"] = content[:997] + "..."
        else:
            simplified["content"] = content
    
    # Add title if available
    title = getattr(node, 'title', None)
    if title:
        simplified["title"] = title
    
    # Add financial statement type if available
    metadata = getattr(node, 'metadata', {})
    if metadata and 'financial_statement_type' in metadata:
        simplified["financial_statement_type"] = metadata['financial_statement_type']
    
    # Add XBRL facts count if available
    xbrl_facts = getattr(node, 'xbrl_facts', [])
    if xbrl_facts:
        simplified["xbrl_facts_count"] = len(xbrl_facts)
        
        # Include a sample of XBRL facts (maximum 5)
        if len(xbrl_facts) > 0:
            sample_facts = []
            for fact in xbrl_facts[:5]:
                fact_info = {
                    "name": fact.name if hasattr(fact, 'name') else str(fact)[:50],
                    "value": fact.value if hasattr(fact, 'value') else None
                }
                sample_facts.append(fact_info)
            simplified["xbrl_facts_sample"] = sample_facts
    
    # Recursively process children
    children = getattr(node, 'children', [])
    if children:
        simplified_children = []
        for child in children:
            simplified_child = _simplify_node(child, max_depth, current_depth + 1)
            if simplified_child:
                simplified_children.append(simplified_child)
        
        if simplified_children:
            simplified["children"] = simplified_children
    
    return simplified


def extract_key_metrics(document_tree):
    """
    Extract key financial metrics from the document tree.
    
    Args:
        document_tree: The document tree to extract metrics from
        
    Returns:
        Dictionary of key financial metrics
    """
    metrics = {
        "income_statement": {},
        "balance_sheet": {},
        "cash_flow": {},
        "ratios": {}
    }
    
    if not document_tree or not hasattr(document_tree, 'root'):
        return metrics
    
    # Find all tables with financial statement types
    financial_tables = {}
    
    def find_financial_tables(node):
        if not node:
            return
        
        # Check if this is a table with a financial statement type
        if hasattr(node, 'type') and node.type == 'table' and hasattr(node, 'metadata'):
            statement_type = node.metadata.get('financial_statement_type')
            if statement_type:
                if statement_type not in financial_tables:
                    financial_tables[statement_type] = []
                financial_tables[statement_type].append(node)
        
        # Process children
        for child in getattr(node, 'children', []):
            find_financial_tables(child)
    
    # Traverse the tree to find financial tables
    find_financial_tables(document_tree.root)
    
    # Common financial metrics to look for
    metric_patterns = {
        "income_statement": {
            "revenue": [r"revenue", r"sales", r"net sales"],
            "gross_profit": [r"gross profit"],
            "operating_income": [r"operating income", r"income from operations"],
            "net_income": [r"net income", r"net earnings", r"net profit"],
            "earnings_per_share": [r"earnings per share", r"diluted earnings per share", r"eps"]
        },
        "balance_sheet": {
            "total_assets": [r"total assets"],
            "total_liabilities": [r"total liabilities"],
            "total_equity": [r"total equity", r"stockholders equity", r"shareholders equity"],
            "cash_and_equivalents": [r"cash and cash equivalents", r"cash and equivalents"]
        },
        "cash_flow": {
            "operating_cash_flow": [r"net cash .*? operating activities", r"cash from operations"],
            "investing_cash_flow": [r"net cash .*? investing activities"],
            "financing_cash_flow": [r"net cash .*? financing activities"],
            "free_cash_flow": [r"free cash flow"]
        }
    }
    
    # Extract metrics from each type of financial statement
    for statement_type, tables in financial_tables.items():
        # Skip unrecognized statement types
        if statement_type not in metrics:
            continue
        
        for table in tables:
            # Look for rows containing key metrics
            structure = getattr(table, 'metadata', {}).get('structure', [])
            if not structure:
                continue
            
            # Check each row for metrics
            for row in structure:
                if not row or len(row) < 2:
                    continue
                
                # First cell usually contains the label
                if not isinstance(row[0], dict) or 'content' not in row[0]:
                    continue
                
                label = row[0]['content'].lower().strip()
                
                # Check if this label matches any of our metric patterns
                for metric_name, patterns in metric_patterns.get(statement_type, {}).items():
                    if any(re.search(pattern, label, re.IGNORECASE) for pattern in patterns):
                        # Extract value (assume the second column is the most recent period)
                        value_cell = row[1] if len(row) > 1 else None
                        if isinstance(value_cell, dict) and 'content' in value_cell:
                            value = value_cell['content']
                            # Clean up the value
                            clean_value = re.sub(r'[^\d.-]', '', value)
                            try:
                                metrics[statement_type][metric_name] = float(clean_value)
                            except (ValueError, TypeError):
                                metrics[statement_type][metric_name] = value
    
    # Calculate some basic financial ratios if we have the necessary metrics
    if metrics["balance_sheet"].get("total_assets") and metrics["balance_sheet"].get("total_liabilities"):
        metrics["ratios"]["debt_to_assets"] = metrics["balance_sheet"]["total_liabilities"] / metrics["balance_sheet"]["total_assets"]
    
    if metrics["income_statement"].get("net_income") and metrics["balance_sheet"].get("total_equity"):
        metrics["ratios"]["return_on_equity"] = metrics["income_statement"]["net_income"] / metrics["balance_sheet"]["total_equity"]
    
    return metrics


def generate_table_of_contents(document_tree):
    """
    Generate a table of contents from the document tree.
    
    Args:
        document_tree: The document tree to generate TOC from
        
    Returns:
        List of TOC entries with title, id, and level
    """
    toc = []
    
    if not document_tree or not hasattr(document_tree, 'root'):
        return toc
    
    # Function to extract headings from the tree
    def extract_headings(node, current_level=0):
        if not node:
            return
        
        # Check if this is a heading or section with a title
        title = None
        node_id = getattr(node, 'id', None)
        
        if hasattr(node, 'type'):
            if node.type == 'heading':
                title = getattr(node, 'content', None)
            elif node.type == 'section':
                title = getattr(node, 'title', None)
        
        # For financial statement tables, use the caption or metadata
        if getattr(node, 'type', None) == 'table' and getattr(node, 'metadata', {}).get('financial_statement_type'):
            caption_node = next((child for child in getattr(node, 'children', []) 
                              if getattr(child, 'type', None) == 'table_caption'), None)
            if caption_node and getattr(caption_node, 'content', None):
                title = caption_node.content
            elif getattr(node, 'metadata', {}).get('financial_statement_type'):
                statement_type = node.metadata['financial_statement_type']
                title = f"{statement_type.replace('_', ' ').title()}"
        
        # Add to TOC if we have a title
        if title and node_id:
            toc.append({
                "title": title,
                "id": node_id,
                "level": current_level
            })
        
        # Process children
        for child in getattr(node, 'children', []):
            extract_headings(child, current_level + 1)
    
    # Extract all headings
    extract_headings(document_tree.root)
    
    return toc


def generate_section_summaries(document_tree):
    """
    Generate summaries for main sections of the document.
    
    Args:
        document_tree: The document tree to generate summaries from
        
    Returns:
        Dictionary mapping section IDs to summary information
    """
    summaries = {}
    
    if not document_tree or not hasattr(document_tree, 'root'):
        return summaries
    
    # Function to find main sections and create summaries
    def process_sections(node, current_level=0):
        if not node:
            return
        
        node_id = getattr(node, 'id', None)
        node_type = getattr(node, 'type', None)
        
        # Process sections, headings, and financial tables
        if node_type in ['section', 'heading'] or (node_type == 'table' and 
                                                   getattr(node, 'metadata', {}).get('financial_statement_type')):
            # Get title
            title = None
            if node_type == 'heading':
                title = getattr(node, 'content', None)
            elif node_type == 'section':
                title = getattr(node, 'title', None)
            elif node_type == 'table':
                statement_type = node.metadata['financial_statement_type']
                title = statement_type.replace('_', ' ').title()
                
                # Look for caption
                caption_node = next((child for child in getattr(node, 'children', []) 
                                  if getattr(child, 'type', None) == 'table_caption'), None)
                if caption_node:
                    title = getattr(caption_node, 'content', title)
            
            if title and node_id:
                # Create summary object
                summary = {
                    "title": title,
                    "type": node_type,
                    "level": current_level
                }
                
                # Add content summary
                if node_type in ['section', 'heading']:
                    # Extract and summarize text content
                    content = _extract_section_content(node)
                    if content:
                        # If content is very long, truncate it
                        if len(content) > 500:
                            summary["content_preview"] = content[:497] + "..."
                        else:
                            summary["content_preview"] = content
                        
                        summary["word_count"] = len(content.split())
                
                # Add financial metadata for tables
                if node_type == 'table' and getattr(node, 'metadata', {}).get('financial_statement_type'):
                    summary["financial_statement_type"] = node.metadata['financial_statement_type']
                    
                    # Add information about calculation relationships if available
                    if 'calculation_relationships' in node.metadata:
                        summary["has_calculations"] = True
                        summary["calculation_count"] = len(node.metadata['calculation_relationships'])
                
                # Add XBRL facts count if available
                xbrl_facts = getattr(node, 'xbrl_facts', [])
                if xbrl_facts:
                    summary["xbrl_facts_count"] = len(xbrl_facts)
                
                summaries[node_id] = summary
        
        # Process children
        for child in getattr(node, 'children', []):
            process_sections(child, current_level + 1)
    
    # Process all sections
    process_sections(document_tree.root)
    
    return summaries


def _extract_section_content(node):
    """
    Extract text content from a section or heading node.
    
    Args:
        node: The node to extract content from
        
    Returns:
        Concatenated text content
    """
    content = []
    
    # Add this node's content if available
    if getattr(node, 'content', None):
        content.append(node.content)
    
    # Extract content from paragraph children
    for child in getattr(node, 'children', []):
        if getattr(child, 'type', None) == 'paragraph' and getattr(child, 'content', None):
            content.append(child.content)
        elif getattr(child, 'type', None) not in ['heading', 'section', 'table']:
            # Recursively extract content from non-structural nodes
            child_content = _extract_section_content(child)
            if child_content:
                content.append(child_content)
    
    return " ".join(content)


def generate_llm_optimized_output(document_tree, original_markdown):
    """
    Generate an output format specifically designed for LLM processing.
    
    Args:
        document_tree: The document tree to process
        original_markdown: The original Markdown content
        
    Returns:
        Dictionary with optimized data for LLM consumption
    """
    # Create a simplified tree representation
    simplified_tree = simplify_tree_for_llm(document_tree)
    
    # Extract key financial metrics
    key_metrics = extract_key_metrics(document_tree)
    
    # Generate table of contents
    toc = generate_table_of_contents(document_tree)
    
    # Create section summaries
    section_summaries = generate_section_summaries(document_tree)
    
    # Get metadata from the document tree
    metadata = getattr(document_tree, 'metadata', {})
    
    # Combine everything into a single output format
    result = {
        "document_metadata": {
            "title": getattr(document_tree, 'title', None),
            "filing_type": metadata.get("filing_type"),
            "entity": metadata.get("entity"),
            "filing_date": metadata.get("filing_date"),
            "reporting_periods": metadata.get("reporting_periods")
        },
        "table_of_contents": toc,
        "key_metrics": key_metrics,
        "section_summaries": section_summaries,
        "document_tree": simplified_tree,
        "full_content": original_markdown[:100000]  # Limit size of full content to avoid overwhelming LLMs
    }
    
    return result


def convert_to_qa_format(document_tree, key_metrics=None):
    """
    Convert document content to a Q&A format for fine-tuning LLMs.
    
    Args:
        document_tree: The document tree to process
        key_metrics: Optional pre-extracted key metrics
        
    Returns:
        List of question-answer pairs derived from the document
    """
    qa_pairs = []
    
    if not document_tree or not hasattr(document_tree, 'root'):
        return qa_pairs
    
    # If key metrics not provided, extract them
    if key_metrics is None:
        key_metrics = extract_key_metrics(document_tree)
    
    # Generate metadata questions
    metadata = getattr(document_tree, 'metadata', {})
    
    # Basic metadata questions
    filing_type = metadata.get("filing_type")
    if filing_type:
        qa_pairs.append({
            "question": "What type of filing is this document?",
            "answer": f"This document is a {filing_type} filing."
        })
    
    entity = metadata.get("entity")
    if entity:
        qa_pairs.append({
            "question": "What company or entity filed this document?",
            "answer": f"This document was filed by {entity}."
        })
        
        if filing_type:
            qa_pairs.append({
                "question": f"What is the {filing_type} for {entity}?",
                "answer": f"This document contains the {filing_type} for {entity}."
            })
    
    filing_date = metadata.get("filing_date")
    if filing_date:
        qa_pairs.append({
            "question": "When was this document filed?",
            "answer": f"This document was filed on {filing_date}."
        })
    
    # Financial metric questions
    if key_metrics:
        # Income statement metrics
        for metric, value in key_metrics.get("income_statement", {}).items():
            metric_name = metric.replace("_", " ")
            qa_pairs.append({
                "question": f"What is the {metric_name}?",
                "answer": f"The {metric_name} is {value}."
            })
            
            if entity:
                qa_pairs.append({
                    "question": f"What is {entity}'s {metric_name}?",
                    "answer": f"{entity}'s {metric_name} is {value}."
                })
        
        # Balance sheet metrics
        for metric, value in key_metrics.get("balance_sheet", {}).items():
            metric_name = metric.replace("_", " ")
            qa_pairs.append({
                "question": f"What are the {metric_name}?",
                "answer": f"The {metric_name} are {value}."
            })
            
            if entity:
                qa_pairs.append({
                    "question": f"What are {entity}'s {metric_name}?",
                    "answer": f"{entity}'s {metric_name} are {value}."
                })
        
        # Cash flow metrics
        for metric, value in key_metrics.get("cash_flow", {}).items():
            metric_name = metric.replace("_", " ")
            qa_pairs.append({
                "question": f"What is the {metric_name}?",
                "answer": f"The {metric_name} is {value}."
            })
            
            if entity:
                qa_pairs.append({
                    "question": f"What is {entity}'s {metric_name}?",
                    "answer": f"{entity}'s {metric_name} is {value}."
                })
        
        # Financial ratios
        for metric, value in key_metrics.get("ratios", {}).items():
            metric_name = metric.replace("_", " ")
            qa_pairs.append({
                "question": f"What is the {metric_name} ratio?",
                "answer": f"The {metric_name} ratio is {value:.4f}."
            })
            
            if entity:
                qa_pairs.append({
                    "question": f"What is {entity}'s {metric_name} ratio?",
                    "answer": f"{entity}'s {metric_name} ratio is {value:.4f}."
                })
    
    # Generate questions about sections
    section_summaries = generate_section_summaries(document_tree)
    for section_id, summary in section_summaries.items():
        title = summary.get("title")
        if title:
            if summary.get("content_preview"):
                qa_pairs.append({
                    "question": f"What information is in the '{title}' section?",
                    "answer": f"The '{title}' section contains: {summary['content_preview']}"
                })
            
            if summary.get("financial_statement_type"):
                statement_type = summary.get("financial_statement_type").replace("_", " ")
                qa_pairs.append({
                    "question": f"What type of financial statement is the '{title}' table?",
                    "answer": f"The '{title}' table is a {statement_type}."
                })
    
    return qa_pairs 