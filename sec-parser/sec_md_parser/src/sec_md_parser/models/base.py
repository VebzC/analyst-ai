"""Base models for SEC filings."""

from __future__ import annotations
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime, date
import json


@dataclass
class XBRLFact:
    """XBRL fact model."""
    
    name: str
    value: Any
    context_ref: Optional[str] = None
    unit_ref: Optional[str] = None
    decimals: Optional[str] = None
    precision: Optional[str] = None
    id: Optional[str] = None
    period: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the XBRL fact to a dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "context_ref": self.context_ref,
            "unit_ref": self.unit_ref,
            "decimals": self.decimals,
            "precision": self.precision,
            "id": self.id,
            "period": self.period,
        }


@dataclass
class FinancialMetric:
    """Financial metric model."""
    
    name: str
    value: Any
    unit: Optional[str] = None
    period_start: Optional[Union[str, datetime, date]] = None
    period_end: Optional[Union[str, datetime, date]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the financial metric to a dictionary."""
        # Convert datetime objects to strings
        period_start = self.period_start
        if isinstance(period_start, (datetime, date)):
            period_start = period_start.isoformat()
            
        period_end = self.period_end
        if isinstance(period_end, (datetime, date)):
            period_end = period_end.isoformat()
        
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "period_start": period_start,
            "period_end": period_end,
        }


@dataclass
class DocumentNode:
    """Document node model."""
    
    type: str
    content: Optional[str] = None
    children: List["DocumentNode"] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent: Optional["DocumentNode"] = None
    id: Optional[str] = None
    xbrl_facts: List[XBRLFact] = field(default_factory=list)
    
    def __post_init__(self):
        # Ensure children is a list
        if self.children is None:
            self.children = []
        
        # Ensure attributes is a dict
        if self.attributes is None:
            self.attributes = {}
        
        # Ensure metadata is a dict
        if self.metadata is None:
            self.metadata = {}
        
        # Ensure xbrl_facts is a list
        if self.xbrl_facts is None:
            self.xbrl_facts = []
    
    def add_child(self, child: "DocumentNode") -> "DocumentNode":
        """Add a child node to this node."""
        self.children.append(child)
        child.parent = self
        return child
    
    def find_nodes_by_type(self, node_type: str) -> List["DocumentNode"]:
        """Find all nodes of a specific type in this node and its children."""
        result = []
        
        if self.type == node_type:
            result.append(self)
        
        for child in self.children:
            result.extend(child.find_nodes_by_type(node_type))
        
        return result
    
    def to_dict(self, include_parent: bool = False) -> Dict[str, Any]:
        """Convert the document node to a dictionary."""
        result = {
            "type": self.type,
            "content": self.content,
            "children": [child.to_dict(include_parent) for child in self.children],
            "attributes": self.attributes,
            "metadata": self.metadata,
            "id": self.id,
        }
        
        if self.xbrl_facts:
            result["xbrl_facts"] = [fact.to_dict() for fact in self.xbrl_facts]
        
        if include_parent and self.parent:
            result["parent"] = {"type": self.parent.type, "id": self.parent.id}
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentNode":
        """Create a document node from a dictionary."""
        node = cls(
            type=data["type"],
            content=data.get("content"),
            attributes=data.get("attributes", {}),
            metadata=data.get("metadata", {}),
            id=data.get("id"),
        )
        
        # Create child nodes
        for child_data in data.get("children", []):
            child_node = cls.from_dict(child_data)
            node.add_child(child_node)
        
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
        
        node.xbrl_facts = xbrl_facts
        
        return node 