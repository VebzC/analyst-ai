"""Calculation relationship handler for financial statements in SEC filings."""

from typing import Dict, List, Optional, Any, Set, Tuple
import re

from sec_md_parser.models.document import DocumentNode


class CalculationRelationshipHandler:
    """Handles calculation relationships in financial statements."""
    
    def __init__(self, xbrl_metadata=None):
        """
        Initialize the calculation relationship handler.
        
        Args:
            xbrl_metadata: Optional XBRL metadata dictionary with calculation linkbase info
        """
        self.xbrl_metadata = xbrl_metadata or {}
        self.detected_calculations = {}
        
        # Common calculation patterns by statement type
        self.statement_rules = {
            "income_statement": {
                "subtotals": {
                    "gross_profit": ["revenue", "sales", "net sales", "cost of", "cost of sales", "cost of revenue"],
                    "operating_income": ["gross profit", "operating expenses", "selling", "marketing", "research", "general and administrative"],
                    "income_before_tax": ["operating income", "other income", "interest", "investment"],
                    "net_income": ["income before", "tax", "provision for", "income tax"]
                },
                "calculations": {
                    "gross_profit": {"formula": "revenue - cost_of_sales", "items": {"revenue": 1, "cost_of_sales": -1}},
                    "operating_income": {"formula": "gross_profit - operating_expenses", "items": {"gross_profit": 1, "operating_expenses": -1}},
                    "income_before_tax": {"formula": "operating_income + other_income - interest_expense", 
                                         "items": {"operating_income": 1, "other_income": 1, "interest_expense": -1}},
                    "net_income": {"formula": "income_before_tax - income_tax", "items": {"income_before_tax": 1, "income_tax": -1}}
                }
            },
            "balance_sheet": {
                "subtotals": {
                    "total_current_assets": ["current assets", "cash", "cash equivalents", "accounts receivable", "inventory", "prepaid"],
                    "total_assets": ["current assets", "total current assets", "non-current assets", "property", "equipment", "intangible"],
                    "total_current_liabilities": ["current liabilities", "accounts payable", "accrued", "short-term", "unearned"],
                    "total_liabilities": ["current liabilities", "total current liabilities", "long-term", "debt", "non-current"],
                    "total_equity": ["common stock", "additional paid", "retained earnings", "treasury stock", "accumulated other"],
                    "total_liabilities_and_equity": ["total liabilities", "total equity", "stockholders equity", "shareholders equity"]
                },
                "calculations": {
                    "total_current_assets": {"formula": "sum(current_assets_items)", "items": {}},
                    "total_assets": {"formula": "current_assets + non_current_assets", "items": {"current_assets": 1, "non_current_assets": 1}},
                    "total_current_liabilities": {"formula": "sum(current_liabilities_items)", "items": {}},
                    "total_liabilities": {"formula": "current_liabilities + non_current_liabilities", 
                                         "items": {"current_liabilities": 1, "non_current_liabilities": 1}},
                    "total_equity": {"formula": "sum(equity_items)", "items": {}},
                    "total_liabilities_and_equity": {"formula": "total_liabilities + total_equity", 
                                                   "items": {"total_liabilities": 1, "total_equity": 1}}
                }
            },
            "cash_flow": {
                "subtotals": {
                    "net_cash_from_operating": ["operating activities", "cash from operations", "net income", "depreciation", "amortization", 
                                               "changes in working capital", "accounts receivable", "inventory", "accounts payable"],
                    "net_cash_from_investing": ["investing activities", "capital expenditures", "purchase of", "acquisition", "sale of"],
                    "net_cash_from_financing": ["financing activities", "debt", "loan", "borrowing", "dividend", "repurchase", "stock"]
                },
                "calculations": {
                    "net_cash_from_operating": {"formula": "sum(operating_activities_items)", "items": {}},
                    "net_cash_from_investing": {"formula": "sum(investing_activities_items)", "items": {}},
                    "net_cash_from_financing": {"formula": "sum(financing_activities_items)", "items": {}},
                    "net_change_in_cash": {"formula": "operating + investing + financing", 
                                          "items": {"operating": 1, "investing": 1, "financing": 1}}
                }
            }
        }
    
    def analyze_financial_statement(self, table_node, statement_type):
        """
        Analyze a financial statement table to detect calculation relationships.
        
        Args:
            table_node: DocumentNode representing a financial statement table
            statement_type: Type of financial statement (income_statement, balance_sheet, etc.)
            
        Returns:
            Dictionary of detected calculation relationships
        """
        calculations = {}
        
        # Use XBRL calculation linkbase if available
        if self.xbrl_metadata and 'calculation_links' in self.xbrl_metadata:
            calculations = self._extract_from_calculation_linkbase(
                self.xbrl_metadata['calculation_links'], 
                table_node.xbrl_facts
            )
            
        # If no XBRL calculations or incomplete, detect from table structure
        if not calculations:
            calculations = self._detect_from_table_structure(table_node, statement_type)
            
        # Apply financial statement specific rules
        calculations = self._apply_statement_rules(calculations, statement_type)
        
        # Store the detected calculations in the table node metadata
        if calculations:
            table_node.metadata['calculation_relationships'] = calculations
        
        return calculations
        
    def _extract_from_calculation_linkbase(self, calculation_links, xbrl_facts):
        """
        Extract calculation relationships from XBRL calculation linkbase.
        
        Args:
            calculation_links: XBRL calculation linkbase data
            xbrl_facts: List of XBRL facts in the table
            
        Returns:
            Dictionary of calculation relationships
        """
        calculations = {}
        
        if not calculation_links or not xbrl_facts:
            return calculations
            
        # Build a map of fact names for quick lookup
        fact_names = {fact.name for fact in xbrl_facts}
        
        # Process each calculation relationship in the linkbase
        for calc_rel in calculation_links:
            parent = calc_rel.get('parent')
            children = calc_rel.get('children', [])
            
            # Skip if no parent or children
            if not parent or not children:
                continue
                
            # Only include relationships where we have both parent and at least some children in our facts
            if parent not in fact_names:
                continue
                
            # Find the children that are present in our facts
            valid_children = []
            for child in children:
                child_name = child.get('name')
                weight = child.get('weight')
                
                if child_name and child_name in fact_names:
                    valid_children.append({
                        'name': child_name,
                        'weight': weight
                    })
            
            # Only add the calculation if we have enough information
            if valid_children:
                calculations[parent] = {
                    'source': 'xbrl_linkbase',
                    'formula': f"{parent} = {' + '.join([f'{c.get('weight', 1)} * {c.get('name')}' for c in valid_children])}",
                    'children': valid_children
                }
        
        return calculations
    
    def _detect_from_table_structure(self, table_node, statement_type):
        """
        Detect calculation relationships by analyzing table structure.
        
        Args:
            table_node: DocumentNode representing a table
            statement_type: Type of financial statement
            
        Returns:
            Dictionary of detected calculation relationships
        """
        calculations = {}
        
        # Only process if we have table structure
        if 'structure' not in table_node.metadata:
            return calculations
            
        structure = table_node.metadata['structure']
        
        # Extract labels and numerical values from each row
        rows_data = []
        for row in structure:
            if not row or len(row) < 2:
                continue
                
            # First cell is usually the label
            label_cell = row[0]
            if not label_cell or not isinstance(label_cell, dict) or 'content' not in label_cell:
                continue
                
            label = label_cell['content'].strip()
            if not label:
                continue
                
            # Extract numerical values from remaining cells
            values = []
            for cell in row[1:]:
                if cell and isinstance(cell, dict) and 'content' in cell:
                    try:
                        # Try to convert to float
                        value_str = cell['content'].replace(',', '').replace('$', '').replace('(', '-').replace(')', '')
                        value = float(value_str)
                        values.append(value)
                    except (ValueError, TypeError):
                        values.append(None)
                else:
                    values.append(None)
                    
            rows_data.append({'label': label, 'values': values, 'index': len(rows_data)})
        
        # First pass: identify potential total and subtotal rows
        total_indicators = ['total', 'subtotal', 'net', 'gross']
        indentation_levels = self._detect_indentation_levels(rows_data)
        
        total_rows = []
        for i, row in enumerate(rows_data):
            label_lower = row['label'].lower()
            
            # Check if this is a potential total row
            is_total = any(indicator in label_lower for indicator in total_indicators)
            
            # Check indentation - totals are usually less indented than their components
            indent_level = indentation_levels.get(i, 0)
            
            # Is this a bold/emphasized row? (if available in metadata)
            is_emphasized = False
            if row.get('emphasized') or (isinstance(label_cell, dict) and label_cell.get('is_bold')):
                is_emphasized = True
            
            # If it looks like a total or is emphasized and has numeric values
            if (is_total or is_emphasized or indent_level == 0) and any(v is not None for v in row['values']):
                total_rows.append({
                    'index': i,
                    'label': row['label'],
                    'values': row['values'],
                    'indent_level': indent_level,
                    'is_emphasized': is_emphasized
                })
        
        # Second pass: for each total row, find its component rows
        for total_row in total_rows:
            total_idx = total_row['index']
            
            # Look for component rows before this total
            components = []
            start_idx = max(0, total_idx - 15)  # Look for components within reasonable range
            
            # Components are usually at a higher indent level and between the previous total and this one
            prev_total_idx = -1
            for prev_total in total_rows:
                if prev_total['index'] < total_idx and prev_total['index'] > prev_total_idx:
                    prev_total_idx = prev_total['index']
            
            if prev_total_idx != -1:
                start_idx = prev_total_idx + 1
            
            for i in range(start_idx, total_idx):
                if i < len(rows_data):
                    row = rows_data[i]
                    # Component should be at higher indent level than total
                    if indentation_levels.get(i, 0) > total_row['indent_level']:
                        components.append({
                            'label': row['label'],
                            'values': row['values'],
                            'index': i
                        })
            
            # Verify that sum of components approximately equals total
            is_valid_calculation = False
            if components and len(total_row['values']) > 0:
                for col_idx in range(len(total_row['values'])):
                    if total_row['values'][col_idx] is None:
                        continue
                    
                    component_sum = 0
                    all_components_valid = True
                    
                    for comp in components:
                        if col_idx < len(comp['values']) and comp['values'][col_idx] is not None:
                            component_sum += comp['values'][col_idx]
                        else:
                            all_components_valid = False
                            break
                    
                    # Check if sum approximately equals total (allow for rounding differences)
                    if all_components_valid:
                        total_value = total_row['values'][col_idx]
                        if abs(component_sum - total_value) < 0.01 * abs(total_value):
                            is_valid_calculation = True
                            break
            
            # Add calculation if valid
            if is_valid_calculation:
                calc_name = re.sub(r'[^a-zA-Z0-9_]', '_', total_row['label'].lower()).strip('_')
                child_items = {
                    re.sub(r'[^a-zA-Z0-9_]', '_', comp['label'].lower()).strip('_'): 1 
                    for comp in components
                }
                
                calculations[calc_name] = {
                    'source': 'table_structure',
                    'formula': f"{calc_name} = {' + '.join(child_items.keys())}",
                    'items': child_items,
                    'row_index': total_row['index'],
                    'components': [comp['index'] for comp in components]
                }
        
        return calculations
    
    def _detect_indentation_levels(self, rows_data):
        """
        Detect indentation levels based on row labels.
        
        Args:
            rows_data: List of row data dictionaries
            
        Returns:
            Dictionary mapping row index to indentation level
        """
        indentation = {}
        
        # Simple heuristic: count leading spaces in labels
        for i, row in enumerate(rows_data):
            label = row['label']
            leading_spaces = len(label) - len(label.lstrip())
            indentation[i] = leading_spaces // 2  # Assuming 2 spaces per indent level
        
        return indentation
    
    def _apply_statement_rules(self, detected_calculations, statement_type):
        """
        Apply financial statement specific rules to enhance detected calculations.
        
        Args:
            detected_calculations: Dictionary of detected calculation relationships
            statement_type: Type of financial statement
            
        Returns:
            Enhanced dictionary of calculation relationships
        """
        enhanced_calculations = detected_calculations.copy()
        
        # Apply statement-specific rules if available
        if statement_type in self.statement_rules:
            rules = self.statement_rules[statement_type]
            
            # Apply standard calculations based on statement type
            for calc_name, calc_info in rules['calculations'].items():
                # Only add if not already detected
                if calc_name not in enhanced_calculations:
                    enhanced_calculations[calc_name] = {
                        'source': 'statement_rules',
                        'formula': calc_info['formula'],
                        'items': calc_info['items']
                    }
        
        return enhanced_calculations
    
    def get_calculation_hierarchy(self, calculations):
        """
        Build a hierarchy of calculations showing parent-child relationships.
        
        Args:
            calculations: Dictionary of calculation relationships
            
        Returns:
            Hierarchical structure of calculations
        """
        hierarchy = {}
        
        # Find root calculations (those that aren't components of others)
        all_components = set()
        for calc_name, calc_info in calculations.items():
            if 'items' in calc_info:
                all_components.update(calc_info['items'].keys())
        
        roots = []
        for calc_name in calculations:
            if calc_name not in all_components:
                roots.append(calc_name)
        
        # Build hierarchy for each root
        for root in roots:
            hierarchy[root] = self._build_calc_tree(root, calculations)
        
        return hierarchy
    
    def _build_calc_tree(self, calc_name, calculations):
        """
        Recursively build a calculation tree.
        
        Args:
            calc_name: Name of the calculation to build tree for
            calculations: Dictionary of all calculations
            
        Returns:
            Tree structure for this calculation
        """
        if calc_name not in calculations:
            return {'name': calc_name, 'children': []}
        
        calc_info = calculations[calc_name]
        children = []
        
        # Add child components if they exist
        if 'items' in calc_info:
            for child_name in calc_info['items']:
                # Only include as child if it's a calculation itself
                if child_name in calculations:
                    children.append(self._build_calc_tree(child_name, calculations))
                else:
                    children.append({'name': child_name, 'children': []})
        
        return {
            'name': calc_name,
            'formula': calc_info.get('formula', ''),
            'children': children
        } 