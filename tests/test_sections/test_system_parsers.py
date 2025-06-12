"""Tests for system section parsers."""
import unittest
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from parser.sections.system_parser import (
    PasswordParser, ImportParser, ExportParser, ConsoleParser,
    FileParser, PortParser, RadiusParser, SpecialLoginParser, PartitionsParser
)


class TestPasswordParser(unittest.TestCase):
    """Test password parser."""
    
    def setUp(self):
        self.parser = PasswordParser()
        
    def test_password_set(self):
        """Test password setting with redaction."""
        lines = ['set password=secret123 old-password=oldpass confirm-with-old-password=yes']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertTrue(cmd['password_set'])
        self.assertEqual(cmd['password_length'], 9)
        self.assertEqual(cmd['password_redacted'], '***REDACTED***')
        self.assertTrue(cmd['old_password_provided'])
        self.assertTrue(cmd['confirm-with-old-password'])


class TestImportExportParsers(unittest.TestCase):
    """Test import and export parsers."""
    
    def setUp(self):
        self.import_parser = ImportParser()
        self.export_parser = ExportParser()
        
    def test_import_rsc_file(self):
        """Test importing RSC file."""
        lines = ['config-backup.rsc']
        result = self.import_parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['action'], 'import')
        self.assertEqual(cmd['filename'], 'config-backup.rsc')
        self.assertEqual(cmd['file_extension'], 'rsc')
        self.assertTrue(cmd['is_rsc_file'])
        self.assertFalse(cmd['is_backup_file'])
        
    def test_export_with_file(self):
        """Test export to file."""
        lines = ['file=backup.rsc compact show-sensitive=yes']
        result = self.export_parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['action'], 'export')
        self.assertEqual(cmd['filename'], 'backup.rsc')
        self.assertEqual(cmd['format'], 'compact')
        self.assertTrue(cmd['show_sensitive'])


class TestConsoleParser(unittest.TestCase):
    """Test console parser."""
    
    def setUp(self):
        self.parser = ConsoleParser()
        
    def test_console_settings(self):
        """Test console configuration."""
        lines = ['set auto-logout=1h session-timeout=30m silent-boot=yes']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['auto_logout_seconds'], 3600)
        self.assertEqual(cmd['session_timeout_seconds'], 1800)
        self.assertTrue(cmd['silent-boot'])


class TestFileParser(unittest.TestCase):
    """Test file parser."""
    
    def setUp(self):
        self.parser = FileParser()
        
    def test_file_operations(self):
        """Test various file operations."""
        lines = [
            'remove old-config.rsc',
            'copy config.rsc to backup-config.rsc',
            'rename backup.rsc to old-backup.rsc'
        ]
        result = self.parser.parse(lines)
        
        commands = result['commands']
        
        # Test remove
        self.assertEqual(commands[0]['action'], 'remove')
        self.assertEqual(commands[0]['filename'], 'old-config.rsc')
        
        # Test copy
        self.assertEqual(commands[1]['action'], 'copy')
        self.assertEqual(commands[1]['source'], 'config.rsc')
        self.assertEqual(commands[1]['destination'], 'backup-config.rsc')
        
        # Test rename
        self.assertEqual(commands[2]['action'], 'rename')
        self.assertEqual(commands[2]['old_name'], 'backup.rsc')
        self.assertEqual(commands[2]['new_name'], 'old-backup.rsc')


class TestPortParser(unittest.TestCase):
    """Test port parser."""
    
    def setUp(self):
        self.parser = PortParser()
        
    def test_serial_port_config(self):
        """Test serial port configuration."""
        lines = ['set baud-rate=115200 data-bits=8 parity=none stop-bits=1 flow-control=none']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['baud_rate_value'], 115200)
        self.assertTrue(cmd['is_standard_baud'])
        self.assertEqual(cmd['data_bits_value'], 8)
        self.assertEqual(cmd['parity_type'], 'none')
        self.assertEqual(cmd['stop_bits_value'], 1)


class TestRadiusParser(unittest.TestCase):
    """Test RADIUS parser."""
    
    def setUp(self):
        self.parser = RadiusParser()
        
    def test_radius_server_config(self):
        """Test RADIUS server configuration."""
        lines = ['add address=192.168.1.10 secret=radiussecret service=login timeout=3s']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['server_address'], '192.168.1.10')
        self.assertTrue(cmd['address_valid'])
        self.assertTrue(cmd['is_private'])
        self.assertTrue(cmd['secret_set'])
        self.assertEqual(cmd['secret_redacted'], '***REDACTED***')
        self.assertEqual(cmd['radius_service'], 'login')
        self.assertEqual(cmd['timeout_seconds'], 3)


class TestSpecialLoginParser(unittest.TestCase):
    """Test special login parser."""
    
    def setUp(self):
        self.parser = SpecialLoginParser()
        
    def test_special_login_methods(self):
        """Test special login method configuration."""
        lines = ['set telnet=no ssh=yes ftp=no www=yes winbox=yes']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertFalse(cmd['telnet_enabled'])
        self.assertTrue(cmd['ssh_enabled'])
        self.assertFalse(cmd['ftp_enabled'])
        self.assertTrue(cmd['www_enabled'])
        self.assertTrue(cmd['winbox_enabled'])


class TestPartitionsParser(unittest.TestCase):
    """Test partitions parser."""
    
    def setUp(self):
        self.parser = PartitionsParser()
        
    def test_partition_config(self):
        """Test partition configuration."""
        lines = ['add size=2G type=system active=yes primary=yes']
        result = self.parser.parse(lines)
        
        cmd = result['commands'][0]
        self.assertEqual(cmd['size_gb'], 2.0)
        self.assertEqual(cmd['size_mb'], 2048.0)
        self.assertEqual(cmd['partition_type'], 'system')
        self.assertTrue(cmd['is_system'])
        self.assertTrue(cmd['active'])
        self.assertTrue(cmd['primary'])


if __name__ == '__main__':
    unittest.main()