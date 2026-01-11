from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class Insured:
    name: Optional[str] = None
    address: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    additional_data: Dict[str, str] = field(default_factory=dict)

@dataclass
class Agency:
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    producer_name: Optional[str] = None
    producer_code: Optional[str] = None
    additional_data: Dict[str, str] = field(default_factory=dict)

@dataclass
class Policy:
    policy_number: Optional[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    premium: Optional[str] = None
    status: Optional[str] = None
    carrier: Optional[str] = None
    coverage_type: Optional[str] = None
    additional_data: Dict[str, str] = field(default_factory=dict)

@dataclass
class ScrapeResult:
    # A single page might contain info about one insured, one agency, and multiple policies
    insured: Optional[Insured] = None
    agency: Optional[Agency] = None
    policies: List[Policy] = field(default_factory=list)
    raw_data: Dict = field(default_factory=dict)

    def merge(self, other: 'ScrapeResult'):
        if other.insured:
            if not self.insured: 
                self.insured = other.insured    
        
        if other.agency:
            if not self.agency: 
                self.agency = other.agency
            
        self.policies.extend(other.policies)
        # merge raw data
        for key, value in other.raw_data.items():
            if key not in self.raw_data:
                self.raw_data[key] = value
            else:
                if isinstance(value, dict) and isinstance(self.raw_data[key], dict):
                    self.raw_data[key].get("tables", []).extend(value.get("tables", []))
                    self.raw_data[key].get("lists", []).extend(value.get("lists", []))
                    self.raw_data[key].get("kv_pairs", {}).update(value.get("kv_pairs", {}))
