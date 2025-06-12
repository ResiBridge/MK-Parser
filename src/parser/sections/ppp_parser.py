"""PPP and tunneling parsers for RouterOS configurations."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class PPPSecretParser(BaseSectionParser):
    """Parser for /ppp secret section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse PPP secret configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_secret_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ppp secret',
            'commands': commands
        }
        
    def _parse_secret_command(self, line: str) -> Dict[str, Any]:
        """Parse a single PPP secret command."""
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
        self._parse_secret_parameters(params, command)
        
        return command
        
    def _parse_secret_parameters(self, params: str, command: Dict[str, Any]):
        """Parse PPP secret parameters."""
        parts = self._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'name':
                    command['username'] = value
                    command[key] = value
                elif key == 'password':
                    command['has_password'] = bool(value)
                    command['password_length'] = len(value) if value else 0
                    # Don't store actual password for security
                elif key == 'service':
                    services = [s.strip() for s in value.split(',')]
                    command['services'] = services
                    command['service_count'] = len(services)
                    command['supports_pppoe'] = 'pppoe' in services
                    command['supports_pptp'] = 'pptp' in services
                    command['supports_l2tp'] = 'l2tp' in services
                    command['supports_ovpn'] = 'ovpn' in services
                elif key == 'local-address':
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['local_ip_valid'] = True
                        command['local_is_private'] = RouterOSPatterns.is_private_ip(network_info[0])
                    else:
                        command['local_ip_valid'] = False
                    command[key] = value
                elif key == 'remote-address':
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['remote_ip_valid'] = True
                        command['remote_is_private'] = RouterOSPatterns.is_private_ip(network_info[0])
                    else:
                        command['remote_ip_valid'] = False
                    command[key] = value
                elif key == 'profile':
                    command['uses_profile'] = value != 'default'
                    command[key] = value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'limit-bytes-in':
                    try:
                        command['upload_limit_bytes'] = int(value)
                    except ValueError:
                        command['upload_limit_bytes'] = value
                elif key == 'limit-bytes-out':
                    try:
                        command['download_limit_bytes'] = int(value)
                    except ValueError:
                        command['download_limit_bytes'] = value
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
        """Get PPP secret section summary."""
        return {
            'section': 'PPP Secrets',
            'command_count': len(self.commands)
        }


class PPPProfileParser(BaseSectionParser):
    """Parser for /ppp profile section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse PPP profile configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_profile_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ppp profile',
            'commands': commands
        }
        
    def _parse_profile_command(self, line: str) -> Dict[str, Any]:
        """Parse a single PPP profile command."""
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
        self._parse_profile_parameters(params, command)
        
        return command
        
    def _parse_profile_parameters(self, params: str, command: Dict[str, Any]):
        """Parse PPP profile parameters."""
        parser = PPPSecretParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'local-address':
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['assigns_ip'] = True
                        command['ip_pool'] = value
                    else:
                        command['assigns_ip'] = False
                    command[key] = value
                elif key == 'dns-server':
                    if ',' in value:
                        dns_servers = [dns.strip() for dns in value.split(',')]
                        command['dns_servers'] = dns_servers
                        command['dns_count'] = len(dns_servers)
                    else:
                        command['dns_servers'] = [value] if value else []
                        command['dns_count'] = 1 if value else 0
                    command[key] = value
                elif key == 'wins-server':
                    command['provides_wins'] = bool(value)
                    command[key] = value
                elif key == 'use-encryption':
                    command['encryption_required'] = value.lower() in ['yes', 'required']
                    command['encryption_optional'] = value.lower() == 'default'
                    command[key] = value
                elif key in ['use-mpls', 'use-compression', 'use-vj-compression']:
                    command[key] = value.lower() in ['yes', 'true', '1', 'default']
                elif key == 'session-timeout':
                    command['timeout_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command['has_timeout'] = command['timeout_seconds'] > 0
                    command[key] = value
                elif key == 'rate-limit':
                    # Parse rate limit (format: upload/download)
                    if '/' in value:
                        parts = value.split('/')
                        if len(parts) == 2:
                            command['upload_limit'] = parts[0].strip()
                            command['download_limit'] = parts[1].strip()
                    command['has_rate_limit'] = bool(value)
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get PPP profile section summary."""
        return {
            'section': 'PPP Profiles',
            'command_count': len(self.commands)
        }


class PPPAAAParser(BaseSectionParser):
    """Parser for /ppp aaa section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse PPP AAA configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_aaa_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ppp aaa',
            'commands': commands
        }
        
    def _parse_aaa_command(self, line: str) -> Dict[str, Any]:
        """Parse a single PPP AAA command."""
        command = {'raw_line': line}
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_aaa_parameters(params, command)
        
        return command
        
    def _parse_aaa_parameters(self, params: str, command: Dict[str, Any]):
        """Parse PPP AAA parameters."""
        parser = PPPSecretParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'use-radius':
                    command['uses_radius'] = value.lower() in ['yes', 'true', '1']
                elif key == 'accounting':
                    command['radius_accounting'] = value.lower() in ['yes', 'true', '1']
                elif key == 'interim-update':
                    command['interim_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command['has_interim_updates'] = command['interim_seconds'] > 0
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get PPP AAA section summary."""
        return {
            'section': 'PPP AAA',
            'command_count': len(self.commands)
        }


class TunnelInterfaceParser(BaseSectionParser):
    """Generic parser for tunnel interfaces (EoIP, GRE, IPIP, etc.)."""
    
    def __init__(self, tunnel_type: str = "tunnel"):
        super().__init__()
        self.tunnel_type = tunnel_type
        
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse tunnel interface configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_tunnel_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': f'/interface {self.tunnel_type}',
            'commands': commands
        }
        
    def _parse_tunnel_command(self, line: str) -> Dict[str, Any]:
        """Parse a single tunnel command."""
        command = {'raw_line': line, 'tunnel_type': self.tunnel_type}
        
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
        self._parse_tunnel_parameters(params, command)
        
        return command
        
    def _parse_tunnel_parameters(self, params: str, command: Dict[str, Any]):
        """Parse tunnel parameters."""
        parser = PPPSecretParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'remote-address':
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['remote_ip_valid'] = True
                        command['remote_is_private'] = RouterOSPatterns.is_private_ip(network_info[0])
                        command['remote_ip'] = network_info[0]
                    else:
                        command['remote_ip_valid'] = False
                    command[key] = value
                elif key == 'local-address':
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['local_ip_valid'] = True
                        command['local_is_private'] = RouterOSPatterns.is_private_ip(network_info[0])
                        command['local_ip'] = network_info[0]
                    else:
                        command['local_ip_valid'] = False
                    command[key] = value
                elif key == 'tunnel-id':
                    try:
                        command['tunnel_id'] = int(value)
                    except ValueError:
                        command['tunnel_id'] = value
                elif key == 'mtu':
                    try:
                        command['mtu_size'] = int(value)
                        command['jumbo_frames'] = int(value) > 1500
                    except ValueError:
                        command['mtu_size'] = value
                elif key in ['disabled', 'keepalive']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'ipsec-secret':
                    command['uses_ipsec'] = bool(value)
                    command['ipsec_key_length'] = len(value) if value else 0
                elif key == 'dscp':
                    try:
                        command['dscp_value'] = int(value)
                    except ValueError:
                        command['dscp_value'] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get tunnel section summary."""
        return {
            'section': f'{self.tunnel_type.title()} Tunnels',
            'command_count': len(self.commands)
        }


class PPPoEClientParser(TunnelInterfaceParser):
    """Parser for /interface pppoe-client section."""
    
    def __init__(self):
        super().__init__('pppoe-client')
        
    def _parse_tunnel_parameters(self, params: str, command: Dict[str, Any]):
        """Parse PPPoE client specific parameters."""
        super()._parse_tunnel_parameters(params, command)
        
        # PPPoE-specific parsing
        parser = PPPSecretParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'interface':
                    command['physical_interface'] = value
                elif key == 'user':
                    command['username'] = value
                elif key == 'password':
                    command['has_password'] = bool(value)
                elif key == 'service-name':
                    command['service_name'] = value
                    command['uses_service_name'] = bool(value)
                elif key == 'ac-name':
                    command['access_concentrator'] = value
                    command['uses_ac_name'] = bool(value)
                elif key in ['add-default-route', 'use-peer-dns']:
                    command[key] = value.lower() in ['yes', 'true', '1']


class PPPoEServerParser(TunnelInterfaceParser):
    """Parser for /interface pppoe-server section."""
    
    def __init__(self):
        super().__init__('pppoe-server')
        
    def _parse_tunnel_parameters(self, params: str, command: Dict[str, Any]):
        """Parse PPPoE server specific parameters."""
        super()._parse_tunnel_parameters(params, command)
        
        # PPPoE server-specific parsing
        parser = PPPSecretParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'interface':
                    command['physical_interface'] = value
                elif key == 'service-name':
                    command['service_name'] = value
                elif key == 'ac-name':
                    command['access_concentrator'] = value
                elif key == 'authentication':
                    auth_methods = [auth.strip() for auth in value.split(',')]
                    command['auth_methods'] = auth_methods
                    command['uses_pap'] = 'pap' in auth_methods
                    command['uses_chap'] = 'chap' in auth_methods
                    command['uses_mschap'] = 'mschap1' in auth_methods or 'mschap2' in auth_methods
                elif key == 'default-profile':
                    command['profile'] = value


# Register PPP and tunnel parsers
SectionParserRegistry.register('/ppp secret', PPPSecretParser)
SectionParserRegistry.register('/ppp profile', PPPProfileParser)
SectionParserRegistry.register('/ppp aaa', PPPAAAParser)
SectionParserRegistry.register('/ppp', PPPSecretParser)  # Generic fallback

# Tunnel interface parsers
SectionParserRegistry.register('/interface pppoe-client', PPPoEClientParser)
SectionParserRegistry.register('/interface pppoe-server', PPPoEServerParser)
SectionParserRegistry.register('/interface pptp-client', lambda: TunnelInterfaceParser('pptp-client'))
SectionParserRegistry.register('/interface pptp-server', lambda: TunnelInterfaceParser('pptp-server'))
SectionParserRegistry.register('/interface l2tp-client', lambda: TunnelInterfaceParser('l2tp-client'))
SectionParserRegistry.register('/interface l2tp-server', lambda: TunnelInterfaceParser('l2tp-server'))
SectionParserRegistry.register('/interface sstp-client', lambda: TunnelInterfaceParser('sstp-client'))
SectionParserRegistry.register('/interface sstp-server', lambda: TunnelInterfaceParser('sstp-server'))
SectionParserRegistry.register('/interface ovpn-client', lambda: TunnelInterfaceParser('ovpn-client'))
SectionParserRegistry.register('/interface ovpn-server', lambda: TunnelInterfaceParser('ovpn-server'))
SectionParserRegistry.register('/interface eoip', lambda: TunnelInterfaceParser('eoip'))
SectionParserRegistry.register('/interface gre', lambda: TunnelInterfaceParser('gre'))
SectionParserRegistry.register('/interface ipip', lambda: TunnelInterfaceParser('ipip'))
SectionParserRegistry.register('/interface 6to4', lambda: TunnelInterfaceParser('6to4'))