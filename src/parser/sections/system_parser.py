"""System section parsers for RouterOS configurations."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class SystemIdentityParser(BaseSectionParser):
    """Parser for /system identity section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse system identity configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_identity_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/system identity',
            'commands': commands
        }
        
    def _parse_identity_command(self, line: str) -> Dict[str, Any]:
        """Parse a single identity command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_identity_parameters(params, command)
        
        return command
        
    def _parse_identity_parameters(self, params: str, command: Dict[str, Any]):
        """Parse identity parameters."""
        parts = self._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'name':
                    command['name'] = value
                    command['device_name'] = value  # Alias for easier access
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
        """Get identity section summary."""
        return {
            'section': 'System Identity',
            'command_count': len(self.commands)
        }


class SystemClockParser(BaseSectionParser):
    """Parser for /system clock section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse system clock configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_clock_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/system clock',
            'commands': commands
        }
        
    def _parse_clock_command(self, line: str) -> Dict[str, Any]:
        """Parse a single clock command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_clock_parameters(params, command)
        
        return command
        
    def _parse_clock_parameters(self, params: str, command: Dict[str, Any]):
        """Parse clock parameters."""
        parser = SystemIdentityParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'time-zone-name':
                    command['timezone'] = value
                    command[key] = value
                elif key == 'time-zone-autodetect':
                    command['autodetect_timezone'] = value.lower() in ['yes', 'true', '1']
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get clock section summary."""
        return {
            'section': 'System Clock',
            'command_count': len(self.commands)
        }


class UserParser(BaseSectionParser):
    """Parser for /user section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse user configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_user_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/user',
            'commands': commands
        }
        
    def _parse_user_command(self, line: str) -> Dict[str, Any]:
        """Parse a single user command."""
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
        self._parse_user_parameters(params, command)
        
        return command
        
    def _parse_user_parameters(self, params: str, command: Dict[str, Any]):
        """Parse user parameters."""
        parser = SystemIdentityParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'group':
                    command['group'] = value
                    # Classify user privilege level
                    if value == 'full':
                        command['privilege_level'] = 'admin'
                    elif value in ['read', 'write']:
                        command['privilege_level'] = 'user'
                    else:
                        command['privilege_level'] = 'custom'
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'password':
                    # Don't store actual password, just note that it's set
                    command['has_password'] = bool(value)
                    command['password_length'] = len(value) if value else 0
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get user section summary."""
        return {
            'section': 'Users',
            'command_count': len(self.commands)
        }


class IPServiceParser(BaseSectionParser):
    """Parser for /ip service section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse IP service configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_service_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/ip service',
            'commands': commands
        }
        
    def _parse_service_command(self, line: str) -> Dict[str, Any]:
        """Parse a single service command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_service_parameters(params, command)
        
        return command
        
    def _parse_service_parameters(self, params: str, command: Dict[str, Any]):
        """Parse service parameters."""
        parser = SystemIdentityParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'port':
                    # Parse port specification
                    ports = RouterOSPatterns.parse_port_range(value)
                    command['ports'] = ports
                    command['port'] = value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                    command['enabled'] = not (value.lower() in ['yes', 'true', '1'])
                elif key == 'address':
                    # Parse allowed addresses (can be network ranges)
                    if ',' in value:
                        addresses = [addr.strip() for addr in value.split(',')]
                        command['allowed_addresses'] = addresses
                    else:
                        command['allowed_addresses'] = [value] if value else []
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get service section summary."""
        return {
            'section': 'IP Services',
            'command_count': len(self.commands)
        }


class SystemNoteParser(BaseSectionParser):
    """Parser for /system note section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse system note configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_note_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/system note',
            'commands': commands
        }
        
    def _parse_note_command(self, line: str) -> Dict[str, Any]:
        """Parse a single note command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_note_parameters(params, command)
        
        return command
        
    def _parse_note_parameters(self, params: str, command: Dict[str, Any]):
        """Parse note parameters."""
        parser = SystemIdentityParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'show-at-login':
                    command['login_message'] = value
                    command[key] = value
                elif key == 'note':
                    command['note_text'] = value
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get note section summary."""
        return {
            'section': 'System Note',
            'command_count': len(self.commands)
        }


class PasswordParser(BaseSectionParser):
    """Parser for /password section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse password configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_password_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/password',
            'commands': commands
        }
        
    def _parse_password_command(self, line: str) -> Dict[str, Any]:
        """Parse a single password command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_password_parameters(params, command)
        
        return command
        
    def _parse_password_parameters(self, params: str, command: Dict[str, Any]):
        """Parse password parameters."""
        parser = SystemIdentityParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'password':
                    # Don't store the actual password, just metadata
                    command['password_set'] = bool(value)
                    command['password_length'] = len(value) if value else 0
                    command['password_redacted'] = '***REDACTED***' if value else ''
                elif key == 'old-password':
                    command['old_password_provided'] = bool(value)
                elif key in ['confirm-with-old-password']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get password section summary."""
        return {
            'section': 'Password Configuration',
            'command_count': len(self.commands)
        }


class ImportParser(BaseSectionParser):
    """Parser for /import section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse import configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_import_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/import',
            'commands': commands
        }
        
    def _parse_import_command(self, line: str) -> Dict[str, Any]:
        """Parse a single import command."""
        command = {'raw_line': line}
        
        # Most import commands are just filenames
        if line.strip():
            filename = line.strip()
            command['action'] = 'import'
            command['filename'] = filename
            command['file_extension'] = filename.split('.')[-1] if '.' in filename else ''
            command['is_rsc_file'] = filename.endswith('.rsc')
            command['is_backup_file'] = filename.endswith('.backup')
        
        return command
        
    def get_summary(self) -> Dict[str, Any]:
        """Get import section summary."""
        return {
            'section': 'Import Operations',
            'command_count': len(self.commands)
        }


class ExportParser(BaseSectionParser):
    """Parser for /export section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse export configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_export_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/export',
            'commands': commands
        }
        
    def _parse_export_command(self, line: str) -> Dict[str, Any]:
        """Parse a single export command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if 'file=' in line:
            command['action'] = 'export'
            parts = line.split()
            for part in parts:
                if part.startswith('file='):
                    filename = part[5:].strip('"')
                    command['filename'] = filename
                    command['file_extension'] = filename.split('.')[-1] if '.' in filename else ''
                    command['is_rsc_file'] = filename.endswith('.rsc')
                elif part in ['compact', 'verbose']:
                    command['format'] = part
                elif part.startswith('show-sensitive'):
                    command['show_sensitive'] = part.split('=')[1] == 'yes' if '=' in part else True
        else:
            command['action'] = 'export'
            command['console_output'] = True
        
        return command
        
    def get_summary(self) -> Dict[str, Any]:
        """Get export section summary."""
        return {
            'section': 'Export Operations',
            'command_count': len(self.commands)
        }


class ConsoleParser(BaseSectionParser):
    """Parser for /console section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse console configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_console_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/console',
            'commands': commands
        }
        
    def _parse_console_command(self, line: str) -> Dict[str, Any]:
        """Parse a single console command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_console_parameters(params, command)
        
        return command
        
    def _parse_console_parameters(self, params: str, command: Dict[str, Any]):
        """Parse console parameters."""
        parser = SystemIdentityParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'auto-logout':
                    command['auto_logout_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key == 'session-timeout':
                    command['session_timeout_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key in ['silent-boot']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get console section summary."""
        return {
            'section': 'Console Configuration',
            'command_count': len(self.commands)
        }


class FileParser(BaseSectionParser):
    """Parser for /file section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse file system management."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_file_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/file',
            'commands': commands
        }
        
    def _parse_file_command(self, line: str) -> Dict[str, Any]:
        """Parse a single file command."""
        command = {'raw_line': line}
        
        # File commands can be various operations
        if line.startswith('remove '):
            command['action'] = 'remove'
            filename = line[7:].strip()
            command['filename'] = filename
        elif line.startswith('copy '):
            command['action'] = 'copy'
            params = line[5:].strip()
            # Simple parsing for copy operations
            if ' to ' in params:
                src, dst = params.split(' to ', 1)
                command['source'] = src.strip()
                command['destination'] = dst.strip()
        elif line.startswith('rename '):
            command['action'] = 'rename'
            params = line[7:].strip()
            if ' to ' in params:
                old, new = params.split(' to ', 1)
                command['old_name'] = old.strip()
                command['new_name'] = new.strip()
        else:
            command['action'] = 'unknown'
            command['command_text'] = line
        
        return command
        
    def get_summary(self) -> Dict[str, Any]:
        """Get file section summary."""
        return {
            'section': 'File Management',
            'command_count': len(self.commands)
        }


class PortParser(BaseSectionParser):
    """Parser for /port section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse serial port configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_port_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/port',
            'commands': commands
        }
        
    def _parse_port_command(self, line: str) -> Dict[str, Any]:
        """Parse a single port command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_port_parameters(params, command)
        
        return command
        
    def _parse_port_parameters(self, params: str, command: Dict[str, Any]):
        """Parse port parameters."""
        parser = SystemIdentityParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'baud-rate':
                    try:
                        command['baud_rate_value'] = int(value)
                        command['is_standard_baud'] = int(value) in [9600, 19200, 38400, 57600, 115200]
                    except ValueError:
                        command['baud_rate_value'] = value
                    command[key] = value
                elif key == 'data-bits':
                    try:
                        command['data_bits_value'] = int(value)
                    except ValueError:
                        command['data_bits_value'] = value
                    command[key] = value
                elif key == 'parity':
                    command['parity_type'] = value
                    command[key] = value
                elif key == 'stop-bits':
                    try:
                        command['stop_bits_value'] = int(value)
                    except ValueError:
                        command['stop_bits_value'] = value
                    command[key] = value
                elif key in ['flow-control']:
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get port section summary."""
        return {
            'section': 'Serial Ports',
            'command_count': len(self.commands)
        }


class RadiusParser(BaseSectionParser):
    """Parser for /radius section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse RADIUS client configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_radius_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/radius',
            'commands': commands
        }
        
    def _parse_radius_command(self, line: str) -> Dict[str, Any]:
        """Parse a single RADIUS command."""
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
        self._parse_radius_parameters(params, command)
        
        return command
        
    def _parse_radius_parameters(self, params: str, command: Dict[str, Any]):
        """Parse RADIUS parameters."""
        parser = SystemIdentityParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'address':
                    # Validate RADIUS server address
                    if RouterOSPatterns.IP_ADDRESS_PATTERN.match(value):
                        command['server_address'] = value
                        command['address_valid'] = True
                        command['is_private'] = RouterOSPatterns.is_private_ip(value)
                    else:
                        command['server_address'] = value
                        command['address_valid'] = False
                elif key == 'secret':
                    # Don't store the actual secret, just metadata
                    command['secret_set'] = bool(value)
                    command['secret_length'] = len(value) if value else 0
                    command['secret_redacted'] = '***REDACTED***' if value else ''
                elif key == 'service':
                    command['radius_service'] = value
                    command['service_type'] = value
                elif key == 'timeout':
                    command['timeout_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get RADIUS section summary."""
        return {
            'section': 'RADIUS Client',
            'command_count': len(self.commands)
        }


class SpecialLoginParser(BaseSectionParser):
    """Parser for /special-login section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse special login methods configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_special_login_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/special-login',
            'commands': commands
        }
        
    def _parse_special_login_command(self, line: str) -> Dict[str, Any]:
        """Parse a single special login command."""
        command = {'raw_line': line}
        
        # Handle different command types
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_special_login_parameters(params, command)
        
        return command
        
    def _parse_special_login_parameters(self, params: str, command: Dict[str, Any]):
        """Parse special login parameters."""
        parser = SystemIdentityParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key in ['telnet', 'ssh', 'ftp', 'www', 'winbox']:
                    command[f"{key}_enabled"] = value.lower() in ['yes', 'true', '1']
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get special login section summary."""
        return {
            'section': 'Special Login Methods',
            'command_count': len(self.commands)
        }


class PartitionsParser(BaseSectionParser):
    """Parser for /partitions section (CHR)."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse disk partitions configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_partitions_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/partitions',
            'commands': commands
        }
        
    def _parse_partitions_command(self, line: str) -> Dict[str, Any]:
        """Parse a single partitions command."""
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
        self._parse_partitions_parameters(params, command)
        
        return command
        
    def _parse_partitions_parameters(self, params: str, command: Dict[str, Any]):
        """Parse partitions parameters."""
        parser = SystemIdentityParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'size':
                    # Parse partition size
                    if 'G' in value.upper():
                        try:
                            command['size_gb'] = float(value.upper().replace('G', ''))
                            command['size_mb'] = command['size_gb'] * 1024
                        except ValueError:
                            command['size_gb'] = value
                    elif 'M' in value.upper():
                        try:
                            command['size_mb'] = float(value.upper().replace('M', ''))
                            command['size_gb'] = command['size_mb'] / 1024
                        except ValueError:
                            command['size_mb'] = value
                    command[key] = value
                elif key == 'type':
                    command['partition_type'] = value
                    command['is_system'] = value.lower() in ['system', 'boot']
                elif key in ['active', 'primary']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get partitions section summary."""
        return {
            'section': 'Disk Partitions',
            'command_count': len(self.commands)
        }


# Register parsers
SectionParserRegistry.register('/system identity', SystemIdentityParser)
SectionParserRegistry.register('/system clock', SystemClockParser)
SectionParserRegistry.register('/system note', SystemNoteParser)
SectionParserRegistry.register('/user', UserParser)
SectionParserRegistry.register('/ip service', IPServiceParser)
SectionParserRegistry.register('/password', PasswordParser)
SectionParserRegistry.register('/import', ImportParser)
SectionParserRegistry.register('/export', ExportParser)
SectionParserRegistry.register('/console', ConsoleParser)
SectionParserRegistry.register('/file', FileParser)
SectionParserRegistry.register('/port', PortParser)
SectionParserRegistry.register('/radius', RadiusParser)
SectionParserRegistry.register('/special-login', SpecialLoginParser)
SectionParserRegistry.register('/partitions', PartitionsParser)
SectionParserRegistry.register('/system*', SystemIdentityParser)  # Fallback for other system sections