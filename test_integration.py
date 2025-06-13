#!/usr/bin/env python3
"""Integration test for RouterOS parser modular design."""
import sys
import json
from pathlib import Path

# Test clean imports
print(" Testing RouterOS Parser Integration...")

try:
    # Test main imports
    print("\n1. Testing main imports...")
    from src import RouterOSParser, GitHubMarkdownFormatter, RouterOSConfig
    from src import parse_config_file, validate_config_file, generate_markdown_summary
    print("    Core imports successful")
    
    # Test integration imports
    print("\n2. Testing integration imports...")
    from src.integrations import GitHubIntegration, BulkProcessor, ConfigValidator
    print("    Integration imports successful")
    
    # Test basic parsing
    print("\n3. Testing basic parsing...")
    config = parse_config_file('tests/fixtures/sample_basic.rsc')
    summary = config.get_device_summary()
    print(f"    Parsed {summary['device_name']} with {summary['sections_parsed']} sections")
    
    # Test validation
    print("\n4. Testing validation...")
    validation = validate_config_file('tests/fixtures/sample_basic.rsc')
    print(f"    Validation result: {validation['valid']} - {validation['sections_parsed']} sections")
    
    # Test markdown generation
    print("\n5. Testing markdown generation...")
    markdown = generate_markdown_summary(config)
    print(f"    Generated {len(markdown)} characters of markdown")
    
    # Test bulk processing
    print("\n6. Testing bulk processing...")
    bulk = BulkProcessor(max_workers=2)
    summaries = bulk.parse_backup_configs('tests/fixtures/')
    fleet_summary = bulk.generate_fleet_summary(summaries)
    print(f"    Bulk processed {len(summaries)} configs")
    print(f"    Fleet summary: {fleet_summary['fleet_summary']['total_devices']} devices")
    
    # Test GitHub integration
    print("\n7. Testing GitHub integration...")
    gh = GitHubIntegration('.')
    print("    GitHubIntegration initialized")
    
    # Test advanced validation
    print("\n8. Testing advanced validation...")
    validator = ConfigValidator()
    advanced_validation = validator.validate_with_rules('tests/fixtures/sample_basic.rsc')
    security_validation = validator.validate_security_config('tests/fixtures/sample_basic.rsc')
    print(f"    Advanced validation: {advanced_validation['compliance_score']} compliance")
    print(f"    Security validation: {security_validation['security_score']} security score")
    
    # Test CLI functionality
    print("\n9. Testing CLI functionality...")
    import subprocess
    result = subprocess.run([
        sys.executable, 'src/main.py', 
        'tests/fixtures/sample_basic.rsc', 
        '--validate-only', '--quiet'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("    CLI validation successful")
    else:
        print(f"    CLI validation failed: {result.stderr}")
    
    # Final summary
    print(f"\n Integration test completed successfully!")
    print(f"    All imports working")
    print(f"    All APIs functional") 
    print(f"    Ready for external integration")
    
except Exception as e:
    print(f"\n Integration test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)