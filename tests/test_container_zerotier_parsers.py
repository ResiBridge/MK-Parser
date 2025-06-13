"""Tests for Container and ZeroTier parsers."""
import unittest
from pathlib import Path
import sys

# Add src to path for imports
test_dir = Path(__file__).parent
project_root = test_dir.parent
src_dir = project_root / 'src'
sys.path.insert(0, str(src_dir))

from parser.sections.advanced_parser import (
    ContainerConfigParser, ContainerEnvsParser, 
    ContainerMountsParser, ZeroTierParser
)


class TestContainerConfigParser(unittest.TestCase):
    """Test cases for /container config parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ContainerConfigParser()
        
    def test_container_config_basic(self):
        """Test basic container config parsing."""
        lines = [
            'set registry-url="https://registry.example.com"',
            'set tmpdir="/flash/containers/tmp"',
            'set ram-high=1024M',
            'set extract-timeout=10m',
            'set enabled=yes'
        ]
        
        result = self.parser.parse(lines)
        
        self.assertEqual(result['section'], '/container config')
        self.assertEqual(len(result['commands']), 5)
        
        # Check parsed registry URL
        registry_cmd = result['commands'][0]
        self.assertEqual(registry_cmd['registry_url'], 'https://registry.example.com')
        self.assertTrue(registry_cmd['uses_custom_registry'])
        self.assertEqual(registry_cmd['registry_type'], 'custom')
        
        # Check RAM high watermark
        ram_cmd = result['commands'][2]
        self.assertEqual(ram_cmd['ram_high_mb'], 1024)
        self.assertTrue(ram_cmd['high_ram_limit'])
        
    def test_docker_hub_registry_detection(self):
        """Test Docker Hub registry detection."""
        lines = ['set registry-url="https://hub.docker.com"']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['registry_type'], 'docker_hub')
        
    def test_summary_generation(self):
        """Test summary generation."""
        lines = ['set enabled=yes']
        self.parser.parse(lines)
        
        summary = self.parser.get_summary()
        self.assertEqual(summary['section'], 'Container Config')
        self.assertEqual(summary['command_count'], 1)


class TestContainerEnvsParser(unittest.TestCase):
    """Test cases for /container envs parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ContainerEnvsParser()
        
    def test_container_envs_basic(self):
        """Test basic container environment variables parsing."""
        lines = [
            'add name="APP_DEBUG" value="true"',
            'add name="DB_PASSWORD" value="secret123"',
            'add name="LOG_LEVEL" value="info"',
            'add name="PATH" value="/usr/local/bin:/usr/bin"'
        ]
        
        result = self.parser.parse(lines)
        
        self.assertEqual(result['section'], '/container envs')
        self.assertEqual(len(result['commands']), 4)
        
        # Check environment variable classification
        app_debug = result['commands'][0]
        self.assertEqual(app_debug['env_name'], 'APP_DEBUG')
        self.assertEqual(app_debug['env_type'], 'application')
        
        db_password = result['commands'][1]
        self.assertEqual(db_password['env_type'], 'secret')
        self.assertTrue(db_password['contains_sensitive'])
        
        log_level = result['commands'][2]
        self.assertEqual(log_level['env_type'], 'logging')
        
        path_env = result['commands'][3]
        self.assertEqual(path_env['env_type'], 'system')
        
    def test_sensitive_value_detection(self):
        """Test detection of sensitive values."""
        lines = [
            'add name="API_TOKEN" value="abc123"',
            'add name="SECRET_KEY" value="xyz789"'
        ]
        
        result = self.parser.parse(lines)
        
        # These should be detected as sensitive by name, not value
        for cmd in result['commands']:
            self.assertTrue(cmd.get('contains_sensitive', False) or cmd.get('potentially_sensitive', False))
            
    def test_summary_with_sensitive_data(self):
        """Test summary generation with sensitive data."""
        lines = [
            'add name="APP_NAME" value="myapp"',
            'add name="DB_PASSWORD" value="secret"'
        ]
        
        self.parser.parse(lines)
        summary = self.parser.get_summary()
        
        self.assertEqual(summary['section'], 'Container Environment Variables')
        self.assertEqual(summary['environment_variable_count'], 2)
        self.assertEqual(summary['sensitive_variables'], 1)
        self.assertTrue(summary['has_sensitive_data'])


class TestContainerMountsParser(unittest.TestCase):
    """Test cases for /container mounts parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ContainerMountsParser()
        
    def test_container_mounts_basic(self):
        """Test basic container mounts parsing."""
        lines = [
            'add name="app-data" src="/flash/app" dst="/app" options="rw,bind"',
            'add name="config" src="/etc/app" dst="/config" options="ro,bind"',
            'add name="logs" src="/var/log/app" dst="/var/log" options="rw"'
        ]
        
        result = self.parser.parse(lines)
        
        self.assertEqual(result['section'], '/container mounts')
        self.assertEqual(len(result['commands']), 3)
        
        # Check mount classification
        app_data = result['commands'][0]
        self.assertEqual(app_data['mount_name'], 'app-data')
        self.assertEqual(app_data['source_type'], 'flash')
        self.assertEqual(app_data['mount_purpose'], 'application')
        self.assertTrue(app_data['read_write'])
        self.assertTrue(app_data['bind_mount'])
        
        config_mount = result['commands'][1]
        self.assertEqual(config_mount['mount_purpose'], 'configuration')
        self.assertTrue(config_mount['read_only'])
        
        logs_mount = result['commands'][2]
        self.assertEqual(logs_mount['source_type'], 'variable_data')
        self.assertEqual(logs_mount['mount_purpose'], 'logging')
        
    def test_source_path_classification(self):
        """Test source path type classification."""
        test_cases = [
            ('/flash/data', 'flash'),
            ('/rw/app', 'rw_partition'),
            ('/tmp/cache', 'temporary'),
            ('/etc/config', 'system_config'),
            ('/var/lib/app', 'variable_data'),
            ('/custom/path', 'other')
        ]
        
        for src_path, expected_type in test_cases:
            lines = [f'add name="test" src="{src_path}" dst="/app"']
            result = self.parser.parse(lines)
            cmd = result['commands'][0]
            self.assertEqual(cmd['source_type'], expected_type, f"Failed for {src_path}")
            
    def test_summary_generation(self):
        """Test summary generation."""
        lines = [
            'add name="ro-mount" src="/etc/app" dst="/config" options="ro"',
            'add name="rw-mount" src="/data" dst="/app" options="rw,bind"'
        ]
        
        self.parser.parse(lines)
        summary = self.parser.get_summary()
        
        self.assertEqual(summary['section'], 'Container Mounts')
        self.assertEqual(summary['mount_point_count'], 2)
        self.assertEqual(summary['read_only_mounts'], 1)
        self.assertEqual(summary['read_write_mounts'], 1)
        self.assertTrue(summary['has_bind_mounts'])


class TestZeroTierParser(unittest.TestCase):
    """Test cases for /zerotier parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ZeroTierParser()
        
    def test_zerotier_basic(self):
        """Test basic ZeroTier parsing."""
        lines = [
            'add network="8056c2e21c000001" name="zt-network1"',
            'add network="1234567890abcdef" port=9993 copy-routes=yes',
            'add network="invalid-network-id" disabled=yes'
        ]
        
        result = self.parser.parse(lines)
        
        self.assertEqual(result['section'], '/zerotier')
        self.assertEqual(len(result['commands']), 3)
        
        # Check valid network ID
        net1 = result['commands'][0]
        self.assertEqual(net1['network_id'], '8056c2e21c000001')
        self.assertTrue(net1['valid_network_id'])
        self.assertEqual(net1['interface_name'], 'zt-network1')
        
        # Check port configuration
        net2 = result['commands'][1]
        self.assertEqual(net2['port_number'], 9993)
        self.assertTrue(net2['uses_default_port'])
        self.assertTrue(net2['valid_port'])
        self.assertTrue(net2['copy_routes'])
        
        # Check invalid network ID
        net3 = result['commands'][2]
        self.assertFalse(net3['valid_network_id'])
        self.assertTrue(net3['disabled'])
        
    def test_network_id_validation(self):
        """Test ZeroTier network ID validation."""
        test_cases = [
            ('8056c2e21c000001', True),   # Valid 16-char hex
            ('1234567890abcdef', True),   # Valid 16-char hex
            ('ABCDEF1234567890', True),   # Valid uppercase hex
            ('123456789', False),         # Too short
            ('8056c2e21c0000012', False), # Too long
            ('8056c2e21c00000g', False),  # Invalid character
            ('', False)                   # Empty
        ]
        
        for network_id, expected_valid in test_cases:
            lines = [f'add network="{network_id}"']
            result = self.parser.parse(lines)
            cmd = result['commands'][0]
            self.assertEqual(cmd['valid_network_id'], expected_valid, 
                           f"Failed for network ID: {network_id}")
            
    def test_port_validation(self):
        """Test port number validation."""
        lines = [
            'add network="8056c2e21c000001" port=8080',
            'add network="8056c2e21c000002" port=65536',  # Invalid - too high
            'add network="8056c2e21c000003" port=0'       # Invalid - too low
        ]
        
        result = self.parser.parse(lines)
        
        # Valid port
        self.assertTrue(result['commands'][0]['valid_port'])
        self.assertFalse(result['commands'][0]['uses_default_port'])
        
        # Invalid ports
        self.assertFalse(result['commands'][1]['valid_port'])
        self.assertFalse(result['commands'][2]['valid_port'])
        
    def test_summary_generation(self):
        """Test summary generation."""
        lines = [
            'add network="8056c2e21c000001" allow-managed=yes',
            'add network="1234567890abcdef" allow-global=yes',
            'add network="invalid-id" disabled=yes'
        ]
        
        self.parser.parse(lines)
        summary = self.parser.get_summary()
        
        self.assertEqual(summary['section'], 'ZeroTier Networks')
        self.assertEqual(summary['network_count'], 3)
        self.assertEqual(summary['valid_network_ids'], 2)
        self.assertEqual(summary['managed_networks'], 1)
        self.assertTrue(summary['has_global_routes'])
        self.assertFalse(summary['has_default_routes'])


if __name__ == '__main__':
    unittest.main()