"""Tools and monitoring parsers for RouterOS configurations."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class ToolNetwatchParser(BaseSectionParser):
    """Parser for /tool netwatch section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse netwatch configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_netwatch_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/tool netwatch',
            'commands': commands
        }
        
    def _parse_netwatch_command(self, line: str) -> Dict[str, Any]:
        """Parse a single netwatch command."""
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
        self._parse_netwatch_parameters(params, command)
        
        return command
        
    def _parse_netwatch_parameters(self, params: str, command: Dict[str, Any]):
        """Parse netwatch parameters."""
        parts = self._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'host':
                    # Parse monitored host
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['host_ip_valid'] = True
                        command['host_is_private'] = RouterOSPatterns.is_private_ip(network_info[0])
                        command['host_ip'] = network_info[0]
                    else:
                        command['host_ip_valid'] = False
                        command['host_type'] = 'hostname' if '.' in value else 'unknown'
                    command[key] = value
                elif key == 'interval':
                    command['check_interval_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key == 'timeout':
                    command['timeout_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key == 'type':
                    command['monitor_type'] = value
                    command['uses_icmp'] = value == 'icmp'
                    command['uses_tcp'] = value == 'tcp-conn'
                    command['uses_simple'] = value == 'simple'
                elif key == 'port':
                    try:
                        port = int(value)
                        command['monitor_port'] = port
                        command['well_known_port'] = port <= 1024
                    except ValueError:
                        command['monitor_port'] = value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'up-script':
                    command['has_up_script'] = bool(value)
                    command['up_script_length'] = len(value) if value else 0
                elif key == 'down-script':
                    command['has_down_script'] = bool(value)
                    command['down_script_length'] = len(value) if value else 0
                elif key == 'test-script':
                    command['has_test_script'] = bool(value)
                    command['test_script_length'] = len(value) if value else 0
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
        """Get netwatch section summary."""
        return {
            'section': 'Network Monitoring',
            'command_count': len(self.commands)
        }


class ToolEmailParser(BaseSectionParser):
    """Parser for /tool e-mail section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse email configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_email_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/tool e-mail',
            'commands': commands
        }
        
    def _parse_email_command(self, line: str) -> Dict[str, Any]:
        """Parse a single email command."""
        command = {'raw_line': line}
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_email_parameters(params, command)
        
        return command
        
    def _parse_email_parameters(self, params: str, command: Dict[str, Any]):
        """Parse email parameters."""
        parser = ToolNetwatchParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'server':
                    # Parse SMTP server
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['server_type'] = 'ip'
                        command['server_is_private'] = RouterOSPatterns.is_private_ip(network_info[0])
                    else:
                        command['server_type'] = 'hostname'
                    command[key] = value
                elif key == 'port':
                    try:
                        port = int(value)
                        command['smtp_port'] = port
                        command['uses_ssl'] = port == 465
                        command['uses_tls'] = port == 587
                        command['standard_smtp'] = port == 25
                    except ValueError:
                        command['smtp_port'] = value
                elif key == 'from':
                    command['sender_email'] = value
                    command['has_sender'] = bool(value)
                elif key == 'user':
                    command['smtp_username'] = value
                    command['uses_auth'] = bool(value)
                elif key == 'password':
                    command['has_password'] = bool(value)
                    command['password_length'] = len(value) if value else 0
                elif key in ['tls', 'start-tls']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                    command['uses_encryption'] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get email section summary."""
        return {
            'section': 'Email Notifications',
            'command_count': len(self.commands)
        }


class ToolMacServerParser(BaseSectionParser):
    """Parser for /tool mac-server section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse MAC server configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_mac_server_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/tool mac-server',
            'commands': commands
        }
        
    def _parse_mac_server_command(self, line: str) -> Dict[str, Any]:
        """Parse a single MAC server command."""
        command = {'raw_line': line}
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_mac_server_parameters(params, command)
        
        return command
        
    def _parse_mac_server_parameters(self, params: str, command: Dict[str, Any]):
        """Parse MAC server parameters."""
        parser = ToolNetwatchParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'allowed-interface-list':
                    interfaces = [iface.strip() for iface in value.split(',') if iface.strip()]
                    command['allowed_interfaces'] = interfaces
                    command['interface_count'] = len(interfaces)
                    command['restricted_access'] = len(interfaces) > 0
                elif key in ['enabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get MAC server section summary."""
        return {
            'section': 'MAC Server',
            'command_count': len(self.commands)
        }


class ToolGraphingParser(BaseSectionParser):
    """Parser for /tool graphing section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse graphing configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_graphing_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/tool graphing',
            'commands': commands
        }
        
    def _parse_graphing_command(self, line: str) -> Dict[str, Any]:
        """Parse a single graphing command."""
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
        self._parse_graphing_parameters(params, command)
        
        return command
        
    def _parse_graphing_parameters(self, params: str, command: Dict[str, Any]):
        """Parse graphing parameters."""
        parser = ToolNetwatchParser()
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
                elif key == 'store-every':
                    command['store_interval_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key in ['allow-address', 'page-refresh']:
                    # Parse allow-address (IP ranges) and refresh interval
                    if key == 'allow-address':
                        addresses = [addr.strip() for addr in value.split(',') if addr.strip()]
                        command['allowed_addresses'] = addresses
                        command['address_restrictions'] = len(addresses) > 0
                    elif key == 'page-refresh':
                        command['refresh_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key in ['enabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get graphing section summary."""
        return {
            'section': 'SNMP Graphing',
            'command_count': len(self.commands)
        }


class ToolRomonParser(BaseSectionParser):
    """Parser for /tool romon section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse RoMON configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_romon_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/tool romon',
            'commands': commands
        }
        
    def _parse_romon_command(self, line: str) -> Dict[str, Any]:
        """Parse a single RoMON command."""
        command = {'raw_line': line}
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_romon_parameters(params, command)
        
        return command
        
    def _parse_romon_parameters(self, params: str, command: Dict[str, Any]):
        """Parse RoMON parameters."""
        parser = ToolNetwatchParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key in ['enabled', 'discover-interface-list']:
                    if key == 'enabled':
                        command[key] = value.lower() in ['yes', 'true', '1']
                    else:
                        # Parse interface list for discovery
                        interfaces = [iface.strip() for iface in value.split(',') if iface.strip()]
                        command['discovery_interfaces'] = interfaces
                        command['discovery_interface_count'] = len(interfaces)
                    command[key] = value
                elif key == 'secrets':
                    command['has_secrets'] = bool(value)
                    command['secret_count'] = len(value.split(',')) if value else 0
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get RoMON section summary."""
        return {
            'section': 'RoMON',
            'command_count': len(self.commands)
        }


class ToolSnifferParser(BaseSectionParser):
    """Parser for /tool sniffer section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse packet sniffer configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_sniffer_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/tool sniffer',
            'commands': commands
        }
        
    def _parse_sniffer_command(self, line: str) -> Dict[str, Any]:
        """Parse a single sniffer command."""
        command = {'raw_line': line}
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_sniffer_parameters(params, command)
        
        return command
        
    def _parse_sniffer_parameters(self, params: str, command: Dict[str, Any]):
        """Parse sniffer parameters."""
        parser = ToolNetwatchParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'filter-interface':
                    interface_info = RouterOSPatterns.parse_interface_reference(value)
                    command['filter_interface'] = value
                    command['interface_type'] = interface_info['type']
                elif key == 'filter-ip-address':
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['filter_ip_valid'] = True
                        command['filter_is_private'] = RouterOSPatterns.is_private_ip(network_info[0])
                    else:
                        command['filter_ip_valid'] = False
                    command[key] = value
                elif key == 'filter-port':
                    ports = RouterOSPatterns.parse_port_range(value)
                    command['filter_ports'] = ports
                    command['port_count'] = len(ports)
                elif key == 'filter-protocol':
                    command['protocol_filter'] = value
                    command['monitors_tcp'] = 'tcp' in value.lower()
                    command['monitors_udp'] = 'udp' in value.lower()
                    command['monitors_icmp'] = 'icmp' in value.lower()
                elif key == 'memory-limit':
                    # Parse memory limit (usually in MB/KB)
                    if 'M' in value.upper():
                        try:
                            command['memory_limit_mb'] = int(value.upper().replace('M', ''))
                        except ValueError:
                            command['memory_limit_mb'] = value
                    elif 'K' in value.upper():
                        try:
                            command['memory_limit_kb'] = int(value.upper().replace('K', ''))
                            command['memory_limit_mb'] = command['memory_limit_kb'] / 1024
                        except ValueError:
                            command['memory_limit_kb'] = value
                    command[key] = value
                elif key == 'file-name':
                    command['saves_to_file'] = bool(value)
                    command['output_file'] = value
                elif key in ['only-headers', 'streaming-enabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get sniffer section summary."""
        return {
            'section': 'Packet Sniffer',
            'command_count': len(self.commands)
        }


# Register tools and monitoring parsers
SectionParserRegistry.register('/tool netwatch', ToolNetwatchParser)
SectionParserRegistry.register('/tool e-mail', ToolEmailParser)
SectionParserRegistry.register('/tool mac-server', ToolMacServerParser)
SectionParserRegistry.register('/tool mac-server mac-winbox', ToolMacServerParser)  # Reuse MAC server parser
SectionParserRegistry.register('/tool graphing', ToolGraphingParser)
SectionParserRegistry.register('/tool romon', ToolRomonParser)
SectionParserRegistry.register('/tool sniffer', ToolSnifferParser)
SectionParserRegistry.register('/tool torch', ToolSnifferParser)  # Similar to sniffer
SectionParserRegistry.register('/tool ping', ToolNetwatchParser)  # Similar monitoring tool
SectionParserRegistry.register('/tool traceroute', ToolNetwatchParser)  # Similar monitoring tool
SectionParserRegistry.register('/tool bandwidth-test', ToolNetwatchParser)  # Similar tool