"""SNMP and management parsers for RouterOS configurations."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class SNMPParser(BaseSectionParser):
    """Parser for /snmp section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse SNMP configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_snmp_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/snmp',
            'commands': commands
        }
        
    def _parse_snmp_command(self, line: str) -> Dict[str, Any]:
        """Parse a single SNMP command."""
        command = {'raw_line': line}
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_snmp_parameters(params, command)
        
        return command
        
    def _parse_snmp_parameters(self, params: str, command: Dict[str, Any]):
        """Parse SNMP parameters."""
        parts = self._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key in ['enabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'contact':
                    command['contact_info'] = value
                    command['has_contact'] = bool(value)
                elif key == 'location':
                    command['location_info'] = value
                    command['has_location'] = bool(value)
                elif key == 'engine-id':
                    command['engine_id'] = value
                    command['has_custom_engine_id'] = bool(value)
                elif key == 'trap-community':
                    command['trap_community'] = value
                    command['uses_traps'] = bool(value)
                elif key == 'trap-version':
                    command['trap_version'] = value
                    try:
                        version = int(value)
                        command['trap_version_num'] = version
                        command['uses_snmpv1_traps'] = version == 1
                        command['uses_snmpv2_traps'] = version == 2
                        command['uses_snmpv3_traps'] = version == 3
                    except ValueError:
                        command['trap_version_num'] = value
                elif key == 'trap-generators':
                    generators = [gen.strip() for gen in value.split(',')]
                    command['trap_generators'] = generators
                    command['trap_generator_count'] = len(generators)
                    command['generates_interface_traps'] = 'interfaces' in generators
                    command['generates_temp_traps'] = 'temp-exception' in generators
                elif key == 'trap-target':
                    targets = [target.strip() for target in value.split(',')]
                    command['trap_targets'] = targets
                    command['trap_target_count'] = len(targets)
                    # Validate IP addresses in targets
                    valid_targets = []
                    for target in targets:
                        network_info = RouterOSPatterns.extract_ip_network(target)
                        if network_info:
                            valid_targets.append(network_info[0])
                    command['valid_trap_targets'] = valid_targets
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
        """Get SNMP section summary."""
        return {
            'section': 'SNMP',
            'command_count': len(self.commands)
        }


class SNMPCommunityParser(BaseSectionParser):
    """Parser for /snmp community section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse SNMP community configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_community_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/snmp community',
            'commands': commands
        }
        
    def _parse_community_command(self, line: str) -> Dict[str, Any]:
        """Parse a single SNMP community command."""
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
        self._parse_community_parameters(params, command)
        
        return command
        
    def _parse_community_parameters(self, params: str, command: Dict[str, Any]):
        """Parse SNMP community parameters."""
        parser = SNMPParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'name':
                    command['community_name'] = value
                    command['is_default'] = value in ['public', 'private']
                    command['community_length'] = len(value)
                elif key == 'security':
                    command['security_level'] = value
                    command['read_only'] = value == 'none'
                    command['read_write'] = value == 'private'
                elif key == 'read-access':
                    command['read_access'] = value.lower() in ['yes', 'true', '1']
                elif key == 'write-access':
                    command['write_access'] = value.lower() in ['yes', 'true', '1']
                elif key == 'addresses':
                    # Parse allowed addresses
                    addresses = [addr.strip() for addr in value.split(',') if addr.strip()]
                    command['allowed_addresses'] = addresses
                    command['address_count'] = len(addresses)
                    command['restricted_access'] = len(addresses) > 0
                    
                    # Validate addresses
                    valid_addresses = []
                    private_addresses = []
                    for addr in addresses:
                        network_info = RouterOSPatterns.extract_ip_network(addr)
                        if network_info:
                            valid_addresses.append(network_info[0])
                            if RouterOSPatterns.is_private_ip(network_info[0]):
                                private_addresses.append(network_info[0])
                    command['valid_addresses'] = valid_addresses
                    command['private_addresses'] = private_addresses
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get SNMP community section summary."""
        return {
            'section': 'SNMP Communities',
            'command_count': len(self.commands)
        }


class RadiusParser(BaseSectionParser):
    """Parser for /radius section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse RADIUS configuration."""
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
        parser = SNMPParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'address':
                    # Parse RADIUS server address
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['server_ip_valid'] = True
                        command['server_is_private'] = RouterOSPatterns.is_private_ip(network_info[0])
                        command['server_ip'] = network_info[0]
                    else:
                        command['server_ip_valid'] = False
                        command['server_type'] = 'hostname'
                    command[key] = value
                elif key == 'secret':
                    command['has_secret'] = bool(value)
                    command['secret_length'] = len(value) if value else 0
                    # Don't store actual secret for security
                elif key == 'service':
                    services = [svc.strip() for svc in value.split(',')]
                    command['services'] = services
                    command['service_count'] = len(services)
                    command['auth_service'] = 'login' in services
                    command['accounting_service'] = 'accounting' in services
                elif key == 'authentication-port':
                    try:
                        port = int(value)
                        command['auth_port'] = port
                        command['standard_auth_port'] = port == 1812
                    except ValueError:
                        command['auth_port'] = value
                elif key == 'accounting-port':
                    try:
                        port = int(value)
                        command['accounting_port'] = port
                        command['standard_accounting_port'] = port == 1813
                    except ValueError:
                        command['accounting_port'] = value
                elif key == 'timeout':
                    command['timeout_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'realm':
                    command['uses_realm'] = bool(value)
                    command['realm'] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get RADIUS section summary."""
        return {
            'section': 'RADIUS',
            'command_count': len(self.commands)
        }


class CertificateParser(BaseSectionParser):
    """Parser for /certificate section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse certificate configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_certificate_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/certificate',
            'commands': commands
        }
        
    def _parse_certificate_command(self, line: str) -> Dict[str, Any]:
        """Parse a single certificate command."""
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
        self._parse_certificate_parameters(params, command)
        
        return command
        
    def _parse_certificate_parameters(self, params: str, command: Dict[str, Any]):
        """Parse certificate parameters."""
        parser = SNMPParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'name':
                    command['cert_name'] = value
                elif key == 'common-name':
                    command['common_name'] = value
                    command['has_cn'] = bool(value)
                elif key == 'subject-alt-name':
                    alt_names = [name.strip() for name in value.split(',') if name.strip()]
                    command['alt_names'] = alt_names
                    command['alt_name_count'] = len(alt_names)
                elif key == 'key-size':
                    try:
                        key_size = int(value)
                        command['key_size_bits'] = key_size
                        command['weak_key'] = key_size < 2048
                        command['strong_key'] = key_size >= 4096
                    except ValueError:
                        command['key_size_bits'] = value
                elif key == 'days-valid':
                    try:
                        days = int(value)
                        command['validity_days'] = days
                        command['long_validity'] = days > 365
                        command['short_validity'] = days < 90
                    except ValueError:
                        command['validity_days'] = value
                elif key == 'key-usage':
                    usages = [usage.strip() for usage in value.split(',')]
                    command['key_usages'] = usages
                    command['usage_count'] = len(usages)
                    command['can_sign'] = 'digital-signature' in usages
                    command['can_encrypt'] = 'key-encipherment' in usages
                    command['is_ca'] = 'key-cert-sign' in usages
                elif key in ['trusted', 'invalid']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get certificate section summary."""
        return {
            'section': 'Certificates',
            'command_count': len(self.commands)
        }


class FileParser(BaseSectionParser):
    """Parser for /file section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse file system configuration."""
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
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_file_parameters(params, command)
        
        return command
        
    def _parse_file_parameters(self, params: str, command: Dict[str, Any]):
        """Parse file parameters."""
        parser = SNMPParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'name':
                    command['file_name'] = value
                    command['file_extension'] = value.split('.')[-1] if '.' in value else ''
                elif key == 'size':
                    try:
                        size_bytes = int(value)
                        command['size_bytes'] = size_bytes
                        command['size_mb'] = size_bytes / (1024 * 1024)
                        command['large_file'] = size_bytes > 10 * 1024 * 1024  # >10MB
                    except ValueError:
                        command['size_bytes'] = value
                elif key == 'type':
                    command['file_type'] = value
                    command['is_directory'] = value == 'directory'
                    command['is_link'] = value == 'link'
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get file section summary."""
        return {
            'section': 'File System',
            'command_count': len(self.commands)
        }


# Register SNMP and management parsers
SectionParserRegistry.register('/snmp', SNMPParser)
SectionParserRegistry.register('/snmp community', SNMPCommunityParser)
SectionParserRegistry.register('/radius', RadiusParser)
SectionParserRegistry.register('/certificate', CertificateParser)
SectionParserRegistry.register('/file', FileParser)

# Additional system parsers
SectionParserRegistry.register('/import', FileParser)  # Similar to file operations
SectionParserRegistry.register('/export', FileParser)  # Similar to file operations  
SectionParserRegistry.register('/log', SNMPParser)  # Similar configuration pattern
SectionParserRegistry.register('/console', SNMPParser)  # Simple config parser
SectionParserRegistry.register('/password', SNMPParser)  # Simple config parser
SectionParserRegistry.register('/port', SNMPParser)  # Serial port config