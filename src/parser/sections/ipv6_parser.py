"""IPv6 section parsers for RouterOS configurations."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
import ipaddress
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class IPv6AddressParser(BaseSectionParser):
    """Parser for /ipv6 address section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse IPv6 address configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_ipv6_address_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ipv6 address',
            'commands': commands
        }
        
    def _parse_ipv6_address_command(self, line: str) -> Dict[str, Any]:
        """Parse a single IPv6 address command."""
        command = {'raw_line': line}
        
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
        self._parse_ipv6_address_parameters(params, command)
        
        return command
        
    def _parse_ipv6_address_parameters(self, params: str, command: Dict[str, Any]):
        """Parse IPv6 address parameters."""
        parts = self._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'address':
                    # Parse and validate IPv6 address
                    try:
                        ipv6_obj = ipaddress.ip_interface(value)
                        command['address'] = value
                        command['ipv6_valid'] = True
                        command['ipv6_address'] = str(ipv6_obj.ip)
                        command['ipv6_network'] = str(ipv6_obj.network.network_address)
                        command['ipv6_prefix'] = ipv6_obj.network.prefixlen
                        
                        # Classify IPv6 address type
                        ip = ipv6_obj.ip
                        command['is_link_local'] = ip.is_link_local
                        command['is_loopback'] = ip.is_loopback
                        command['is_multicast'] = ip.is_multicast
                        command['is_private'] = ip.is_private
                        command['is_global'] = ip.is_global
                        command['is_site_local'] = ip.is_site_local
                        
                        # Check for special addresses
                        if str(ip).startswith('2001:db8:'):
                            command['is_documentation'] = True
                        if str(ip).startswith('fc00:') or str(ip).startswith('fd00:'):
                            command['is_unique_local'] = True
                            
                    except ValueError:
                        command['address'] = value
                        command['ipv6_valid'] = False
                        
                elif key == 'interface':
                    interface_info = RouterOSPatterns.parse_interface_reference(value)
                    command['interface'] = value
                    command['interface_type'] = interface_info['type']
                elif key in ['disabled', 'invalid', 'no-dad']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'advertise':
                    command['router_advertisement'] = value.lower() in ['yes', 'true', '1']
                elif key == 'eui-64':
                    command['auto_config_eui64'] = value.lower() in ['yes', 'true', '1']
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
        """Get IPv6 address section summary."""
        return {
            'section': 'IPv6 Addresses',
            'command_count': len(self.commands)
        }


class IPv6RouteParser(BaseSectionParser):
    """Parser for /ipv6 route section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse IPv6 route configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_ipv6_route_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ipv6 route',
            'commands': commands
        }
        
    def _parse_ipv6_route_command(self, line: str) -> Dict[str, Any]:
        """Parse a single IPv6 route command."""
        command = {'raw_line': line}
        
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
        self._parse_ipv6_route_parameters(params, command)
        
        return command
        
    def _parse_ipv6_route_parameters(self, params: str, command: Dict[str, Any]):
        """Parse IPv6 route parameters."""
        parser = IPv6AddressParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'dst-address':
                    # Parse destination network
                    try:
                        if value == '::/0':
                            command['is_default_route'] = True
                        ipv6_net = ipaddress.ip_network(value, strict=False)
                        command['dst_address'] = value
                        command['dst_network'] = str(ipv6_net.network_address)
                        command['dst_prefix'] = ipv6_net.prefixlen
                        command['dst_valid'] = True
                    except ValueError:
                        command['dst_address'] = value
                        command['dst_valid'] = False
                        
                elif key == 'gateway':
                    # Parse gateway (can be IPv6 or interface)
                    try:
                        ipv6_addr = ipaddress.ip_address(value)
                        command['gateway'] = value
                        command['gateway_type'] = 'ipv6'
                        command['gateway_is_link_local'] = ipv6_addr.is_link_local
                        command['gateway_valid'] = True
                    except ValueError:
                        command['gateway'] = value
                        command['gateway_type'] = 'interface'
                        command['gateway_valid'] = False
                        
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
        """Get IPv6 route section summary."""
        return {
            'section': 'IPv6 Routes',
            'command_count': len(self.commands)
        }


class IPv6DHCPClientParser(BaseSectionParser):
    """Parser for /ipv6 dhcp-client section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse IPv6 DHCP client configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_dhcp_client_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ipv6 dhcp-client',
            'commands': commands
        }
        
    def _parse_dhcp_client_command(self, line: str) -> Dict[str, Any]:
        """Parse a single DHCPv6 client command."""
        command = {'raw_line': line}
        
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
        self._parse_dhcp_client_parameters(params, command)
        
        return command
        
    def _parse_dhcp_client_parameters(self, params: str, command: Dict[str, Any]):
        """Parse DHCPv6 client parameters."""
        parser = IPv6AddressParser()
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
                elif key == 'request':
                    # Parse DHCPv6 request options
                    options = [opt.strip() for opt in value.split(',')]
                    command['request_options'] = options
                    command['requests_prefix'] = 'prefix' in options
                    command['requests_address'] = 'address' in options
                    command['requests_dns'] = 'dns' in options
                elif key == 'pool-name':
                    command['uses_pool'] = bool(value)
                    command['pool_name'] = value
                elif key == 'pool-prefix-length':
                    try:
                        command['pool_prefix_length'] = int(value)
                    except ValueError:
                        command['pool_prefix_length'] = value
                elif key in ['disabled', 'add-default-route', 'use-peer-dns']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get DHCPv6 client section summary."""
        return {
            'section': 'DHCPv6 Client',
            'command_count': len(self.commands)
        }


class IPv6DHCPServerParser(BaseSectionParser):
    """Parser for /ipv6 dhcp-server section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse IPv6 DHCP server configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_dhcp_server_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ipv6 dhcp-server',
            'commands': commands
        }
        
    def _parse_dhcp_server_command(self, line: str) -> Dict[str, Any]:
        """Parse a single DHCPv6 server command."""
        command = {'raw_line': line}
        
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
        self._parse_dhcp_server_parameters(params, command)
        
        return command
        
    def _parse_dhcp_server_parameters(self, params: str, command: Dict[str, Any]):
        """Parse DHCPv6 server parameters."""
        parser = IPv6AddressParser()
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
                elif key == 'address-pool':
                    command['uses_address_pool'] = bool(value)
                    command['address_pool'] = value
                elif key == 'lease-time':
                    command['lease_time_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get DHCPv6 server section summary."""
        return {
            'section': 'DHCPv6 Server',
            'command_count': len(self.commands)
        }


class IPv6NeighborDiscoveryParser(BaseSectionParser):
    """Parser for /ipv6 nd section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse IPv6 neighbor discovery configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_nd_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ipv6 nd',
            'commands': commands
        }
        
    def _parse_nd_command(self, line: str) -> Dict[str, Any]:
        """Parse a single neighbor discovery command."""
        command = {'raw_line': line}
        
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
        self._parse_nd_parameters(params, command)
        
        return command
        
    def _parse_nd_parameters(self, params: str, command: Dict[str, Any]):
        """Parse neighbor discovery parameters."""
        parser = IPv6AddressParser()
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
                elif key == 'ra-interval':
                    command['ra_interval_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key == 'ra-lifetime':
                    command['ra_lifetime_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key in ['disabled', 'advertise-mac-address', 'advertise-dns', 'managed-address-configuration', 'other-configuration']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'mtu':
                    try:
                        command['mtu_size'] = int(value)
                        command['jumbo_frames'] = int(value) > 1500
                    except ValueError:
                        command['mtu_size'] = value
                elif key == 'reachable-time':
                    command['reachable_time_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key == 'retransmit-interval':
                    command['retransmit_interval_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get neighbor discovery section summary."""
        return {
            'section': 'IPv6 Neighbor Discovery',
            'command_count': len(self.commands)
        }


class IPv6SettingsParser(BaseSectionParser):
    """Parser for /ipv6 settings section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse IPv6 settings configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_settings_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ipv6 settings',
            'commands': commands
        }
        
    def _parse_settings_command(self, line: str) -> Dict[str, Any]:
        """Parse a single IPv6 settings command."""
        command = {'raw_line': line}
        
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
        """Parse IPv6 settings parameters."""
        parser = IPv6AddressParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key in ['disable-ipv6', 'accept-redirects', 'accept-router-advertisements', 'forward']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'max-neighbor-entries':
                    try:
                        command['max_neighbor_entries'] = int(value)
                    except ValueError:
                        command['max_neighbor_entries'] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get IPv6 settings section summary."""
        return {
            'section': 'IPv6 Settings',
            'command_count': len(self.commands)
        }


# Register IPv6 parsers
SectionParserRegistry.register('/ipv6 address', IPv6AddressParser)
SectionParserRegistry.register('/ipv6 route', IPv6RouteParser)
SectionParserRegistry.register('/ipv6 dhcp-client', IPv6DHCPClientParser)
SectionParserRegistry.register('/ipv6 dhcp-server', IPv6DHCPServerParser)
SectionParserRegistry.register('/ipv6 nd', IPv6NeighborDiscoveryParser)
SectionParserRegistry.register('/ipv6 settings', IPv6SettingsParser)
SectionParserRegistry.register('/ipv6 neighbor', IPv6NeighborDiscoveryParser)  # Alias for nd
SectionParserRegistry.register('/ipv6 firewall filter', IPv6AddressParser)  # Use existing firewall parser
SectionParserRegistry.register('/ipv6 firewall address-list', IPv6AddressParser)  # Use existing address-list parser