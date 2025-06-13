"""Bulk processing for multiple RouterOS configurations."""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from .. import parse_config_file, validate_config_file
    from ..formatters.markdown import GitHubMarkdownFormatter
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from __init__ import parse_config_file, validate_config_file
    from formatters.markdown import GitHubMarkdownFormatter


class BulkProcessor:
    """Bulk processing for multiple RouterOS configurations."""
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize bulk processor.
        
        Args:
            max_workers: Maximum number of parallel processing threads
        """
        self.max_workers = max_workers
    
    def parse_backup_configs(self, backup_directory: str, pattern: str = "*.rsc") -> List[Dict[str, Any]]:
        """
        Parse all backup configuration files in a directory.
        
        Args:
            backup_directory: Directory containing backup .rsc files
            pattern: File pattern to match (default: "*.rsc")
            
        Returns:
            List of parsed configuration summaries
        """
        backup_path = Path(backup_directory)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup directory not found: {backup_path}")
        
        # Find all config files
        config_files = list(backup_path.rglob(pattern))
        
        if not config_files:
            return []
        
        # Parse configs in parallel
        summaries = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all parsing tasks
            future_to_file = {
                executor.submit(self._parse_single_config, config_file): config_file 
                for config_file in config_files
            }
            
            # Collect results
            for future in as_completed(future_to_file):
                config_file = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        summaries.append(result)
                except Exception as e:
                    print(f"Error parsing {config_file}: {e}")
        
        return summaries
    
    def validate_configs(self, config_directory: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Validate all RouterOS configurations in a directory.
        
        Args:
            config_directory: Directory containing .rsc files
            recursive: Search recursively in subdirectories
            
        Returns:
            Validation summary with detailed results
        """
        config_path = Path(config_directory)
        
        if recursive:
            config_files = list(config_path.rglob("*.rsc"))
        else:
            config_files = list(config_path.glob("*.rsc"))
        
        if not config_files:
            return {
                'total_files': 0,
                'valid_files': 0,
                'invalid_files': 0,
                'success': True,
                'results': []
            }
        
        # Validate configs in parallel
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(validate_config_file, str(config_file)): config_file
                for config_file in config_files
            }
            
            for future in as_completed(future_to_file):
                config_file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'valid': False,
                        'file_path': str(config_file),
                        'error': str(e),
                        'parsing_errors': 1
                    })
        
        # Calculate summary
        valid_count = sum(1 for r in results if r['valid'])
        invalid_count = len(results) - valid_count
        
        return {
            'total_files': len(results),
            'valid_files': valid_count,
            'invalid_files': invalid_count,
            'success': invalid_count == 0,
            'results': results
        }
    
    def generate_fleet_summary(self, summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate fleet-wide summary from multiple device configurations.
        
        Args:
            summaries: List of device configuration summaries
            
        Returns:
            Fleet-wide analytics and summary
        """
        if not summaries:
            return {'devices': 0, 'error': 'No configurations provided'}
        
        # Aggregate statistics
        total_devices = len(summaries)
        total_sections = sum(s.get('sections_parsed', 0) for s in summaries)
        total_errors = sum(s.get('parsing_errors', 0) for s in summaries)
        
        # Interface statistics
        total_interfaces = 0
        total_vlans = 0
        total_bridges = 0
        interface_types = {}
        
        # IP statistics
        total_ip_addresses = 0
        networks = set()
        
        # Device names
        device_names = []
        
        for summary in summaries:
            device_names.append(summary.get('device_name', 'Unknown'))
            
            # Process interface sections
            for section_name, section_data in summary.get('section_summaries', {}).items():
                if 'interface' in section_name.lower():
                    total_interfaces += section_data.get('total_interfaces', 0)
                    total_vlans += section_data.get('vlans', 0)
                    total_bridges += section_data.get('bridges', 0)
                
                # Process IP sections
                elif 'ip address' in section_name.lower():
                    total_ip_addresses += section_data.get('address_count', 0)
                    networks.update(section_data.get('networks', []))
        
        return {
            'fleet_summary': {
                'total_devices': total_devices,
                'total_sections': total_sections,
                'total_errors': total_errors,
                'success_rate': f"{((total_devices - total_errors) / total_devices * 100):.1f}%" if total_devices > 0 else "0%"
            },
            'network_summary': {
                'total_interfaces': total_interfaces,
                'total_vlans': total_vlans,
                'total_bridges': total_bridges,
                'total_ip_addresses': total_ip_addresses,
                'unique_networks': len(networks)
            },
            'devices': device_names,
            'detailed_summaries': summaries
        }
    
    def export_to_json(self, data: Dict[str, Any], output_file: str):
        """
        Export analysis results to JSON file.
        
        Args:
            data: Data to export
            output_file: Output JSON file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def export_to_markdown(self, summaries: List[Dict[str, Any]], output_file: str):
        """
        Export multi-device summary to markdown file.
        
        Args:
            summaries: List of device summaries
            output_file: Output markdown file path
        """
        formatter = GitHubMarkdownFormatter()
        markdown = formatter.format_multi_device_summary(summaries)
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
    
    def _parse_single_config(self, config_file: Path) -> Optional[Dict[str, Any]]:
        """Parse a single configuration file."""
        try:
            config = parse_config_file(str(config_file))
            summary = config.get_device_summary()
            
            # Add file metadata
            summary['file_path'] = str(config_file)
            summary['file_size'] = config_file.stat().st_size
            summary['file_modified'] = config_file.stat().st_mtime
            
            return summary
            
        except Exception as e:
            print(f"Error parsing {config_file}: {e}")
            return None