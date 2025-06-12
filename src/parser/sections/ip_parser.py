"""IP section parsers for RouterOS configurations."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class IPAddressParser(BaseSectionParser):
    """Parser for /ip address section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse IP address configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_address_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip address',
            'commands': commands
        }
        
    def _parse_address_command(self, line: str) -> Dict[str, Any]:
        """Parse a single IP address command."""
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
        self._parse_address_parameters(params, command)
        
        return command
        
    def _parse_address_parameters(self, params: str, command: Dict[str, Any]):
        """Parse IP address parameters."""
        # Split parameters
        parts = self._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'address':
                    # Parse and validate IP address
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['address'] = value
                        command['ip'] = network_info[0]
                        command['network'] = network_info[1]
                        command['prefix'] = network_info[2]
                        command['is_private'] = RouterOSPatterns.is_private_ip(network_info[0])
                    else:
                        command['address'] = value
                        command['address_invalid'] = True
                elif key == 'interface':
                    interface_info = RouterOSPatterns.parse_interface_reference(value)
                    command['interface'] = value
                    command['interface_type'] = interface_info['type']
                elif key in ['disabled', 'invalid']:
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
        """Get IP address section summary."""
        return {
            'section': 'IP Addresses',
            'command_count': len(self.commands)
        }


class IPRouteParser(BaseSectionParser):
    """Parser for /ip route section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse IP route configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_route_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip route',
            'commands': commands
        }
        
    def _parse_route_command(self, line: str) -> Dict[str, Any]:
        """Parse a single route command."""
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
        self._parse_route_parameters(params, command)
        
        return command
        
    def _parse_route_parameters(self, params: str, command: Dict[str, Any]):
        """Parse route parameters."""
        parser = IPAddressParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'dst-address':
                    # Parse destination network
                    if value == '0.0.0.0/0':
                        command['is_default_route'] = True
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['dst-address'] = value
                        command['dst_network'] = network_info[1]
                        command['dst_prefix'] = network_info[2]
                elif key == 'gateway':
                    # Parse gateway (can be IP or interface)
                    if RouterOSPatterns.IP_ADDRESS_PATTERN.match(value):
                        command['gateway'] = value
                        command['gateway_type'] = 'ip'
                        command['gateway_is_private'] = RouterOSPatterns.is_private_ip(value)
                    else:
                        command['gateway'] = value
                        command['gateway_type'] = 'interface'
                elif key == 'distance':
                    try:
                        command['distance'] = int(value)
                    except ValueError:
                        command['distance'] = value
                elif key in ['disabled', 'active']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get IP route section summary."""
        return {
            'section': 'IP Routes',
            'command_count': len(self.commands)
        }


class IPDHCPServerParser(BaseSectionParser):
    """Parser for /ip dhcp-server section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse DHCP server configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_dhcp_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip dhcp-server',
            'commands': commands
        }
        
    def _parse_dhcp_command(self, line: str) -> Dict[str, Any]:
        """Parse a single DHCP server command."""
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
        self._parse_dhcp_parameters(params, command)
        
        return command
        
    def _parse_dhcp_parameters(self, params: str, command: Dict[str, Any]):
        """Parse DHCP server parameters."""
        parser = IPAddressParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'lease-time':
                    command['lease_time_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key in ['disabled', 'authoritative']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get DHCP server section summary."""
        return {
            'section': 'DHCP Server',
            'command_count': len(self.commands)
        }


class IPDHCPServerNetworkParser(BaseSectionParser):
    """Parser for /ip dhcp-server network section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse DHCP server network configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_network_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip dhcp-server network',
            'commands': commands
        }
        
    def _parse_network_command(self, line: str) -> Dict[str, Any]:
        """Parse a single DHCP network command."""
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
        self._parse_network_parameters(params, command)
        
        return command
        
    def _parse_network_parameters(self, params: str, command: Dict[str, Any]):
        """Parse DHCP network parameters."""
        parser = IPAddressParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'address':
                    # Parse network address
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['address'] = value
                        command['network'] = network_info[1]
                        command['prefix'] = network_info[2]
                elif key in ['gateway', 'dns-server']:
                    # Can be comma-separated list
                    if ',' in value:
                        ips = [ip.strip() for ip in value.split(',')]
                        command[key] = ips
                    else:
                        command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get DHCP network section summary."""
        return {
            'section': 'DHCP Networks',
            'command_count': len(self.commands)
        }


class IPDNSParser(BaseSectionParser):
    """Parser for /ip dns section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse DNS configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_dns_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip dns',
            'commands': commands
        }
        
    def _parse_dns_command(self, line: str) -> Dict[str, Any]:
        """Parse a single DNS command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_dns_parameters(params, command)
        
        return command
        
    def _parse_dns_parameters(self, params: str, command: Dict[str, Any]):
        """Parse DNS parameters."""
        parser = IPAddressParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'servers':
                    # Parse comma-separated DNS servers
                    servers = [server.strip() for server in value.split(',')]
                    command['servers'] = servers
                    command['server_count'] = len(servers)
                elif key in ['allow-remote-requests', 'cache-used']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'cache-size':
                    try:
                        # Parse cache size (can have units like KiB)
                        if 'KiB' in value:
                            command['cache_size_kib'] = int(value.replace('KiB', '').strip())
                        else:
                            command['cache_size_kib'] = int(value)
                    except ValueError:
                        command['cache_size_kib'] = value
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get DNS section summary."""
        return {
            'section': 'DNS',
            'command_count': len(self.commands)
        }


class IPArpParser(BaseSectionParser):
    """Parser for /ip arp section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse ARP table configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_arp_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip arp',
            'commands': commands
        }
        
    def _parse_arp_command(self, line: str) -> Dict[str, Any]:
        """Parse a single ARP command."""
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
        self._parse_arp_parameters(params, command)
        
        return command
        
    def _parse_arp_parameters(self, params: str, command: Dict[str, Any]):
        """Parse ARP parameters."""
        parser = IPAddressParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'address':
                    # Validate IP address
                    if RouterOSPatterns.IP_ADDRESS_PATTERN.match(value):
                        command['address'] = value
                        command['is_private'] = RouterOSPatterns.is_private_ip(value)
                    else:
                        command['address'] = value
                        command['address_invalid'] = True
                elif key == 'mac-address':
                    # Validate MAC address
                    if RouterOSPatterns.MAC_ADDRESS_PATTERN.match(value):
                        command['mac-address'] = value
                        command['mac_vendor'] = RouterOSPatterns.get_mac_vendor(value)
                    else:
                        command['mac-address'] = value
                        command['mac_invalid'] = True
                elif key == 'interface':
                    interface_info = RouterOSPatterns.parse_interface_reference(value)
                    command['interface'] = value
                    command['interface_type'] = interface_info['type']
                elif key in ['disabled', 'published', 'invalid', 'DHCP', 'dynamic', 'complete']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get ARP section summary."""
        return {
            'section': 'ARP Table',
            'command_count': len(self.commands)
        }


class IPNeighborParser(BaseSectionParser):
    """Parser for /ip neighbor section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse IP neighbor discovery configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_neighbor_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip neighbor',
            'commands': commands
        }
        
    def _parse_neighbor_command(self, line: str) -> Dict[str, Any]:
        """Parse a single neighbor command."""
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
        self._parse_neighbor_parameters(params, command)
        
        return command
        
    def _parse_neighbor_parameters(self, params: str, command: Dict[str, Any]):
        """Parse neighbor parameters."""
        parser = IPAddressParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'address':
                    # Validate IP address
                    if RouterOSPatterns.IP_ADDRESS_PATTERN.match(value):
                        command['address'] = value
                        command['is_private'] = RouterOSPatterns.is_private_ip(value)
                    else:
                        command['address'] = value
                        command['address_invalid'] = True
                elif key == 'mac-address':
                    # Validate MAC address
                    if RouterOSPatterns.MAC_ADDRESS_PATTERN.match(value):
                        command['mac-address'] = value
                        command['mac_vendor'] = RouterOSPatterns.get_mac_vendor(value)
                    else:
                        command['mac-address'] = value
                        command['mac_invalid'] = True
                elif key == 'interface':
                    interface_info = RouterOSPatterns.parse_interface_reference(value)
                    command['interface'] = value
                    command['interface_type'] = interface_info['type']
                elif key in ['disabled', 'static', 'dynamic']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get neighbor section summary."""
        return {
            'section': 'IP Neighbor Discovery',
            'command_count': len(self.commands)
        }


class IPSettingsParser(BaseSectionParser):
    """Parser for /ip settings section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse IP global settings configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_settings_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip settings',
            'commands': commands
        }
        
    def _parse_settings_command(self, line: str) -> Dict[str, Any]:
        """Parse a single IP settings command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_settings_parameters(params, command)
        
        return command
        
    def _parse_settings_parameters(self, params: str, command: Dict[str, Any]):
        """Parse IP settings parameters."""
        parser = IPAddressParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key in ['accept-redirects', 'accept-source-route', 'allow-fast-path', 'icmp-rate-limit', 'icmp-rate-mask']:
                    if key in ['accept-redirects', 'accept-source-route', 'allow-fast-path']:
                        command[key] = value.lower() in ['yes', 'true', '1']
                    else:
                        command[key] = value
                elif key == 'max-neighbor-entries':
                    try:
                        command[key] = int(value)
                    except ValueError:
                        command[key] = value
                elif key == 'route-cache':
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'rp-filter':
                    # Can be strict, loose, or no
                    command[key] = value
                    command['rp_filter_level'] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get IP settings section summary."""
        return {
            'section': 'IP Global Settings',
            'command_count': len(self.commands)
        }


class IPDHCPRelayParser(BaseSectionParser):
    """Parser for /ip dhcp-relay section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse DHCP relay configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_dhcp_relay_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip dhcp-relay',
            'commands': commands
        }
        
    def _parse_dhcp_relay_command(self, line: str) -> Dict[str, Any]:
        """Parse a single DHCP relay command."""
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
        self._parse_dhcp_relay_parameters(params, command)
        
        return command
        
    def _parse_dhcp_relay_parameters(self, params: str, command: Dict[str, Any]):
        """Parse DHCP relay parameters."""
        parser = IPAddressParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'dhcp-server':
                    # Parse DHCP server IP addresses (can be comma-separated)
                    if ',' in value:
                        servers = [server.strip() for server in value.split(',')]
                        command['dhcp_servers'] = servers
                        command['server_count'] = len(servers)
                        # Validate each server IP
                        valid_servers = []
                        for server in servers:
                            if RouterOSPatterns.IP_ADDRESS_PATTERN.match(server):
                                valid_servers.append(server)
                        command['valid_servers'] = valid_servers
                        command['has_invalid_servers'] = len(valid_servers) != len(servers)
                    else:
                        command['dhcp_servers'] = [value]
                        command['server_count'] = 1
                        if RouterOSPatterns.IP_ADDRESS_PATTERN.match(value):
                            command['valid_servers'] = [value]
                            command['has_invalid_servers'] = False
                        else:
                            command['valid_servers'] = []
                            command['has_invalid_servers'] = True
                elif key == 'interface':
                    # Parse interface list (can be comma-separated)
                    if ',' in value:
                        interfaces = [iface.strip() for iface in value.split(',')]
                        command['interfaces'] = interfaces
                        command['interface_count'] = len(interfaces)
                    else:
                        command['interfaces'] = [value]
                        command['interface_count'] = 1
                elif key == 'local-address':
                    # Validate local address
                    if RouterOSPatterns.IP_ADDRESS_PATTERN.match(value):
                        command['local_address'] = value
                        command['local_address_valid'] = True
                        command['local_is_private'] = RouterOSPatterns.is_private_ip(value)
                    else:
                        command['local_address'] = value
                        command['local_address_valid'] = False
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'delay-threshold':
                    try:
                        command['delay_threshold_ms'] = int(value)
                    except ValueError:
                        command['delay_threshold_ms'] = value
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get DHCP relay section summary."""
        return {
            'section': 'DHCP Relay',
            'command_count': len(self.commands)
        }


# Register parsers
SectionParserRegistry.register('/ip address', IPAddressParser)
SectionParserRegistry.register('/ip route', IPRouteParser)
SectionParserRegistry.register('/ip dhcp-server', IPDHCPServerParser)
SectionParserRegistry.register('/ip dhcp-server network', IPDHCPServerNetworkParser)
SectionParserRegistry.register('/ip dhcp-client', IPAddressParser)  # Use generic IP parser
SectionParserRegistry.register('/ip dns', IPDNSParser)
SectionParserRegistry.register('/ip pool', IPAddressParser)  # Use generic IP parser
SectionParserRegistry.register('/ip service', IPAddressParser)  # Use generic IP parser
SectionParserRegistry.register('/ip arp', IPArpParser)
SectionParserRegistry.register('/ip neighbor', IPNeighborParser)
SectionParserRegistry.register('/ip settings', IPSettingsParser)
SectionParserRegistry.register('/ip dhcp-relay', IPDHCPRelayParser)