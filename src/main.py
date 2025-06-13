#!/usr/bin/env python3
"""Main CLI interface for RouterOS configuration parser."""
import argparse
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Support both package and direct execution
try:
    from .parser.core import RouterOSParser
    from .formatters.markdown import GitHubMarkdownFormatter
    from . import parse_config_file as convenience_parse_config_file
    from . import validate_config_file, generate_markdown_summary
except ImportError:
    # Direct execution fallback
    sys.path.insert(0, str(Path(__file__).parent))
    from parser.core import RouterOSParser
    from formatters.markdown import GitHubMarkdownFormatter
    
    def convenience_parse_config_file(file_path, device_name=None):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if not device_name:
            device_name = Path(file_path).stem.replace('.rsc', '')
        parser = RouterOSParser(content, device_name)
        return parser.parse()
    
    def validate_config_file(file_path):
        try:
            config = convenience_parse_config_file(file_path)
            summary = config.get_device_summary()
            return {
                'valid': True,
                'file_path': file_path,
                'device_name': summary['device_name'],
                'sections_parsed': summary['sections_parsed'],
                'parsing_errors': summary['parsing_errors'],
                'errors': config.errors if config.errors else []
            }
        except Exception as e:
            return {
                'valid': False,
                'file_path': file_path,
                'error': str(e),
                'parsing_errors': 1
            }
    
    def generate_markdown_summary(config):
        formatter = GitHubMarkdownFormatter()
        return formatter.format_device_summary(config.get_device_summary())


def parse_config_file(file_path: Path) -> Dict[str, Any]:
    """
    Parse a single RouterOS config file.
    
    Args:
        file_path: Path to .rsc config file
        
    Returns:
        Device summary dictionary
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract device name from filename
        device_name = file_path.stem.replace('.rsc', '')
        
        print(f"Parsing {file_path.name}...", file=sys.stderr)
        
        parser = RouterOSParser(content, device_name)
        config = parser.parse()
        
        summary = config.get_device_summary()
        
        # Add file info
        summary['file_path'] = str(file_path)
        summary['file_size'] = file_path.stat().st_size
        
        return summary
        
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return {
            'device_name': file_path.stem,
            'file_path': str(file_path),
            'error': str(e),
            'sections_parsed': 0,
            'parsing_errors': 1,
            'section_summaries': {}
        }


def find_config_files(directory: Path, recursive: bool = False) -> List[Path]:
    """
    Find all .rsc files in directory.
    
    Args:
        directory: Directory to search
        recursive: Search recursively in subdirectories
        
    Returns:
        List of .rsc file paths
    """
    if recursive:
        return list(directory.rglob('*.rsc'))
    else:
        return list(directory.glob('*.rsc'))


def setup_github_output():
    """Setup GitHub Actions output environment."""
    # Create output directory if it doesn't exist
    output_dir = Path('.github-output')
    output_dir.mkdir(exist_ok=True)
    
    return output_dir


def write_github_output(content: str, output_type: str = 'summary'):
    """
    Write content to GitHub Actions output.
    
    Args:
        content: Content to write
        output_type: Type of output ('summary', 'artifact')
    """
    if output_type == 'summary':
        # Write to step summary
        summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary_file:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            # Fallback to file in current directory
            with open('router-config-summary.md', 'w', encoding='utf-8') as f:
                f.write(content)
                
    elif output_type == 'artifact':
        # Write to artifact file
        output_dir = setup_github_output()
        artifact_file = output_dir / 'router-config-analysis.md'
        with open(artifact_file, 'w', encoding='utf-8') as f:
            f.write(content)


def print_github_commands(content: str):
    """Print GitHub Actions workflow commands."""
    print("::group::RouterOS Configuration Summary")
    print(content)
    print("::endgroup::")


def validate_arguments(args):
    """Validate command line arguments."""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path '{path}' does not exist", file=sys.stderr)
        sys.exit(1)
        
    if path.is_file() and not path.suffix == '.rsc':
        print(f"Warning: File '{path}' does not have .rsc extension", file=sys.stderr)
        
    return path


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description='Parse RouterOS configuration files for GitHub',
        epilog="""
Examples:
  %(prog)s config.rsc                    # Parse single file
  %(prog)s configs/                      # Parse directory
  %(prog)s configs/ --recursive          # Parse directory recursively
  %(prog)s config.rsc --github           # GitHub Actions mode
  %(prog)s configs/ --output json        # JSON output
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        'path', 
        help='Path to .rsc file or directory containing .rsc files'
    )
    
    # Optional arguments
    parser.add_argument(
        '--output', 
        choices=['markdown', 'json'], 
        default='markdown',
        help='Output format (default: markdown)'
    )
    
    parser.add_argument(
        '--github', 
        action='store_true',
        help='Format output for GitHub Actions (step summary and workflow commands)'
    )
    
    parser.add_argument(
        '--recursive', 
        action='store_true',
        help='Search for .rsc files recursively in subdirectories'
    )
    
    parser.add_argument(
        '--compare',
        metavar='OLD_PATH',
        help='Compare with previous configuration (provide path to old config)'
    )
    
    parser.add_argument(
        '--sections',
        help='Comma-separated list of sections to include (default: all)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress messages'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate configuration syntax, do not generate summary'
    )
    
    parser.add_argument(
        '--device-name',
        help='Override device name (for single file parsing)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    path = validate_arguments(args)
    
    # Find config files
    if path.is_file():
        config_files = [path]
    else:
        config_files = find_config_files(path, args.recursive)
        
    if not config_files:
        print("No .rsc files found", file=sys.stderr)
        sys.exit(1)
        
    if not args.quiet:
        print(f"Found {len(config_files)} configuration file(s)", file=sys.stderr)
    
    # Parse all config files
    summaries = []
    errors = 0
    
    for config_file in config_files:
        summary = parse_config_file(config_file)
        summaries.append(summary)
        
        if summary.get('parsing_errors', 0) > 0:
            errors += 1
            
    # Validation-only mode
    if args.validate_only:
        if errors == 0:
            print("✅ All configuration files are valid")
            sys.exit(0)
        else:
            print(f"❌ {errors} configuration file(s) have validation errors")
            sys.exit(1)
    
    # Filter sections if specified
    if args.sections:
        requested_sections = set(section.strip() for section in args.sections.split(','))
        for summary in summaries:
            filtered_summaries = {}
            for section_name, section_data in summary.get('section_summaries', {}).items():
                if any(req_section in section_name for req_section in requested_sections):
                    filtered_summaries[section_name] = section_data
            summary['section_summaries'] = filtered_summaries
    
    # Handle comparison mode
    if args.compare:
        if len(summaries) != 1:
            print("Error: Comparison mode only supports single file analysis", file=sys.stderr)
            sys.exit(1)
            
        compare_path = Path(args.compare)
        if not compare_path.exists():
            print(f"Error: Comparison file '{compare_path}' does not exist", file=sys.stderr)
            sys.exit(1)
            
        old_summary = parse_config_file(compare_path)
        new_summary = summaries[0]
        
        # Generate comparison
        formatter = GitHubMarkdownFormatter()
        output = formatter.format_comparison_summary(old_summary, new_summary)
        
    else:
        # Format output
        if args.output == 'markdown':
            formatter = GitHubMarkdownFormatter()
            if len(summaries) == 1:
                output = formatter.format_device_summary(summaries[0])
            else:
                output = formatter.format_multi_device_summary(summaries)
        else:  # json
            if len(summaries) == 1:
                output = json.dumps(summaries[0], indent=2)
            else:
                output = json.dumps({
                    'summary': {
                        'total_devices': len(summaries),
                        'total_errors': errors,
                        'analysis_date': formatter._get_current_date() if 'formatter' in locals() else None
                    },
                    'devices': summaries
                }, indent=2)
    
    # Output results
    if args.github:
        # GitHub Actions mode
        print_github_commands(output)
        write_github_output(output, 'summary')
        write_github_output(output, 'artifact')
        
        # Set GitHub outputs
        if errors == 0:
            print("::set-output name=status::success")
            print("::set-output name=has_errors::false")
        else:
            print("::set-output name=status::warning")
            print("::set-output name=has_errors::true")
            
        print(f"::set-output name=device_count::{len(summaries)}")
        print(f"::set-output name=error_count::{errors}")
        
    else:
        # Standard output
        print(output)
    
    # Exit with appropriate code
    if errors > 0 and not args.github:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()