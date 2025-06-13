#!/usr/bin/env python3
"""Demo script to show RouterOS parser functionality."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parser.core import RouterOSParser
from formatters.markdown import GitHubMarkdownFormatter


def main():
    """Run demo parsing."""
    print(" RouterOS Configuration Parser Demo\n")
    
    # Parse the comprehensive sample config
    config_file = Path(__file__).parent / 'tests' / 'fixtures' / 'comprehensive_config.rsc'
    
    if not config_file.exists():
        print(f" Config file not found: {config_file}")
        return
        
    print(f" Parsing: {config_file.name}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Parse configuration
    parser = RouterOSParser(content, 'ComprehensiveRouter')
    config = parser.parse()
    
    # Get summary
    summary = config.get_device_summary()
    
    print(f" Parsed {summary['sections_parsed']} sections")
    print(f" Sections found: {', '.join(summary['section_list'])}")
    
    if summary['parsing_errors'] > 0:
        print(f"  Parsing errors: {summary['parsing_errors']}")
    
    # Generate markdown
    print("\n Generating GitHub Markdown Summary...\n")
    
    formatter = GitHubMarkdownFormatter()
    markdown = formatter.format_device_summary(summary)
    
    # Show first part of markdown
    lines = markdown.split('\n')
    for i, line in enumerate(lines[:30]):  # Show first 30 lines
        print(line)
        
    if len(lines) > 30:
        print(f"\n... ({len(lines) - 30} more lines)")
        
    # Save full output
    output_file = Path(__file__).parent / 'demo_output.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
        
    print(f"\n Full output saved to: {output_file}")
    print(f" Total markdown lines: {len(lines)}")
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f" Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)