"""Tests for MPLS section parsers."""
import unittest
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from parser.sections.mpls_parser import (
    MPLSParser, MPLSLDPParser, MPLSInterfaceParser, MPLSForwardingTableParser
)


class TestMPLSParser(unittest.TestCase):
    """Test basic MPLS parser."""
    
    def setUp(self):
        self.parser = MPLSParser()
        
    def test_mpls_settings(self):
        """Test MPLS global settings."""
        lines = ['set propagate-ttl=yes']
        result = self.parser.parse(lines)
        
        self.assertEqual(result['section'], '/mpls')
        cmd = result['commands'][0]
        self.assertTrue(cmd['propagate-ttl'])


class TestMPLSLDPParser(unittest.TestCase):
    """Test MPLS LDP parser."""
    
    def setUp(self):
        self.parser = MPLSLDPParser()
        
    def test_ldp_configuration(self):
        """Test LDP configuration."""
        lines = ['set enabled=yes lsr-id=10.0.0.1 transport-address=10.0.0.1 use-explicit-null=no']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertTrue(cmd['ldp_enabled'])
        self.assertEqual(cmd['lsr_id'], '10.0.0.1')
        self.assertTrue(cmd['lsr_id_valid'])
        self.assertEqual(cmd['transport_address'], '10.0.0.1')
        self.assertTrue(cmd['transport_address_valid'])
        self.assertFalse(cmd['use-explicit-null'])
        
    def test_ldp_invalid_addresses(self):
        """Test LDP with invalid addresses."""
        lines = ['set lsr-id=invalid-ip transport-address=bad-addr']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertFalse(cmd['lsr_id_valid'])
        self.assertFalse(cmd['transport_address_valid'])


class TestMPLSInterfaceParser(unittest.TestCase):
    """Test MPLS interface parser."""
    
    def setUp(self):
        self.parser = MPLSInterfaceParser()
        
    def test_mpls_interface_config(self):
        """Test MPLS interface configuration."""
        lines = ['add interface=ether1 disabled=no mpls-mtu=1500']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['interface'], 'ether1')
        self.assertEqual(cmd['interface_type'], 'ether')
        self.assertFalse(cmd['disabled'])
        self.assertEqual(cmd['mpls_mtu_size'], 1500)
        self.assertFalse(cmd['jumbo_frames'])
        
    def test_mpls_interface_jumbo(self):
        """Test MPLS interface with jumbo frames."""
        lines = ['add interface=ether2 mpls-mtu=9000']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['mpls_mtu_size'], 9000)
        self.assertTrue(cmd['jumbo_frames'])


class TestMPLSForwardingTableParser(unittest.TestCase):
    """Test MPLS forwarding table parser."""
    
    def setUp(self):
        self.parser = MPLSForwardingTableParser()
        
    def test_forwarding_entry_valid(self):
        """Test valid forwarding table entry."""
        lines = ['add label=100 dest-fec=192.168.1.0/24 interface=ether1 gateway=10.0.0.2']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['label_value'], 100)
        self.assertTrue(cmd['label_valid'])
        self.assertFalse(cmd.get('reserved_label', False))
        self.assertEqual(cmd['dest_network'], '192.168.1.0')
        self.assertEqual(cmd['dest_prefix'], 24)
        self.assertTrue(cmd['dest_fec_valid'])
        self.assertTrue(cmd['gateway_valid'])
        
    def test_forwarding_reserved_label(self):
        """Test reserved label detection."""
        lines = ['add label=15 dest-fec=10.0.0.0/8']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['label_value'], 15)
        self.assertTrue(cmd['reserved_label'])
        
    def test_forwarding_invalid_label(self):
        """Test invalid label detection."""
        lines = ['add label=1048577 dest-fec=invalid-network']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertTrue(cmd['invalid_label'])
        self.assertFalse(cmd['dest_fec_valid'])
        
    def test_forwarding_private_gateway(self):
        """Test private gateway detection."""
        lines = ['add label=200 gateway=192.168.1.1']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertTrue(cmd['gateway_is_private'])


if __name__ == '__main__':
    unittest.main()