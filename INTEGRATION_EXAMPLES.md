# RouterOS Parser - Integration Examples

This document provides practical examples for integrating the RouterOS parser into different repositories and workflows.

## 📦 Installation Options

### Option 1: Git Submodule (Recommended for MK-build repo)
```bash
# In your config generator repo
git submodule add https://github.com/ResiBridge/MK-Parser.git parser
git submodule update --init --recursive

# Use in Python
import sys
sys.path.append('./parser/src')
from routeros_parser import RouterOSParser, generate_markdown_summary
```

### Option 2: Package Dependency 
```bash
# requirements.txt
routeros-parser @ git+https://github.com/ResiBridge/MK-Parser.git

# Use in Python
from routeros_parser import RouterOSParser, generate_markdown_summary
```

### Option 3: Direct Import
```bash
# Download and import directly
git clone https://github.com/ResiBridge/MK-Parser.git
cd MK-Parser/routeros-parser

# Use in Python
import sys
sys.path.append('./src')
from routeros_parser import RouterOSParser, generate_markdown_summary
```

## 🔧 Integration Patterns

### For MK-build (Config Generator Repo)

**Validate Generated Configs Before Commit:**
```python
#!/usr/bin/env python3
"""Pre-commit hook to validate generated RouterOS configs."""
import sys
from pathlib import Path

# Add parser to path (adjust based on your setup)
sys.path.append('./parser/src')  # If using submodule
from routeros_parser import validate_config_file
from routeros_parser.integrations import BulkProcessor

def validate_generated_configs():
    """Validate all generated .rsc files."""
    bulk = BulkProcessor()
    results = bulk.validate_configs('./generated_configs/', recursive=True)
    
    if not results['success']:
        print(f"❌ {results['invalid_files']} config(s) failed validation")
        for result in results['results']:
            if not result['valid']:
                print(f"  {result['file_path']}: {result.get('error', 'Unknown error')}")
        sys.exit(1)
    
    print(f"✅ All {results['valid_files']} config(s) are valid")

if __name__ == "__main__":
    validate_generated_configs()
```

**Generate Config Documentation:**
```python
#!/usr/bin/env python3
"""Generate documentation for config templates."""
from routeros_parser import parse_config_file, generate_markdown_summary
from routeros_parser.integrations import BulkProcessor

# Parse all template configs
bulk = BulkProcessor()
summaries = bulk.parse_backup_configs('./config_templates/')

# Generate multi-device documentation
bulk.export_to_markdown(summaries, './docs/CONFIG_TEMPLATES.md')
print("📝 Template documentation generated")
```

### For Backup Repo

**Automated Backup Analysis:**
```python
#!/usr/bin/env python3
"""Analyze RouterOS backup configurations."""
import os
from datetime import datetime
from routeros_parser.integrations import BulkProcessor, GitHubIntegration

def analyze_daily_backups():
    """Analyze today's backup configurations."""
    today = datetime.now().strftime('%Y-%m-%d')
    backup_dir = f'./backups/{today}'
    
    if not os.path.exists(backup_dir):
        print(f"No backups found for {today}")
        return
    
    # Parse all backup configs
    bulk = BulkProcessor()
    summaries = bulk.parse_backup_configs(backup_dir)
    
    # Generate fleet summary
    fleet_summary = bulk.generate_fleet_summary(summaries)
    
    print(f"📊 Fleet Summary for {today}:")
    print(f"  Total Devices: {fleet_summary['fleet_summary']['total_devices']}")
    print(f"  Success Rate: {fleet_summary['fleet_summary']['success_rate']}")
    print(f"  Total Interfaces: {fleet_summary['network_summary']['total_interfaces']}")
    print(f"  Total VLANs: {fleet_summary['network_summary']['total_vlans']}")
    
    # Export results
    bulk.export_to_json(fleet_summary, f'./reports/{today}-fleet-analysis.json')
    bulk.export_to_markdown(summaries, f'./reports/{today}-backup-summary.md')

if __name__ == "__main__":
    analyze_daily_backups()
```

**Backup Change Detection:**
```python
#!/usr/bin/env python3
"""Detect changes between backup configurations."""
from routeros_parser.integrations import ConfigValidator
from pathlib import Path
import json

def compare_backup_configs(device_name: str, backup1_date: str, backup2_date: str):
    """Compare two backup configurations for a device."""
    config1 = f"./backups/{backup1_date}/{device_name}.rsc"
    config2 = f"./backups/{backup2_date}/{device_name}.rsc"
    
    if not (Path(config1).exists() and Path(config2).exists()):
        print(f"❌ Backup files not found for {device_name}")
        return
    
    validator = ConfigValidator()
    comparison = validator.compare_configs(config1, config2)
    
    print(f"🔍 Config Changes for {device_name}:")
    print(f"  From: {backup1_date} → To: {backup2_date}")
    print(f"  Total Changes: {comparison['change_summary']['total_changes']}")
    print(f"  Sections Added: {comparison['change_summary']['sections_added']}")
    print(f"  Sections Removed: {comparison['change_summary']['sections_removed']}")
    print(f"  Sections Modified: {comparison['change_summary']['sections_modified']}")
    
    # Save detailed comparison
    output_file = f"./changes/{device_name}-{backup1_date}-to-{backup2_date}.json"
    Path(output_file).parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(comparison, f, indent=2)

if __name__ == "__main__":
    # Example usage
    compare_backup_configs("router01", "2024-01-01", "2024-01-02")
```

### For GitHub Actions

**Workflow: Validate RouterOS Configs**
```yaml
# .github/workflows/validate-configs.yml
name: Validate RouterOS Configurations

on:
  push:
    paths:
      - 'configs/*.rsc'
  pull_request:
    paths:
      - 'configs/*.rsc'

jobs:
  validate-configs:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install RouterOS Parser
        run: |
          git clone https://github.com/ResiBridge/MK-Parser.git parser
          
      - name: Validate Configurations
        run: |
          python3 parser/routeros-parser/src/main.py configs/ --validate-only --recursive
          
      - name: Generate Analysis Report
        if: success()
        run: |
          python3 parser/routeros-parser/src/main.py configs/ --github --recursive
        
      - name: Upload Analysis Artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: config-analysis
          path: router-analysis-artifacts/
```

**Python Integration in GitHub Actions:**
```python
#!/usr/bin/env python3
"""GitHub Actions integration script."""
import os
import sys
from routeros_parser.integrations import GitHubIntegration

def main():
    """Main GitHub Actions integration."""
    # Initialize GitHub integration
    gh = GitHubIntegration()
    
    # Get config path from environment or argument
    config_path = os.environ.get('CONFIG_PATH', 'configs/')
    
    try:
        # Parse and create GitHub outputs
        result = gh.parse_and_comment(config_path)
        
        print(f"✅ Parsed {result['configs_parsed']} configurations")
        print(f"📁 Found {result['config_files_found']} config files")
        print(f"❌ {result['parsing_errors']} parsing errors")
        
        # Validate configurations
        validation = gh.validate_configs(config_path)
        
        if not validation['success']:
            print(f"❌ Validation failed: {validation['invalid_files']} invalid configs")
            sys.exit(1)
        else:
            print(f"✅ All {validation['valid_files']} configs are valid")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 🛠️ Command Line Usage

### Basic Operations
```bash
# Parse single config
python3 -m routeros_parser config.rsc

# Parse directory
python3 -m routeros_parser configs/ --recursive

# Validate only
python3 -m routeros_parser configs/ --validate-only

# JSON output
python3 -m routeros_parser config.rsc --output json

# GitHub Actions mode
python3 -m routeros_parser configs/ --github
```

### Advanced Operations
```bash
# Filter specific sections
python3 -m routeros_parser config.rsc --sections "interface,firewall,system"

# Compare configurations
python3 -m routeros_parser new_config.rsc --compare old_config.rsc

# Custom device name
python3 -m routeros_parser config.rsc --device-name "Production-Router"

# Quiet mode (suppress progress)
python3 -m routeros_parser configs/ --quiet
```

## 🐍 Python API Examples

### Simple Parsing
```python
from routeros_parser import parse_config_file, generate_markdown_summary

# Parse a configuration
config = parse_config_file('router.rsc', device_name='MyRouter')
summary = config.get_device_summary()

print(f"Device: {summary['device_name']}")
print(f"Sections: {summary['sections_parsed']}")

# Generate markdown
markdown = generate_markdown_summary(config)
print(markdown)
```

### Bulk Processing
```python
from routeros_parser.integrations import BulkProcessor

# Process multiple configs
bulk = BulkProcessor(max_workers=4)
summaries = bulk.parse_backup_configs('./backup_configs/')

# Generate fleet summary
fleet = bulk.generate_fleet_summary(summaries)
print(f"Fleet has {fleet['fleet_summary']['total_devices']} devices")

# Export results
bulk.export_to_json(fleet, 'fleet-analysis.json')
bulk.export_to_markdown(summaries, 'fleet-summary.md')
```

### Advanced Validation
```python
from routeros_parser.integrations import ConfigValidator

validator = ConfigValidator()

# Basic validation
result = validator.validate_with_rules('config.rsc')
print(f"Compliance: {result['compliance_score']}")

# Security validation
security = validator.validate_security_config('config.rsc')
print(f"Security Score: {security['security_score']}")

# Configuration comparison
comparison = validator.compare_configs('old.rsc', 'new.rsc')
print(f"Changes: {comparison['change_summary']['total_changes']}")
```

## 🔗 Integration Best Practices

### 1. Error Handling
```python
from routeros_parser import validate_config_file

try:
    result = validate_config_file('config.rsc')
    if result['valid']:
        print("✅ Configuration is valid")
    else:
        print(f"❌ Validation failed: {result['error']}")
except Exception as e:
    print(f"💥 Parser error: {e}")
```

### 2. Performance Optimization
```python
from routeros_parser.integrations import BulkProcessor

# Use parallel processing for multiple files
bulk = BulkProcessor(max_workers=8)  # Adjust based on your system

# Process in batches for very large datasets
config_files = list(Path('./configs').rglob('*.rsc'))
batch_size = 100

for i in range(0, len(config_files), batch_size):
    batch = config_files[i:i + batch_size]
    # Process batch...
```

### 3. Memory Management
```python
# For very large configurations, consider streaming
def process_large_configs(config_dir):
    for config_file in Path(config_dir).rglob('*.rsc'):
        try:
            # Process one at a time to manage memory
            config = parse_config_file(str(config_file))
            yield config.get_device_summary()
        except Exception as e:
            print(f"Error processing {config_file}: {e}")
```

This modular design allows easy integration into any Python project while providing powerful CLI tools for automation and CI/CD workflows.