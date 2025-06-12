"""Tests for firewall section parsers."""
import unittest
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from parser.sections.firewall_parser import (
    FirewallLayer7ProtocolParser, FirewallServicePortParser
)


class TestFirewallLayer7ProtocolParser(unittest.TestCase):
    """Test Layer 7 protocol parser."""
    
    def setUp(self):
        self.parser = FirewallLayer7ProtocolParser()
        
    def test_layer7_protocol_simple(self):
        """Test simple Layer 7 protocol definition."""
        lines = ['add name=http regexp="^(GET|POST|HEAD)" comment="HTTP protocol detection"']
        result = self.parser.parse(lines)
        
        self.assertEqual(result['section'], '/ip firewall layer7-protocol')
        cmd = result['commands'][0]
        self.assertEqual(cmd['protocol_name'], 'http')
        self.assertEqual(cmd['regex_pattern'], '^(GET|POST|HEAD)')
        self.assertTrue(cmd['has_regex'])
        self.assertTrue(cmd['has_groups'])
        self.assertTrue(cmd['has_alternation'])
        self.assertTrue(cmd['has_comment'])
        
    def test_layer7_protocol_complex_regex(self):
        """Test complex regex pattern."""
        lines = ['add name=ssh regexp="^SSH-[12]\\.[0-9]" disabled=yes']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['protocol_name'], 'ssh')
        self.assertTrue(cmd['disabled'])
        self.assertGreater(cmd['pattern_length'], 10)
        

class TestFirewallServicePortParser(unittest.TestCase):
    """Test service port parser."""
    
    def setUp(self):
        self.parser = FirewallServicePortParser()
        
    def test_service_port_single(self):
        """Test single port service."""
        lines = ['add name=ssh ports=22 protocol=tcp']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['service_name'], 'ssh')
        self.assertEqual(cmd['transport_protocol'], 'tcp')
        self.assertTrue(cmd['is_tcp'])
        self.assertFalse(cmd['is_udp'])
        self.assertEqual(cmd['port_count'], 1)
        self.assertFalse(cmd['has_range'])
        
    def test_service_port_range(self):
        """Test port range service."""
        lines = ['add name=ftp-data ports=20-21 protocol=tcp comment="FTP control and data"']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['service_name'], 'ftp-data')
        self.assertTrue(cmd['has_range'])
        self.assertTrue(cmd['has_comment'])
        self.assertGreater(cmd['port_count'], 1)
        
    def test_service_port_multiple(self):
        """Test multiple ports service."""
        lines = ['add name=dns ports=53,5353 protocol=udp']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertTrue(cmd['is_udp'])
        self.assertEqual(cmd['port_count'], 2)


if __name__ == '__main__':
    unittest.main()