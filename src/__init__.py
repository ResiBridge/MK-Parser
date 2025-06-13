"""RouterOS configuration parser for GitHub integration."""

__version__ = "1.0.0"
__author__ = "RouterOS Parser Team"
__description__ = "Parse RouterOS configuration files and generate GitHub-friendly summaries"

from .parser import RouterOSParser, ParseError
from .formatters.markdown import GitHubMarkdownFormatter
from .models.config import RouterOSConfig
from .utils.patterns import RouterOSPatterns

# Convenience functions for common use cases
def parse_config_file(file_path: str, device_name: str = None) -> RouterOSConfig:
    """
    Parse a RouterOS configuration file.
    
    Args:
        file_path: Path to .rsc configuration file
        device_name: Optional device name (auto-detected if not provided)
        
    Returns:
        RouterOSConfig object with parsed configuration
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if not device_name:
        device_name = file_path.split('/')[-1].replace('.rsc', '')
    
    parser = RouterOSParser(content, device_name)
    return parser.parse()

def parse_config_string(content: str, device_name: str = "RouterOS Device") -> RouterOSConfig:
    """
    Parse RouterOS configuration from string content.
    
    Args:
        content: RouterOS configuration content
        device_name: Device name for the configuration
        
    Returns:
        RouterOSConfig object with parsed configuration
    """
    parser = RouterOSParser(content, device_name)
    return parser.parse()

def generate_markdown_summary(config: RouterOSConfig) -> str:
    """
    Generate GitHub markdown summary from parsed configuration.
    
    Args:
        config: Parsed RouterOS configuration
        
    Returns:
        Formatted markdown string
    """
    formatter = GitHubMarkdownFormatter()
    return formatter.format_device_summary(config.get_device_summary())

def validate_config_file(file_path: str) -> dict:
    """
    Validate a RouterOS configuration file.
    
    Args:
        file_path: Path to .rsc configuration file
        
    Returns:
        Dictionary with validation results
    """
    try:
        config = parse_config_file(file_path)
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

__all__ = [
    'RouterOSParser',
    'ParseError', 
    'GitHubMarkdownFormatter',
    'RouterOSConfig',
    'RouterOSPatterns',
    'parse_config_file',
    'parse_config_string',
    'generate_markdown_summary',
    'validate_config_file'
]