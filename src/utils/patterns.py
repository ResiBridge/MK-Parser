"""Common pattern extractors and validators for RouterOS configuration data."""
import re
import ipaddress
from typing import Optional, Tuple, Dict, List


class RouterOSPatterns:
    """Common RouterOS pattern matching and extraction utilities."""
    
    # Regex patterns
    IP_ADDRESS_PATTERN = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?:/(\d{1,2}))?')
    MAC_ADDRESS_PATTERN = re.compile(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})')
    TIME_PATTERN = re.compile(r'(?:(\d+)w)?(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?')
    INTERFACE_PATTERN = re.compile(r'(ether|wlan|bridge|vlan|bonding|pppoe|l2tp|sstp|ovpn|eoip|gre|ipip|6to4|lte)[\d\-\.]+')
    VLAN_ID_PATTERN = re.compile(r'vlan-id=(\d+)')
    
    @staticmethod
    def extract_ip_network(address: str) -> Optional[Tuple[str, str, int]]:
        """
        Extract IP address, network, and prefix length.
        
        Args:
            address: IP address string (e.g., "192.168.1.1/24")
            
        Returns:
            Tuple of (ip_address, network, prefix_length) or None
        """
        match = RouterOSPatterns.IP_ADDRESS_PATTERN.match(address)
        if match:
            ip = match.group(1)
            prefix = int(match.group(2)) if match.group(2) else 32
            
            try:
                ip_obj = ipaddress.ip_interface(f"{ip}/{prefix}")
                return (str(ip_obj.ip), str(ip_obj.network.network_address), prefix)
            except ValueError:
                return None
        return None
        
    @staticmethod
    def parse_interface_reference(value: str) -> Dict[str, str]:
        """
        Parse interface reference (e.g., "ether1", "bridge=BR1").
        
        Args:
            value: Interface reference string
            
        Returns:
            Dictionary with interface details
        """
        if '=' in value:
            key, interface = value.split('=', 1)
            return {'type': key, 'name': interface}
        else:
            # Try to extract interface type from name
            match = RouterOSPatterns.INTERFACE_PATTERN.match(value)
            if match:
                iface_type = match.group(1)
                return {'type': iface_type, 'name': value}
            return {'type': 'unknown', 'name': value}
            
    @staticmethod
    def parse_time_value(value: str) -> int:
        """
        Parse RouterOS time format to seconds.
        
        Args:
            value: Time string (e.g., "1d2h3m4s", "30m", "1w")
            
        Returns:
            Time in seconds
        """
        match = RouterOSPatterns.TIME_PATTERN.match(value)
        if not match:
            return 0
            
        weeks = int(match.group(1) or 0)
        days = int(match.group(2) or 0)
        hours = int(match.group(3) or 0)
        minutes = int(match.group(4) or 0)
        seconds = int(match.group(5) or 0)
        
        total_seconds = (
            weeks * 7 * 24 * 3600 +
            days * 24 * 3600 +
            hours * 3600 +
            minutes * 60 +
            seconds
        )
        
        return total_seconds
        
    @staticmethod
    def validate_mac_address(mac: str) -> bool:
        """Validate MAC address format."""
        return bool(RouterOSPatterns.MAC_ADDRESS_PATTERN.match(mac))
        
    @staticmethod
    def validate_vlan_id(vlan_id: int) -> bool:
        """Validate VLAN ID range (1-4094)."""
        return 1 <= vlan_id <= 4094
        
    @staticmethod
    def extract_vlan_id(line: str) -> Optional[int]:
        """Extract VLAN ID from configuration line."""
        match = RouterOSPatterns.VLAN_ID_PATTERN.search(line)
        if match:
            vlan_id = int(match.group(1))
            if RouterOSPatterns.validate_vlan_id(vlan_id):
                return vlan_id
        return None
        
    @staticmethod
    def parse_firewall_action(action: str) -> Dict[str, str]:
        """
        Parse firewall action.
        
        Args:
            action: Firewall action (accept, drop, reject, jump, etc.)
            
        Returns:
            Dictionary with action details
        """
        action_map = {
            'accept': {'type': 'accept', 'description': 'Allow packet'},
            'drop': {'type': 'drop', 'description': 'Silently drop packet'},
            'reject': {'type': 'reject', 'description': 'Drop and notify sender'},
            'jump': {'type': 'jump', 'description': 'Jump to another chain'},
            'return': {'type': 'return', 'description': 'Return to previous chain'},
            'log': {'type': 'log', 'description': 'Log packet'},
            'passthrough': {'type': 'passthrough', 'description': 'Pass to next rule'}
        }
        
        return action_map.get(action.lower(), {'type': action, 'description': 'Custom action'})
        
    @staticmethod
    def parse_port_range(port_spec: str) -> List[int]:
        """
        Parse port specification (single port or range).
        
        Args:
            port_spec: Port specification (e.g., "80", "80-443", "80,443,8080")
            
        Returns:
            List of port numbers
        """
        ports = []
        
        if ',' in port_spec:
            # Multiple ports
            for part in port_spec.split(','):
                ports.extend(RouterOSPatterns.parse_port_range(part.strip()))
        elif '-' in port_spec:
            # Port range
            try:
                start, end = map(int, port_spec.split('-', 1))
                ports.extend(range(start, end + 1))
            except ValueError:
                pass
        else:
            # Single port
            try:
                ports.append(int(port_spec))
            except ValueError:
                pass
                
        return ports
        
    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """Check if IP address is in private range."""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return False
            
    @staticmethod
    def parse_bandwidth(bandwidth: str) -> Optional[int]:
        """
        Parse bandwidth specification to bits per second.
        
        Args:
            bandwidth: Bandwidth string (e.g., "10M", "1G", "100k")
            
        Returns:
            Bandwidth in bits per second
        """
        multipliers = {
            'k': 1000,
            'K': 1000,
            'm': 1000000,
            'M': 1000000,
            'g': 1000000000,
            'G': 1000000000
        }
        
        match = re.match(r'(\d+(?:\.\d+)?)\s*([kKmMgG])?', bandwidth)
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            
            if unit:
                value *= multipliers.get(unit, 1)
                
            return int(value)
            
        return None
        
    @staticmethod
    def get_mac_vendor(mac_address: str) -> str:
        """
        Get MAC address vendor (simplified version).
        
        Args:
            mac_address: MAC address string
            
        Returns:
            Vendor name or 'Unknown'
        """
        # This is a simplified implementation
        # In a real implementation, you'd use a MAC vendor database
        oui = mac_address.replace(':', '').replace('-', '').upper()[:6]
        
        # Some common OUIs for demonstration
        vendors = {
            '000C29': 'VMware',
            '001B63': 'Apple',
            '00505A': 'IBM',
            '001E68': 'Cisco',
            '001F3F': 'Ubiquiti',
        }
        
        return vendors.get(oui, 'Unknown')
        
    @staticmethod
    def parse_firewall_action(action: str) -> Dict[str, str]:
        """
        Parse firewall action and provide metadata.
        
        Args:
            action: Action string (e.g., "accept", "drop", "reject")
            
        Returns:
            Dictionary with action details
        """
        action_types = {
            'accept': {'type': 'allow', 'description': 'Allow packet'},
            'drop': {'type': 'deny', 'description': 'Silently drop packet'},
            'reject': {'type': 'deny', 'description': 'Reject packet with ICMP'},
            'log': {'type': 'log', 'description': 'Log packet'},
            'passthrough': {'type': 'modify', 'description': 'Continue processing'},
            'fasttrack-connection': {'type': 'optimize', 'description': 'Fast track connection'},
            'tarpit': {'type': 'mitigation', 'description': 'Slow down connection'},
        }
        
        return action_types.get(action.lower(), {
            'type': 'unknown',
            'description': f'Unknown action: {action}'
        })