"""Financial statement identification system for SEC filings."""

from typing import Dict, List, Optional, Set
import re

from sec_md_parser.models.document import DocumentNode


class FinancialStatementIdentifier:
    """System for identifying and categorizing financial statements in SEC filings."""
    
    def __init__(self):
        """Initialize the financial statement identifier with patterns and XBRL concepts for identification."""
        # Keywords for identifying different financial statement types
        self.statement_patterns = {
            "income_statement": [
                "statement of operations", 
                "income statement", 
                "statement of earnings", 
                "statement of comprehensive income",
                "consolidated statements of income",
                "consolidated statements of operations",
                "statement of profit or loss"
            ],
            "balance_sheet": [
                "balance sheet", 
                "statement of financial position", 
                "statement of financial condition",
                "consolidated balance sheets",
                "consolidated statements of financial position"
            ],
            "cash_flow": [
                "statement of cash flows", 
                "cash flow statement",
                "consolidated statements of cash flows",
                "consolidated cash flow statements"
            ],
            "equity": [
                "statement of stockholders equity", 
                "statement of shareholders equity", 
                "statement of changes in equity",
                "statement of stockholders' equity",
                "consolidated statements of stockholders' equity",
                "changes in shareholders' equity"
            ]
        }
        
        # XBRL concepts typically found in each statement type
        self.statement_concepts = {
            "income_statement": [
                "Revenue", "SalesRevenueNet", "CostOfRevenue", "GrossProfit",
                "OperatingExpenses", "OperatingIncomeLoss", "IncomeTaxExpenseBenefit",
                "NetIncomeLoss", "EarningsPerShareBasic", "EarningsPerShareDiluted"
            ],
            "balance_sheet": [
                "Assets", "AssetsCurrent", "CashAndCashEquivalents", "Inventory",
                "PropertyPlantAndEquipmentNet", "Liabilities", "LiabilitiesCurrent",
                "LongTermDebt", "StockholdersEquity", "CommonStock", "RetainedEarnings"
            ],
            "cash_flow": [
                "NetCashProvidedByUsedInOperatingActivities",
                "NetCashProvidedByUsedInInvestingActivities",
                "NetCashProvidedByUsedInFinancingActivities",
                "CashAndCashEquivalentsPeriodIncreaseDecrease"
            ],
            "equity": [
                "StockholdersEquity", "CommonStock", "RetainedEarnings",
                "AccumulatedOtherComprehensiveIncomeLoss", "TreasuryStock"
            ]
        }
    
    def identify_statement_type(self, table_node: DocumentNode) -> Optional[str]:
        """
        Identify the type of financial statement for a given table node.
        
        Args:
            table_node: DocumentNode representing a table
            
        Returns:
            String indicating the statement type or None if not identifiable
        """
        if not table_node or table_node.type != "table":
            return None
            
        # Check by title if available
        if hasattr(table_node, 'title') and table_node.title:
            title_lower = table_node.title.lower()
            for statement_type, patterns in self.statement_patterns.items():
                if any(pattern in title_lower for pattern in patterns):
                    return statement_type
                    
        # Check by caption if available
        caption_node = next((child for child in table_node.children if child.type == "table_caption"), None)
        if caption_node and caption_node.content:
            caption_lower = caption_node.content.lower()
            for statement_type, patterns in self.statement_patterns.items():
                if any(pattern in caption_lower for pattern in patterns):
                    return statement_type
        
        # If title/caption check fails, analyze content using XBRL concepts
        if table_node.xbrl_facts:
            concept_matches = {stype: 0 for stype in self.statement_concepts.keys()}
            
            # Count matches for each statement type
            for fact in table_node.xbrl_facts:
                fact_name = fact.name
                for stype, concepts in self.statement_concepts.items():
                    for concept in concepts:
                        if concept.lower() in fact_name.lower():
                            concept_matches[stype] += 1
            
            # Find the statement type with the most matches
            max_matches = 0
            best_match = None
            for stype, count in concept_matches.items():
                if count > max_matches:
                    max_matches = count
                    best_match = stype
            
            # Only return if we have a minimum threshold of matches
            if max_matches >= 3:
                return best_match
                
        # Look for clues in table header and body content
        return self._identify_by_table_content(table_node)
    
    def _identify_by_table_content(self, table_node: DocumentNode) -> Optional[str]:
        """
        Identify statement type by analyzing the content of table cells.
        
        Args:
            table_node: DocumentNode representing a table
            
        Returns:
            String indicating the statement type or None if not identifiable
        """
        # Collect all text from headers and first column
        header_texts = []
        first_col_texts = []
        
        # Extract header texts
        header_node = next((child for child in table_node.children if child.type == "table_header"), None)
        if header_node:
            for row_node in header_node.children:
                for cell_node in row_node.children:
                    if cell_node.content:
                        header_texts.append(cell_node.content.lower())
        
        # Extract first column texts
        body_node = next((child for child in table_node.children if child.type == "table_body"), None)
        if body_node:
            for row_node in body_node.children:
                if row_node.children and row_node.children[0].content:
                    first_col_texts.append(row_node.children[0].content.lower())
        
        # Combine all texts for analysis
        all_texts = header_texts + first_col_texts
        
        # Check for income statement indicators
        income_indicators = {
            "revenue", "sales", "cost of", "gross profit", "operating income",
            "net income", "earnings per share", "ebitda", "operating expenses",
            "income tax", "profit", "loss"
        }
        
        # Check for balance sheet indicators
        balance_indicators = {
            "assets", "liabilities", "equity", "cash and cash equivalents", 
            "inventory", "property", "equipment", "debt", "common stock",
            "retained earnings", "current assets", "total assets"
        }
        
        # Check for cash flow indicators
        cashflow_indicators = {
            "cash flow", "operating activities", "investing activities", 
            "financing activities", "net increase", "net decrease", "cash and cash equivalents"
        }
        
        # Check for equity statement indicators
        equity_indicators = {
            "common stock", "preferred stock", "treasury stock", 
            "additional paid-in", "retained earnings", "comprehensive income",
            "stockholders equity", "shareholders equity"
        }
        
        # Count matches for each type
        counts = {
            "income_statement": sum(1 for text in all_texts for indicator in income_indicators if indicator in text),
            "balance_sheet": sum(1 for text in all_texts for indicator in balance_indicators if indicator in text),
            "cash_flow": sum(1 for text in all_texts for indicator in cashflow_indicators if indicator in text),
            "equity": sum(1 for text in all_texts for indicator in equity_indicators if indicator in text)
        }
        
        # Find the statement type with the most matches
        max_count = max(counts.values()) if counts else 0
        if max_count >= 3:  # Threshold for confidence
            return max(counts, key=counts.get)
            
        return None
    
    def process_document_tree(self, document_tree) -> Dict[str, List[DocumentNode]]:
        """
        Process an entire document tree to identify financial statements.
        
        Args:
            document_tree: DocumentTree object to process
            
        Returns:
            Dictionary mapping statement types to lists of table nodes
        """
        result = {
            "income_statement": [],
            "balance_sheet": [],
            "cash_flow": [],
            "equity": [],
            "unclassified": []
        }
        
        # Find all tables in the document
        tables = document_tree.find_nodes_by_type("table")
        
        # Identify each table
        for table in tables:
            statement_type = self.identify_statement_type(table)
            if statement_type:
                # Add to the appropriate category
                result[statement_type].append(table)
                # Also store the type in the table's metadata
                table.metadata["financial_statement_type"] = statement_type
            else:
                result["unclassified"].append(table)
        
        return result 