"""MPLS section parsers for RouterOS configurations."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class MPLSParser(BaseSectionParser):
    """Parser for /mpls section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse MPLS configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_mpls_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/mpls',
            'commands': commands
        }
        
    def _parse_mpls_command(self, line: str) -> Dict[str, Any]:
        """Parse a single MPLS command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_mpls_parameters(params, command)
        
        return command
        
    def _parse_mpls_parameters(self, params: str, command: Dict[str, Any]):
        """Parse MPLS parameters."""
        parts = self._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key in ['propagate-ttl']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def _split_parameters(self, params: str) -> List[str]:
        """Split parameters handling quoted values."""
        parts = []
        current = ""
        in_quotes = False
        
        for char in params:
            if char == '"' and (not current or current[-1] != '\\'):
                in_quotes = not in_quotes
                current += char
            elif char == ' ' and not in_quotes:
                if current.strip():
                    parts.append(current.strip())
                current = ""
            else:
                current += char
                
        if current.strip():
            parts.append(current.strip())
            
        return parts
        
    def get_summary(self) -> Dict[str, Any]:
        """Get MPLS section summary."""
        return {
            'section': 'MPLS',
            'command_count': len(self.commands)
        }


class MPLSLDPParser(BaseSectionParser):
    """Parser for /mpls ldp section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse MPLS LDP configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_ldp_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/mpls ldp',
            'commands': commands
        }
        
    def _parse_ldp_command(self, line: str) -> Dict[str, Any]:
        """Parse a single LDP command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_ldp_parameters(params, command)
        
        return command
        
    def _parse_ldp_parameters(self, params: str, command: Dict[str, Any]):
        """Parse LDP parameters."""
        parser = MPLSParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'enabled':
                    command['ldp_enabled'] = value.lower() in ['yes', 'true', '1']
                elif key == 'lsr-id':
                    # Validate LSR ID (should be IPv4 address format)
                    if RouterOSPatterns.IP_ADDRESS_PATTERN.match(value):
                        command['lsr_id_valid'] = True
                        command['lsr_id'] = value
                    else:
                        command['lsr_id_valid'] = False
                        command['lsr_id'] = value
                elif key == 'transport-address':
                    # Validate transport address
                    if RouterOSPatterns.IP_ADDRESS_PATTERN.match(value):
                        command['transport_address_valid'] = True
                        command['transport_address'] = value
                    else:
                        command['transport_address_valid'] = False
                        command['transport_address'] = value
                elif key in ['use-explicit-null']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get MPLS LDP section summary."""
        return {
            'section': 'MPLS LDP',
            'command_count': len(self.commands)
        }


class MPLSInterfaceParser(BaseSectionParser):
    """Parser for /mpls interface section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse MPLS interface configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_mpls_interface_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/mpls interface',
            'commands': commands
        }
        
    def _parse_mpls_interface_command(self, line: str) -> Dict[str, Any]:
        """Parse a single MPLS interface command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('add '):
            command['action'] = 'add'
            params = line[4:].strip()
        elif line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_mpls_interface_parameters(params, command)
        
        return command
        
    def _parse_mpls_interface_parameters(self, params: str, command: Dict[str, Any]):
        """Parse MPLS interface parameters."""
        parser = MPLSParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'interface':
                    interface_info = RouterOSPatterns.parse_interface_reference(value)
                    command['interface'] = value
                    command['interface_type'] = interface_info['type']
                elif key in ['disabled', 'mpls-mtu']:
                    if key == 'disabled':
                        command[key] = value.lower() in ['yes', 'true', '1']
                    elif key == 'mpls-mtu':
                        try:
                            command['mpls_mtu_size'] = int(value)
                            command['jumbo_frames'] = int(value) > 1500
                        except ValueError:
                            command['mpls_mtu_size'] = value
                        command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get MPLS interface section summary."""
        return {
            'section': 'MPLS Interfaces',
            'command_count': len(self.commands)
        }


class MPLSForwardingTableParser(BaseSectionParser):
    """Parser for /mpls forwarding-table section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse MPLS forwarding table configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_forwarding_table_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/mpls forwarding-table',
            'commands': commands
        }
        
    def _parse_forwarding_table_command(self, line: str) -> Dict[str, Any]:
        """Parse a single MPLS forwarding table command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('add '):
            command['action'] = 'add'
            params = line[4:].strip()
        elif line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_forwarding_table_parameters(params, command)
        
        return command
        
    def _parse_forwarding_table_parameters(self, params: str, command: Dict[str, Any]):
        """Parse MPLS forwarding table parameters."""
        parser = MPLSParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'label':
                    try:
                        label_value = int(value)
                        command['label_value'] = label_value
                        command['label_valid'] = True
                        # Check for reserved label ranges
                        if 0 <= label_value <= 15:
                            command['reserved_label'] = True
                        elif label_value >= 1048576:
                            command['invalid_label'] = True
                    except ValueError:
                        command['label_valid'] = False
                    command[key] = value
                elif key == 'dest-fec':
                    # Parse destination FEC (Forwarding Equivalence Class)
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['dest_fec_valid'] = True
                        command['dest_network'] = network_info[1]
                        command['dest_prefix'] = network_info[2]
                    else:
                        command['dest_fec_valid'] = False
                    command[key] = value
                elif key == 'interface':
                    interface_info = RouterOSPatterns.parse_interface_reference(value)
                    command['interface'] = value
                    command['interface_type'] = interface_info['type']
                elif key == 'gateway':
                    # Validate gateway address
                    if RouterOSPatterns.IP_ADDRESS_PATTERN.match(value):
                        command['gateway_valid'] = True
                        command['gateway_is_private'] = RouterOSPatterns.is_private_ip(value)
                    else:
                        command['gateway_valid'] = False
                    command[key] = value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get MPLS forwarding table section summary."""
        return {
            'section': 'MPLS Forwarding Table',
            'command_count': len(self.commands)
        }


# Register MPLS parsers
SectionParserRegistry.register('/mpls', MPLSParser)
SectionParserRegistry.register('/mpls ldp', MPLSLDPParser)
SectionParserRegistry.register('/mpls interface', MPLSInterfaceParser)
SectionParserRegistry.register('/mpls forwarding-table', MPLSForwardingTableParser)