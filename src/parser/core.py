"""Core RouterOS configuration parser with multi-line command support."""
import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from .registry import SectionParserRegistry


class ParseError(Exception):
    """Parser error exception."""
    pass


class RouterOSParser:
    """
    Main parser class for RouterOS configuration files.
    
    Handles:
    - Multi-line commands (backslash continuation)
    - Section detection and routing
    - Dynamic section discovery
    - Error recovery
    """
    
    def __init__(self, config_content: str, device_name: str = None):
        """
        Initialize parser with config content.
        
        Args:
            config_content: Raw .rsc file content as string
            device_name: Name of the device (extracted from filename)
        """
        self.config_content = config_content
        self.device_name = device_name
        self.sections = {}
        self.parsed_data = None
        self.errors = []
        
    def parse(self) -> 'RouterOSConfig':
        """
        Parse the entire configuration file.
        
        Returns:
            RouterOSConfig object containing all parsed sections
        """
        # Normalize line endings
        self.config_content = self.config_content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Process multi-line commands
        lines = self._process_multiline_commands(self.config_content.split('\n'))
        
        # Split into sections
        sections = self._split_into_sections(lines)
        
        # Parse each section
        parsed_sections = {}
        for section_name, section_lines in sections.items():
            try:
                parser = SectionParserRegistry.get_parser(section_name)
                parsed_sections[section_name] = parser.parse(section_lines)
            except Exception as e:
                self.errors.append({
                    'section': section_name,
                    'error': str(e),
                    'line_count': len(section_lines)
                })
                # Continue parsing other sections
                
        # Import here to avoid circular import
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))
        from models.config import RouterOSConfig
        self.parsed_data = RouterOSConfig(parsed_sections, self.device_name, self.errors)
        return self.parsed_data
        
    def _process_multiline_commands(self, lines: List[str]) -> List[str]:
        """
        Process multi-line commands with backslash continuation.
        
        Args:
            lines: List of raw configuration lines
            
        Returns:
            List of processed lines with multi-line commands joined
        """
        processed_lines = []
        current_line = ""
        
        for line in lines:
            # Remove comments (but preserve inline comments for now)
            comment_pos = line.find('#')
            if comment_pos == 0:
                # Full line comment, skip
                continue
            elif comment_pos > 0:
                # Inline comment, keep the part before it
                line = line[:comment_pos].rstrip()
            
            line = line.rstrip()
            
            # Check for line continuation
            if line.endswith('\\'):
                # Remove backslash and accumulate
                current_line += line[:-1] + " "
            else:
                # Complete line
                current_line += line
                if current_line.strip():
                    processed_lines.append(current_line.strip())
                current_line = ""
                
        # Don't forget the last line if it doesn't end with newline
        if current_line.strip():
            processed_lines.append(current_line.strip())
            
        return processed_lines
        
    def _split_into_sections(self, lines: List[str]) -> Dict[str, List[str]]:
        """
        Split configuration into RouterOS sections.
        
        Args:
            lines: Processed configuration lines
            
        Returns:
            Dictionary mapping section names to their command lines
        """
        sections = defaultdict(list)
        current_section = None
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Check if this is a section header
            if line.startswith('/'):
                # Extract section name
                parts = line.split(maxsplit=1)
                section_name = parts[0]
                
                # Handle hierarchical sections (e.g., /ip firewall filter)
                # Check if this might be a multi-level section command
                if len(parts) > 1:
                    remaining = parts[1]
                    
                    # Try to match 3-level sections first (e.g., firewall filter, dhcp-server network)
                    three_level_match = re.match(r'^([a-z\-]+)\s+([a-z\-]+)(?:\s|$)', remaining)
                    if three_level_match:
                        subsection1 = three_level_match.group(1)
                        subsection2 = three_level_match.group(2)
                        potential_section = f"{section_name} {subsection1} {subsection2}"
                        if self._is_known_section(potential_section):
                            section_name = potential_section
                            # Remove subsections from the line
                            consumed = len(subsection1) + 1 + len(subsection2)
                            if len(remaining) > consumed:
                                line = remaining[consumed:].strip()
                            else:
                                line = ""
                        else:
                            # Try 2-level section
                            potential_section = f"{section_name} {subsection1}"
                            if self._is_known_section(potential_section):
                                section_name = potential_section
                                # Remove first subsection from line
                                if len(remaining) > len(subsection1):
                                    line = remaining[len(subsection1):].strip()
                                else:
                                    line = ""
                            else:
                                # Not a hierarchical section, treat as command
                                line = remaining
                    else:
                        # Try 2-level sections (e.g., firewall, dhcp-server)
                        two_level_match = re.match(r'^([a-z\-]+)(?:\s|$)', remaining)
                        if two_level_match:
                            subsection = two_level_match.group(1)
                            potential_section = f"{section_name} {subsection}"
                            if self._is_known_section(potential_section):
                                section_name = potential_section
                                # Remove subsection from the line
                                if len(remaining) > len(subsection):
                                    line = remaining[len(subsection):].strip()
                                else:
                                    line = ""
                            else:
                                # Not a hierarchical section, treat as command
                                line = remaining
                        else:
                            # Not a subsection, treat as command
                            line = remaining
                else:
                    # Just section name, no command
                    line = ""
                    
                current_section = section_name
                
                # If there's a command on the same line as section
                if line:
                    sections[current_section].append(line)
            else:
                # Command line within current section
                if current_section:
                    sections[current_section].append(line)
                else:
                    # Command before any section (shouldn't happen in valid config)
                    sections['_global'].append(line)
                    
        return dict(sections)
        
    def _is_known_section(self, section_name: str) -> bool:
        """
        Check if a section name is a known RouterOS section.
        
        This helps identify hierarchical sections like '/ip firewall filter'.
        """
        known_hierarchical_sections = {
            '/interface bridge port',
            '/interface bridge vlan',
            '/interface bridge settings',
            '/interface vlan',
            '/interface bonding',
            '/interface ethernet',
            '/interface wireless',
            '/interface eoip',
            '/interface gre',
            '/interface ipip',
            '/interface 6to4',
            '/interface lte',
            '/interface pppoe-client',
            '/interface pppoe-server',
            '/interface l2tp-client',
            '/interface l2tp-server',
            '/interface sstp-client',
            '/interface sstp-server',
            '/interface ovpn-client',
            '/interface ovpn-server',
            '/interface pptp-client',
            '/interface pptp-server',
            '/interface vrrp',
            '/interface list member',
            '/interface wireless security-profiles',
            '/ip address',
            '/ip route',
            '/ip firewall filter',
            '/ip firewall nat',
            '/ip firewall mangle',
            '/ip firewall raw',
            '/ip firewall address-list',
            '/ip firewall layer7-protocol',
            '/ip firewall service-port',
            '/ip dhcp-client',
            '/ip dhcp-server',
            '/ip dhcp-server network',
            '/ip dhcp-server lease',
            '/ip dhcp-relay',
            '/ip dns',
            '/ip pool',
            '/ip service',
            '/ip arp',
            '/ip neighbor',
            '/ip settings',
            '/ipv6 address',
            '/ipv6 route',
            '/ipv6 firewall filter',
            '/ipv6 firewall address-list',
            '/system identity',
            '/system clock',
            '/system note',
            '/system routerboard settings',
            '/routing ospf instance',
            '/routing ospf area',
            '/routing ospf interface',
            '/routing bgp instance',
            '/routing bgp peer',
            '/routing filter',
            '/queue simple',
            '/queue tree',
            '/queue type',
            '/tool bandwidth-server',
            '/tool mac-server',
            '/tool mac-server mac-winbox',
            '/snmp community',
            '/ppp secret',
            '/ppp profile',
            '/ppp aaa',
            '/caps-man manager',
            '/caps-man datapath',
            '/caps-man security',
            '/caps-man configuration',
            '/caps-man channel',
            '/caps-man interface',
            '/caps-man provisioning',
            '/mpls',
            '/mpls ldp',
            '/mpls interface',
            '/mpls forwarding-table',
            '/password',
            '/import',
            '/export',
            '/console',
            '/file',
            '/port',
            '/radius',
            '/special-login',
            '/partitions',
        }
        
        return section_name in known_hierarchical_sections
        
    def discover_sections(self) -> List[str]:
        """
        Dynamically discover all sections in the configuration.
        
        Returns:
            List of unique section names found
        """
        sections = set()
        lines = self._process_multiline_commands(self.config_content.split('\n'))
        
        for line in lines:
            if line.startswith('/'):
                parts = line.split(maxsplit=1)
                section = parts[0]
                
                # Check for hierarchical sections using same logic as _split_into_sections
                if len(parts) > 1:
                    remaining = parts[1]
                    
                    # Try 3-level sections first (e.g., firewall filter)
                    three_level_match = re.match(r'^([a-z\-]+)\s+([a-z\-]+)(?:\s|$)', remaining)
                    if three_level_match:
                        subsection1 = three_level_match.group(1)
                        subsection2 = three_level_match.group(2)
                        potential_section = f"{section} {subsection1} {subsection2}"
                        if self._is_known_section(potential_section):
                            section = potential_section
                        else:
                            # Try 2-level section
                            potential_section = f"{section} {subsection1}"
                            if self._is_known_section(potential_section):
                                section = potential_section
                    else:
                        # Try 2-level sections
                        two_level_match = re.match(r'^([a-z\-]+)(?:\s|$)', remaining)
                        if two_level_match:
                            potential_section = f"{section} {two_level_match.group(1)}"
                            if self._is_known_section(potential_section):
                                section = potential_section
                            
                sections.add(section)
                
        return sorted(list(sections))
        
    def get_parse_errors(self) -> List[Dict]:
        """Get list of parsing errors encountered."""
        return self.errors