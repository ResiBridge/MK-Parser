"""Firewall section parsers for RouterOS configurations."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class FirewallFilterParser(BaseSectionParser):
    """Parser for /ip firewall filter section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse firewall filter rules."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_filter_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip firewall filter',
            'commands': commands
        }
        
    def _parse_filter_command(self, line: str) -> Dict[str, Any]:
        """Parse a single filter rule command."""
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
        self._parse_filter_parameters(params, command)
        
        return command
        
    def _parse_filter_parameters(self, params: str, command: Dict[str, Any]):
        """Parse firewall filter parameters."""
        parts = self._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'action':
                    action_info = RouterOSPatterns.parse_firewall_action(value)
                    command['action_type'] = action_info['type']
                    command['action_description'] = action_info['description']
                    command[key] = value
                elif key in ['src-address', 'dst-address']:
                    # Parse source/destination addresses
                    if value.startswith('!'):
                        # Negated address
                        command[f"{key}_negated"] = True
                        address = value[1:]
                    else:
                        address = value
                        
                    # Check if it's an address list reference
                    if address.startswith(':'):
                        command[f"{key}_type"] = 'address_list'
                        command[f"{key}_list"] = address[1:]
                    else:
                        command[f"{key}_type"] = 'ip'
                        # Validate IP/network
                        network_info = RouterOSPatterns.extract_ip_network(address)
                        if network_info:
                            command[f"{key}_valid"] = True
                            command[f"{key}_is_private"] = RouterOSPatterns.is_private_ip(network_info[0])
                        else:
                            command[f"{key}_valid"] = False
                            
                    command[key] = value
                elif key in ['src-port', 'dst-port']:
                    # Parse port specifications
                    if value.startswith('!'):
                        command[f"{key}_negated"] = True
                        port_spec = value[1:]
                    else:
                        port_spec = value
                        
                    ports = RouterOSPatterns.parse_port_range(port_spec)
                    command[f"{key}_list"] = ports
                    command[f"{key}_count"] = len(ports)
                    command[key] = value
                elif key == 'protocol':
                    # Parse protocol
                    if value in ['tcp', 'udp', 'icmp', 'ipv6-icmp']:
                        command['protocol_type'] = 'layer4'
                    elif value in ['ip', 'ipv6']:
                        command['protocol_type'] = 'layer3'
                    else:
                        command['protocol_type'] = 'other'
                    command[key] = value
                elif key == 'connection-state':
                    # Parse connection state
                    states = [state.strip() for state in value.split(',')]
                    command['connection_states'] = states
                    command['tracks_established'] = 'established' in states
                    command['tracks_related'] = 'related' in states
                    command[key] = value
                elif key == 'in-interface':
                    interface_info = RouterOSPatterns.parse_interface_reference(value)
                    command['in_interface_type'] = interface_info['type']
                    command[key] = value
                elif key == 'out-interface':
                    interface_info = RouterOSPatterns.parse_interface_reference(value)
                    command['out_interface_type'] = interface_info['type']
                    command[key] = value
                elif key in ['disabled', 'invalid']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'comment':
                    command['comment'] = value
                    command['has_comment'] = True
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
        """Get firewall filter section summary."""
        return {
            'section': 'Firewall Filter',
            'command_count': len(self.commands)
        }


class FirewallNATParser(BaseSectionParser):
    """Parser for /ip firewall nat section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse firewall NAT rules."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_nat_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip firewall nat',
            'commands': commands
        }
        
    def _parse_nat_command(self, line: str) -> Dict[str, Any]:
        """Parse a single NAT rule command."""
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
            
        # Parse parameters (reuse filter parser logic)
        filter_parser = FirewallFilterParser()
        filter_parser._parse_filter_parameters(params, command)
        
        # NAT-specific parameter handling
        self._parse_nat_specific_parameters(command)
        
        return command
        
    def _parse_nat_specific_parameters(self, command: Dict[str, Any]):
        """Parse NAT-specific parameters."""
        # Determine NAT type from chain
        chain = command.get('chain', '')
        if chain == 'srcnat':
            command['nat_type'] = 'source_nat'
        elif chain == 'dstnat':
            command['nat_type'] = 'destination_nat'
        else:
            command['nat_type'] = 'unknown'
            
        # Parse NAT action details
        action = command.get('action', '')
        if action == 'masquerade':
            command['nat_action'] = 'masquerade'
            command['changes_source'] = True
        elif action == 'src-nat':
            command['nat_action'] = 'source_nat'
            command['changes_source'] = True
        elif action == 'dst-nat':
            command['nat_action'] = 'destination_nat'
            command['changes_destination'] = True
        elif action == 'redirect':
            command['nat_action'] = 'redirect'
            command['changes_destination'] = True
            
        # Parse to-addresses and to-ports
        if 'to-addresses' in command:
            addresses = command['to-addresses'].split('-')
            command['nat_address_range'] = len(addresses) > 1
            command['nat_address_count'] = len(addresses)
            
        if 'to-ports' in command:
            ports = RouterOSPatterns.parse_port_range(command['to-ports'])
            command['nat_port_range'] = len(ports) > 1
            command['nat_port_count'] = len(ports)
            
    def get_summary(self) -> Dict[str, Any]:
        """Get firewall NAT section summary."""
        return {
            'section': 'Firewall NAT',
            'command_count': len(self.commands)
        }


class FirewallMangleParser(BaseSectionParser):
    """Parser for /ip firewall mangle section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse firewall mangle rules."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_mangle_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip firewall mangle',
            'commands': commands
        }
        
    def _parse_mangle_command(self, line: str) -> Dict[str, Any]:
        """Parse a single mangle rule command."""
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
            
        # Parse parameters (reuse filter parser logic)
        filter_parser = FirewallFilterParser()
        filter_parser._parse_filter_parameters(params, command)
        
        # Mangle-specific handling
        self._parse_mangle_specific_parameters(command)
        
        return command
        
    def _parse_mangle_specific_parameters(self, command: Dict[str, Any]):
        """Parse mangle-specific parameters."""
        action = command.get('action', '')
        
        # Classify mangle actions
        marking_actions = ['mark-packet', 'mark-connection', 'mark-routing']
        qos_actions = ['set-priority', 'change-mss', 'change-ttl']
        
        if action in marking_actions:
            command['mangle_type'] = 'marking'
        elif action in qos_actions:
            command['mangle_type'] = 'qos'
        elif action == 'passthrough':
            command['mangle_type'] = 'passthrough'
        else:
            command['mangle_type'] = 'other'
            
        # Parse mark values
        if 'new-packet-mark' in command:
            command['packet_mark'] = command['new-packet-mark']
        if 'new-connection-mark' in command:
            command['connection_mark'] = command['new-connection-mark']
        if 'new-routing-mark' in command:
            command['routing_mark'] = command['new-routing-mark']
            
    def get_summary(self) -> Dict[str, Any]:
        """Get firewall mangle section summary."""
        return {
            'section': 'Firewall Mangle',
            'command_count': len(self.commands)
        }


class FirewallAddressListParser(BaseSectionParser):
    """Parser for /ip firewall address-list section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse firewall address list entries."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_address_list_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip firewall address-list',
            'commands': commands
        }
        
    def _parse_address_list_command(self, line: str) -> Dict[str, Any]:
        """Parse a single address list command."""
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
        self._parse_address_list_parameters(params, command)
        
        return command
        
    def _parse_address_list_parameters(self, params: str, command: Dict[str, Any]):
        """Parse address list parameters."""
        filter_parser = FirewallFilterParser()
        parts = filter_parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'address':
                    # Validate IP address/network
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['address_valid'] = True
                        command['is_private'] = RouterOSPatterns.is_private_ip(network_info[0])
                        command['network'] = network_info[1]
                        command['prefix'] = network_info[2]
                    else:
                        command['address_valid'] = False
                    command[key] = value
                elif key == 'list':
                    command['list_name'] = value
                    command[key] = value
                elif key == 'timeout':
                    # Parse timeout
                    command['timeout_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command['has_timeout'] = True
                    command[key] = value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get address list section summary."""
        return {
            'section': 'Firewall Address Lists',
            'command_count': len(self.commands)
        }


class FirewallLayer7ProtocolParser(BaseSectionParser):
    """Parser for /ip firewall layer7-protocol section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse firewall layer7 protocol definitions."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_layer7_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip firewall layer7-protocol',
            'commands': commands
        }
        
    def _parse_layer7_command(self, line: str) -> Dict[str, Any]:
        """Parse a single layer7 protocol command."""
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
        self._parse_layer7_parameters(params, command)
        
        return command
        
    def _parse_layer7_parameters(self, params: str, command: Dict[str, Any]):
        """Parse layer7 protocol parameters."""
        filter_parser = FirewallFilterParser()
        parts = filter_parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'name':
                    command['protocol_name'] = value
                    command[key] = value
                elif key == 'regexp':
                    command['regex_pattern'] = value
                    command['has_regex'] = True
                    command['pattern_length'] = len(value)
                    # Analyze regex complexity
                    command['has_wildcards'] = '*' in value or '?' in value
                    command['has_groups'] = '(' in value and ')' in value
                    command['has_alternation'] = '|' in value
                    command[key] = value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'comment':
                    command['comment'] = value
                    command['has_comment'] = True
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get layer7 protocol section summary."""
        return {
            'section': 'Firewall Layer 7 Protocols',
            'command_count': len(self.commands)
        }


class FirewallServicePortParser(BaseSectionParser):
    """Parser for /ip firewall service-port section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse firewall service port definitions."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_service_port_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip firewall service-port',
            'commands': commands
        }
        
    def _parse_service_port_command(self, line: str) -> Dict[str, Any]:
        """Parse a single service port command."""
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
        self._parse_service_port_parameters(params, command)
        
        return command
        
    def _parse_service_port_parameters(self, params: str, command: Dict[str, Any]):
        """Parse service port parameters."""
        filter_parser = FirewallFilterParser()
        parts = filter_parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'name':
                    command['service_name'] = value
                    command[key] = value
                elif key == 'ports':
                    # Parse port list
                    ports = RouterOSPatterns.parse_port_range(value)
                    command['port_list'] = ports
                    command['port_count'] = len(ports)
                    command['has_range'] = '-' in value
                    command[key] = value
                elif key == 'protocol':
                    command['transport_protocol'] = value
                    command['is_tcp'] = value.lower() == 'tcp'
                    command['is_udp'] = value.lower() == 'udp'
                    command[key] = value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'comment':
                    command['comment'] = value
                    command['has_comment'] = True
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get service port section summary."""
        return {
            'section': 'Firewall Service Ports',
            'command_count': len(self.commands)
        }


# Register parsers
SectionParserRegistry.register('/ip firewall filter', FirewallFilterParser)
SectionParserRegistry.register('/ip firewall nat', FirewallNATParser)
SectionParserRegistry.register('/ip firewall mangle', FirewallMangleParser)
SectionParserRegistry.register('/ip firewall raw', FirewallFilterParser)  # Similar to filter
SectionParserRegistry.register('/ip firewall address-list', FirewallAddressListParser)
SectionParserRegistry.register('/ip firewall layer7-protocol', FirewallLayer7ProtocolParser)
SectionParserRegistry.register('/ip firewall service-port', FirewallServicePortParser)
SectionParserRegistry.register('/ipv6 firewall filter', FirewallFilterParser)  # IPv6 uses same logic
SectionParserRegistry.register('/ipv6 firewall address-list', FirewallAddressListParser)