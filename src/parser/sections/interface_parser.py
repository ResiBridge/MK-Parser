"""Interface section parsers for RouterOS configurations."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class InterfaceParser(BaseSectionParser):
    """Parser for /interface section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse interface configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_interface_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/interface',
            'commands': commands
        }
        
    def _parse_interface_command(self, line: str) -> Dict[str, Any]:
        """Parse a single interface command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('add '):
            command['action'] = 'add'
            params = line[4:].strip()
        elif line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        elif line.startswith('remove '):
            command['action'] = 'remove'
            params = line[7:].strip()
        else:
            # Direct parameter line
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_parameters(params, command)
        
        return command
        
    def _parse_parameters(self, params: str, command: Dict[str, Any]):
        """Parse interface parameters."""
        # Split parameters carefully (handle quoted values)
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
            
        # Parse each parameter
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                # Type-specific parsing
                if key == 'vlan-id':
                    try:
                        command[key] = int(value)
                    except ValueError:
                        command[key] = value
                elif key in ['disabled', 'running', 'slave']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'mtu':
                    try:
                        command[key] = int(value)
                    except ValueError:
                        command[key] = value
                elif key == 'mac-address':
                    if RouterOSPatterns.validate_mac_address(value):
                        command[key] = value
                    else:
                        command[key] = value  # Keep invalid MAC for error reporting
                else:
                    command[key] = value
            else:
                # Flag parameter
                command[part] = True
                
    def get_summary(self) -> Dict[str, Any]:
        """Get interface section summary."""
        return {
            'section': 'Interfaces',
            'command_count': len(self.commands)
        }


class BridgeParser(BaseSectionParser):
    """Parser for /interface bridge section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse bridge configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_bridge_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/interface bridge',
            'commands': commands
        }
        
    def _parse_bridge_command(self, line: str) -> Dict[str, Any]:
        """Parse a single bridge command."""
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
        self._parse_bridge_parameters(params, command)
        
        return command
        
    def _parse_bridge_parameters(self, params: str, command: Dict[str, Any]):
        """Parse bridge-specific parameters."""
        # Use same parameter parsing as interface
        parser = InterfaceParser()
        parser._parse_parameters(params, command)
        
        # Bridge-specific parameter handling
        if 'stp' in command:
            command['stp_enabled'] = command['stp'].lower() in ['yes', 'true', '1']
            
        if 'forward-delay' in command:
            command['forward_delay_seconds'] = RouterOSPatterns.parse_time_value(command['forward-delay'])
            
        if 'max-age' in command:
            command['max_age_seconds'] = RouterOSPatterns.parse_time_value(command['max-age'])
            
    def get_summary(self) -> Dict[str, Any]:
        """Get bridge section summary."""
        return {
            'section': 'Bridge',
            'command_count': len(self.commands)
        }


class BridgePortParser(BaseSectionParser):
    """Parser for /interface bridge port section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse bridge port configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_bridge_port_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/interface bridge port',
            'commands': commands
        }
        
    def _parse_bridge_port_command(self, line: str) -> Dict[str, Any]:
        """Parse a single bridge port command."""
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
        self._parse_bridge_port_parameters(params, command)
        
        return command
        
    def _parse_bridge_port_parameters(self, params: str, command: Dict[str, Any]):
        """Parse bridge port parameters."""
        # Use same parameter parsing as interface
        parser = InterfaceParser()
        parser._parse_parameters(params, command)
        
        # Bridge port specific handling
        if 'pvid' in command:
            try:
                pvid = int(command['pvid'])
                if RouterOSPatterns.validate_vlan_id(pvid):
                    command['pvid'] = pvid
                else:
                    command['pvid_invalid'] = True
            except ValueError:
                command['pvid_invalid'] = True
                
    def get_summary(self) -> Dict[str, Any]:
        """Get bridge port section summary."""
        return {
            'section': 'Bridge Ports',
            'command_count': len(self.commands)
        }


class VLANParser(BaseSectionParser):
    """Parser for /interface vlan section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse VLAN configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_vlan_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/interface vlan',
            'commands': commands
        }
        
    def _parse_vlan_command(self, line: str) -> Dict[str, Any]:
        """Parse a single VLAN command."""
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
        self._parse_vlan_parameters(params, command)
        
        return command
        
    def _parse_vlan_parameters(self, params: str, command: Dict[str, Any]):
        """Parse VLAN-specific parameters."""
        # Use same parameter parsing as interface
        parser = InterfaceParser()
        parser._parse_parameters(params, command)
        
        # VLAN-specific validation
        if 'vlan-id' in command:
            try:
                vlan_id = int(command['vlan-id'])
                if not RouterOSPatterns.validate_vlan_id(vlan_id):
                    command['vlan_id_invalid'] = True
            except (ValueError, TypeError):
                command['vlan_id_invalid'] = True
                
    def get_summary(self) -> Dict[str, Any]:
        """Get VLAN section summary."""
        return {
            'section': 'VLANs',
            'command_count': len(self.commands)
        }


# Register parsers
SectionParserRegistry.register('/interface', InterfaceParser)
SectionParserRegistry.register('/interface bridge', BridgeParser)
SectionParserRegistry.register('/interface bridge port', BridgePortParser)
SectionParserRegistry.register('/interface vlan', VLANParser)
SectionParserRegistry.register('/interface ethernet', InterfaceParser)
SectionParserRegistry.register('/interface wireless', InterfaceParser)
SectionParserRegistry.register('/interface bonding', InterfaceParser)
SectionParserRegistry.register('/interface pppoe-*', InterfaceParser)
SectionParserRegistry.register('/interface l2tp-*', InterfaceParser)
SectionParserRegistry.register('/interface sstp-*', InterfaceParser)
SectionParserRegistry.register('/interface ovpn-*', InterfaceParser)
SectionParserRegistry.register('/interface eoip', InterfaceParser)
SectionParserRegistry.register('/interface gre', InterfaceParser)
SectionParserRegistry.register('/interface ipip', InterfaceParser)
SectionParserRegistry.register('/interface 6to4', InterfaceParser)
SectionParserRegistry.register('/interface lte', InterfaceParser)