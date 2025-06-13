"""Data models for RouterOS configuration."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json


@dataclass
class ConfigSection:
    """Base class for configuration sections."""
    name: str
    commands: List[Dict[str, Any]] = field(default_factory=list)
    raw_lines: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'commands': self.commands,
            'command_count': len(self.commands)
        }
        
    def get_summary(self) -> Dict[str, Any]:
        """Get section summary for GitHub display."""
        return {
            'section': self.name,
            'command_count': len(self.commands)
        }


@dataclass
class InterfaceSection(ConfigSection):
    """Interface configuration section with parsed interface data."""
    
    def __post_init__(self):
        """Parse interfaces after initialization."""
        self.interfaces = []
        self.bridges = []
        self.vlans = []
        self.bridge_ports = []
        self.tunnels = []
        
        self._categorize_interfaces()
        
    def _categorize_interfaces(self):
        """Categorize interfaces by type."""
        for cmd in self.commands:
            if 'name' not in cmd:
                continue
                
            name = cmd.get('name', '')
            
            # Use section name to determine interface type first
            iface_type = self._detect_interface_type_from_section()
            
            # If section doesn't give us the type, use name-based detection
            if iface_type == 'unknown':
                iface_type = cmd.get('type', self._detect_interface_type(name))
            
            interface_data = {
                'name': name,
                'type': iface_type,
                **cmd
            }
            
            if iface_type == 'bridge':
                self.bridges.append(interface_data)
            elif iface_type == 'vlan':
                self.vlans.append(interface_data)
            elif iface_type in ['eoip', 'gre', 'ipip', 'l2tp', 'pptp', 'sstp', 'ovpn']:
                self.tunnels.append(interface_data)
            else:
                self.interfaces.append(interface_data)
                
    def _detect_interface_type_from_section(self) -> str:
        """Detect interface type from section name."""
        section_lower = self.name.lower()
        
        if 'vlan' in section_lower:
            return 'vlan'
        elif 'bridge' in section_lower:
            return 'bridge'
        elif 'ethernet' in section_lower:
            return 'ethernet'
        elif 'wireless' in section_lower:
            return 'wireless'
        elif 'bonding' in section_lower:
            return 'bonding'
        elif 'eoip' in section_lower:
            return 'eoip'
        elif 'gre' in section_lower:
            return 'gre'
        elif 'ipip' in section_lower:
            return 'ipip'
        elif 'l2tp' in section_lower:
            return 'l2tp'
        elif 'pptp' in section_lower:
            return 'pptp'
        elif 'sstp' in section_lower:
            return 'sstp'
        elif 'ovpn' in section_lower:
            return 'ovpn'
        elif 'lte' in section_lower:
            return 'lte'
            
        return 'unknown'
                
    def _detect_interface_type(self, name: str) -> str:
        """Detect interface type from name."""
        type_patterns = {
            'ether': 'ethernet',
            'wlan': 'wireless', 
            'bridge': 'bridge',
            'vlan': 'vlan',
            'bond': 'bonding',
            'eoip': 'eoip',
            'gre': 'gre',
            'ipip': 'ipip',
            'l2tp': 'l2tp',
            'pptp': 'pptp',
            'sstp': 'sstp',
            'ovpn': 'ovpn',
            'lte': 'lte'
        }
        
        # Convert name to lowercase for case-insensitive matching
        name_lower = name.lower()
        
        for pattern, iface_type in type_patterns.items():
            if name_lower.startswith(pattern):
                return iface_type
                
        return 'unknown'
        
    def get_summary(self) -> Dict[str, Any]:
        """Get interface section summary."""
        summary = {
            'section': 'Interfaces',
            'total_interfaces': len(self.interfaces) + len(self.bridges) + len(self.vlans) + len(self.tunnels),
            'physical_interfaces': len([i for i in self.interfaces if i['type'] in ['ethernet', 'wireless', 'lte']]),
            'bridges': len(self.bridges),
            'vlans': len(self.vlans),
            'tunnels': len(self.tunnels),
            'bridge_list': [b.get('name', 'unnamed') for b in self.bridges],
            'vlan_list': [f"VLAN {v.get('vlan-id', '?')} ({v.get('name', 'unnamed')})" for v in self.vlans]
        }
        
        # Add tunnel breakdown if any
        if self.tunnels:
            tunnel_types = {}
            for t in self.tunnels:
                t_type = t.get('type', 'unknown')
                tunnel_types[t_type] = tunnel_types.get(t_type, 0) + 1
            summary['tunnel_types'] = tunnel_types
            
        return summary
        
    def get_bridge_members(self) -> Dict[str, List[str]]:
        """Return mapping of bridges to their member interfaces."""
        bridge_members = {b['name']: [] for b in self.bridges}
        
        for port in self.bridge_ports:
            bridge = port.get('bridge')
            interface = port.get('interface')
            if bridge and interface and bridge in bridge_members:
                bridge_members[bridge].append(interface)
                
        return bridge_members


@dataclass
class IPSection(ConfigSection):
    """IP configuration section with parsed IP data."""
    
    def __post_init__(self):
        """Parse IP configuration after initialization."""
        self.addresses = []
        self.routes = []
        self.pools = []
        self.dhcp_servers = []
        self.dhcp_networks = []
        self.dns_servers = []
        
        self._parse_ip_config()
        
    def _parse_ip_config(self):
        """Parse IP configuration from commands."""
        for cmd in self.commands:
            section_type = self._determine_ip_section_type()
            
            if 'address' in cmd and section_type == 'address':
                self.addresses.append(cmd)
            elif section_type == 'route':
                self.routes.append(cmd)
            elif section_type == 'pool':
                self.pools.append(cmd)
            elif section_type == 'dhcp-server':
                self.dhcp_servers.append(cmd)
            elif section_type == 'dhcp-server network':
                self.dhcp_networks.append(cmd)
            elif section_type == 'dns':
                if 'servers' in cmd:
                    servers = cmd['servers']
                    if isinstance(servers, str):
                        self.dns_servers.extend(servers.split(','))
                    elif isinstance(servers, list):
                        self.dns_servers.extend(servers)
                    
    def _determine_ip_section_type(self) -> str:
        """Determine IP section type from section name."""
        if 'address' in self.name:
            return 'address'
        elif 'route' in self.name:
            return 'route'
        elif 'pool' in self.name:
            return 'pool'
        elif 'dhcp-server network' in self.name:
            return 'dhcp-server network'
        elif 'dhcp-server' in self.name:
            return 'dhcp-server'
        elif 'dns' in self.name:
            return 'dns'
        return 'unknown'
        
    def get_summary(self) -> Dict[str, Any]:
        """Get IP section summary."""
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))
        from utils.patterns import RouterOSPatterns
        
        summary = {
            'section': 'IP Configuration',
            'address_count': len(self.addresses),
            'route_count': len(self.routes),
            'pool_count': len(self.pools),
            'dhcp_server_count': len(self.dhcp_servers),
            'dhcp_network_count': len(self.dhcp_networks),
            'ip_addresses': []
        }
        
        # Extract IP addresses and networks
        networks = set()
        for addr in self.addresses:
            if 'address' in addr:
                summary['ip_addresses'].append(addr['address'])
                # Extract network
                network_info = RouterOSPatterns.extract_ip_network(addr['address'])
                if network_info:
                    networks.add(f"{network_info[1]}/{network_info[2]}")
                    
        summary['networks'] = sorted(list(networks))
        
        # Add DNS servers if any
        if self.dns_servers:
            summary['dns_servers'] = self.dns_servers
            
        return summary


@dataclass
class SystemSection(ConfigSection):
    """System configuration section."""
    
    def __post_init__(self):
        """Parse system configuration."""
        self.identity = None
        self.users = []
        self.services = []
        self.clock_settings = {}
        self.note = None
        
        self._parse_system_config()
        
    def _parse_system_config(self):
        """Parse system configuration from commands."""
        for cmd in self.commands:
            if 'identity' in self.name.lower():
                self.identity = cmd.get('name', 'Unknown')
            elif 'user' in self.name.lower():
                self.users.append(cmd)
            elif 'service' in self.name.lower():
                self.services.append(cmd)
            elif 'clock' in self.name.lower():
                self.clock_settings = cmd
            elif 'note' in self.name.lower():
                self.note = cmd.get('show-at-login', '')
                
    def get_summary(self) -> Dict[str, Any]:
        """Get system section summary."""
        summary = {
            'section': 'System',
            'device_name': self.identity or 'Unknown',
            'user_count': len(self.users),
            'service_count': len(self.services)
        }
        
        if self.users:
            summary['user_list'] = [u.get('name', 'unnamed') for u in self.users]
            summary['admin_users'] = [u['name'] for u in self.users if u.get('group') == 'full']
            
        if self.services:
            enabled_services = [s for s in self.services if s.get('disabled') != 'yes']
            summary['enabled_services'] = [s.get('name', 'unknown') for s in enabled_services]
            summary['management_access'] = self._check_management_access(enabled_services)
            
        if self.clock_settings:
            summary['timezone'] = self.clock_settings.get('time-zone-name', 'Not set')
            
        return summary
        
    def _check_management_access(self, enabled_services: List[Dict]) -> List[str]:
        """Check what management services are enabled."""
        access_methods = []
        service_map = {
            'ssh': 'SSH',
            'telnet': 'Telnet',
            'www': 'WebFig',
            'www-ssl': 'WebFig SSL',
            'api': 'API',
            'api-ssl': 'API SSL',
            'winbox': 'Winbox',
            'ftp': 'FTP'
        }
        
        for service in enabled_services:
            name = service.get('name', '')
            if name in service_map:
                access_methods.append(service_map[name])
                
        return access_methods


@dataclass
class FirewallSection(ConfigSection):
    """Firewall configuration section."""
    
    def __post_init__(self):
        """Parse firewall rules."""
        self.filter_rules = []
        self.nat_rules = []
        self.mangle_rules = []
        self.raw_rules = []
        self.address_lists = []
        
        self._parse_firewall_rules()
        
    def _parse_firewall_rules(self):
        """Parse firewall rules from commands."""
        for cmd in self.commands:
            if 'filter' in self.name:
                self.filter_rules.append(cmd)
            elif 'nat' in self.name:
                self.nat_rules.append(cmd)
            elif 'mangle' in self.name:
                self.mangle_rules.append(cmd)
            elif 'raw' in self.name:
                self.raw_rules.append(cmd)
            elif 'address-list' in self.name:
                self.address_lists.append(cmd)
                
    def get_summary(self) -> Dict[str, Any]:
        """Get firewall section summary."""
        summary = {
            'section': 'Firewall',
            'filter_rules': len(self.filter_rules),
            'nat_rules': len(self.nat_rules),
            'mangle_rules': len(self.mangle_rules),
            'raw_rules': len(self.raw_rules),
            'address_lists': len(self.address_lists),
            'total_rules': len(self.filter_rules) + len(self.nat_rules) + len(self.mangle_rules) + len(self.raw_rules)
        }
        
        # Analyze filter rules by chain
        if self.filter_rules:
            chains = {}
            actions = {}
            for rule in self.filter_rules:
                chain = rule.get('chain', 'unknown')
                action = rule.get('action', 'unknown')
                chains[chain] = chains.get(chain, 0) + 1
                actions[action] = actions.get(action, 0) + 1
                
            summary['filter_by_chain'] = chains
            summary['filter_by_action'] = actions
            
        # Analyze NAT rules
        if self.nat_rules:
            nat_types = {'srcnat': 0, 'dstnat': 0}
            for rule in self.nat_rules:
                chain = rule.get('chain', '')
                if chain in nat_types:
                    nat_types[chain] += 1
            summary['nat_types'] = nat_types
            
        # List address lists
        if self.address_lists:
            list_names = {}
            for entry in self.address_lists:
                list_name = entry.get('list', 'unknown')
                list_names[list_name] = list_names.get(list_name, 0) + 1
            summary['address_list_names'] = list(list_names.keys())
            
        return summary


class RouterOSConfig:
    """Complete RouterOS configuration."""
    
    def __init__(self, sections: Dict[str, Dict], device_name: str = None, errors: List[Dict] = None):
        """
        Initialize RouterOS configuration.
        
        Args:
            sections: Dictionary of parsed sections
            device_name: Device name/identity
            errors: List of parsing errors
        """
        self.sections = {}
        self.device_name = device_name
        self.errors = errors or []
        
        # Create appropriate section objects
        for section_name, section_data in sections.items():
            self.sections[section_name] = self._create_section_object(section_name, section_data)
            
    def _create_section_object(self, section_name: str, section_data: Dict) -> ConfigSection:
        """Create appropriate section object based on section type."""
        # Determine section type and create appropriate object
        if 'interface' in section_name and 'list' not in section_name:
            section = InterfaceSection(section_name)
        elif section_name.startswith('/ip') and 'firewall' not in section_name:
            section = IPSection(section_name)
        elif 'system' in section_name or 'user' in section_name:
            section = SystemSection(section_name)
        elif 'firewall' in section_name:
            section = FirewallSection(section_name)
        else:
            section = ConfigSection(section_name)
            
        # Populate section data
        section.commands = section_data.get('commands', [])
        
        # Re-run post-init processing for sections that need it
        if isinstance(section, InterfaceSection):
            section._categorize_interfaces()
        elif isinstance(section, IPSection):
            section._parse_ip_config()
        elif isinstance(section, SystemSection):
            section._parse_system_config()
        elif isinstance(section, FirewallSection):
            section._parse_firewall_rules()
            
        return section
        
    def get_section(self, name: str) -> Optional[ConfigSection]:
        """Get specific configuration section."""
        return self.sections.get(name)
        
    def to_json(self) -> str:
        """Serialize to JSON."""
        data = {
            'device_name': self.device_name,
            'sections': {name: section.to_dict() for name, section in self.sections.items()},
            'errors': self.errors
        }
        return json.dumps(data, indent=2)
        
    def get_device_summary(self) -> Dict[str, Any]:
        """Generate complete device summary for GitHub display."""
        summary = {
            'device_name': self.device_name or self._find_device_name(),
            'sections_parsed': len(self.sections),
            'section_list': sorted(list(self.sections.keys())),
            'parsing_errors': len(self.errors),
            'section_summaries': {}
        }
        
        # Get summary from each section
        for name, section in self.sections.items():
            try:
                summary['section_summaries'][name] = section.get_summary()
            except Exception as e:
                summary['section_summaries'][name] = {
                    'section': name,
                    'error': f"Failed to generate summary: {str(e)}"
                }
                
        # Add error details if any
        if self.errors:
            summary['errors'] = self.errors
            
        return summary
        
    def _find_device_name(self) -> str:
        """Try to find device name from system identity section."""
        for section_name, section in self.sections.items():
            if 'system' in section_name and 'identity' in section_name:
                if isinstance(section, SystemSection) and section.identity:
                    return section.identity
                    
        return 'Unknown Device'