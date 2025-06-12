# Comprehensive RouterOS Configuration - Testing All Sections
# Generated for testing the complete RouterOS parser implementation

# System & Administration
/system identity
set name=ComprehensiveRouter

/system clock
set time-zone-name=UTC

/system note
set show-at-login="Complete RouterOS Configuration Test - All Sections"

/user
add name=admin password=admin123 group=full comment="Primary Administrator"
add name=operator password=op123 group=write comment="Network Operator"  
add name=monitor password=mon123 group=read comment="Monitoring User"

# Certificate Management
/certificate
add name=server-cert common-name=router.example.com key-size=2048 days-valid=365 key-usage=digital-signature,key-encipherment

# Interface Configuration
/interface ethernet
set [ find default-name=ether1 ] name=WAN
set [ find default-name=ether2 ] name=LAN1
set [ find default-name=ether3 ] name=LAN2

/interface bridge
add name=BR-LAN protocol-mode=rstp stp=yes comment="Main LAN Bridge"

/interface bridge port
add bridge=BR-LAN interface=LAN1
add bridge=BR-LAN interface=LAN2

/interface vlan
add interface=BR-LAN name=VLAN100-Users vlan-id=100 comment="User VLAN"
add interface=BR-LAN name=VLAN200-Servers vlan-id=200 comment="Server VLAN"

/interface bonding
add slaves=ether4,ether5 name=bond1 mode=802.3ad

# Wireless Configuration
/interface wireless security-profiles
add name=WPA2-Personal mode=dynamic-keys authentication-types=wpa2-psk wpa2-pre-shared-key=wireless123 group-ciphers=aes-ccm unicast-ciphers=aes-ccm

/interface wireless
add name=wlan1 ssid=TestNetwork mode=ap-bridge frequency=2437 channel-width=20mhz wireless-protocol=802.11 security-profile=WPA2-Personal tx-power=20

# CAPsMAN Configuration
/caps-man manager
set enabled=yes upgrade-policy=require-same-version certificate=none

/caps-man configuration
add name=2.4GHz-Config ssid=CAPsMAN-2.4G mode=ap frequency=2437 channel-width=20mhz

/caps-man datapath
add name=bridge-datapath local-forwarding=no client-to-client-forwarding=yes bridge=BR-LAN

/caps-man channel
add name=channel-2.4 frequency=2437 extension-channel=disabled

# Tunnel Interfaces
/interface eoip
add name=eoip-branch1 remote-address=203.0.113.10 tunnel-id=1 mtu=1500

/interface gre
add name=gre-tunnel1 remote-address=203.0.113.20 local-address=198.51.100.1

/interface l2tp-client
add name=l2tp-client1 connect-to=vpn.example.com user=client1 password=client123

/interface pppoe-client
add name=pppoe-wan interface=WAN user=user@isp.com password=isppass123 add-default-route=yes

# IP Configuration
/ip address
add address=192.168.100.1/24 interface=VLAN100-Users network=192.168.100.0
add address=192.168.200.1/24 interface=VLAN200-Servers network=192.168.200.0
add address=10.10.1.1/30 interface=eoip-branch1 network=10.10.1.0

/ip route
add dst-address=0.0.0.0/0 gateway=pppoe-wan distance=1
add dst-address=192.168.0.0/16 gateway=10.10.1.2 distance=5

/ip pool
add name=dhcp-pool-users ranges=192.168.100.50-192.168.100.200
add name=dhcp-pool-servers ranges=192.168.200.50-192.168.200.100

/ip dhcp-server
add interface=VLAN100-Users name=dhcp-users address-pool=dhcp-pool-users lease-time=1d
add interface=VLAN200-Servers name=dhcp-servers address-pool=dhcp-pool-servers lease-time=12h

/ip dhcp-server network
add address=192.168.100.0/24 gateway=192.168.100.1 dns-server=1.1.1.1,8.8.8.8
add address=192.168.200.0/24 gateway=192.168.200.1 dns-server=192.168.200.10,1.1.1.1

/ip dns
set servers=1.1.1.1,8.8.8.8,208.67.222.222 allow-remote-requests=yes cache-size=4096KiB

# IPv6 Configuration
/ipv6 address
add address=2001:db8:100::1/64 interface=VLAN100-Users advertise=yes
add address=2001:db8:200::1/64 interface=VLAN200-Servers advertise=yes

/ipv6 route
add dst-address=::/0 gateway=2001:db8::1 distance=1

/ipv6 dhcp-server
add name=dhcpv6-users interface=VLAN100-Users address-pool=ipv6-pool-users lease-time=1d

/ipv6 nd
add interface=VLAN100-Users ra-interval=30s ra-lifetime=1800s advertise-dns=yes

/ipv6 settings
set disable-ipv6=no accept-router-advertisements=yes forward=yes

# Firewall Configuration
/ip firewall address-list
add list=internal-networks address=192.168.0.0/16
add list=internal-networks address=10.0.0.0/8
add list=blacklist address=192.0.2.100 timeout=1d

/ip firewall filter
add chain=input connection-state=established,related action=accept comment="Allow established"
add chain=input connection-state=invalid action=drop comment="Drop invalid"
add chain=input protocol=icmp action=accept comment="Allow ICMP"
add chain=input src-address-list=internal-networks action=accept comment="Allow internal"
add chain=input action=drop comment="Drop all other input"
add chain=forward connection-state=established,related action=accept comment="Allow established"
add chain=forward connection-state=invalid action=drop comment="Drop invalid"
add chain=forward src-address-list=blacklist action=drop comment="Drop blacklisted"
add chain=forward action=accept comment="Allow forward"

/ip firewall nat
add chain=srcnat out-interface=pppoe-wan action=masquerade comment="Masquerade WAN"
add chain=dstnat protocol=tcp dst-port=80 action=dst-nat to-addresses=192.168.200.10 to-ports=80 comment="Web server"
add chain=dstnat protocol=tcp dst-port=443 action=dst-nat to-addresses=192.168.200.10 to-ports=443 comment="HTTPS server"

/ip firewall mangle
add chain=prerouting src-address=192.168.100.0/24 action=mark-connection new-connection-mark=users
add chain=prerouting connection-mark=users action=mark-packet new-packet-mark=user-traffic
add chain=prerouting src-address=192.168.200.0/24 action=mark-connection new-connection-mark=servers
add chain=prerouting connection-mark=servers action=mark-packet new-packet-mark=server-traffic

# QoS Configuration
/queue simple
add name=Users target=192.168.100.0/24 max-limit=50M/50M priority=3 queue=default/default
add name=Servers target=192.168.200.0/24 max-limit=100M/100M priority=1 queue=default/default

/queue tree
add name=upload-parent parent=global packet-mark=server-traffic limit-at=0 max-limit=100M priority=1
add name=download-parent parent=global packet-mark=user-traffic limit-at=0 max-limit=50M priority=3

/queue type
add name=fair-queue kind=sfq pfifo-limit=10

# Routing Protocols
/routing ospf instance
add name=default router-id=192.168.100.1 redistribute-connected=as-external-1

/routing ospf area
add name=backbone area-id=0.0.0.0 instance=default

/routing bgp instance
set default as=65001 router-id=192.168.100.1 redistribute-connected=yes

/routing bgp peer
add name=isp-peer remote-address=203.0.113.1 remote-as=65000 instance=default

/routing filter
add chain=ospf-out action=accept prefix=192.168.100.0/24
add chain=ospf-out action=reject

# PPP Configuration
/ppp secret
add name=vpnuser1 password=vpnpass123 service=l2tp local-address=192.168.250.1 remote-address=192.168.250.10
add name=vpnuser2 password=vpnpass456 service=l2tp local-address=192.168.250.1 remote-address=192.168.250.11

/ppp profile
add name=vpn-profile local-address=192.168.250.1 remote-address=192.168.250.0/24 dns-server=192.168.100.1,1.1.1.1 use-encryption=required

/ppp aaa
set use-radius=no accounting=yes

# Tools and Monitoring
/tool netwatch
add host=8.8.8.8 interval=30s timeout=5s type=icmp up-script="" down-script="" comment="Monitor Google DNS"
add host=192.168.200.10 interval=60s timeout=3s type=tcp-conn port=80 comment="Monitor web server"

/tool e-mail
set server=smtp.example.com port=587 from=router@example.com user=router@example.com password=emailpass123 tls=yes

/tool mac-server
set allowed-interface-list=LAN

/tool graphing
set enabled=yes store-every=5min

/tool romon
set enabled=yes secrets=romon123

/tool bandwidth-server
set enabled=yes authenticate=yes max-sessions=10

# SNMP Configuration
/snmp
set enabled=yes contact="Network Admin" location="Data Center" trap-community=public trap-version=2 trap-generators=interfaces

/snmp community
add name=public security=none read-access=yes write-access=no addresses=192.168.100.0/24,192.168.200.0/24

# RADIUS Configuration
/radius
add address=192.168.200.20 secret=radius123 service=login,accounting authentication-port=1812 accounting-port=1813 timeout=3s

# MPLS Configuration
/mpls
set enabled=yes propagate-ttl=yes

/mpls ldp
set enabled=yes lsr-id=192.168.100.1 transport-address=192.168.100.1

/mpls interface
add interface=bond1 mpls-mtu=1508

# Container Configuration (RouterOS 7)
/container
add remote-image=nginx:latest tag=latest interface=veth1 root-dir=container/nginx mounts=/etc/nginx:/etc/nginx start-on-boot=yes

# Service Configuration
/ip service
set telnet disabled=yes
set ftp disabled=yes
set www disabled=no port=8080 address=192.168.100.0/24,192.168.200.0/24
set ssh disabled=no port=2222 address=192.168.100.0/24
set www-ssl disabled=no port=8443 address=192.168.100.0/24
set api disabled=yes
set winbox disabled=no port=8291 address=192.168.100.0/24
set api-ssl disabled=yes

# Special Features
/special-login
set enabled=no

/partitions
set type=data size=10G