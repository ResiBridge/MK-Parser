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
SectionParserRegistry.register('/special-login', SpecialLoginParser)
SectionParserRegistry.register('/partitions', PartitionsParser)

# Additional interface types using existing parsers
SectionParserRegistry.register('/interface lte', MPLSInterfaceParser)  # Simple interface config
SectionParserRegistry.register('/interface vrrp', MPLSInterfaceParser)  # Simple interface config