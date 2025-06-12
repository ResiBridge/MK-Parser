"""Basic tests for RouterOS parser."""
import unittest
from pathlib import Path
import sys
import os

# Add src to path for imports
test_dir = Path(__file__).parent
project_root = test_dir.parent
src_dir = project_root / 'src'
sys.path.insert(0, str(src_dir))

from parser.core import RouterOSParser
from formatters.markdown import GitHubMarkdownFormatter


class TestRouterOSParser(unittest.TestCase):
    """Test cases for RouterOS parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fixtures_dir = test_dir / 'fixtures'
        self.basic_config = self.fixtures_dir / 'sample_basic.rsc'
        self.complex_config = self.fixtures_dir / 'sample_complex.rsc'
        
    def test_basic_config_parsing(self):
        """Test parsing of basic configuration file."""
        with open(self.basic_config, 'r', encoding='utf-8') as f:
            content = f.read()
            
        parser = RouterOSParser(content, 'TestRouter')
        config = parser.parse()
        
        # Check that config was created
        self.assertIsNotNone(config)
        
        # Check device summary
        summary = config.get_device_summary()
        self.assertEqual(summary['device_name'], 'TestRouter')
        self.assertGreater(summary['sections_parsed'], 0)
        self.assertEqual(summary['parsing_errors'], 0)
        
        # Check that key sections were parsed
        sections = summary['section_summaries']
        self.assertIn('/system identity', sections)
        self.assertIn('/interface ethernet', sections)
        self.assertIn('/ip address', sections)
        self.assertIn('/ip firewall filter', sections)
        
        print(f"✅ Basic config: {summary['sections_parsed']} sections parsed successfully")
        
    def test_complex_config_parsing(self):
        """Test parsing of complex configuration file."""
        with open(self.complex_config, 'r', encoding='utf-8') as f:
            content = f.read()
            
        parser = RouterOSParser(content, 'BorderRouter-01')
        config = parser.parse()
        
        # Check that config was created
        self.assertIsNotNone(config)
        
        # Check device summary
        summary = config.get_device_summary()
        self.assertEqual(summary['device_name'], 'BorderRouter-01')
        self.assertGreater(summary['sections_parsed'], 5)
        
        # Check that advanced sections were parsed
        sections = summary['section_summaries']
        self.assertIn('/interface vlan', sections)
        self.assertIn('/ip firewall address-list', sections)
        self.assertIn('/queue simple', sections)
        
        print(f"✅ Complex config: {summary['sections_parsed']} sections parsed successfully")
        
    def test_section_discovery(self):
        """Test dynamic section discovery."""
        with open(self.complex_config, 'r', encoding='utf-8') as f:
            content = f.read()
            
        parser = RouterOSParser(content, 'BorderRouter-01')
        discovered_sections = parser.discover_sections()
        
        # Check that sections were discovered
        self.assertGreater(len(discovered_sections), 10)
        self.assertIn('/system identity', discovered_sections)
        self.assertIn('/interface vlan', discovered_sections)
        self.assertIn('/ip firewall filter', discovered_sections)
        
        print(f"✅ Section discovery: {len(discovered_sections)} sections found")
        
    def test_markdown_formatter(self):
        """Test GitHub markdown formatter."""
        with open(self.basic_config, 'r', encoding='utf-8') as f:
            content = f.read()
            
        parser = RouterOSParser(content, 'TestRouter')
        config = parser.parse()
        summary = config.get_device_summary()
        
        formatter = GitHubMarkdownFormatter()
        markdown = formatter.format_device_summary(summary)
        
        # Check markdown content
        self.assertIsInstance(markdown, str)
        self.assertIn('# 🔧 TestRouter', markdown)
        self.assertIn('## 📊 Overview', markdown)
        self.assertIn('## 🔌 Interfaces', markdown)
        self.assertIn('## 🌐 IP', markdown)
        
        print("✅ Markdown formatting completed successfully")
        
    def test_multi_device_formatting(self):
        """Test multi-device summary formatting."""
        # Parse both configs
        summaries = []
        
        for config_file in [self.basic_config, self.complex_config]:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            device_name = config_file.stem.replace('sample_', '').replace('_', '-')
            parser = RouterOSParser(content, device_name)
            config = parser.parse()
            summaries.append(config.get_device_summary())
            
        # Format multi-device summary
        formatter = GitHubMarkdownFormatter()
        markdown = formatter.format_multi_device_summary(summaries)
        
        # Check content
        self.assertIn('# 🏢 Network Configuration Summary', markdown)
        self.assertIn('**Total Devices:** 2', markdown)
        self.assertIn('## 📱 Devices Overview', markdown)
        
        print("✅ Multi-device formatting completed successfully")
        
    def test_error_handling(self):
        """Test error handling with malformed config."""
        malformed_content = """
        /system identity
        set name=BrokenRouter
        
        /ip address
        add address=invalid-ip interface=ether1
        
        /interface ethernet
        set [ find default-name=ether1 ] name=
        """
        
        parser = RouterOSParser(malformed_content, 'BrokenRouter')
        config = parser.parse()
        
        # Should not crash, but may have parsing errors
        summary = config.get_device_summary()
        self.assertIsNotNone(summary)
        
        print("✅ Error handling test completed")


class TestPatternExtraction(unittest.TestCase):
    """Test pattern extraction utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        sys.path.insert(0, str(project_root / 'src'))
        from utils.patterns import RouterOSPatterns
        self.patterns = RouterOSPatterns
        
    def test_ip_extraction(self):
        """Test IP address extraction."""
        # Test valid IP
        result = self.patterns.extract_ip_network('192.168.1.1/24')
        self.assertIsNotNone(result)
        self.assertEqual(result[0], '192.168.1.1')
        self.assertEqual(result[1], '192.168.1.0')
        self.assertEqual(result[2], 24)
        
        # Test invalid IP
        result = self.patterns.extract_ip_network('invalid-ip')
        self.assertIsNone(result)
        
        print("✅ IP extraction tests passed")
        
    def test_time_parsing(self):
        """Test time value parsing."""
        # Test various time formats
        self.assertEqual(self.patterns.parse_time_value('1d'), 86400)
        self.assertEqual(self.patterns.parse_time_value('2h30m'), 9000)
        self.assertEqual(self.patterns.parse_time_value('1w2d3h4m5s'), 788645)
        
        print("✅ Time parsing tests passed")
        
    def test_vlan_validation(self):
        """Test VLAN ID validation."""
        self.assertTrue(self.patterns.validate_vlan_id(1))
        self.assertTrue(self.patterns.validate_vlan_id(4094))
        self.assertFalse(self.patterns.validate_vlan_id(0))
        self.assertFalse(self.patterns.validate_vlan_id(4095))
        
        print("✅ VLAN validation tests passed")


def run_tests():
    """Run all tests and display results."""
    print("🧪 Running RouterOS Parser Tests\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add core test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRouterOSParser))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternExtraction))
    
    # Add section-specific tests
    try:
        # Import test modules
        import test_sections.test_ip_parsers as ip_tests
        import test_sections.test_firewall_parsers as fw_tests
        import test_sections.test_system_parsers as sys_tests
        import test_sections.test_mpls_parsers as mpls_tests
        
        # IP parser tests
        suite.addTests(loader.loadTestsFromTestCase(ip_tests.TestIPArpParser))
        suite.addTests(loader.loadTestsFromTestCase(ip_tests.TestIPNeighborParser))
        suite.addTests(loader.loadTestsFromTestCase(ip_tests.TestIPSettingsParser))
        suite.addTests(loader.loadTestsFromTestCase(ip_tests.TestIPDHCPRelayParser))
        
        # Firewall parser tests
        suite.addTests(loader.loadTestsFromTestCase(fw_tests.TestFirewallLayer7ProtocolParser))
        suite.addTests(loader.loadTestsFromTestCase(fw_tests.TestFirewallServicePortParser))
        
        # System parser tests
        suite.addTests(loader.loadTestsFromTestCase(sys_tests.TestPasswordParser))
        suite.addTests(loader.loadTestsFromTestCase(sys_tests.TestImportExportParsers))
        suite.addTests(loader.loadTestsFromTestCase(sys_tests.TestConsoleParser))
        suite.addTests(loader.loadTestsFromTestCase(sys_tests.TestFileParser))
        suite.addTests(loader.loadTestsFromTestCase(sys_tests.TestPortParser))
        suite.addTests(loader.loadTestsFromTestCase(sys_tests.TestRadiusParser))
        suite.addTests(loader.loadTestsFromTestCase(sys_tests.TestSpecialLoginParser))
        suite.addTests(loader.loadTestsFromTestCase(sys_tests.TestPartitionsParser))
        
        # MPLS parser tests
        suite.addTests(loader.loadTestsFromTestCase(mpls_tests.TestMPLSParser))
        suite.addTests(loader.loadTestsFromTestCase(mpls_tests.TestMPLSLDPParser))
        suite.addTests(loader.loadTestsFromTestCase(mpls_tests.TestMPLSInterfaceParser))
        suite.addTests(loader.loadTestsFromTestCase(mpls_tests.TestMPLSForwardingTableParser))
        
        print("✅ All section-specific tests loaded")
        
    except ImportError as e:
        print(f"⚠️ Warning: Could not load some section tests: {e}")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure}")
            
    if result.errors:
        print("\n💥 Errors:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
            
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed.'}")
    
    return success


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)