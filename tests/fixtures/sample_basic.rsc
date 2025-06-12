# Sample RouterOS Configuration - Basic Setup
# Generated for testing RouterOS parser

/system identity
set name=TestRouter

/system clock
set time-zone-name=America/New_York

/user
add name=admin password=admin123 group=full
add name=guest password=guest123 group=read

/interface ethernet
set [ find default-name=ether1 ] name=WAN
set [ find default-name=ether2 ] name=LAN
set [ find default-name=ether3 ] disabled=yes
set [ find default-name=ether4 ] disabled=yes

/interface bridge
add name=BR-LAN protocol-mode=rstp

/interface bridge port
add bridge=BR-LAN interface=LAN
add bridge=BR-LAN interface=ether3
add bridge=BR-LAN interface=ether4

/interface vlan
add interface=BR-LAN name=VLAN100 vlan-id=100
add interface=BR-LAN name=VLAN200 vlan-id=200

/ip address
add address=192.168.1.1/24 interface=VLAN100 network=192.168.1.0
add address=192.168.2.1/24 interface=VLAN200 network=192.168.2.0
add address=10.0.0.2/30 interface=WAN network=10.0.0.0

/ip route
add distance=1 gateway=10.0.0.1 dst-address=0.0.0.0/0

/ip dhcp-server
add interface=VLAN100 name=dhcp100
add interface=VLAN200 name=dhcp200

/ip dhcp-server network
add address=192.168.1.0/24 gateway=192.168.1.1 dns-server=1.1.1.1,8.8.8.8
add address=192.168.2.0/24 gateway=192.168.2.1 dns-server=1.1.1.1,8.8.8.8

/ip dns
set servers=1.1.1.1,8.8.8.8 allow-remote-requests=yes

/ip firewall filter
add chain=input connection-state=established,related action=accept
add chain=input connection-state=invalid action=drop
add chain=input protocol=icmp action=accept
add chain=input src-address=192.168.0.0/16 action=accept
add chain=input action=drop
add chain=forward connection-state=established,related action=accept
add chain=forward connection-state=invalid action=drop
add chain=forward action=accept

/ip firewall nat
add chain=srcnat out-interface=WAN action=masquerade

/ip service
set telnet disabled=yes
set ftp disabled=yes
set www disabled=no
set ssh disabled=no
set www-ssl disabled=no
set api disabled=yes
set winbox disabled=no
set api-ssl disabled=yes