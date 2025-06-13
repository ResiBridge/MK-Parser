"""Configuration validation utilities for RouterOS parser."""
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re

try:
    from .. import parse_config_file, validate_config_file
    from ..utils.patterns import RouterOSPatterns
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from __init__ import parse_config_file, validate_config_file
    from utils.patterns import RouterOSPatterns


class ConfigValidator:
    """Advanced configuration validation for RouterOS configurations."""
    
    def __init__(self):
        """Initialize configuration validator."""
        self.patterns = RouterOSPatterns
        self.validation_rules = self._load_validation_rules()
    
    def validate_with_rules(self, config_file: str, custom_rules: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Validate configuration against best practice rules.
        
        Args:
            config_file: Path to RouterOS configuration file
            custom_rules: Optional custom validation rules
            
        Returns:
            Validation results with rule compliance
        """
        # Basic validation first
        basic_validation = validate_config_file(config_file)
        if not basic_validation['valid']:
            return basic_validation
        
        # Advanced validation
        config = parse_config_file(config_file)
        summary = config.get_device_summary()
        
        # Apply validation rules
        rule_results = []
        rules_to_check = self.validation_rules + (custom_rules or [])
        
        for rule in rules_to_check:
            result = self._apply_rule(summary, rule)
            rule_results.append(result)
        
        # Calculate compliance score
        passed_rules = sum(1 for r in rule_results if r['passed'])
        compliance_score = (passed_rules / len(rule_results)) * 100 if rule_results else 100
        
        return {
            **basic_validation,
            'advanced_validation': True,
            'compliance_score': f"{compliance_score:.1f}%",
            'rules_checked': len(rule_results),
            'rules_passed': passed_rules,
            'rules_failed': len(rule_results) - passed_rules,
            'rule_results': rule_results
        }
    
    def validate_security_config(self, config_file: str) -> Dict[str, Any]:
        """
        Validate security-specific configuration aspects.
        
        Args:
            config_file: Path to RouterOS configuration file
            
        Returns:
            Security validation results
        """
        config = parse_config_file(config_file)
        summary = config.get_device_summary()
        
        security_checks = []
        
        # Check for default passwords
        security_checks.append(self._check_default_passwords(summary))
        
        # Check firewall configuration
        security_checks.append(self._check_firewall_rules(summary))
        
        # Check service security
        security_checks.append(self._check_service_security(summary))
        
        # Check access control
        security_checks.append(self._check_access_control(summary))
        
        # Calculate security score
        passed_checks = sum(1 for check in security_checks if check['passed'])
        security_score = (passed_checks / len(security_checks)) * 100
        
        return {
            'security_score': f"{security_score:.1f}%",
            'security_checks': len(security_checks),
            'checks_passed': passed_checks,
            'checks_failed': len(security_checks) - passed_checks,
            'security_results': security_checks,
            'recommendations': self._generate_security_recommendations(security_checks)
        }
    
    def compare_configs(self, config1_path: str, config2_path: str) -> Dict[str, Any]:
        """
        Compare two RouterOS configurations.
        
        Args:
            config1_path: Path to first configuration
            config2_path: Path to second configuration
            
        Returns:
            Configuration comparison results
        """
        config1 = parse_config_file(config1_path)
        config2 = parse_config_file(config2_path)
        
        summary1 = config1.get_device_summary()
        summary2 = config2.get_device_summary()
        
        differences = {
            'sections_added': [],
            'sections_removed': [],
            'sections_modified': [],
            'interface_changes': self._compare_interfaces(summary1, summary2),
            'ip_changes': self._compare_ip_config(summary1, summary2),
            'firewall_changes': self._compare_firewall(summary1, summary2)
        }
        
        # Compare sections
        sections1 = set(summary1.get('section_summaries', {}).keys())
        sections2 = set(summary2.get('section_summaries', {}).keys())
        
        differences['sections_added'] = list(sections2 - sections1)
        differences['sections_removed'] = list(sections1 - sections2)
        
        # Check for modifications in common sections
        common_sections = sections1 & sections2
        for section in common_sections:
            if summary1['section_summaries'][section] != summary2['section_summaries'][section]:
                differences['sections_modified'].append(section)
        
        return {
            'config1': config1_path,
            'config2': config2_path,
            'device1': summary1.get('device_name', 'Unknown'),
            'device2': summary2.get('device_name', 'Unknown'),
            'differences': differences,
            'change_summary': {
                'total_changes': (len(differences['sections_added']) + 
                                len(differences['sections_removed']) + 
                                len(differences['sections_modified'])),
                'sections_added': len(differences['sections_added']),
                'sections_removed': len(differences['sections_removed']),
                'sections_modified': len(differences['sections_modified'])
            }
        }
    
    def _load_validation_rules(self) -> List[Dict[str, Any]]:
        """Load default validation rules."""
        return [
            {
                'name': 'Device Identity Set',
                'description': 'Device should have a proper identity name',
                'check': lambda summary: summary.get('device_name', '') not in ['Unknown', 'Unknown Device', ''],
                'severity': 'warning'
            },
            {
                'name': 'Firewall Rules Present',
                'description': 'Device should have firewall rules configured',
                'check': lambda summary: any('firewall' in section for section in summary.get('section_summaries', {})),
                'severity': 'warning'
            },
            {
                'name': 'Interface Configuration',
                'description': 'Device should have at least one configured interface',
                'check': lambda summary: any(
                    section_data.get('total_interfaces', 0) > 0 
                    for section_data in summary.get('section_summaries', {}).values()
                    if isinstance(section_data, dict) and 'total_interfaces' in section_data
                ),
                'severity': 'error'
            },
            {
                'name': 'IP Address Assignment',
                'description': 'Device should have at least one IP address configured',
                'check': lambda summary: any(
                    section_data.get('address_count', 0) > 0
                    for section_data in summary.get('section_summaries', {}).values()
                    if isinstance(section_data, dict) and 'address_count' in section_data
                ),
                'severity': 'warning'
            }
        ]
    
    def _apply_rule(self, summary: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single validation rule."""
        try:
            passed = rule['check'](summary)
            return {
                'rule_name': rule['name'],
                'description': rule['description'],
                'severity': rule['severity'],
                'passed': passed,
                'message': 'PASS' if passed else 'FAIL'
            }
        except Exception as e:
            return {
                'rule_name': rule['name'],
                'description': rule['description'],
                'severity': rule['severity'],
                'passed': False,
                'message': f'ERROR: {str(e)}'
            }
    
    def _check_default_passwords(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Check for default or weak passwords."""
        # This would need access to the actual parsed commands
        # For now, return a placeholder check
        return {
            'check_name': 'Default Passwords',
            'description': 'Check for default or weak passwords',
            'passed': True,  # Would implement actual check with access to user commands
            'details': 'Password security check placeholder'
        }
    
    def _check_firewall_rules(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Check firewall configuration."""
        has_firewall = any('firewall' in section for section in summary.get('section_summaries', {}))
        
        return {
            'check_name': 'Firewall Configuration',
            'description': 'Device should have firewall rules configured',
            'passed': has_firewall,
            'details': 'Firewall rules found' if has_firewall else 'No firewall rules configured'
        }
    
    def _check_service_security(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Check service security configuration."""
        # Check if services section exists
        has_services = any('service' in section for section in summary.get('section_summaries', {}))
        
        return {
            'check_name': 'Service Security',
            'description': 'Management services should be properly configured',
            'passed': has_services,
            'details': 'Services configured' if has_services else 'No service configuration found'
        }
    
    def _check_access_control(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Check access control configuration."""
        has_users = any('user' in section for section in summary.get('section_summaries', {}))
        
        return {
            'check_name': 'Access Control',
            'description': 'User accounts should be properly configured',
            'passed': has_users,
            'details': 'User accounts configured' if has_users else 'No user configuration found'
        }
    
    def _generate_security_recommendations(self, security_checks: List[Dict]) -> List[str]:
        """Generate security recommendations based on check results."""
        recommendations = []
        
        for check in security_checks:
            if not check['passed']:
                if check['check_name'] == 'Firewall Configuration':
                    recommendations.append("Configure firewall rules to protect the device")
                elif check['check_name'] == 'Service Security':
                    recommendations.append("Review and secure management services")
                elif check['check_name'] == 'Access Control':
                    recommendations.append("Configure user accounts with appropriate permissions")
        
        return recommendations
    
    def _compare_interfaces(self, summary1: Dict, summary2: Dict) -> Dict[str, Any]:
        """Compare interface configurations between two summaries."""
        # Placeholder for interface comparison
        return {'changes': 'Interface comparison not yet implemented'}
    
    def _compare_ip_config(self, summary1: Dict, summary2: Dict) -> Dict[str, Any]:
        """Compare IP configurations between two summaries."""
        # Placeholder for IP comparison
        return {'changes': 'IP configuration comparison not yet implemented'}
    
    def _compare_firewall(self, summary1: Dict, summary2: Dict) -> Dict[str, Any]:
        """Compare firewall configurations between two summaries."""
        # Placeholder for firewall comparison
        return {'changes': 'Firewall comparison not yet implemented'}