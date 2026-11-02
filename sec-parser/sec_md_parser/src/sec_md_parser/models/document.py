"""Document models for SEC filings."""

from __future__ import annotations
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime, date
import json

from sec_md_parser.models.base import DocumentNode, XBRLFact, FinancialMetric


@dataclass
class DocumentTree:
    """Document tree model."""
    
    root: DocumentNode
    
    def find_nodes_by_type(self, node_type: str) -> List[DocumentNode]:
        """Find all nodes of a specific type in the document tree."""
        return self.root.find_nodes_by_type(node_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the document tree to a dictionary."""
        return self.root.to_dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentTree":
        """Create a document tree from a dictionary."""
        root_node = DocumentNode.from_dict(data)
        return cls(root=root_node)
    
    def to_markdown(self, include_xbrl: bool = True, include_financial_metadata: bool = True) -> str:
        """
        Convert the document tree to Markdown.
        
        Args:
            include_xbrl: Whether to include XBRL metadata in the Markdown
            include_financial_metadata: Whether to include financial metadata
            
        Returns:
            Markdown string representation of the document tree
        """
        # Import here to avoid circular imports
        from sec_md_parser.converter.markdown_converter import MarkdownConverter
        
        converter = MarkdownConverter()
        return converter.convert(
            self, 
            include_xbrl=include_xbrl, 
            include_financial_metadata=include_financial_metadata
        )
    
    def get_text(self) -> str:
        """Get all text content from the document tree."""
        return self._get_text_from_node(self.root)
    
    def _get_text_from_node(self, node: DocumentNode) -> str:
        """Get all text content from a node and its children."""
        text = ""
        
        if node.content:
            text += node.content + "\n"
        
        for child in node.children:
            text += self._get_text_from_node(child)
        
        return text


@dataclass
class SECDocument:
    """SEC document model."""
    
    document_tree: DocumentTree
    metadata: Dict[str, Any] = field(default_factory=dict)
    financial_metrics: List[FinancialMetric] = field(default_factory=list)
    xbrl_facts: List[XBRLFact] = field(default_factory=list)
    
    def __post_init__(self):
        # Ensure metadata is a dict
        if self.metadata is None:
            self.metadata = {}
        
        # Ensure financial_metrics is a list
        if self.financial_metrics is None:
            self.financial_metrics = []
        
        # Ensure xbrl_facts is a list
        if self.xbrl_facts is None:
            self.xbrl_facts = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the SEC document to a dictionary."""
        return {
            "document_tree": self.document_tree.to_dict(),
            "metadata": self.metadata,
            "financial_metrics": [metric.to_dict() for metric in self.financial_metrics],
            "xbrl_facts": [fact.to_dict() for fact in self.xbrl_facts],
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert the SEC document to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SECDocument":
        """Create a SEC document from a dictionary."""
        # Create document tree
        document_tree = DocumentTree.from_dict(data["document_tree"])
        
        # Create financial metrics
        financial_metrics = []
        for metric_data in data.get("financial_metrics", []):
            financial_metric = FinancialMetric(
                name=metric_data["name"],
                value=metric_data["value"],
                unit=metric_data.get("unit"),
                period_start=metric_data.get("period_start"),
                period_end=metric_data.get("period_end"),
            )
            financial_metrics.append(financial_metric)
        
        # Create XBRL facts
        xbrl_facts = []
        for fact_data in data.get("xbrl_facts", []):
            xbrl_fact = XBRLFact(
                name=fact_data["name"],
                value=fact_data["value"],
                context_ref=fact_data.get("context_ref"),
                unit_ref=fact_data.get("unit_ref"),
                decimals=fact_data.get("decimals"),
                precision=fact_data.get("precision"),
                id=fact_data.get("id"),
                period=fact_data.get("period"),
            )
            xbrl_facts.append(xbrl_fact)
        
        return cls(
            document_tree=document_tree,
            metadata=data.get("metadata", {}),
            financial_metrics=financial_metrics,
            xbrl_facts=xbrl_facts,
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "SECDocument":
        """Create a SEC document from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_markdown(self, include_xbrl: bool = True, include_financial_metadata: bool = True) -> str:
        """
        Convert the SEC document to Markdown.
        
        Args:
            include_xbrl: Whether to include XBRL metadata in the Markdown
            include_financial_metadata: Whether to include financial metadata
            
        Returns:
            Markdown representation of the document
        """
        return self.document_tree.to_markdown(
            include_xbrl=include_xbrl,
            include_financial_metadata=include_financial_metadata
        )
    
    def extract_tables(self) -> List[Dict[str, Any]]:
        """
        Extract all tables from the document.
        
        Returns:
            List of table dictionaries with metadata
        """
        tables = []
        table_nodes = self.document_tree.find_nodes_by_type("table")
        
        for node in table_nodes:
            table_data = {
                "content": node.content,
                "metadata": node.metadata
            }
            
            # Extract caption if available
            caption_node = next((child for child in node.children if child.type == "table_caption"), None)
            if caption_node:
                table_data["caption"] = caption_node.content
            
            # Add xbrl facts if available
            if node.xbrl_facts:
                table_data["xbrl_facts"] = [fact.to_dict() for fact in node.xbrl_facts]
            
            tables.append(table_data)
        
        return tables
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the document and extract key information.
        
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "metadata": self.metadata,
            "structure": {
                "sections": len(self.document_tree.find_nodes_by_type("section")),
                "headings": len(self.document_tree.find_nodes_by_type("heading")),
                "paragraphs": len(self.document_tree.find_nodes_by_type("paragraph")),
                "tables": len(self.document_tree.find_nodes_by_type("table")),
                "lists": len(self.document_tree.find_nodes_by_type("list")),
            },
            "financial_metrics": [metric.to_dict() for metric in self.financial_metrics],
        }
        
        # Count XBRL facts
        if self.xbrl_facts:
            analysis["xbrl"] = {
                "total_facts": len(self.xbrl_facts),
                "facts_by_context": {}
            }
            
            # Group facts by context
            for fact in self.xbrl_facts:
                context = fact.context_ref or "unknown"
                if context not in analysis["xbrl"]["facts_by_context"]:
                    analysis["xbrl"]["facts_by_context"][context] = 0
                analysis["xbrl"]["facts_by_context"][context] += 1
        
        # Extract financial section information
        financial_sections = []
        for node in self.document_tree.find_nodes_by_type("section"):
            if node.metadata.get("financial_section_type"):
                section_info = {
                    "type": node.metadata["financial_section_type"],
                    "tables": len([child for child in node.find_nodes_by_type("table")]),
                    "xbrl_facts": len(node.xbrl_facts)
                }
                financial_sections.append(section_info)
        
        if financial_sections:
            analysis["financial_sections"] = financial_sections
        
        return analysis
