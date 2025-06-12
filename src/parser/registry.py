"""Section parser registry for RouterOS configuration sections."""
import fnmatch
from typing import Dict, Type, Optional
from abc import ABC, abstractmethod


class BaseSectionParser(ABC):
    """Base class for all section parsers."""
    
    def __init__(self):
        self.commands = []
        
    @abstractmethod
    def parse(self, lines: list) -> dict:
        """Parse section lines into structured data."""
        pass
        
    @abstractmethod
    def get_summary(self) -> dict:
        """Get section summary for display."""
        pass


class GenericSectionParser(BaseSectionParser):
    """Generic parser for unknown sections."""
    
    def __init__(self, section_name: str):
        super().__init__()
        self.section_name = section_name
        
    def parse(self, lines: list) -> dict:
        """Parse lines as generic key-value pairs."""
        commands = []
        current_command = {}
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Handle add/set commands
            if line.startswith('add ') or line.startswith('set '):
                if current_command:
                    commands.append(current_command)
                current_command = {'action': line.split()[0]}
                params = line[4:].strip()
            else:
                params = line
                
            # Parse parameters
            self._parse_parameters(params, current_command)
            
        if current_command:
            commands.append(current_command)
            
        return {
            'section': self.section_name,
            'commands': commands
        }
        
    def _parse_parameters(self, params: str, command: dict):
        """Parse command parameters."""
        # Simple key=value parsing
        parts = params.split()
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                command[key] = value.strip('"')
            else:
                # Flag parameter
                command[part] = True
                
    def get_summary(self) -> dict:
        """Get generic section summary."""
        return {
            'section': self.section_name,
            'command_count': len(self.commands)
        }


class SectionParserRegistry:
    """Registry for section parsers."""
    
    _parsers: Dict[str, Type[BaseSectionParser]] = {}
    
    @classmethod
    def register(cls, section_pattern: str, parser_class: Type[BaseSectionParser]):
        """Register a parser for a section pattern."""
        cls._parsers[section_pattern] = parser_class
        
    @classmethod
    def get_parser(cls, section_name: str) -> BaseSectionParser:
        """Get parser instance for a section."""
        # Try exact match first
        if section_name in cls._parsers:
            return cls._parsers[section_name]()
            
        # Try pattern matching
        for pattern, parser_class in cls._parsers.items():
            if fnmatch.fnmatch(section_name, pattern):
                return parser_class()
                
        # Return generic parser for unknown sections
        return GenericSectionParser(section_name)
        
    @classmethod
    def list_registered(cls) -> list:
        """List all registered section patterns."""
        return list(cls._parsers.keys())