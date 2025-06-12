"""RouterOS parser package."""
from .core import RouterOSParser, ParseError
from .registry import SectionParserRegistry, BaseSectionParser, GenericSectionParser

# Import all section parsers to register them
from .sections import (
    interface_parser, 
    ip_parser, 
    system_parser, 
    firewall_parser,
    routing_parser,
    wireless_parser,
    ppp_parser,
    queue_parser,
    ipv6_parser,
    tools_parser,
    snmp_parser,
    advanced_parser,
    mpls_parser
)

__all__ = [
    'RouterOSParser',
    'ParseError', 
    'SectionParserRegistry',
    'BaseSectionParser',
    'GenericSectionParser'
]