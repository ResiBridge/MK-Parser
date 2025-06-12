"""Routing protocol parsers for RouterOS configurations."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class RoutingOSPFInstanceParser(BaseSectionParser):
    """Parser for /routing ospf instance section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse OSPF instance configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_ospf_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/routing ospf instance',
            'commands': commands
        }
        
    def _parse_ospf_command(self, line: str) -> Dict[str, Any]:
        """Parse a single OSPF instance command."""
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
        self._parse_ospf_parameters(params, command)
        
        return command
        
    def _parse_ospf_parameters(self, params: str, command: Dict[str, Any]):
        """Parse OSPF instance parameters."""
        parts = self._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'router-id':
                    # Validate router ID (should be IP format)
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['router_id_valid'] = True
                    else:
                        command['router_id_valid'] = False
                    command[key] = value
                elif key == 'distribute-default':
                    command['distributes_default'] = value.lower() in ['always', 'if-installed-as-default']
                    command[key] = value
                elif key in ['disabled', 'redistribute-connected', 'redistribute-static', 'redistribute-ospf']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'metric-default':
                    try:
                        command['metric_default'] = int(value)
                    except ValueError:
                        command['metric_default'] = value
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
        """Get OSPF instance section summary."""
        return {
            'section': 'OSPF Instances',
            'command_count': len(self.commands)
        }


class RoutingOSPFAreaParser(BaseSectionParser):
    """Parser for /routing ospf area section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse OSPF area configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_area_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/routing ospf area',
            'commands': commands
        }
        
    def _parse_area_command(self, line: str) -> Dict[str, Any]:
        """Parse a single OSPF area command."""
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
        parser = RoutingOSPFInstanceParser()
        parser._parse_ospf_parameters(params, command)
        
        # Area-specific parsing
        if 'area-id' in command:
            area_id = command['area-id']
            if area_id == '0.0.0.0':
                command['is_backbone_area'] = True
            else:
                command['is_backbone_area'] = False
                
        if 'type' in command:
            area_type = command['type']
            command['area_type'] = area_type
            command['is_stub'] = area_type in ['stub', 'nssa']
            
        return command
        
    def get_summary(self) -> Dict[str, Any]:
        """Get OSPF area section summary."""
        return {
            'section': 'OSPF Areas',
            'command_count': len(self.commands)
        }


class RoutingBGPInstanceParser(BaseSectionParser):
    """Parser for /routing bgp instance section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse BGP instance configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_bgp_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/routing bgp instance',
            'commands': commands
        }
        
    def _parse_bgp_command(self, line: str) -> Dict[str, Any]:
        """Parse a single BGP instance command."""
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
        self._parse_bgp_parameters(params, command)
        
        return command
        
    def _parse_bgp_parameters(self, params: str, command: Dict[str, Any]):
        """Parse BGP instance parameters."""
        parser = RoutingOSPFInstanceParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'as':
                    try:
                        command['as_number'] = int(value)
                        # Classify AS number type
                        if 1 <= int(value) <= 64511:
                            command['as_type'] = 'public'
                        elif 64512 <= int(value) <= 65534:
                            command['as_type'] = 'private'
                        else:
                            command['as_type'] = 'extended'
                    except ValueError:
                        command['as_number'] = value
                        command['as_type'] = 'invalid'
                elif key == 'router-id':
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    command['router_id_valid'] = network_info is not None
                    command[key] = value
                elif key in ['disabled', 'redistribute-connected', 'redistribute-static', 'redistribute-ospf']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'client-to-client-reflection':
                    command['route_reflection'] = value.lower() in ['yes', 'true', '1']
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get BGP instance section summary."""
        return {
            'section': 'BGP Instances',
            'command_count': len(self.commands)
        }


class RoutingBGPPeerParser(BaseSectionParser):
    """Parser for /routing bgp peer section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse BGP peer configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_peer_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/routing bgp peer',
            'commands': commands
        }
        
    def _parse_peer_command(self, line: str) -> Dict[str, Any]:
        """Parse a single BGP peer command."""
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
        self._parse_peer_parameters(params, command)
        
        return command
        
    def _parse_peer_parameters(self, params: str, command: Dict[str, Any]):
        """Parse BGP peer parameters."""
        parser = RoutingOSPFInstanceParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'remote-address':
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['peer_ip_valid'] = True
                        command['peer_is_private'] = RouterOSPatterns.is_private_ip(network_info[0])
                    else:
                        command['peer_ip_valid'] = False
                    command[key] = value
                elif key == 'remote-as':
                    try:
                        command['remote_as_number'] = int(value)
                    except ValueError:
                        command['remote_as_number'] = value
                elif key in ['disabled', 'passive', 'route-reflect']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'tcp-md5-key':
                    command['has_md5_auth'] = bool(value)
                    command['auth_key_length'] = len(value) if value else 0
                elif key in ['hold-time', 'keepalive-time']:
                    command[f"{key.replace('-', '_')}_seconds"] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get BGP peer section summary."""
        return {
            'section': 'BGP Peers',
            'command_count': len(self.commands)
        }


class RoutingRIPParser(BaseSectionParser):
    """Parser for /routing rip section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse RIP configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_rip_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/routing rip',
            'commands': commands
        }
        
    def _parse_rip_command(self, line: str) -> Dict[str, Any]:
        """Parse a single RIP command."""
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
        self._parse_rip_parameters(params, command)
        
        return command
        
    def _parse_rip_parameters(self, params: str, command: Dict[str, Any]):
        """Parse RIP parameters."""
        parser = RoutingOSPFInstanceParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key in ['disabled', 'redistribute-connected', 'redistribute-static', 'redistribute-ospf']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'metric-default':
                    try:
                        command['metric_default'] = int(value)
                    except ValueError:
                        command['metric_default'] = value
                elif key == 'timeout':
                    command['timeout_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get RIP section summary."""
        return {
            'section': 'RIP',
            'command_count': len(self.commands)
        }


class RoutingFilterParser(BaseSectionParser):
    """Parser for /routing filter section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse routing filter configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_filter_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/routing filter',
            'commands': commands
        }
        
    def _parse_filter_command(self, line: str) -> Dict[str, Any]:
        """Parse a single routing filter command."""
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
        self._parse_filter_parameters(params, command)
        
        return command
        
    def _parse_filter_parameters(self, params: str, command: Dict[str, Any]):
        """Parse routing filter parameters."""
        parser = RoutingOSPFInstanceParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'action':
                    command['filter_action'] = value
                    command['permits_route'] = value == 'accept'
                elif key == 'prefix':
                    # Parse prefix filter
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['prefix_valid'] = True
                        command['network'] = network_info[1]
                        command['prefix_length'] = network_info[2]
                    else:
                        command['prefix_valid'] = False
                    command[key] = value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get routing filter section summary."""
        return {
            'section': 'Routing Filters',
            'command_count': len(self.commands)
        }


# Register routing parsers
SectionParserRegistry.register('/routing ospf instance', RoutingOSPFInstanceParser)
SectionParserRegistry.register('/routing ospf area', RoutingOSPFAreaParser)
SectionParserRegistry.register('/routing ospf interface', RoutingOSPFInstanceParser)  # Use generic OSPF parser
SectionParserRegistry.register('/routing bgp instance', RoutingBGPInstanceParser)
SectionParserRegistry.register('/routing bgp peer', RoutingBGPPeerParser)
SectionParserRegistry.register('/routing rip', RoutingRIPParser)
SectionParserRegistry.register('/routing filter', RoutingFilterParser)
SectionParserRegistry.register('/routing table', RoutingFilterParser)  # Use generic filter parser