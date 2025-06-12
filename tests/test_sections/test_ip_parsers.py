"""Tests for IP section parsers."""
import unittest
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from parser.sections.ip_parser import (
    IPArpParser, IPNeighborParser, IPSettingsParser, IPDHCPRelayParser
)


class TestIPArpParser(unittest.TestCase):
    """Test ARP parser."""
    
    def setUp(self):
        self.parser = IPArpParser()
        
    def test_arp_add_command(self):
        """Test parsing ARP add command."""
        lines = ['add address=192.168.1.100 mac-address=00:11:22:33:44:55 interface=ether1']
        result = self.parser.parse(lines)
        
        self.assertEqual(result['section'], '/ip arp')
        self.assertEqual(len(result['commands']), 1)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['action'], 'add')
        self.assertEqual(cmd['address'], '192.168.1.100')
        self.assertEqual(cmd['mac-address'], '00:11:22:33:44:55')
        self.assertEqual(cmd['interface'], 'ether1')
        self.assertTrue(cmd['is_private'])
        
    def test_arp_invalid_address(self):
        """Test ARP with invalid IP address."""
        lines = ['add address=invalid-ip mac-address=00:11:22:33:44:55']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertTrue(cmd['address_invalid'])
        

class TestIPNeighborParser(unittest.TestCase):
    """Test neighbor discovery parser."""
    
    def setUp(self):
        self.parser = IPNeighborParser()
        
    def test_neighbor_static_entry(self):
        """Test static neighbor entry."""
        lines = ['add address=192.168.1.1 mac-address=aa:bb:cc:dd:ee:ff interface=ether1 static=yes']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['address'], '192.168.1.1')
        self.assertTrue(cmd['static'])
        

class TestIPSettingsParser(unittest.TestCase):
    """Test IP settings parser."""
    
    def setUp(self):
        self.parser = IPSettingsParser()
        
    def test_ip_settings(self):
        """Test IP global settings."""
        lines = ['set accept-redirects=yes route-cache=no rp-filter=strict max-neighbor-entries=8192']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertTrue(cmd['accept-redirects'])
        self.assertFalse(cmd['route-cache'])
        self.assertEqual(cmd['rp_filter_level'], 'strict')
        self.assertEqual(cmd['max-neighbor-entries'], 8192)
        

class TestIPDHCPRelayParser(unittest.TestCase):
    """Test DHCP relay parser."""
    
    def setUp(self):
        self.parser = IPDHCPRelayParser()
        
    def test_dhcp_relay_single_server(self):
        """Test DHCP relay with single server."""
        lines = ['add interface=ether1 dhcp-server=192.168.1.1 local-address=192.168.1.254']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['dhcp_servers'], ['192.168.1.1'])
        self.assertEqual(cmd['server_count'], 1)
        self.assertTrue(cmd['local_address_valid'])
        self.assertFalse(cmd['has_invalid_servers'])
        
    def test_dhcp_relay_multiple_servers(self):
        """Test DHCP relay with multiple servers."""
        lines = ['add interface=ether1,ether2 dhcp-server=192.168.1.1,192.168.1.2,invalid-ip']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['server_count'], 3)
        self.assertEqual(len(cmd['valid_servers']), 2)
        self.assertTrue(cmd['has_invalid_servers'])
        self.assertEqual(cmd['interface_count'], 2)


if __name__ == '__main__':
    unittest.main()