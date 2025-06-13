"""Professional RouterOS markdown formatter for GitHub display."""
from typing import Dict, List, Any, Optional


class GitHubMarkdownFormatter:
    """Format parsed RouterOS config data in professional numbered format."""
    
    def __init__(self):
        pass
        
    def format_device_summary(self, summary: Dict[str, Any], config_sections: Dict = None) -> str:
        """
        Format complete device summary as professional RouterOS analysis.
        
        Args:
            summary: Device summary from RouterOSConfig.get_device_summary()
            config_sections: Optional raw section objects for detailed data access
            
        Returns:
            Formatted markdown string matching target professional format
        """
        device_name = summary.get('device_name', 'Unknown Device')
        sections = summary.get('section_summaries', {})
        file_path = summary.get('file_path', f'{device_name}.rsc')
        
        # Extract consolidated data
        consolidated_data = self._extract_detailed_data(sections, config_sections)
        
        # Build professional format
        markdown = "---\n"
        markdown += f"### RouterOS Configuration Analysis for `{device_name}`\n\n"
        
        # Header with metadata
        markdown += f"**Generated On:** {self._get_current_timestamp()}\n"
        markdown += f"**Source Config File:** `{file_path.split('/')[-1] if '/' in file_path else file_path}`\n"
        
        # Extract system info if available
        system_info = self._extract_system_info(sections)
        if system_info.get('version'):
            markdown += f"**RouterOS Version:** {system_info['version']}\n"
        if system_info.get('model'):
            markdown += f"**Model:** {system_info['model']}\n"
        if system_info.get('serial'):
            markdown += f"**Serial Number:** {system_info['serial']}\n"
        
        markdown += "\n---\n"
        
        # Section 1: General Information
        markdown += self._format_general_info(device_name, consolidated_data)
        
        # Section 2: Network Interfaces
        markdown += self._format_network_interfaces(consolidated_data)
        
        # Section 3: IP Addresses & Pools
        markdown += self._format_ip_configuration(consolidated_data)
        
        # Section 4: Firewall Configuration
        markdown += self._format_firewall_detailed(consolidated_data)
        
        # Section 5: IP Services
        markdown += self._format_ip_services(consolidated_data)
        
        # Section 6: User Management
        markdown += self._format_user_management(consolidated_data)
        
        # Section 7: Additional Configuration
        markdown += self._format_additional_config(consolidated_data)
        
        # Section 8: Security Analysis
        markdown += self._format_security_analysis(consolidated_data)
        
        return markdown
    
    def _extract_detailed_data(self, sections: Dict[str, Any], config_sections: Dict = None) -> Dict[str, Any]:
        """Extract detailed configuration data for professional formatting."""
        data = {
            'interfaces': {'bridges': [], 'physical': [], 'vlans': [], 'bridge_ports': [], 'interface_details': {}},
            'ip_config': {'addresses': [], 'routes': [], 'dhcp': [], 'dns': [], 'pools': [], 'address_details': [], 'dhcp_leases': []},
            'firewall': {'filter_rules': [], 'nat_rules': [], 'address_lists': []},
            'services': [],
            'users': [],
            'user_details': [],
            'system': {'identity': None, 'timezone': None, 'logging': []},
            'additional': [],
            'additional_details': {}
        }
        
        for section_name, section_data in sections.items():
            section_type = section_data.get('section', '')
            
            # Extract IP services specifically (check this BEFORE generic System check)
            if '/ip service' in section_name:
                data['services'].append(section_data)
            
            # Extract interface data
            elif 'Interface' in section_type:
                data['interfaces']['bridges'].extend(section_data.get('bridge_list', []))
                # Store detailed interface information
                for interface in section_data.get('interfaces', []):
                    name = interface.get('name', 'unnamed')
                    if name not in data['interfaces']['physical']:
                        data['interfaces']['physical'].append(name)
                    
                    # Store interface details for later formatting
                    details = []
                    if interface.get('type'):
                        details.append(f"Type: {interface['type']}")
                    if interface.get('mtu'):
                        details.append(f"MTU: {interface['mtu']}")
                    if interface.get('mac_address'):
                        details.append(f"MAC: {interface['mac_address']}")
                    if interface.get('disabled'):
                        details.append("Status: Disabled")
                    elif interface.get('running'):
                        details.append("Status: Running")
                    if interface.get('comment'):
                        details.append(f"Comment: {interface['comment']}")
                    
                    # Merge with existing details if interface already exists
                    if name in data['interfaces']['interface_details']:
                        data['interfaces']['interface_details'][name].extend(details)
                    else:
                        data['interfaces']['interface_details'][name] = details
                
                data['interfaces']['vlans'].extend(section_data.get('vlan_list', []))
                data['interfaces']['bridge_ports'].extend(section_data.get('bridge_ports', []))
                # Add physical interfaces from bridge ports
                for port in section_data.get('bridge_ports', []):
                    interface = port.get('interface', '')
                    if interface and interface not in data['interfaces']['physical']:
                        data['interfaces']['physical'].append(interface)
                
                # Special handling for ZeroTier interface sections that should appear in additional config
                if '/zerotier interface' in section_name:
                    data['additional'].append({'name': section_name, 'data': section_data})
                    
                    # Extract ZeroTier interface details for additional config display
                    if config_sections and section_name in config_sections:
                        section_obj = config_sections[section_name]
                        section_details = []
                        
                        for cmd in section_obj.commands:
                            if cmd.get('action') == 'add':
                                # Handle network field for /zerotier interface
                                network_id = cmd.get('network_id') or cmd.get('network')
                                if network_id:
                                    details = []
                                    details.append(f"Network: {network_id}")
                                    if cmd.get('name'):
                                        details.append(f"Interface: {cmd.get('name')}")
                                    if cmd.get('allow-managed') == 'yes':
                                        details.append("Managed routes allowed")
                                    if cmd.get('instance'):
                                        details.append(f"Instance: {cmd.get('instance')}")
                                    if details:
                                        section_details.append(" | ".join(details))
                        
                        # Store detailed information
                        if section_details:
                            data['additional_details'][section_name] = section_details
            
            # Extract IP configuration
            elif 'IP Configuration' in section_type:
                data['ip_config']['addresses'].extend(section_data.get('ip_addresses', []))
                data['ip_config']['dns'].extend(section_data.get('dns_servers', []))
                
                # Extract detailed IP address information from raw commands if available
                if config_sections and section_name in config_sections and '/ip address' in section_name:
                    section_obj = config_sections[section_name]
                    for cmd in section_obj.commands:
                        if cmd.get('action') == 'add' and cmd.get('address'):
                            address_detail = {
                                'address': cmd.get('address'),
                                'interface': cmd.get('interface', 'Unknown'),
                                'comment': cmd.get('comment', ''),
                                'network': cmd.get('network', ''),
                                'is_private': cmd.get('is_private', False)
                            }
                            data['ip_config']['address_details'].append(address_detail)
                
                # Extract DHCP lease information from raw commands if available
                if config_sections and section_name in config_sections and '/ip dhcp-server lease' in section_name:
                    section_obj = config_sections[section_name]
                    for cmd in section_obj.commands:
                        if cmd.get('action') == 'add' and cmd.get('address'):
                            # Extract MAC address - it might be parsed as a key due to parsing quirk
                            mac_address = cmd.get('mac-address', '')
                            if not mac_address:
                                # Check if MAC address was parsed as a key (happens with some MAC formats)
                                for key in cmd.keys():
                                    if ':' in key and len(key) == 17:  # MAC address format
                                        mac_address = key
                                        break
                            
                            lease_detail = {
                                'address': cmd.get('address'),
                                'mac_address': mac_address or 'Unknown',
                                'server': cmd.get('server', 'Unknown'),
                                'client_id': cmd.get('client-id', '')
                            }
                            data['ip_config']['dhcp_leases'].append(lease_detail)
                
                if '/ip dhcp-server' in section_name:
                    data['ip_config']['dhcp'].append(section_data)
                elif '/ip pool' in section_name:
                    data['ip_config']['pools'].append(section_data)
                elif '/ip route' in section_name:
                    data['ip_config']['routes'].append(section_data)
            
            # Extract firewall data
            elif 'Firewall' in section_type:
                if section_data.get('filter_rules', 0) > 0:
                    data['firewall']['filter_rules'].append(section_data)
                if section_data.get('nat_rules', 0) > 0:
                    data['firewall']['nat_rules'].append(section_data)
                if section_data.get('address_lists', 0) > 0:
                    data['firewall']['address_lists'].append(section_data)
            
            # Extract system data
            elif 'System' in section_type:
                if section_data.get('device_name') != 'Unknown':
                    data['system']['identity'] = section_data.get('device_name')
                if section_data.get('timezone'):
                    data['system']['timezone'] = section_data.get('timezone')
                data['users'].extend(section_data.get('user_list', []))
                
                # Extract detailed user information from raw commands if available
                if config_sections and section_name in config_sections and '/user' in section_name:
                    section_obj = config_sections[section_name]
                    for cmd in section_obj.commands:
                        if cmd.get('action') == 'add' and cmd.get('name') and 'group' in cmd:
                            user_detail = {
                                'name': cmd.get('name'),
                                'group': cmd.get('group', 'Unknown'),
                                'privilege_level': cmd.get('privilege_level', 'Standard'),
                                'has_password': cmd.get('has_password', False),
                                'password_length': cmd.get('password_length', 0)
                            }
                            data['user_details'].append(user_detail)
            
            # Collect other sections for additional config
            else:
                if section_name not in ['/system identity', '/system clock', '/user']:
                    data['additional'].append({'name': section_name, 'data': section_data})
                    
                    # Extract detailed information for specific additional sections
                    if config_sections and section_name in config_sections:
                        section_obj = config_sections[section_name]
                        section_details = []
                        
                        if '/snmp' in section_name:
                            for cmd in section_obj.commands:
                                if cmd.get('action') == 'set':
                                    details = []
                                    if cmd.get('enabled'):
                                        details.append("Enabled")
                                    if cmd.get('trap_version'):
                                        details.append(f"SNMP v{cmd.get('trap_version')} traps")
                                    if cmd.get('contact'):
                                        details.append(f"Contact: {cmd.get('contact')}")
                                    if cmd.get('location'):
                                        details.append(f"Location: {cmd.get('location')}")
                                    if details:
                                        section_details.extend(details)
                        
                        elif '/radius' in section_name:
                            for cmd in section_obj.commands:
                                if cmd.get('action') == 'add':
                                    details = []
                                    if cmd.get('address'):
                                        details.append(f"Server: {cmd.get('address')}")
                                    if cmd.get('services'):
                                        services = ", ".join(cmd.get('services', []))
                                        details.append(f"Services: {services}")
                                    if cmd.get('server_is_private'):
                                        details.append("Private network")
                                    if details:
                                        section_details.append(" | ".join(details))
                        
                        elif '/tool' in section_name:
                            netwatch_count = 0
                            for cmd in section_obj.commands:
                                if cmd.get('action') == 'add' and cmd.get('host'):
                                    netwatch_count += 1
                                elif cmd.get('netwatch'):
                                    # This indicates netwatch configuration
                                    pass
                            
                            if netwatch_count > 0:
                                section_details.append(f"Netwatch monitoring {netwatch_count} hosts")
                        
                        elif '/zerotier' in section_name:
                            # Handle both /zerotier and /zerotier interface sections
                            for cmd in section_obj.commands:
                                if cmd.get('action') == 'set' and cmd.get('interface_name'):
                                    details = []
                                    details.append(f"Instance: {cmd.get('interface_name')}")
                                    if cmd.get('port_number'):
                                        details.append(f"Port: {cmd.get('port_number')}")
                                    if cmd.get('comment'):
                                        details.append(f"Comment: {cmd.get('comment')}")
                                    if details:
                                        section_details.append(" | ".join(details))
                                elif cmd.get('action') == 'add':
                                    # Handle both network_id and network fields for /zerotier interface
                                    network_id = cmd.get('network_id') or cmd.get('network')
                                    if network_id:
                                        details = []
                                        details.append(f"Network: {network_id}")
                                        if cmd.get('interface_name') or cmd.get('name'):
                                            interface_name = cmd.get('interface_name') or cmd.get('name')
                                            details.append(f"Interface: {interface_name}")
                                        if cmd.get('allow_managed') == True or cmd.get('allow-managed') == 'yes':
                                            details.append("Managed routes allowed")
                                        if cmd.get('instance'):
                                            details.append(f"Instance: {cmd.get('instance')}")
                                        if details:
                                            section_details.append(" | ".join(details))
                        
                        # Store detailed information
                        if section_details:
                            data['additional_details'][section_name] = section_details
        
        return data
    
    def _extract_system_info(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """Extract system information like version, model, serial."""
        info = {}
        
        # Look for system resource or similar sections
        for section_name, section_data in sections.items():
            if 'system' in section_name.lower():
                # RouterOS version extraction would need specific parsing
                # For now, return empty - would need access to /system resource
                pass
        
        return info
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for report generation."""
        from datetime import datetime
        import time
        
        # Get current time in EDT
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S EDT")
    
    def _format_general_info(self, device_name: str, data: Dict[str, Any]) -> str:
        """Format Section 1: General Information."""
        markdown = "#### **1. General Information**\n\n"
        markdown += f"* **Identity:** `{device_name}`\n"
        
        if data['system']['timezone']:
            markdown += f"* **Time Zone:** {data['system']['timezone']}\n"
        
        # Add software ID if available (would need specific parsing)
        markdown += "* **Software ID:** [If available]\n"
        
        markdown += "\n---\n"
        return markdown
    
    def _format_network_interfaces(self, data: Dict[str, Any]) -> str:
        """Format Section 2: Network Interfaces."""
        markdown = "#### **2. Network Interfaces**\n\n"
        
        # Bridge Interfaces
        if data['interfaces']['bridges']:
            markdown += "* **Bridge Interfaces:**\n"
            for bridge in data['interfaces']['bridges']:
                markdown += f"    * `{bridge}`\n"
        
        # Physical Interfaces
        if data['interfaces']['physical']:
            markdown += "* **Physical Interfaces:**\n"
            for interface in sorted(data['interfaces']['physical']):
                details = data['interfaces']['interface_details'].get(interface, [])
                if details:
                    details_str = " | ".join(details)
                    markdown += f"    * `{interface}`: {details_str}\n"
                else:
                    markdown += f"    * `{interface}`: Active interface\n"
        
        # VLAN Interfaces
        if data['interfaces']['vlans']:
            markdown += "* **VLAN Interfaces:**\n"
            for vlan in data['interfaces']['vlans']:
                markdown += f"    * {vlan}\n"
        
        markdown += "\n---\n"
        return markdown
    
    def _format_ip_configuration(self, data: Dict[str, Any]) -> str:
        """Format Section 3: IP Addresses & Pools."""
        markdown = "#### **3. IP Addresses & Pools**\n\n"
        
        # IP Addresses by interface
        if data['ip_config']['address_details']:
            markdown += "* **Interface IP Addresses:**\n"
            for addr_detail in data['ip_config']['address_details']:
                address = addr_detail['address']
                interface = addr_detail['interface']
                comment = addr_detail['comment']
                private_status = " (Private)" if addr_detail['is_private'] else " (Public)"
                comment_str = f" - {comment}" if comment else ""
                markdown += f"    * `{address}` on `{interface}`{private_status}{comment_str}\n"
        elif data['ip_config']['addresses']:
            markdown += "* **Interface IP Addresses:**\n"
            for addr in data['ip_config']['addresses']:
                markdown += f"    * `{addr}`\n"
        
        # DHCP Servers
        if data['ip_config']['dhcp']:
            markdown += "* **DHCP Servers:**\n"
            for dhcp in data['ip_config']['dhcp']:
                server_count = dhcp.get('dhcp_server_count', 0)
                if server_count > 0:
                    markdown += f"    * **DHCP Server**: {server_count} configured\n"
        
        # DNS Servers
        if data['ip_config']['dns']:
            markdown += "* **DNS Servers:**\n"
            for dns in data['ip_config']['dns']:
                markdown += f"    * `{dns}`\n"
        
        # DHCP Leases
        if data['ip_config']['dhcp_leases']:
            markdown += "* **DHCP Static Leases:**\n"
            for lease in data['ip_config']['dhcp_leases']:
                address = lease['address']
                mac = lease['mac_address']
                server = lease['server']
                markdown += f"    * `{address}` → MAC: {mac} (Server: {server})\n"
        
        markdown += "\n---\n"
        return markdown
    
    def _format_firewall_detailed(self, data: Dict[str, Any]) -> str:
        """Format Section 4: Firewall Configuration."""
        markdown = "#### **4. Firewall Configuration**\n\n"
        
        # Address Lists
        if data['firewall']['address_lists']:
            markdown += "##### **4.1. Address Lists**\n"
            for addr_list in data['firewall']['address_lists']:
                list_count = addr_list.get('address_lists', 0)
                if list_count > 0:
                    markdown += f"* Address Lists: {list_count} configured\n"
                    if addr_list.get('address_list_names'):
                        for list_name in addr_list['address_list_names']:
                            markdown += f"    * `{list_name}`\n"
            markdown += "\n"
        
        # Filter Rules
        if data['firewall']['filter_rules']:
            markdown += "##### **4.2. Filter Rules**\n"
            for filter_section in data['firewall']['filter_rules']:
                filter_count = filter_section.get('filter_rules', 0)
                if filter_count > 0:
                    markdown += f"* **Filter Rules**: {filter_count} total\n"
                    
                    # Rules by chain
                    if filter_section.get('filter_by_chain'):
                        for chain, count in filter_section['filter_by_chain'].items():
                            markdown += f"    * **Chain `{chain}`**: {count} rules\n"
                    
                    # Rules by action
                    if filter_section.get('filter_by_action'):
                        markdown += "    * **Actions:**\n"
                        for action, count in filter_section['filter_by_action'].items():
                            markdown += f"        * {action.title()}: {count}\n"
        
        # NAT Rules
        if data['firewall']['nat_rules']:
            markdown += "\n##### **4.3. NAT Rules**\n"
            for nat_section in data['firewall']['nat_rules']:
                nat_count = nat_section.get('nat_rules', 0)
                if nat_count > 0:
                    markdown += f"* **NAT Rules**: {nat_count} total\n"
                    if nat_section.get('nat_types'):
                        for nat_type, count in nat_section['nat_types'].items():
                            markdown += f"    * **{nat_type.upper()}**: {count} rules\n"
        
        markdown += "\n---\n"
        return markdown
    
    def _format_ip_services(self, data: Dict[str, Any]) -> str:
        """Format Section 5: IP Services (Management Access)."""
        markdown = "#### **5. IP Services (Management Access)**\n\n"
        
        if data['services']:
            for service_section in data['services']:
                if service_section.get('enabled_services'):
                    for service in service_section['enabled_services']:
                        markdown += f"* **`{service}`**: Enabled\n"
                
                if service_section.get('management_access'):
                    markdown += "* **Management Access:**\n"
                    for access in service_section['management_access']:
                        markdown += f"    * {access}\n"
        else:
            markdown += "* **No IP services configured or detected**\n"
        
        markdown += "\n---\n"
        return markdown
    
    def _format_user_management(self, data: Dict[str, Any]) -> str:
        """Format Section 6: User Management."""
        markdown = "#### **6. User Management**\n\n"
        
        if data['user_details']:
            markdown += "##### **6.1. User Accounts**\n"
            for user_detail in data['user_details']:
                name = user_detail['name']
                group = user_detail['group']
                privilege = user_detail['privilege_level']
                has_password = "✓" if user_detail['has_password'] else "✗"
                password_len = user_detail['password_length']
                
                details = f"Group: {group} | Privilege: {privilege} | Password: {has_password}"
                if password_len > 0:
                    details += f" ({password_len} chars)"
                
                markdown += f"* **`{name}`**: {details}\n"
        elif data['users']:
            markdown += "##### **6.1. User Accounts**\n"
            for user in data['users']:
                markdown += f"* **`{user}`**: User account configured\n"
        else:
            markdown += "* **No user accounts configured**\n"
        
        markdown += "\n---\n"
        return markdown
    
    def _format_additional_config(self, data: Dict[str, Any]) -> str:
        """Format Section 7: Additional Configuration."""
        markdown = "#### **7. Additional Configuration**\n\n"
        
        if data['additional']:
            for config in data['additional']:
                section_name = config['name'].replace('/', '')
                section_data = config['data']
                command_count = section_data.get('command_count', 0)
                
                # Check if we have detailed information for this section first
                section_details = data['additional_details'].get(config['name'], [])
                
                if section_details:
                    details_str = " | ".join(section_details)
                    markdown += f"* **{section_name}**: {details_str}\n"
                elif command_count > 0:
                    markdown += f"* **{section_name}**: {command_count} configuration entries\n"
        else:
            markdown += "* **No additional configuration sections detected**\n"
        
        markdown += "\n---\n"
        return markdown
    
    def _format_security_analysis(self, data: Dict[str, Any]) -> str:
        """Format Section 8: Security Analysis."""
        markdown = "#### **8. Security Analysis**\n\n"
        
        # Management Access Analysis
        markdown += "* **Management Access**: "
        if data['services']:
            service_count = sum(len(s.get('enabled_services', [])) for s in data['services'])
            markdown += f"{service_count} management services enabled\n"
        else:
            markdown += "No management services detected\n"
        
        # Firewall Analysis
        filter_count = sum(f.get('filter_rules', 0) for f in data['firewall']['filter_rules'])
        nat_count = sum(n.get('nat_rules', 0) for n in data['firewall']['nat_rules'])
        markdown += f"* **Firewall Rules**: {filter_count} filter rules, {nat_count} NAT rules configured\n"
        
        # User Account Analysis
        user_count = len(data['users'])
        markdown += f"* **User Accounts**: {user_count} user accounts configured\n"
        
        markdown += "\n---\n"
        return markdown

    def format_multi_device_summary(self, device_summaries: List[Dict[str, Any]]) -> str:
        """Format multiple device summaries in professional format."""
        markdown = "---\n"
        markdown += "### RouterOS Fleet Configuration Analysis\n\n"
        
        markdown += f"**Generated On:** {self._get_current_timestamp()}\n"
        markdown += f"**Total Devices:** {len(device_summaries)}\n\n"
        markdown += "---\n"
        
        markdown += "#### **Fleet Overview**\n\n"
        
        # Device list
        markdown += "* **Devices Analyzed:**\n"
        for i, summary in enumerate(device_summaries, 1):
            device_name = summary.get('device_name', 'Unknown')
            sections = summary.get('sections_parsed', 0)
            errors = summary.get('parsing_errors', 0)
            status = "✅ OK" if errors == 0 else f"⚠️ {errors} errors"
            markdown += f"    * **{i}.** `{device_name}` - {sections} sections - {status}\n"
        
        markdown += "\n---\n"
        
        # Fleet statistics
        total_sections = sum(s.get('sections_parsed', 0) for s in device_summaries)
        total_errors = sum(s.get('parsing_errors', 0) for s in device_summaries)
        success_rate = ((len(device_summaries) - total_errors) / len(device_summaries) * 100) if device_summaries else 0
        
        markdown += "#### **Fleet Statistics**\n\n"
        markdown += f"* **Total Configuration Sections:** {total_sections}\n"
        markdown += f"* **Parsing Success Rate:** {success_rate:.1f}%\n"
        markdown += f"* **Total Parsing Errors:** {total_errors}\n\n"
        markdown += "---\n"
        
        # Individual device details with professional format
        markdown += "#### **Individual Device Configurations**\n\n"
        for i, summary in enumerate(device_summaries, 1):
            device_name = summary.get('device_name', 'Unknown Device')
            markdown += f"##### **Device {i}: {device_name}**\n\n"
            
            # Use professional format for each device
            device_markdown = self.format_device_summary(summary)
            # Remove the header from individual device output
            device_lines = device_markdown.split('\n')
            # Skip the first few lines (header) and join the rest
            if len(device_lines) > 5:
                device_content = '\n'.join(device_lines[5:])
                markdown += device_content
            
            markdown += "\n\n"
            
        return markdown
        
    def _get_current_date(self) -> str:
        """Get current date for reports."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")