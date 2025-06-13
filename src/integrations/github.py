"""GitHub Actions integration for RouterOS parser."""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from .. import parse_config_file, generate_markdown_summary, validate_config_file
    from ..formatters.markdown import GitHubMarkdownFormatter
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from __init__ import parse_config_file, generate_markdown_summary, validate_config_file
    from formatters.markdown import GitHubMarkdownFormatter


class GitHubIntegration:
    """GitHub Actions integration for RouterOS configuration parsing."""
    
    def __init__(self, workspace_path: str = None):
        """
        Initialize GitHub integration.
        
        Args:
            workspace_path: GitHub workspace path (defaults to GITHUB_WORKSPACE env var)
        """
        self.workspace_path = Path(workspace_path or os.environ.get('GITHUB_WORKSPACE', '.'))
        self.is_github_actions = 'GITHUB_ACTIONS' in os.environ
        
    def parse_and_comment(self, config_path: str, comment_on_pr: bool = True) -> Dict[str, Any]:
        """
        Parse RouterOS configs and create GitHub comment/summary.
        
        Args:
            config_path: Path to config file or directory (relative to workspace)
            comment_on_pr: Whether to comment on PR (default: True)
            
        Returns:
            Dictionary with parsing results and GitHub outputs
        """
        full_path = self.workspace_path / config_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Config path not found: {full_path}")
        
        # Find config files
        if full_path.is_file():
            config_files = [full_path]
        else:
            config_files = list(full_path.rglob('*.rsc'))
        
        if not config_files:
            raise ValueError(f"No .rsc files found in {full_path}")
        
        # Parse all configs
        summaries = []
        for config_file in config_files:
            config = parse_config_file(str(config_file))
            summaries.append(config.get_device_summary())
        
        # Generate markdown
        formatter = GitHubMarkdownFormatter()
        if len(summaries) == 1:
            markdown = formatter.format_device_summary(summaries[0])
        else:
            markdown = formatter.format_multi_device_summary(summaries)
        
        # Write to GitHub outputs
        result = {
            'config_files_found': len(config_files),
            'configs_parsed': len(summaries),
            'parsing_errors': sum(s.get('parsing_errors', 0) for s in summaries),
            'markdown_summary': markdown
        }
        
        if self.is_github_actions:
            self._write_github_outputs(markdown, result)
        
        return result
    
    def validate_configs(self, config_path: str) -> Dict[str, Any]:
        """
        Validate RouterOS configurations for CI/CD.
        
        Args:
            config_path: Path to config file or directory
            
        Returns:
            Validation results dictionary
        """
        full_path = self.workspace_path / config_path
        
        if full_path.is_file():
            config_files = [full_path]
        else:
            config_files = list(full_path.rglob('*.rsc'))
        
        results = []
        total_errors = 0
        
        for config_file in config_files:
            validation = validate_config_file(str(config_file))
            results.append(validation)
            if not validation['valid']:
                total_errors += 1
        
        summary = {
            'total_files': len(config_files),
            'valid_files': len(config_files) - total_errors,
            'invalid_files': total_errors,
            'success': total_errors == 0,
            'results': results
        }
        
        if self.is_github_actions:
            self._write_validation_outputs(summary)
        
        return summary
    
    def _write_github_outputs(self, markdown: str, result: Dict[str, Any]):
        """Write outputs for GitHub Actions."""
        # Write step summary
        summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary_file:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
        
        # Set output variables
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a', encoding='utf-8') as f:
                f.write(f"configs_parsed={result['configs_parsed']}\\n")
                f.write(f"parsing_errors={result['parsing_errors']}\\n")
                f.write(f"config_files_found={result['config_files_found']}\\n")
        
        # Write artifact
        artifact_dir = Path('router-analysis-artifacts')
        artifact_dir.mkdir(exist_ok=True)
        
        with open(artifact_dir / 'config-summary.md', 'w', encoding='utf-8') as f:
            f.write(markdown)
    
    def _write_validation_outputs(self, summary: Dict[str, Any]):
        """Write validation outputs for GitHub Actions."""
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a', encoding='utf-8') as f:
                f.write(f"validation_success={str(summary['success']).lower()}\\n")
                f.write(f"total_files={summary['total_files']}\\n")
                f.write(f"valid_files={summary['valid_files']}\\n")
                f.write(f"invalid_files={summary['invalid_files']}\\n")
        
        # Set exit code for CI/CD
        if not summary['success']:
            print(" Configuration validation failed", file=sys.stderr)
            for result in summary['results']:
                if not result['valid']:
                    print(f"  {result['file_path']}: {result.get('error', 'Unknown error')}", file=sys.stderr)
    
    def create_pr_comment(self, markdown: str) -> str:
        """
        Create PR comment with configuration analysis.
        
        Args:
            markdown: Markdown content for the comment
            
        Returns:
            Comment content with GitHub formatting
        """
        return f"""##  RouterOS Configuration Analysis

{markdown}

---
*Generated by RouterOS Parser v1.0.0*
"""