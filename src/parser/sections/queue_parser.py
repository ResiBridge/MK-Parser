"""Queue and QoS parsers for RouterOS configurations."""
from typing import Dict, List, Any
from ..registry import BaseSectionParser, SectionParserRegistry
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.patterns import RouterOSPatterns


class QueueSimpleParser(BaseSectionParser):
    """Parser for /queue simple section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse simple queue configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_simple_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/queue simple',
            'commands': commands
        }
        
    def _parse_simple_command(self, line: str) -> Dict[str, Any]:
        """Parse a single simple queue command."""
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
        self._parse_simple_parameters(params, command)
        
        return command
        
    def _parse_simple_parameters(self, params: str, command: Dict[str, Any]):
        """Parse simple queue parameters."""
        parts = self._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'name':
                    command['queue_name'] = value
                    command[key] = value
                elif key == 'target':
                    # Parse target (can be IP, network, or interface)
                    command['target'] = value
                    network_info = RouterOSPatterns.extract_ip_network(value)
                    if network_info:
                        command['target_type'] = 'network'
                        command['target_network'] = network_info[1]
                        command['target_prefix'] = network_info[2]
                        command['target_is_private'] = RouterOSPatterns.is_private_ip(network_info[0])
                    elif '.' in value and not '/' in value:
                        # Single IP
                        command['target_type'] = 'ip'
                        command['target_is_private'] = RouterOSPatterns.is_private_ip(value)
                    else:
                        # Assume interface or other
                        command['target_type'] = 'interface'
                elif key == 'max-limit':
                    # Parse bandwidth limits (format: upload/download)
                    if '/' in value:
                        parts = value.split('/')
                        if len(parts) == 2:
                            upload_bw = RouterOSPatterns.parse_bandwidth(parts[0].strip())
                            download_bw = RouterOSPatterns.parse_bandwidth(parts[1].strip())
                            command['upload_limit_bps'] = upload_bw
                            command['download_limit_bps'] = download_bw
                            command['total_limit_bps'] = (upload_bw or 0) + (download_bw or 0)
                    command[key] = value
                elif key == 'limit-at':
                    # Parse guaranteed bandwidth
                    if '/' in value:
                        parts = value.split('/')
                        if len(parts) == 2:
                            upload_guaranteed = RouterOSPatterns.parse_bandwidth(parts[0].strip())
                            download_guaranteed = RouterOSPatterns.parse_bandwidth(parts[1].strip())
                            command['upload_guaranteed_bps'] = upload_guaranteed
                            command['download_guaranteed_bps'] = download_guaranteed
                    command[key] = value
                elif key == 'priority':
                    try:
                        priority = int(value)
                        command['priority_level'] = priority
                        command['high_priority'] = priority <= 3
                        command['low_priority'] = priority >= 6
                    except ValueError:
                        command['priority_level'] = value
                    command[key] = value
                elif key == 'queue':
                    # Parse queue type
                    queue_parts = value.split('/')
                    if len(queue_parts) == 2:
                        command['upload_queue_type'] = queue_parts[0]
                        command['download_queue_type'] = queue_parts[1]
                    command['queue_type'] = value
                elif key == 'burst-limit':
                    # Parse burst limits
                    if '/' in value:
                        parts = value.split('/')
                        if len(parts) == 2:
                            upload_burst = RouterOSPatterns.parse_bandwidth(parts[0].strip())
                            download_burst = RouterOSPatterns.parse_bandwidth(parts[1].strip())
                            command['upload_burst_bps'] = upload_burst
                            command['download_burst_bps'] = download_burst
                    command['has_burst'] = bool(value and value != '0/0')
                    command[key] = value
                elif key == 'burst-threshold':
                    command['has_burst_threshold'] = bool(value and value != '0/0')
                    command[key] = value
                elif key == 'burst-time':
                    command['burst_time_seconds'] = RouterOSPatterns.parse_time_value(value)
                    command[key] = value
                elif key in ['disabled']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'parent':
                    command['has_parent'] = bool(value and value != 'none')
                    command['parent_queue'] = value
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
        """Get simple queue section summary."""
        return {
            'section': 'Simple Queues',
            'command_count': len(self.commands)
        }


class QueueTreeParser(BaseSectionParser):
    """Parser for /queue tree section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse queue tree configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_tree_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/queue tree',
            'commands': commands
        }
        
    def _parse_tree_command(self, line: str) -> Dict[str, Any]:
        """Parse a single queue tree command."""
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
            
        # Parse parameters (reuse simple queue logic)
        simple_parser = QueueSimpleParser()
        simple_parser._parse_simple_parameters(params, command)
        
        # Tree-specific parsing
        self._parse_tree_specific_parameters(params, command)
        
        return command
        
    def _parse_tree_specific_parameters(self, params: str, command: Dict[str, Any]):
        """Parse queue tree specific parameters."""
        parser = QueueSimpleParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'parent':
                    command['parent_queue'] = value
                    command['is_root'] = value == 'global'
                    command['has_parent'] = value not in ['global', 'none', '']
                elif key == 'packet-mark':
                    command['packet_mark'] = value
                    command['uses_packet_mark'] = bool(value)
                elif key == 'connection-mark':
                    command['connection_mark'] = value
                    command['uses_connection_mark'] = bool(value)
                elif key == 'routing-mark':
                    command['routing_mark'] = value
                    command['uses_routing_mark'] = bool(value)
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get queue tree section summary."""
        return {
            'section': 'Queue Tree',
            'command_count': len(self.commands)
        }


class QueueTypeParser(BaseSectionParser):
    """Parser for /queue type section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse queue type configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_type_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/queue type',
            'commands': commands
        }
        
    def _parse_type_command(self, line: str) -> Dict[str, Any]:
        """Parse a single queue type command."""
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
        self._parse_type_parameters(params, command)
        
        return command
        
    def _parse_type_parameters(self, params: str, command: Dict[str, Any]):
        """Parse queue type parameters."""
        parser = QueueSimpleParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'name':
                    command['type_name'] = value
                    command[key] = value
                elif key == 'kind':
                    command['queue_kind'] = value
                    # Classify queue algorithms
                    fair_queue_types = ['sfq', 'fq_codel', 'cake']
                    strict_types = ['pfifo', 'bfifo', 'pfifo_fast']
                    command['is_fair_queue'] = value in fair_queue_types
                    command['is_strict_queue'] = value in strict_types
                    command['is_cake'] = value == 'cake'
                    command['is_codel'] = 'codel' in value
                elif key in ['pfifo-limit', 'bfifo-limit']:
                    try:
                        command[f"{key.replace('-', '_')}_packets"] = int(value)
                    except ValueError:
                        command[f"{key.replace('-', '_')}_packets"] = value
                    command[key] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get queue type section summary."""
        return {
            'section': 'Queue Types',
            'command_count': len(self.commands)
        }


class InterfaceQueueParser(BaseSectionParser):
    """Parser for interface queue sections."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse interface queue configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_interface_queue_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/interface queue',
            'commands': commands
        }
        
    def _parse_interface_queue_command(self, line: str) -> Dict[str, Any]:
        """Parse a single interface queue command."""
        command = {'raw_line': line}
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_interface_queue_parameters(params, command)
        
        return command
        
    def _parse_interface_queue_parameters(self, params: str, command: Dict[str, Any]):
        """Parse interface queue parameters."""
        parser = QueueSimpleParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == 'interface':
                    interface_info = RouterOSPatterns.parse_interface_reference(value)
                    command['interface_name'] = value
                    command['interface_type'] = interface_info['type']
                elif key == 'queue':
                    command['queue_type'] = value
                elif key in ['only-hardware-queue', 'tx-queue-drop']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get interface queue section summary."""
        return {
            'section': 'Interface Queues',
            'command_count': len(self.commands)
        }


# Traffic shaping and bandwidth test parsers
class ToolBandwidthServerParser(BaseSectionParser):
    """Parser for /tool bandwidth-server section."""
    
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """Parse bandwidth server configuration."""
        commands = []
        
        for line in lines:
            if not line.strip():
                continue
                
            command = self._parse_bandwidth_command(line)
            if command:
                commands.append(command)
                
        return {
            'section': '/tool bandwidth-server',
            'commands': commands
        }
        
    def _parse_bandwidth_command(self, line: str) -> Dict[str, Any]:
        """Parse a single bandwidth server command."""
        command = {'raw_line': line}
        
        if line.startswith('set '):
            command['action'] = 'set'
            params = line[4:].strip()
        else:
            command['action'] = 'set'
            params = line
            
        # Parse parameters
        self._parse_bandwidth_parameters(params, command)
        
        return command
        
    def _parse_bandwidth_parameters(self, params: str, command: Dict[str, Any]):
        """Parse bandwidth server parameters."""
        parser = QueueSimpleParser()
        parts = parser._split_parameters(params)
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key in ['enabled', 'authenticate']:
                    command[key] = value.lower() in ['yes', 'true', '1']
                elif key == 'allocate-udp-ports-from':
                    try:
                        command['udp_port_start'] = int(value)
                    except ValueError:
                        command['udp_port_start'] = value
                elif key == 'max-sessions':
                    try:
                        command['max_concurrent_sessions'] = int(value)
                    except ValueError:
                        command['max_concurrent_sessions'] = value
                else:
                    command[key] = value
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get bandwidth server section summary."""
        return {
            'section': 'Bandwidth Server',
            'command_count': len(self.commands)
        }


# Register queue and QoS parsers
SectionParserRegistry.register('/queue simple', QueueSimpleParser)
SectionParserRegistry.register('/queue tree', QueueTreeParser)
SectionParserRegistry.register('/queue type', QueueTypeParser)
SectionParserRegistry.register('/queue', QueueSimpleParser)  # Generic fallback
SectionParserRegistry.register('/interface queue', InterfaceQueueParser)
SectionParserRegistry.register('/tool bandwidth-server', ToolBandwidthServerParser)