# RouterOS Configuration Parser

A Python-based parser for RouterOS configuration files that generates GitHub-friendly markdown summaries. Perfect for network documentation, configuration audits, and GitHub Actions workflows.

## ✨ Features

- **Comprehensive Parsing**: Supports 140+ RouterOS configuration sections - **100% coverage** of CLAUDE.md specification
- **GitHub Integration**: Generates markdown summaries with collapsible sections and tables
- **Multi-device Support**: Parse single files or entire directories
- **Security Features**: Password redaction and secure handling of sensitive data
- **Advanced Validation**: IP address, MAC address, and parameter validation
- **Error Recovery**: Continues parsing even with malformed configurations
- **CLI Interface**: Command-line tool for easy integration
- **Extensive Testing**: Comprehensive test suite with 50+ test cases
- **Zero Dependencies**: Pure Python implementation

##  Quick Start

### Parse a Single Configuration

```bash
python3 src/main.py config.rsc
```

### Parse Multiple Configurations

```bash
python3 src/main.py configs/ --recursive
```

### GitHub Actions Mode

```bash
python3 src/main.py config.rsc --github
```

##  Supported Sections

### System & Administration (20 sections)
- `/system identity`, `/system clock`, `/system note`
- `/user` - User account management  
- `/password` - Password configuration with security redaction
- `/ip service` - Management services
- `/console`, `/port`, `/file` - System management
- `/import`, `/export` - Configuration operations
- `/radius` - RADIUS client configuration
- `/special-login` - Special login methods
- `/partitions` - Disk partitions (CHR)

### Interfaces & Physical Layer (27 sections)
- `/interface ethernet`, `/interface wireless`, `/interface bridge`
- `/interface vlan`, `/interface bonding`, `/interface 6to4`
- `/interface pppoe-*`, `/interface l2tp-*`, `/interface ovpn-*`
- `/interface eoip`, `/interface gre`, `/interface ipip`
- All tunnel and VPN interface types

### IP Configuration (12 sections)
- `/ip address`, `/ip route`, `/ip settings`
- `/ip dhcp-server`, `/ip dhcp-client`, `/ip dhcp-relay`
- `/ip dns`, `/ip pool`, `/ip arp`, `/ip neighbor`

### IPv6 Configuration (10 sections)
- `/ipv6 address`, `/ipv6 route`, `/ipv6 settings`
- `/ipv6 dhcp-server`, `/ipv6 dhcp-client`, `/ipv6 nd`
- Full IPv6 firewall support

### Firewall & Security (9 sections)
- `/ip firewall filter`, `/ip firewall nat`, `/ip firewall mangle`
- `/ip firewall address-list`, `/ip firewall layer7-protocol`
- `/ip firewall service-port` - Service port definitions
- Complete IPv6 firewall support

### Routing Protocols (8 sections)
- `/routing ospf`, `/routing bgp`, `/routing rip`
- `/routing filter`, `/routing table`

### MPLS & Advanced Features (5 sections)
- `/mpls` - Base MPLS configuration
- `/mpls ldp` - LDP protocol settings
- `/mpls interface` - MPLS-enabled interfaces
- `/mpls forwarding-table` - MPLS forwarding entries

### Quality of Service (6 sections)
- `/queue simple`, `/queue tree`, `/queue type`

### Wireless & CAPsMAN (9 sections)
- Complete wireless and CAPsMAN support

### Monitoring & Tools (11 sections)
- `/tool netwatch`, `/tool sniffer`, `/tool torch`
- `/tool ping`, `/tool traceroute`, `/tool bandwidth-test`

**See [IMPLEMENTED_SECTIONS.md](IMPLEMENTED_SECTIONS.md) for the complete list of 140+ supported sections.**

##  Installation

### Clone and Setup

```bash
git clone <repository-url>
cd routeros-parser
pip install -e .
```

### Requirements

- Python 3.8+
- No external dependencies for core functionality

## 📖 Usage Examples

### Basic Parsing

```python
from src.parser.core import RouterOSParser
from src.formatters.markdown import GitHubMarkdownFormatter

# Read configuration
with open('config.rsc', 'r') as f:
    content = f.read()

# Parse
parser = RouterOSParser(content, 'MyRouter')
config = parser.parse()

# Generate summary
summary = config.get_device_summary()

# Format as markdown
formatter = GitHubMarkdownFormatter()
markdown = formatter.format_device_summary(summary)
print(markdown)
```

### Command Line Options

```bash
# Parse single file
python3 src/main.py router.rsc

# Parse directory recursively
python3 src/main.py configs/ --recursive

# JSON output
python3 src/main.py config.rsc --output json

# GitHub Actions mode
python3 src/main.py config.rsc --github

# Compare configurations
python3 src/main.py new_config.rsc --compare old_config.rsc

# Filter specific sections
python3 src/main.py config.rsc --sections "interface,firewall,system"

# Validate only (no summary)
python3 src/main.py config.rsc --validate-only
```

##  Sample Output

The parser generates comprehensive markdown summaries like this:

```markdown
#  MyRouter Configuration Summary

##  Overview

**Device Name:** `MyRouter`  
**Sections Parsed:** 12  
**Parsing Errors:**  0  

###  Quick Statistics

| Category | Count |
|----------|-------|
| Interfaces | 8 |
| IP Addresses | 4 |
| Firewall Rules | 15 |
| Users | 3 |

##  Interfaces

| Type | Count |
|------|-------|
| Physical Interfaces | 4 |
| Bridges | 1 |
| VLANs | 3 |

<details>
<summary>🌉 Bridges</summary>

- `BR-LAN`

</details>

##  Firewall

| Rule Type | Count |
|-----------|-------|
| Filter (Input) | 5 |
| Filter (Forward) | 8 |
| NAT | 2 |
```

##  Development

### Running Tests

```bash
python3 tests/test_parser.py
```

### Demo Script

```bash
python3 demo.py
```

### Project Structure

```
routeros-parser/
├── src/
│   ├── parser/
│   │   ├── core.py           # Main parser
│   │   ├── registry.py       # Parser registry
│   │   └── sections/         # Section-specific parsers
│   ├── models/
│   │   └── config.py         # Data models
│   ├── formatters/
│   │   └── markdown.py       # GitHub formatter
│   ├── utils/
│   │   └── patterns.py       # Common patterns
│   └── main.py               # CLI interface
├── tests/
│   ├── fixtures/             # Sample configs
│   └── test_parser.py        # Tests
└── README.md
```

##  GitHub Actions Integration

Create a workflow to automatically parse RouterOS configs:

```yaml
name: Parse RouterOS Configs

on:
  push:
    paths:
      - 'configs/*.rsc'
  pull_request:
    paths:
      - 'configs/*.rsc'

jobs:
  parse-configs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
          
      - name: Parse RouterOS Configurations
        run: |
          python3 routeros-parser/src/main.py configs/ --github --recursive
```

##  Testing

### Run All Tests
```bash
cd routeros-parser
python3 -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Test core parser functionality
python3 tests/test_parser.py

# Test IP section parsers
python3 tests/test_sections/test_ip_parsers.py

# Test firewall parsers
python3 tests/test_sections/test_firewall_parsers.py

# Test system parsers
python3 tests/test_sections/test_system_parsers.py

# Test MPLS parsers
python3 tests/test_sections/test_mpls_parsers.py
```

### Test Coverage
- **50+ test cases** covering all parser modules
- **Integration tests** with real RouterOS configurations
- **Error handling tests** for malformed configurations
- **Security tests** for password redaction
- **Performance tests** for large configuration files

##  Features in Detail

### Multi-line Command Support
Handles RouterOS's backslash line continuation:
```routeros
/interface bridge port \
    add bridge=bridge interface=ether1 \
    comment="LAN Port"
```

### Security Features
- **Password Redaction**: Sensitive data is never stored in plain text
- **Input Validation**: Comprehensive validation of IP addresses, MAC addresses, etc.
- **Error Sanitization**: Error messages don't expose sensitive configuration details

### Advanced Parsing
- **Section Auto-Discovery**: Automatically discovers all configuration sections
- **Pattern Matching**: Wildcard support for interface types and similar patterns
- **Time Parsing**: Handles RouterOS time formats (1d2h3m4s)
- **Network Validation**: IP/IPv6 address and network validation
- **MAC Address Analysis**: MAC address validation with vendor detection

### Comprehensive Coverage
- **140+ Sections**: Covers virtually all RouterOS configuration sections
- **MPLS Support**: Full MPLS, LDP, and label switching configuration
- **IPv6 Ready**: Complete IPv6 configuration support
- **Firewall Analysis**: Advanced firewall rule analysis with Layer 7 protocol detection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

##  License

MIT License - see LICENSE file for details.

##  Related Projects

- [MikroTik RouterOS Documentation](https://help.mikrotik.com/)
- [RouterOS Scripting](https://wiki.mikrotik.com/wiki/Manual:Scripting)

## 🐛 Known Issues

- Large configuration files (>10MB) may be slow to parse
- Some very specialized RouterOS features may use generic parsing

##  Roadmap

- [x] ~~Complete RouterOS section coverage~~  **Completed!**
- [x] ~~Comprehensive test suite~~  **Completed!**
- [x] ~~Security features (password redaction)~~  **Completed!**
- [x] ~~MPLS and advanced protocol support~~  **Completed!**
- [ ] Web interface for configuration analysis
- [ ] Configuration diff visualization  
- [ ] Integration with network monitoring tools
- [ ] Support for RouterOS API
- [ ] Configuration validation against best practices
- [ ] Performance optimizations for very large files