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
        
        markdown = f"# {device_name} Configuration Analysis\n\n"
        
        # Overview section
        markdown += "## Overview\n\n"
        markdown += f"**Device Name:** `{device_name}`  \n"
        markdown += f"**Sections Parsed:** {len(sections)}  \n"
        
        if errors > 0:
            markdown += f"**Parsing Errors:** {errors}  \n"
        else:
            markdown += f"**Parsing Errors:** 0  \n"
            
        markdown += "\n"
        
        # Quick stats table
        markdown += self._generate_quick_stats_table(sections)
        
        # Generate consolidated section summaries
        consolidated_sections = self._consolidate_sections(sections)
        
        for section_type, section_data in consolidated_sections.items():
            if 'error' in section_data:
                markdown += self._format_error_section(section_type, section_data)
            else:
                markdown += self._format_consolidated_section(section_type, section_data)
                
        # Add parsing errors if any
        if summary.get('errors'):
            markdown += self._format_parsing_errors(summary['errors'])
            
        return markdown
        
    def _generate_quick_stats_table(self, sections: Dict[str, Any]) -> str:
        """Generate quick statistics table."""
        markdown = "### Quick Statistics\n\n"
        markdown += "| Category | Count |\n"
        markdown += "|----------|-------|\n"
        
        # Aggregate key statistics across all sections
        stats = {
            'Physical Interfaces': 0,
            'Bridge Interfaces': 0,
            'VLAN Interfaces': 0,
            'IP Addresses': 0,
            'Firewall Rules': 0,
            'Users': 0,
            'DHCP Servers': 0
        }
        
        for section_data in sections.values():
            section_name = section_data.get('section', '')
            
            # Interface aggregation
            if 'Interface' in section_name:
                stats['Physical Interfaces'] += section_data.get('physical_interfaces', 0)
                stats['Bridge Interfaces'] += section_data.get('bridges', 0)
                stats['VLAN Interfaces'] += section_data.get('vlans', 0)
            
            # IP configuration aggregation
            elif 'IP Configuration' in section_name:
                stats['IP Addresses'] += section_data.get('address_count', 0)
                stats['DHCP Servers'] += section_data.get('dhcp_server_count', 0)
            
            # Firewall aggregation
            elif 'Firewall' in section_name:
                stats['Firewall Rules'] += section_data.get('total_rules', 0)
            
            # System/User aggregation  
            elif 'System' in section_name:
                stats['Users'] += section_data.get('user_count', 0)
                
        # Only show categories with counts > 0
        for category, count in stats.items():
            if count > 0:
                markdown += f"| {category} | {count} |\n"
                
        markdown += "\n"
        return markdown
        
    def _consolidate_sections(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate related sections into logical groups."""
        consolidated = {
            'System': {'sections': [], 'device_name': 'Unknown', 'users': [], 'services': [], 'timezone': None},
            'Interfaces': {'sections': [], 'physical': [], 'bridges': [], 'vlans': [], 'tunnels': []},
            'IP_Configuration': {'sections': [], 'addresses': [], 'routes': [], 'dhcp': [], 'dns': []},
            'Firewall': {'sections': [], 'filter_rules': [], 'nat_rules': [], 'address_lists': []}
        }
        
        for section_name, section_data in sections.items():
            section_type = section_data.get('section', '')
            
            if 'System' in section_type:
                consolidated['System']['sections'].append(section_name)
                if section_data.get('device_name') != 'Unknown':
                    consolidated['System']['device_name'] = section_data.get('device_name')
                if section_data.get('user_count', 0) > 0:
                    consolidated['System']['users'].extend(section_data.get('user_list', []))
                if section_data.get('timezone'):
                    consolidated['System']['timezone'] = section_data.get('timezone')
                    
            elif 'Interface' in section_type:
                consolidated['Interfaces']['sections'].append(section_name)
                consolidated['Interfaces']['physical'].extend([f"{d.get('name', 'unnamed')}" for d in section_data.get('interfaces', [])])
                consolidated['Interfaces']['bridges'].extend(section_data.get('bridge_list', []))
                consolidated['Interfaces']['vlans'].extend(section_data.get('vlan_list', []))
                # Add physical interfaces from bridge ports
                for port in section_data.get('bridge_ports', []):
                    interface = port.get('interface', '')
                    if interface and interface not in consolidated['Interfaces']['physical']:
                        consolidated['Interfaces']['physical'].append(interface)
                
            elif 'IP Configuration' in section_type:
                consolidated['IP_Configuration']['sections'].append(section_name)
                consolidated['IP_Configuration']['addresses'].extend(section_data.get('ip_addresses', []))
                if section_data.get('dns_servers'):
                    consolidated['IP_Configuration']['dns'].extend(section_data.get('dns_servers', []))
                    
            elif 'Firewall' in section_type:
                consolidated['Firewall']['sections'].append(section_name)
                if section_data.get('filter_rules', 0) > 0:
                    consolidated['Firewall']['filter_rules'].append(section_data)
                if section_data.get('nat_rules', 0) > 0:
                    consolidated['Firewall']['nat_rules'].append(section_data)
                if section_data.get('address_lists', 0) > 0:
                    consolidated['Firewall']['address_lists'].append(section_data)
        
        return consolidated
        
    def _format_consolidated_section(self, section_type: str, section_data: Dict[str, Any]) -> str:
        """Format consolidated section data."""
        if section_type == 'System':
            return self._format_system_consolidated(section_data)
        elif section_type == 'Interfaces':
            return self._format_interfaces_consolidated(section_data)
        elif section_type == 'IP_Configuration':
            return self._format_ip_consolidated(section_data)
        elif section_type == 'Firewall':
            return self._format_firewall_consolidated(section_data)
        else:
            return f"## {section_type}\n\nNo data available.\n\n"
            
    def _format_interfaces_consolidated(self, data: Dict[str, Any]) -> str:
        """Format consolidated interface data."""
        if not data['sections']:
            return ""
            
        markdown = "## Interfaces\n\n"
        
        # Summary counts
        physical_count = len(data['physical'])
        bridge_count = len(data['bridges'])
        vlan_count = len(data['vlans'])
        total_count = physical_count + bridge_count + vlan_count
        
        markdown += "| Type | Count |\n"
        markdown += "|------|-------|\n"
        markdown += f"| Physical Interfaces | {physical_count} |\n"
        markdown += f"| Bridge Interfaces | {bridge_count} |\n"
        markdown += f"| VLAN Interfaces | {vlan_count} |\n"
        markdown += f"| **Total** | **{total_count}** |\n\n"
        
        # Physical interfaces detail
        if data['physical']:
            markdown += "<details>\n<summary>Physical Interfaces</summary>\n\n"
            for iface in data['physical']:
                markdown += f"- `{iface}`\n"
            markdown += "\n</details>\n\n"
            
        # Bridge interfaces detail
        if data['bridges']:
            markdown += "<details>\n<summary>Bridge Interfaces</summary>\n\n"
            for bridge in data['bridges']:
                markdown += f"- `{bridge}`\n"
            markdown += "\n</details>\n\n"
            
        # VLAN interfaces detail
        if data['vlans']:
            markdown += "<details>\n<summary>VLAN Interfaces</summary>\n\n"
            for vlan in data['vlans']:
                markdown += f"- {vlan}\n"
            markdown += "\n</details>\n\n"
            
        return markdown
        
    def _format_system_consolidated(self, data: Dict[str, Any]) -> str:
        """Format consolidated system data."""
        if not data['sections']:
            return ""
            
        markdown = "## System Configuration\n\n"
        
        # Device identity
        markdown += f"**Device Name:** `{data['device_name']}`\n"
        if data['timezone']:
            markdown += f"**Timezone:** `{data['timezone']}`\n"
        markdown += "\n"
        
        # User accounts
        if data['users']:
            markdown += f"**Users:** {len(data['users'])}\n\n"
            markdown += "<details>\n<summary>User Accounts</summary>\n\n"
            for user in data['users']:
                markdown += f"- `{user}`\n"
            markdown += "\n</details>\n\n"
            
        return markdown
        
    def _format_ip_consolidated(self, data: Dict[str, Any]) -> str:
        """Format consolidated IP configuration data."""
        if not data['sections']:
            return ""
            
        markdown = "## IP Configuration\n\n"
        
        # IP addresses
        if data['addresses']:
            markdown += f"**IP Addresses:** {len(data['addresses'])}\n\n"
            markdown += "<details>\n<summary>IP Addresses</summary>\n\n"
            for addr in data['addresses']:
                markdown += f"- `{addr}`\n"
            markdown += "\n</details>\n\n"
            
        # DNS servers
        if data['dns']:
            markdown += f"**DNS Servers:** {', '.join(f'`{dns}`' for dns in data['dns'])}\n\n"
            
        return markdown
        
    def _format_firewall_consolidated(self, data: Dict[str, Any]) -> str:
        """Format consolidated firewall data."""
        if not data['sections']:
            return ""
            
        markdown = "## Firewall Configuration\n\n"
        
        # Calculate totals
        total_filter = sum(s.get('filter_rules', 0) for s in data['filter_rules'])
        total_nat = sum(s.get('nat_rules', 0) for s in data['nat_rules'])
        total_address_lists = sum(s.get('address_lists', 0) for s in data['address_lists'])
        total_rules = total_filter + total_nat
        
        markdown += "| Rule Type | Count |\n"
        markdown += "|-----------|-------|\n"
        if total_filter > 0:
            markdown += f"| Filter Rules | {total_filter} |\n"
        if total_nat > 0:
            markdown += f"| NAT Rules | {total_nat} |\n"
        if total_address_lists > 0:
            markdown += f"| Address Lists | {total_address_lists} |\n"
        markdown += f"| **Total Rules** | **{total_rules}** |\n\n"
        
        # Filter rules breakdown
        if data['filter_rules']:
            for rule_section in data['filter_rules']:
                if rule_section.get('filter_by_chain'):
                    markdown += "<details>\n<summary>Filter Rules by Chain</summary>\n\n"
                    for chain, count in rule_section['filter_by_chain'].items():
                        markdown += f"- **{chain.title()}**: {count}\n"
                    markdown += "\n</details>\n\n"
                    break
                    
        return markdown

    def _format_interface_section(self, data: Dict[str, Any]) -> str:
        """Format interface section data."""
        markdown = f"## Interfaces\n\n"
        
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
        markdown = f"## {section_name}\n\n"
        
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
                markdown += "<details>\n<summary> Users</summary>\n\n"
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
                markdown += "<details>\n<summary> Actions Breakdown</summary>\n\n"
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
                markdown += "<details>\n<summary> Address Lists</summary>\n\n"
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
        markdown = f"## {section_name}\n\n"
        markdown += f"**Status:**  Parsing Error  \n"
        markdown += f"**Error:** `{data.get('error', 'Unknown error')}`  \n\n"
        return markdown
        
    def _format_parsing_errors(self, errors: List[Dict]) -> str:
        """Format parsing errors section."""
        if not errors:
            return ""
            
        markdown = "## Parsing Errors\n\n"
        
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
            status = " OK" if errors == 0 else f" {errors} errors"
            
            markdown += f"| {device_name} | {sections} | {errors} | {status} |\n"
            
        markdown += "\n"
        
        # Network-wide statistics
        markdown += self._generate_network_stats(device_summaries)
        
        # Individual device details
        markdown += "## 📄 Device Details\n\n"
        for summary in device_summaries:
            device_name = summary.get('device_name', 'Unknown Device')
            markdown += f"<details>\n<summary> {device_name}</summary>\n\n"
            markdown += self.format_device_summary(summary)
            markdown += "\n</details>\n\n"
            
        return markdown
        
    def _generate_network_stats(self, device_summaries: List[Dict[str, Any]]) -> str:
        """Generate network-wide statistics."""
        markdown = "## Network Statistics\n\n"
        
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