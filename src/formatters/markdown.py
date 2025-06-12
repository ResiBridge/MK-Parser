"""GitHub markdown formatter for RouterOS configuration data."""
from typing import Dict, List, Any, Optional


class GitHubMarkdownFormatter:
    """Format parsed RouterOS config data for GitHub display."""
    
    def __init__(self):
        pass
        
    def format_device_summary(self, summary: Dict[str, Any]) -> str:
        """
        Format complete device summary as markdown.
        
        Args:
            summary: Device summary from RouterOSConfig.get_device_summary()
            
        Returns:
            Formatted markdown string for GitHub display
        """
        device_name = summary.get('device_name', 'Unknown Device')
        sections = summary.get('section_summaries', {})
        errors = summary.get('parsing_errors', 0)
        
        markdown = f"# 🔧 {device_name} Configuration Summary\n\n"
        
        # Overview section
        markdown += "## 📊 Overview\n\n"
        markdown += f"**Device Name:** `{device_name}`  \n"
        markdown += f"**Sections Parsed:** {len(sections)}  \n"
        
        if errors > 0:
            markdown += f"**Parsing Errors:** {errors}  \n"
        else:
            markdown += f"**Parsing Errors:** 0  \n"
            
        markdown += "\n"
        
        # Quick stats table
        markdown += self._generate_quick_stats_table(sections)
        
        # Generate section summaries
        for section_name, section_data in sections.items():
            if 'error' in section_data:
                markdown += self._format_error_section(section_name, section_data)
            else:
                markdown += self._format_section(section_data)
                
        # Add parsing errors if any
        if summary.get('errors'):
            markdown += self._format_parsing_errors(summary['errors'])
            
        return markdown
        
    def _generate_quick_stats_table(self, sections: Dict[str, Any]) -> str:
        """Generate quick statistics table."""
        markdown = "### Quick Statistics\n\n"
        markdown += "| Category | Count |\n"
        markdown += "|----------|-------|\n"
        
        # Aggregate key statistics
        stats = {
            'Interfaces': 0,
            'IP Addresses': 0,
            'Firewall Rules': 0,
            'Users': 0,
            'VLANs': 0,
            'Bridges': 0
        }
        
        for section_data in sections.values():
            section_name = section_data.get('section', '')
            
            if 'Interface' in section_name:
                stats['Interfaces'] += section_data.get('total_interfaces', 0)
                stats['VLANs'] += section_data.get('vlans', 0)
                stats['Bridges'] += section_data.get('bridges', 0)
            elif 'IP' in section_name and 'address' in section_name.lower():
                stats['IP Addresses'] += section_data.get('address_count', 0)
            elif 'Firewall' in section_name:
                stats['Firewall Rules'] += section_data.get('filter_rules', 0)
                stats['Firewall Rules'] += section_data.get('nat_rules', 0)
                stats['Firewall Rules'] += section_data.get('mangle_rules', 0)
            elif 'User' in section_name:
                stats['Users'] += section_data.get('user_count', 0)
                
        for category, count in stats.items():
            if count > 0:
                markdown += f"| {category} | {count} |\n"
                
        markdown += "\n"
        return markdown
        
    def _format_section(self, section_data: Dict[str, Any]) -> str:
        """Format individual section data."""
        section_name = section_data.get('section', 'Unknown Section')
        
        if section_name == 'Interfaces':
            return self._format_interface_section(section_data)
        elif 'IP' in section_name:
            return self._format_ip_section(section_data)
        elif section_name in ['System', 'System Identity', 'Users', 'IP Services']:
            return self._format_system_section(section_data, '⚙️')
        elif 'Firewall' in section_name:
            return self._format_firewall_section(section_data, '🔥')
        else:
            return self._format_generic_section(section_data, '📋')
            
    def _format_interface_section(self, data: Dict[str, Any]) -> str:
        """Format interface section data."""
        markdown = f"## 🔌 Interfaces\n\n"
        
        # Summary table
        markdown += "| Type | Count |\n"
        markdown += "|------|-------|\n"
        markdown += f"| Physical Interfaces | {data.get('physical_interfaces', 0)} |\n"
        markdown += f"| Bridges | {data.get('bridges', 0)} |\n"
        markdown += f"| VLANs | {data.get('vlans', 0)} |\n"
        markdown += f"| Tunnels | {data.get('tunnels', 0)} |\n"
        markdown += f"| **Total** | **{data.get('total_interfaces', 0)}** |\n\n"
        
        # Bridge details
        if data.get('bridge_list'):
            markdown += "<details>\n<summary>Bridges</summary>\n\n"
            for bridge in data.get('bridge_list', []):
                markdown += f"- `{bridge}`\n"
            markdown += "\n</details>\n\n"
            
        # VLAN details
        if data.get('vlan_list'):
            markdown += "<details>\n<summary>VLANs</summary>\n\n"
            for vlan in data.get('vlan_list', []):
                markdown += f"- {vlan}\n"
            markdown += "\n</details>\n\n"
            
        # Tunnel breakdown
        if data.get('tunnel_types'):
            markdown += "<details>\n<summary>Tunnels by Type</summary>\n\n"
            for tunnel_type, count in data.get('tunnel_types', {}).items():
                markdown += f"- **{tunnel_type.upper()}**: {count}\n"
            markdown += "\n</details>\n\n"
            
        return markdown
        
    def _format_ip_section(self, data: Dict[str, Any]) -> str:
        """Format IP section data."""
        section_name = data.get('section', 'IP Configuration')
        markdown = f"## 🌐 {section_name}\n\n"
        
        # Section-specific formatting
        if 'address' in section_name.lower():
            markdown += f"**Configured IPs:** {data.get('address_count', 0)}  \n\n"
            
            # IP addresses
            if data.get('ip_addresses'):
                markdown += "<details>\n<summary>IP Addresses</summary>\n\n"
                for ip in data.get('ip_addresses', []):
                    markdown += f"- `{ip}`\n"
                markdown += "\n</details>\n\n"
                
            # Networks
            if data.get('networks'):
                markdown += "<details>\n<summary>Networks</summary>\n\n"
                for network in data.get('networks', []):
                    markdown += f"- `{network}`\n"
                markdown += "\n</details>\n\n"
                
        elif 'route' in section_name.lower():
            markdown += f"**Static Routes:** {data.get('route_count', 0)}  \n\n"
            
        elif 'dhcp' in section_name.lower():
            if 'server' in section_name.lower():
                markdown += f"**DHCP Servers:** {data.get('dhcp_server_count', 0)}  \n"
                markdown += f"**DHCP Networks:** {data.get('dhcp_network_count', 0)}  \n\n"
            else:
                markdown += f"**Command Count:** {data.get('command_count', 0)}  \n\n"
                
        elif 'dns' in section_name.lower():
            markdown += f"**Command Count:** {data.get('command_count', 0)}  \n"
            if data.get('dns_servers'):
                markdown += f"**DNS Servers:** {', '.join(f'`{server}`' for server in data.get('dns_servers', []))}  \n"
            markdown += "\n"
            
        else:
            # Generic IP section
            for key, value in data.items():
                if key != 'section' and not key.endswith('_count'):
                    if isinstance(value, int):
                        markdown += f"**{key.replace('_', ' ').title()}:** {value}  \n"
            markdown += "\n"
            
        return markdown
        
    def _format_system_section(self, data: Dict[str, Any], icon: str) -> str:
        """Format system section data."""
        section_name = data.get('section', 'System')
        markdown = f"## {icon} {section_name}\n\n"
        
        if section_name in ['System', 'System Identity']:
            # Device info
            markdown += f"**Device Name:** `{data.get('device_name', 'Unknown')}`  \n"
            if data.get('timezone'):
                markdown += f"**Timezone:** `{data.get('timezone')}`  \n"
            markdown += "\n"
            
        elif section_name == 'Users':
            markdown += f"**Total Users:** {data.get('user_count', 0)}  \n\n"
            
            # Users list
            if data.get('user_list'):
                markdown += "<details>\n<summary>👥 Users</summary>\n\n"
                for user in data.get('user_list', []):
                    markdown += f"- {user}\n"
                markdown += "\n</details>\n\n"
                
            # Admin users
            if data.get('admin_users'):
                markdown += "**Admin Users:** "
                markdown += ", ".join(f"`{user}`" for user in data.get('admin_users', []))
                markdown += "\n\n"
                
        elif section_name == 'IP Services':
            markdown += f"**Services Configured:** {data.get('service_count', 0)}  \n\n"
            
            # Management access
            if data.get('enabled_services'):
                markdown += "**Enabled Services:** "
                markdown += ", ".join(f"`{service}`" for service in data.get('enabled_services', []))
                markdown += "\n\n"
                
            if data.get('management_access'):
                markdown += "**Management Access:** "
                markdown += ", ".join(f"`{service}`" for service in data.get('management_access', []))
                markdown += "\n\n"
                
        else:
            # Generic system section
            markdown += f"**Command Count:** {data.get('command_count', 0)}  \n\n"
            
        return markdown
        
    def _format_firewall_section(self, data: Dict[str, Any], icon: str) -> str:
        """Format firewall section data."""
        section_name = data.get('section', 'Firewall')
        markdown = f"## {icon} {section_name}\n\n"
        
        if section_name == 'Firewall Filter':
            # Rule counts by chain
            markdown += "| Chain | Rules |\n"
            markdown += "|-------|-------|\n"
            
            chains = data.get('filter_by_chain', {})
            for chain, count in chains.items():
                markdown += f"| {chain.title()} | {count} |\n"
                
            total = sum(chains.values())
            markdown += f"| **Total** | **{total}** |\n\n"
            
            # Actions breakdown
            if data.get('filter_by_action'):
                markdown += "<details>\n<summary>🎯 Actions Breakdown</summary>\n\n"
                for action, count in data.get('filter_by_action', {}).items():
                    markdown += f"- **{action.title()}**: {count}\n"
                markdown += "\n</details>\n\n"
                
        elif section_name == 'Firewall NAT':
            markdown += f"**NAT Rules:** {data.get('nat_rules', 0)}  \n\n"
            
            # NAT types
            if data.get('nat_types'):
                markdown += "| NAT Type | Rules |\n"
                markdown += "|----------|-------|\n"
                for nat_type, count in data.get('nat_types', {}).items():
                    markdown += f"| {nat_type.upper()} | {count} |\n"
                markdown += "\n"
                
        elif section_name == 'Firewall Mangle':
            markdown += f"**Mangle Rules:** {data.get('mangle_rules', 0)}  \n\n"
            
        elif section_name == 'Firewall Address Lists':
            markdown += f"**Address List Entries:** {data.get('address_lists', 0)}  \n\n"
            
            # List names
            if data.get('address_list_names'):
                markdown += "<details>\n<summary>📝 Address Lists</summary>\n\n"
                for list_name in data.get('address_list_names', []):
                    markdown += f"- `{list_name}`\n"
                markdown += "\n</details>\n\n"
                
        else:
            # Generic firewall section
            rule_count = (data.get('filter_rules', 0) + 
                         data.get('nat_rules', 0) + 
                         data.get('mangle_rules', 0) + 
                         data.get('raw_rules', 0))
            markdown += f"**Total Rules:** {rule_count}  \n\n"
            
        return markdown
        
    def _format_generic_section(self, data: Dict[str, Any], icon: str) -> str:
        """Format unknown/generic section data."""
        section_name = data.get('section', 'Unknown')
        markdown = f"## {icon} {section_name}\n\n"
        
        markdown += f"**Command Count:** {data.get('command_count', 0)}  \n\n"
        
        # Show other available data
        for key, value in data.items():
            if key not in ['section', 'command_count'] and isinstance(value, (int, str)):
                if isinstance(value, int) and value > 0:
                    markdown += f"**{key.replace('_', ' ').title()}:** {value}  \n"
                elif isinstance(value, str) and value:
                    markdown += f"**{key.replace('_', ' ').title()}:** `{value}`  \n"
                    
        markdown += "\n"
        return markdown
        
    def _format_error_section(self, section_name: str, data: Dict[str, Any]) -> str:
        """Format section with parsing error."""
        markdown = f"## ⚠️ {section_name}\n\n"
        markdown += f"**Status:** ❌ Parsing Error  \n"
        markdown += f"**Error:** `{data.get('error', 'Unknown error')}`  \n\n"
        return markdown
        
    def _format_parsing_errors(self, errors: List[Dict]) -> str:
        """Format parsing errors section."""
        if not errors:
            return ""
            
        markdown = "## ⚠️ Parsing Errors\n\n"
        
        for i, error in enumerate(errors, 1):
            markdown += f"### Error {i}: {error.get('section', 'Unknown Section')}\n\n"
            markdown += f"**Section:** `{error.get('section', 'N/A')}`  \n"
            markdown += f"**Error:** `{error.get('error', 'Unknown error')}`  \n"
            markdown += f"**Lines Affected:** {error.get('line_count', 0)}  \n\n"
            
        return markdown
        
    def format_multi_device_summary(self, device_summaries: List[Dict[str, Any]]) -> str:
        """Format multiple device summaries."""
        markdown = "# 🏢 Network Configuration Summary\n\n"
        
        markdown += f"**Total Devices:** {len(device_summaries)}  \n"
        markdown += f"**Analysis Date:** {self._get_current_date()}  \n\n"
        
        # Device list table
        markdown += "## 📱 Devices Overview\n\n"
        markdown += "| Device | Sections | Errors | Status |\n"
        markdown += "|--------|----------|--------|--------|\n"
        
        for summary in device_summaries:
            device_name = summary.get('device_name', 'Unknown')
            sections = summary.get('sections_parsed', 0)
            errors = summary.get('parsing_errors', 0)
            status = "✅ OK" if errors == 0 else f"⚠️ {errors} errors"
            
            markdown += f"| {device_name} | {sections} | {errors} | {status} |\n"
            
        markdown += "\n"
        
        # Network-wide statistics
        markdown += self._generate_network_stats(device_summaries)
        
        # Individual device details
        markdown += "## 📄 Device Details\n\n"
        for summary in device_summaries:
            device_name = summary.get('device_name', 'Unknown Device')
            markdown += f"<details>\n<summary>📋 {device_name}</summary>\n\n"
            markdown += self.format_device_summary(summary)
            markdown += "\n</details>\n\n"
            
        return markdown
        
    def _generate_network_stats(self, device_summaries: List[Dict[str, Any]]) -> str:
        """Generate network-wide statistics."""
        markdown = "## 📊 Network Statistics\n\n"
        
        # Aggregate statistics
        total_interfaces = 0
        total_vlans = 0
        total_firewall_rules = 0
        total_users = 0
        device_types = {}
        
        for summary in device_summaries:
            sections = summary.get('section_summaries', {})
            
            for section_data in sections.values():
                section_name = section_data.get('section', '')
                
                if 'Interface' in section_name:
                    total_interfaces += section_data.get('total_interfaces', 0)
                    total_vlans += section_data.get('vlans', 0)
                elif 'Firewall' in section_name:
                    total_firewall_rules += section_data.get('filter_rules', 0)
                    total_firewall_rules += section_data.get('nat_rules', 0)
                    total_firewall_rules += section_data.get('mangle_rules', 0)
                elif 'User' in section_name:
                    total_users += section_data.get('user_count', 0)
                    
        markdown += "| Metric | Count |\n"
        markdown += "|--------|-------|\n"
        markdown += f"| Total Devices | {len(device_summaries)} |\n"
        markdown += f"| Total Interfaces | {total_interfaces} |\n"
        markdown += f"| Total VLANs | {total_vlans} |\n"
        markdown += f"| Total Firewall Rules | {total_firewall_rules} |\n"
        markdown += f"| Total Users | {total_users} |\n\n"
        
        return markdown
        
    def _get_current_date(self) -> str:
        """Get current date for reports."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
    def format_comparison_summary(self, before_summary: Dict[str, Any], 
                                after_summary: Dict[str, Any]) -> str:
        """Format configuration comparison summary."""
        markdown = "# 🔄 Configuration Changes Summary\n\n"
        
        device_name = after_summary.get('device_name', 'Unknown Device')
        markdown += f"**Device:** `{device_name}`  \n"
        markdown += f"**Analysis Date:** {self._get_current_date()}  \n\n"
        
        # Compare sections
        before_sections = set(before_summary.get('section_summaries', {}).keys())
        after_sections = set(after_summary.get('section_summaries', {}).keys())
        
        added_sections = after_sections - before_sections
        removed_sections = before_sections - after_sections
        common_sections = before_sections & after_sections
        
        # Changes overview
        markdown += "## 📈 Changes Overview\n\n"
        markdown += f"**Added Sections:** {len(added_sections)}  \n"
        markdown += f"**Removed Sections:** {len(removed_sections)}  \n"
        markdown += f"**Modified Sections:** {len(common_sections)}  \n\n"
        
        # Detail changes
        if added_sections:
            markdown += "### ➕ Added Sections\n\n"
            for section in sorted(added_sections):
                markdown += f"- {section}\n"
            markdown += "\n"
            
        if removed_sections:
            markdown += "### ➖ Removed Sections\n\n"
            for section in sorted(removed_sections):
                markdown += f"- {section}\n"
            markdown += "\n"
            
        # Compare common sections for changes
        if common_sections:
            markdown += "### 🔄 Section Changes\n\n"
            for section in sorted(common_sections):
                before_data = before_summary['section_summaries'][section]
                after_data = after_summary['section_summaries'][section]
                
                changes = self._compare_section_data(before_data, after_data)
                if changes:
                    markdown += f"#### {section}\n\n"
                    for change in changes:
                        markdown += f"- {change}\n"
                    markdown += "\n"
                    
        return markdown
        
    def _compare_section_data(self, before: Dict[str, Any], after: Dict[str, Any]) -> List[str]:
        """Compare two section data dictionaries."""
        changes = []
        
        # Compare numeric values
        numeric_keys = ['command_count', 'total_interfaces', 'bridges', 'vlans', 
                       'address_count', 'filter_rules', 'nat_rules', 'user_count']
        
        for key in numeric_keys:
            before_val = before.get(key, 0)
            after_val = after.get(key, 0)
            
            if before_val != after_val:
                diff = after_val - before_val
                change_type = "increased" if diff > 0 else "decreased"
                changes.append(f"{key.replace('_', ' ').title()} {change_type} by {abs(diff)} "
                             f"({before_val} → {after_val})")
                             
        return changes