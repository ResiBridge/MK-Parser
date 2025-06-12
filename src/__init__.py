"""RouterOS configuration parser for GitHub integration."""

__version__ = "1.0.0"
__author__ = "RouterOS Parser Team"
__description__ = "Parse RouterOS configuration files and generate GitHub-friendly summaries"

from .parser import RouterOSParser, ParseError
from .formatters.markdown import GitHubMarkdownFormatter

__all__ = [
    'RouterOSParser',
    'ParseError',
    'GitHubMarkdownFormatter'
]