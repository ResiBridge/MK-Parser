"""Wireless and CAPsMAN parsers for RouterOS configurations."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class WirelessParser(BaseSectionParser):
    """Parser for /interface wireless section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse wireless interface configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_wireless_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/interface wireless',
            'commands': commands
        }
        
    def _parse_wireless_command(self, line: str) -> Dict[str, Any]:
        """Parse a single wireless command."""
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
        self._parse_wireless_parameters(params, command)
        
        return command
        
    def _parse_wireless_parameters(self, params: str, command: Dict[str, Any]):
        """Parse wireless parameters."""
        parts = self._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'mode':
                    command['wireless_mode'] = value
                    command['is_ap'] = value in ['ap-bridge', 'bridge']
                    command['is_station'] = value in ['station', 'station-bridge']
                elif key == 'ssid':
                    command['network_name'] = value
                    command['ssid_length'] = len(value)
                    command[key] = value
                elif key == 'frequency':
                    try:
                        freq = int(value)
                        if 2400 <= freq <= 2500:
                            command['band'] = '2.4GHz'
                        elif 5000 <= freq <= 6000:
                            command['band'] = '5GHz'
                        else:
                            command['band'] = 'unknown'
                        command['frequency_mhz'] = freq
                    except ValueError:
                        command['frequency_mhz'] = value
                        command['band'] = 'auto' if value == 'auto' else 'unknown'
                    command[key] = value
                elif key == 'channel-width':
                    command['channel_width'] = value
                    try:
                        width = int(value.replace('mhz', '').replace('MHz', ''))
                        command['channel_width_mhz'] = width
                    except (ValueError, AttributeError):
                        command['channel_width_mhz'] = 0
                elif key == 'wireless-protocol':
                    command['protocol'] = value
                    command['supports_n'] = 'n' in value.lower()
                    command['supports_ac'] = 'ac' in value.lower()
                    command['supports_ax'] = 'ax' in value.lower()
                elif key == 'security-profile':
                    command['has_security'] = value != 'default'
                    command[key] = value
                elif key in ['disabled', 'default-forwarding', 'wds-mode']:
                    command[key] = value.lower() in ['yes', 'true', '1', 'enabled', 'dynamic']
                elif key == 'tx-power':
                    try:
                        power = int(value)
                        command['tx_power_dbm'] = power
                        command['high_power'] = power > 20
                    except ValueError:
                        command['tx_power_dbm'] = value
                    command[key] = value
                elif key == 'distance':
                    command['distance'] = value
                    if value == 'indoors':
                        command['indoor_mode'] = True
                    elif value.isdigit():
                        command['distance_km'] = int(value)
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
        """Get wireless section summary."""
        return {
            'section': 'Wireless Interfaces',
            'command_count': len(self.commands)
        }


class WirelessSecurityProfileParser(BaseSectionParser):
    """Parser for /interface wireless security-profiles section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse wireless security profiles."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_security_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/interface wireless security-profiles',
            'commands': commands
        }
        
    def _parse_security_command(self, line: str) -> Dict[str, Any]:
        """Parse a single security profile command."""
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
        self._parse_security_parameters(params, command)
        
        return command
        
    def _parse_security_parameters(self, params: str, command: Dict[str, Any]):
        """Parse security profile parameters."""
        parser = WirelessParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'mode':
                    command['security_mode'] = value
                    command['is_open'] = value == 'none'
                    command['uses_wpa'] = 'wpa' in value.lower()
                    command['uses_wpa2'] = 'wpa2' in value.lower()
                    command['uses_wpa3'] = 'wpa3' in value.lower()
                elif key == 'authentication-types':
                    auth_types = [auth.strip() for auth in value.split(',')]
                    command['auth_types'] = auth_types
                    command['uses_psk'] = 'wpa-psk' in auth_types or 'wpa2-psk' in auth_types
                    command['uses_eap'] = 'wpa-eap' in auth_types or 'wpa2-eap' in auth_types
                elif key == 'wpa-pre-shared-key':
                    command['has_psk'] = bool(value)
                    command['psk_length'] = len(value) if value else 0
                    # Don't store actual PSK for security
                elif key == 'wpa2-pre-shared-key':
                    command['has_wpa2_psk'] = bool(value)
                    command['wpa2_psk_length'] = len(value) if value else 0
                elif key == 'group-ciphers':
                    ciphers = [cipher.strip() for cipher in value.split(',')]
                    command['group_ciphers'] = ciphers
                    command['uses_aes'] = 'aes-ccm' in ciphers
                    command['uses_tkip'] = 'tkip' in ciphers
                elif key == 'unicast-ciphers':
                    ciphers = [cipher.strip() for cipher in value.split(',')]
                    command['unicast_ciphers'] = ciphers
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get security profiles section summary."""
        return {
            'section': 'Wireless Security Profiles',
            'command_count': len(self.commands)
        }


class CapsManManagerParser(BaseSectionParser):
    """Parser for /caps-man manager section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse CAPsMAN manager configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_manager_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/caps-man manager',
            'commands': commands
        }
        
    def _parse_manager_command(self, line: str) -> Dict[str, Any]:
        """Parse a single CAPsMAN manager command."""
        command = {'raw_line': line}
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_manager_parameters(params, command)
        
        return command
        
    def _parse_manager_parameters(self, params: str, command: Dict[str, Any]):
        """Parse CAPsMAN manager parameters."""
        parser = WirelessParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key in ['enabled', 'upgrade-policy']:
                    command[key] = value.lower() in ['yes', 'true', '1', 'require-same-version']
                elif key == 'certificate':
                    command['uses_certificate'] = value != 'none'
                    command[key] = value
                elif key == 'package-path':
                    command['has_package_path'] = bool(value)
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get CAPsMAN manager section summary."""
        return {
            'section': 'CAPsMAN Manager',
            'command_count': len(self.commands)
        }


class CapsManConfigurationParser(BaseSectionParser):
    """Parser for /caps-man configuration section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse CAPsMAN configuration profiles."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_config_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/caps-man configuration',
            'commands': commands
        }
        
    def _parse_config_command(self, line: str) -> Dict[str, Any]:
        """Parse a single CAPsMAN configuration command."""
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
            
        # Parse parameters (reuse wireless parser logic)
        wireless_parser = WirelessParser()
        wireless_parser._parse_wireless_parameters(params, command)
        
        return command
        
    def get_summary(self) -> Dict[str, Any]:
        """Get CAPsMAN configuration section summary."""
        return {
            'section': 'CAPsMAN Configurations',
            'command_count': len(self.commands)
        }


class CapsManDatapathParser(BaseSectionParser):
    """Parser for /caps-man datapath section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse CAPsMAN datapath configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_datapath_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/caps-man datapath',
            'commands': commands
        }
        
    def _parse_datapath_command(self, line: str) -> Dict[str, Any]:
        """Parse a single datapath command."""
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
        self._parse_datapath_parameters(params, command)
        
        return command
        
    def _parse_datapath_parameters(self, params: str, command: Dict[str, Any]):
        """Parse datapath parameters."""
        parser = WirelessParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'local-forwarding':
                    command['forwards_locally'] = value.lower() in ['yes', 'true', '1']
                elif key == 'client-to-client-forwarding':
                    command['client_isolation'] = value.lower() not in ['yes', 'true', '1']
                elif key == 'bridge':
                    command['uses_bridge'] = bool(value)
                    command['bridge_interface'] = value
                elif key == 'vlan-id':
                    try:
                        vlan_id = int(value)
                        command['vlan_valid'] = RouterOSPatterns.validate_vlan_id(vlan_id)
                        command['vlan_id'] = vlan_id
                    except ValueError:
                        command['vlan_valid'] = False
                        command['vlan_id'] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get datapath section summary."""
        return {
            'section': 'CAPsMAN Datapaths',
            'command_count': len(self.commands)
        }


class CapsManChannelParser(BaseSectionParser):
    """Parser for /caps-man channel section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse CAPsMAN channel configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_channel_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/caps-man channel',
            'commands': commands
        }
        
    def _parse_channel_command(self, line: str) -> Dict[str, Any]:
        """Parse a single channel command."""
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
            
        # Parse parameters (reuse wireless parser logic for frequency handling)
        wireless_parser = WirelessParser()
        wireless_parser._parse_wireless_parameters(params, command)
        
        return command
        
    def get_summary(self) -> Dict[str, Any]:
        """Get channel section summary."""
        return {
            'section': 'CAPsMAN Channels',
            'command_count': len(self.commands)
        }


# Register wireless and CAPsMAN parsers
SectionParserRegistry.register('/interface wireless', WirelessParser)
SectionParserRegistry.register('/interface wireless security-profiles', WirelessSecurityProfileParser)
SectionParserRegistry.register('/caps-man manager', CapsManManagerParser)
SectionParserRegistry.register('/caps-man configuration', CapsManConfigurationParser)
SectionParserRegistry.register('/caps-man datapath', CapsManDatapathParser)
SectionParserRegistry.register('/caps-man channel', CapsManChannelParser)
SectionParserRegistry.register('/caps-man security', WirelessSecurityProfileParser)  # Reuse security parser
SectionParserRegistry.register('/caps-man interface', WirelessParser)  # Reuse wireless parser
SectionParserRegistry.register('/caps-man provisioning', CapsManConfigurationParser)  # Reuse config parser