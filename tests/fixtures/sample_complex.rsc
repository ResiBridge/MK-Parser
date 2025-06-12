# Sample RouterOS Configuration - Complex Setup
# Generated for testing RouterOS parser with advanced features

/system identity
set name=BorderRouter-01

/system clock
set time-zone-name=UTC

/system note
set show-at-login="Production Border Router - Handle with Care"

/user
add name=admin password=complexpass123 group=full comment="Primary Administrator"
add name=backup password=backuppass456 group=full disabled=yes comment="Backup Admin Account"
add name=monitoring password=monpass789 group=read comment="Monitoring System Account"
add name=operator password=oppass321 group=write comment="Network Operator"

/interface ethernet
set [ find default-name=ether1 ] name=WAN-Primary
set [ find default-name=ether2 ] name=WAN-Backup
set [ find default-name=ether3 ] name=LAN-Core
set [ find default-name=ether4 ] name=DMZ
set [ find default-name=ether5 ] name=Management

/interface bridge
add name=BR-LAN protocol-mode=rstp stp=yes comment="Main LAN Bridge"
add name=BR-DMZ protocol-mode=none comment="DMZ Bridge"

/interface bridge port
add bridge=BR-LAN interface=LAN-Core
add bridge=BR-DMZ interface=DMZ

/interface vlan
add interface=BR-LAN name=VLAN10-Users vlan-id=10 comment="User Network"
add interface=BR-LAN name=VLAN20-Servers vlan-id=20 comment="Server Network"
add interface=BR-LAN name=VLAN30-Guest vlan-id=30 comment="Guest Network"
add interface=BR-LAN name=VLAN99-Management vlan-id=99 comment="Management Network"

/interface bonding
add slaves=WAN-Primary,WAN-Backup name=WAN-Bond mode=active-backup

/interface eoip
add name=EOIP-Branch1 remote-address=203.0.113.10 tunnel-id=1
add name=EOIP-Branch2 remote-address=203.0.113.20 tunnel-id=2

/ip address
add address=192.168.10.1/24 interface=VLAN10-Users
add address=192.168.20.1/24 interface=VLAN20-Servers  
add address=192.168.30.1/24 interface=VLAN30-Guest
add address=192.168.99.1/24 interface=VLAN99-Management
add address=172.16.0.1/24 interface=BR-DMZ
add address=10.0.1.1/30 interface=WAN-Bond
add address=10.10.1.1/30 interface=EOIP-Branch1
add address=10.10.2.1/30 interface=EOIP-Branch2

/ip route
add dst-address=0.0.0.0/0 gateway=10.0.1.2 distance=1 comment="Default Route"
add dst-address=192.168.0.0/16 gateway=10.10.1.2 distance=5 comment="Branch1 Networks"
add dst-address=172.16.0.0/12 gateway=10.10.2.2 distance=5 comment="Branch2 Networks"

/ip pool
add name=pool-users ranges=192.168.10.100-192.168.10.200
add name=pool-guest ranges=192.168.30.50-192.168.30.100

/ip dhcp-server
add interface=VLAN10-Users name=dhcp-users address-pool=pool-users lease-time=1d
add interface=VLAN30-Guest name=dhcp-guest address-pool=pool-guest lease-time=2h

/ip dhcp-server network
add address=192.168.10.0/24 gateway=192.168.10.1 dns-server=192.168.99.10,1.1.1.1
add address=192.168.30.0/24 gateway=192.168.30.1 dns-server=1.1.1.1,8.8.8.8

/ip dns
set servers=1.1.1.1,8.8.8.8,208.67.222.222 allow-remote-requests=yes cache-size=2048KiB

/ip firewall address-list
add list=internal-networks address=192.168.0.0/16
add list=internal-networks address=172.16.0.0/12
add list=internal-networks address=10.0.0.0/8
add list=blacklist address=192.0.2.100 timeout=1d comment="Suspicious IP"
add list=whitelist address=203.0.113.0/24 comment="Partner Networks"

/ip firewall filter
# Input chain rules
add chain=input connection-state=established,related action=accept comment="Allow established"
add chain=input connection-state=invalid action=drop comment="Drop invalid"
add chain=input protocol=icmp action=accept comment="Allow ICMP"
add chain=input in-interface=VLAN99-Management action=accept comment="Allow management"
add chain=input src-address-list=internal-networks protocol=tcp dst-port=22,80,443,8291 action=accept comment="Allow admin access"
add chain=input src-address-list=blacklist action=drop comment="Drop blacklisted"
add chain=input action=drop comment="Drop all other input"

# Forward chain rules  
add chain=forward connection-state=established,related action=accept comment="Allow established"
add chain=forward connection-state=invalid action=drop comment="Drop invalid"
add chain=forward src-address-list=blacklist action=drop comment="Drop blacklisted"
add chain=forward in-interface=VLAN30-Guest out-interface=!WAN-Bond action=drop comment="Isolate guest network"
add chain=forward in-interface=VLAN10-Users dst-address-list=internal-networks action=accept comment="Users to internal"
add chain=forward in-interface=VLAN20-Servers dst-address-list=internal-networks action=accept comment="Servers to internal"
add chain=forward out-interface=WAN-Bond action=accept comment="Allow internet access"
add chain=forward action=drop comment="Drop all other forward"

/ip firewall nat
add chain=srcnat out-interface=WAN-Bond src-address=192.168.10.0/24 action=masquerade comment="NAT Users"
add chain=srcnat out-interface=WAN-Bond src-address=192.168.20.0/24 action=masquerade comment="NAT Servers"
add chain=srcnat out-interface=WAN-Bond src-address=192.168.30.0/24 action=masquerade comment="NAT Guest"
add chain=dstnat protocol=tcp dst-port=80 in-interface=WAN-Bond action=dst-nat to-addresses=192.168.20.10 to-ports=80 comment="Web Server"
add chain=dstnat protocol=tcp dst-port=443 in-interface=WAN-Bond action=dst-nat to-addresses=192.168.20.10 to-ports=443 comment="HTTPS Server"
add chain=dstnat protocol=tcp dst-port=2222 in-interface=WAN-Bond action=dst-nat to-addresses=192.168.20.5 to-ports=22 comment="SSH Server"

/ip firewall mangle
add chain=prerouting src-address=192.168.10.0/24 action=mark-connection new-connection-mark=users
add chain=prerouting connection-mark=users action=mark-packet new-packet-mark=users-traffic
add chain=prerouting src-address=192.168.20.0/24 action=mark-connection new-connection-mark=servers
add chain=prerouting connection-mark=servers action=mark-packet new-packet-mark=server-traffic
add chain=prerouting src-address=192.168.30.0/24 action=mark-connection new-connection-mark=guest
add chain=prerouting connection-mark=guest action=mark-packet new-packet-mark=guest-traffic

/queue simple
add name=Users target=192.168.10.0/24 max-limit=50M/50M priority=3
add name=Servers target=192.168.20.0/24 max-limit=100M/100M priority=1  
add name=Guest target=192.168.30.0/24 max-limit=10M/10M priority=8

/ip service
set telnet disabled=yes
set ftp disabled=yes  
set www disabled=no port=8080 address=192.168.99.0/24
set ssh disabled=no port=2222 address=192.168.99.0/24,10.0.0.0/8
set www-ssl disabled=no port=8443 address=192.168.99.0/24
set api disabled=yes
set winbox disabled=no port=8291 address=192.168.99.0/24
set api-ssl disabled=yes