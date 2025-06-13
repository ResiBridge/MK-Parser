"""Advanced feature parsers for RouterOS configurations (MPLS, Container, Special Features)."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class MPLSParser(BaseSectionParser):
    """Parser for /mpls section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse MPLS configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_mpls_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/mpls',
            'commands': commands
        }
        
    def _parse_mpls_command(self, line: str) -> Dict[str, Any]:
        """Parse a single MPLS command."""
        command = {'raw_line': line}
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_mpls_parameters(params, command)
        
        return command
        
    def _parse_mpls_parameters(self, params: str, command: Dict[str, Any]):
        """Parse MPLS parameters."""
        parts = self._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key in ['enabled', 'propagate-ttl']:
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
        """Get MPLS section summary."""
        return {
            'section': 'MPLS',
            'command_count': len(self.commands)
        }


class MPLSLDPParser(BaseSectionParser):
    """Parser for /mpls ldp section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse MPLS LDP configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_ldp_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/mpls ldp',
            'commands': commands
        }
        
    def _parse_ldp_command(self, line: str) -> Dict[str, Any]:
        """Parse a single LDP command."""
        command = {'raw_line': line}
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_ldp_parameters(params, command)
        
        return command
        
    def _parse_ldp_parameters(self, params: str, command: Dict[str, Any]):
        """Parse LDP parameters."""
        parser = MPLSParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'lsr-id':
                    # Parse Label Switch Router ID
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['lsr_id_valid'] = True
                        command['lsr_id'] = network_info[0]
                    else:
                        command['lsr_id_valid'] = False
                    command[key] = value
                elif key == 'transport-address':
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['transport_ip_valid'] = True
                        command['transport_ip'] = network_info[0]
                    else:
                        command['transport_ip_valid'] = False
                    command[key] = value
                elif key in ['enabled', 'loop-detect', 'use-explicit-null']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'hello-interval':
                    command['hello_interval_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key == 'hold-time':
                    command['hold_time_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get LDP section summary."""
        return {
            'section': 'MPLS LDP',
            'command_count': len(self.commands)
        }


class MPLSInterfaceParser(BaseSectionParser):
    """Parser for /mpls interface section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse MPLS interface configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_mpls_interface_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/mpls interface',
            'commands': commands
        }
        
    def _parse_mpls_interface_command(self, line: str) -> Dict[str, Any]:
        """Parse a single MPLS interface command."""
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
        self._parse_mpls_interface_parameters(params, command)
        
        return command
        
    def _parse_mpls_interface_parameters(self, params: str, command: Dict[str, Any]):
        """Parse MPLS interface parameters."""
        parser = MPLSParser()
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
                elif key in ['disabled', 'mpls-mtu']:
                    if key == 'disabled':
                        command[key] = value.lower() in ['yes', 'true', '1']
                    else:
                        try:
                            command['mpls_mtu_size'] = int(value)
                        except ValueError:
                            command['mpls_mtu_size'] = value
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get MPLS interface section summary."""
        return {
            'section': 'MPLS Interfaces',
            'command_count': len(self.commands)
        }


class ContainerParser(BaseSectionParser):
    """Parser for /container section (RouterOS 7)."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse container configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_container_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/container',
            'commands': commands
        }
        
    def _parse_container_command(self, line: str) -> Dict[str, Any]:
        """Parse a single container command."""
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
        self._parse_container_parameters(params, command)
        
        return command
        
    def _parse_container_parameters(self, params: str, command: Dict[str, Any]):
        """Parse container parameters."""
        parser = MPLSParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'remote-image':
                    command['image_source'] = value
                    command['uses_remote_image'] = bool(value)
                    # Check for common registries
                    if 'docker.io' in value or 'hub.docker.com' in value:
                        command['registry'] = 'docker_hub'
                    elif 'quay.io' in value:
                        command['registry'] = 'quay'
                    elif 'gcr.io' in value:
                        command['registry'] = 'gcr'
                    else:
                        command['registry'] = 'custom'
                elif key == 'tag':
                    command['image_tag'] = value
                    command['uses_latest'] = value == 'latest'
                    command['uses_specific_version'] = value != 'latest'
                elif key == 'interface':
                    interface_info = RouterOSPatterns.parse_interface_reference(value)
                    command['interface'] = value
                    command['interface_type'] = interface_info['type']
                elif key == 'root-dir':
                    command['root_directory'] = value
                    command['uses_custom_root'] = bool(value)
                elif key == 'mounts':
                    mounts = [mount.strip() for mount in value.split(',') if mount.strip()]
                    command['mounts'] = mounts
                    command['mount_count'] = len(mounts)
                    command['has_mounts'] = len(mounts) > 0
                elif key == 'envlist':
                    env_vars = [env.strip() for env in value.split(',') if env.strip()]
                    command['environment_variables'] = env_vars
                    command['env_var_count'] = len(env_vars)
                elif key == 'dns':
                    dns_servers = [dns.strip() for dns in value.split(',') if dns.strip()]
                    command['dns_servers'] = dns_servers
                    command['custom_dns'] = len(dns_servers) > 0
                elif key in ['start-on-boot', 'disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'cpu':
                    try:
                        command['cpu_limit'] = float(value)
                        command['high_cpu_limit'] = float(value) > 1.0
                    except ValueError:
                        command['cpu_limit'] = value
                elif key == 'memory':
                    # Parse memory limit (usually in MB)
                    if value.endswith('M') or value.endswith('MB'):
                        try:
                            command['memory_limit_mb'] = int(value.rstrip('MB'))
                            command['high_memory'] = command['memory_limit_mb'] > 512
                        except ValueError:
                            command['memory_limit_mb'] = value
                    command['memory'] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get container section summary."""
        return {
            'section': 'Containers',
            'command_count': len(self.commands)
        }


class ContainerConfigParser(BaseSectionParser):
    """Parser for /container config section (RouterOS 7+)."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse container configuration settings."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_container_config_command(line)
            if command:
                commands.append(command)
        
        self.commands = commands
        return {
            'section': '/container config',
            'commands': commands
        }
        
    def _parse_container_config_command(self, line: str) -> Dict[str, Any]:
        """Parse a single container config command."""
        command = {'raw_line': line}
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_container_config_parameters(params, command)
        
        return command
        
    def _parse_container_config_parameters(self, params: str, command: Dict[str, Any]):
        """Parse container config parameters."""
        parser = MPLSParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'registry-url':
                    command['registry_url'] = value
                    command['uses_custom_registry'] = bool(value)
                    # Classify registry type
                    if 'docker.io' in value or 'hub.docker.com' in value:
                        command['registry_type'] = 'docker_hub'
                    elif 'quay.io' in value:
                        command['registry_type'] = 'quay'
                    elif 'gcr.io' in value:
                        command['registry_type'] = 'google'
                    elif 'registry.redhat.io' in value:
                        command['registry_type'] = 'redhat'
                    else:
                        command['registry_type'] = 'custom'
                elif key == 'tmpdir':
                    command['temp_directory'] = value
                    command['uses_custom_tmpdir'] = bool(value)
                elif key == 'ram-high':
                    # RAM high watermark
                    if value.endswith('M') or value.endswith('MB'):
                        try:
                            command['ram_high_mb'] = int(value.rstrip('MB').rstrip('M'))
                            command['high_ram_limit'] = command['ram_high_mb'] > 512  # Changed threshold
                        except ValueError:
                            command['ram_high_mb'] = value
                    command['ram_high'] = value
                elif key == 'extract-timeout':
                    command['extract_timeout_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command['long_timeout'] = command.get('extract_timeout_seconds', 0) > 300
                    command[key] = value
                elif key in ['enabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get container config section summary."""
        return {
            'section': 'Container Config',
            'command_count': len(self.commands)
        }


class ContainerEnvsParser(BaseSectionParser):
    """Parser for /container envs section (RouterOS 7+)."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse container environment variables."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_container_envs_command(line)
            if command:
                commands.append(command)
        
        self.commands = commands
        return {
            'section': '/container envs',
            'commands': commands
        }
        
    def _parse_container_envs_command(self, line: str) -> Dict[str, Any]:
        """Parse a single container envs command."""
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
        self._parse_container_envs_parameters(params, command)
        
        return command
        
    def _parse_container_envs_parameters(self, params: str, command: Dict[str, Any]):
        """Parse container environment variable parameters."""
        parser = MPLSParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'name':
                    command['env_name'] = value
                    # Classify common environment variable types - check for sensitive first
                    if 'PASSWORD' in value.upper() or 'SECRET' in value.upper() or 'KEY' in value.upper() or 'TOKEN' in value.upper():
                        command['env_type'] = 'secret'
                        command['contains_sensitive'] = True
                    elif value.upper() in ['PATH', 'HOME', 'USER', 'SHELL']:
                        command['env_type'] = 'system'
                    elif value.upper().startswith('DB_'):
                        command['env_type'] = 'database'
                    elif value.upper() in ['DEBUG', 'LOG_LEVEL', 'VERBOSE']:
                        command['env_type'] = 'logging'
                    else:
                        command['env_type'] = 'application'
                elif key == 'value':
                    command['env_value'] = value
                    command['has_value'] = bool(value)
                    # Check for sensitive values (but don't log them)
                    if any(word in value.lower() for word in ['password', 'secret', 'key', 'token', 'auth']):
                        command['potentially_sensitive'] = True
                    command['value_length'] = len(value)
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get container envs section summary."""
        env_count = len(self.commands)
        sensitive_count = len([cmd for cmd in self.commands if cmd.get('contains_sensitive', False) or cmd.get('potentially_sensitive', False)])
        
        return {
            'section': 'Container Environment Variables',
            'command_count': env_count,
            'environment_variable_count': env_count,
            'sensitive_variables': sensitive_count,
            'has_sensitive_data': sensitive_count > 0
        }


class ContainerMountsParser(BaseSectionParser):
    """Parser for /container mounts section (RouterOS 7+)."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse container mount point configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_container_mounts_command(line)
            if command:
                commands.append(command)
        
        self.commands = commands
        return {
            'section': '/container mounts',
            'commands': commands
        }
        
    def _parse_container_mounts_command(self, line: str) -> Dict[str, Any]:
        """Parse a single container mounts command."""
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
        self._parse_container_mounts_parameters(params, command)
        
        return command
        
    def _parse_container_mounts_parameters(self, params: str, command: Dict[str, Any]):
        """Parse container mount point parameters."""
        parser = MPLSParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'name':
                    command['mount_name'] = value
                elif key == 'src':
                    command['source_path'] = value
                    # Classify source path types
                    if value.startswith('/flash/'):
                        command['source_type'] = 'flash'
                    elif value.startswith('/rw/'):
                        command['source_type'] = 'rw_partition'
                    elif value.startswith('/tmp/'):
                        command['source_type'] = 'temporary'
                    elif value.startswith('/etc/'):
                        command['source_type'] = 'system_config'
                    elif value.startswith('/var/'):
                        command['source_type'] = 'variable_data'
                    else:
                        command['source_type'] = 'other'
                elif key == 'dst':
                    command['destination_path'] = value
                    # Common container mount points
                    if value in ['/app', '/usr/src/app', '/opt/app']:
                        command['mount_purpose'] = 'application'
                    elif value in ['/data', '/var/lib', '/storage']:
                        command['mount_purpose'] = 'data'
                    elif value in ['/config', '/etc']:
                        command['mount_purpose'] = 'configuration'
                    elif value in ['/logs', '/var/log']:
                        command['mount_purpose'] = 'logging'
                    elif value in ['/tmp', '/temp']:
                        command['mount_purpose'] = 'temporary'
                    else:
                        command['mount_purpose'] = 'custom'
                elif key == 'options':
                    command['mount_options'] = value
                    command['read_only'] = 'ro' in value
                    command['read_write'] = 'rw' in value
                    command['bind_mount'] = 'bind' in value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get container mounts section summary."""
        mount_count = len(self.commands)
        ro_mounts = len([cmd for cmd in self.commands if cmd.get('read_only', False)])
        rw_mounts = len([cmd for cmd in self.commands if cmd.get('read_write', False)])
        
        return {
            'section': 'Container Mounts',
            'command_count': mount_count,
            'mount_point_count': mount_count,
            'read_only_mounts': ro_mounts,
            'read_write_mounts': rw_mounts,
            'has_bind_mounts': any(cmd.get('bind_mount', False) for cmd in self.commands)
        }


class ZeroTierParser(BaseSectionParser):
    """Parser for /zerotier section (RouterOS 7.6+)."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse ZeroTier network configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_zerotier_command(line)
            if command:
                commands.append(command)
        
        self.commands = commands
        return {
            'section': '/zerotier',
            'commands': commands
        }
        
    def _parse_zerotier_command(self, line: str) -> Dict[str, Any]:
        """Parse a single ZeroTier command."""
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
        self._parse_zerotier_parameters(params, command)
        
        return command
        
    def _parse_zerotier_parameters(self, params: str, command: Dict[str, Any]):
        """Parse ZeroTier parameters."""
        parser = MPLSParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'network':
                    command['network_id'] = value
                    # ZeroTier network IDs are 16-character hex strings
                    if len(value) == 16 and all(c in '0123456789abcdefABCDEF' for c in value):
                        command['valid_network_id'] = True
                    else:
                        command['valid_network_id'] = False
                elif key == 'name':
                    command['interface_name'] = value
                elif key == 'identity':
                    command['identity_file'] = value
                    command['uses_custom_identity'] = bool(value)
                elif key == 'port':
                    try:
                        port_num = int(value)
                        command['port_number'] = port_num
                        command['uses_default_port'] = port_num == 9993
                        command['valid_port'] = 1 <= port_num <= 65535
                    except ValueError:
                        command['port_number'] = value
                        command['valid_port'] = False
                    command['port'] = value
                elif key == 'copy-routes':
                    command['copy_routes'] = value.lower() in ['yes', 'true', '1']
                elif key == 'allow-managed':
                    command['allow_managed'] = value.lower() in ['yes', 'true', '1']
                elif key == 'allow-global':
                    command['allow_global'] = value.lower() in ['yes', 'true', '1']
                elif key == 'allow-default':
                    command['allow_default'] = value.lower() in ['yes', 'true', '1']
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get ZeroTier section summary."""
        network_count = len(self.commands)
        valid_networks = len([cmd for cmd in self.commands if cmd.get('valid_network_id', False)])
        managed_networks = len([cmd for cmd in self.commands if cmd.get('allow_managed', False)])
        
        return {
            'section': 'ZeroTier Networks',
            'command_count': network_count,
            'network_count': network_count,
            'valid_network_ids': valid_networks,
            'managed_networks': managed_networks,
            'has_global_routes': any(cmd.get('allow_global', False) for cmd in self.commands),
            'has_default_routes': any(cmd.get('allow_default', False) for cmd in self.commands)
        }


class SpecialLoginParser(BaseSectionParser):
    """Parser for /special-login section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse special login configuration."""
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
        parser = MPLSParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key in ['enabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get special login section summary."""
        return {
            'section': 'Special Login',
            'command_count': len(self.commands)
        }


class PartitionsParser(BaseSectionParser):
    """Parser for /partitions section (CHR)."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse partitions configuration."""
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
        
        if line.startswith('set '):
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
        parser = MPLSParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'size':
                    # Parse partition size
                    if value.endswith('G') or value.endswith('GB'):
                        try:
                            command['size_gb'] = float(value.rstrip('GB'))
                            command['large_partition'] = command['size_gb'] > 10
                        except ValueError:
                            command['size_gb'] = value
                    elif value.endswith('M') or value.endswith('MB'):
                        try:
                            command['size_mb'] = float(value.rstrip('MB'))
                            command['size_gb'] = command['size_mb'] / 1024
                        except ValueError:
                            command['size_mb'] = value
                    command['size'] = value
                elif key == 'type':
                    command['partition_type'] = value
                    command['is_data'] = value == 'data'
                    command['is_swap'] = value == 'swap'
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get partitions section summary."""
        return {
            'section': 'Partitions',
            'command_count': len(self.commands)
        }


# Register advanced feature parsers
SectionParserRegistry.register('/mpls', MPLSParser)
SectionParserRegistry.register('/mpls ldp', MPLSLDPParser)
SectionParserRegistry.register('/mpls interface', MPLSInterfaceParser)
SectionParserRegistry.register('/mpls forwarding-table', MPLSParser)  # Use base MPLS parser

SectionParserRegistry.register('/container', ContainerParser)
SectionParserRegistry.register('/container config', ContainerConfigParser)
SectionParserRegistry.register('/container envs', ContainerEnvsParser)
SectionParserRegistry.register('/container mounts', ContainerMountsParser)
SectionParserRegistry.register('/zerotier', ZeroTierParser)
SectionParserRegistry.register('/special-login', SpecialLoginParser)
SectionParserRegistry.register('/partitions', PartitionsParser)

# Additional interface types using existing parsers
SectionParserRegistry.register('/interface lte', MPLSInterfaceParser)  # Simple interface config
SectionParserRegistry.register('/interface vrrp', MPLSInterfaceParser)  # Simple interface config