############## Complete Device Configuration ##############
# This template uses variables from:
# 1. Device Properties (NetBox Device Object)
# 2. Config Context (device.get_config_context())



### System Identity & Base Config
/system identity
set name=000012-R1

### System Timezone
/system clock
set time-zone-name=America/New_York

### DNS Configuration
/ip dns
set servers=8.8.8.8,8.8.4.4
set allow-remote-requests=yes

### Syslog Configuration
/system logging action
set 3 bsd-syslog=yes remote=54.221.91.223 syslog-facility=local0

/system logging
set 0 action=remote prefix=:info topics=info
set 1 action=remote prefix=:Error
set 2 action=remote prefix=:Warning
set 3 action=remote prefix=:Critical topics=interface
add action=remote prefix=:Firewall topics=firewall
add action=remote prefix=:pppoe topics=pppoe,info

### Service Configuration
/ip service
set telnet disabled=yes
set ftp disabled=yes
set www disabled=yes
set ssh address="192.168.100.0/24,10.0.0.0/8,172.27.0.0/16,54.221.91.223/32,44.207.189.240/32,52.0.162.201/32,98.82.104.1/32"
set api address="192.168.100.0/24,10.0.0.0/8,172.27.0.0/16,54.221.91.223/32,44.207.189.240/32,52.0.162.201/32,98.82.104.1/32"
set winbox address="192.168.100.0/24,10.0.0.0/8,172.27.0.0/16"

### User Groups Configuration
/user group
add name=mktxp_group policy="ssh,read,api,!local,!telnet,!ftp,!reboot,!write,!policy,!test,!winbox,!password,!web,!sniff,!sensitive,!romon,!rest-api"
add name=oxidized policy="ssh,read,password,sensitive,!local,!telnet,!ftp,!reboot,!write,!policy,!test,!winbox,!web,!sniff,!api,!romon,!rest-api"

### User Configuration
/user
add name=mktxp_user group=mktxp_group password=2mint503!
add name=oxidized group=oxidized password=ivoryanimal37

### AAA and RADIUS Configuration
/user aaa
set use-radius=yes

/radius
add address=172.27.209.248 secret=jSniRkQfIwDRJUWG7Mwp service=login

### SNMP Configuration
/snmp
set enabled=yes trap-version=2

### Netwatch Configuration
/tool netwatch
add comment="test" disabled=no host=1.1.1.1 type=icmp
add comment="Grafana Instance" disabled=no host=54.221.91.223 type=simple
add comment="Netbox Instance" disabled=no host=98.82.104.1 type=icmp

### Firewall Address Lists
/ip firewall address-list
add address=54.221.91.223 comment=grafana list=ResiCore
add address=44.207.189.240 comment=jump_a list=ResiCore
add address=52.0.162.201 comment=jump_b list=ResiCore
add address=98.82.104.1 comment=netbox list=ResiCore

### Base Firewall Rules
/ip firewall filter
add action=accept chain=forward comment="Allow ResiBridge Core IPs" src-address-list=ResiCore
add action=accept chain=input comment="Allow ResiBridge Core IPs" src-address-list=ResiCore

add action=drop chain=input comment="Drop SSH brute forcers" dst-port=22 protocol=tcp src-address-list=ssh_blacklist
add action=add-src-to-address-list address-list=ssh_blacklist address-list-timeout=1w3d chain=input comment="Move persistent offenders to blacklist" connection-state=new dst-port=22 protocol=tcp src-address-list=ssh_stage3
add action=add-src-to-address-list address-list=ssh_stage3 address-list-timeout=1m chain=input comment="Escalate to stage 3" connection-state=new dst-port=22 protocol=tcp src-address-list=ssh_stage2
add action=add-src-to-address-list address-list=ssh_stage2 address-list-timeout=1m chain=input comment="Escalate to stage 2" connection-state=new dst-port=22 protocol=tcp src-address-list=ssh_stage1
add action=add-src-to-address-list address-list=ssh_stage1 address-list-timeout=1m chain=input comment="Initial detection - Add to stage 1" connection-state=new dst-port=22 protocol=tcp


# Create WAN Bridge for public interface redundancy
/interface bridge
add name=BR-WAN

# Add physical WAN ports to bridge for redundancy
/interface bridge port
add bridge=BR-WAN interface=sfp-sfpplus1
add bridge=BR-WAN interface=sfp28-1



# Configure WAN IP address
/ip address
add address=172.27.244.218/16 interface=BR-WAN network=172.27.0.0 comment=WAN

# Add default route via WAN gateway
/ip route
add disabled=no distance=1 dst-address=0.0.0.0/0 gateway=172.27.0.1 \
    pref-src="" routing-table=main scope=30 suppress-hw-offload=no \
    target-scope=10

# CGNAT Bridge Configuration
/interface bridge
add name=BR-CGNAT

# Add Bridge Ports
/interface bridge port
add bridge=BR-CGNAT interface=sfp-sfpplus2
add bridge=BR-CGNAT interface=sfp-sfpplus3
add bridge=BR-CGNAT interface=sfp-sfpplus4
add bridge=BR-CGNAT interface=sfp-sfpplus5
add bridge=BR-CGNAT interface=sfp-sfpplus6
add bridge=BR-CGNAT interface=sfp-sfpplus7
add bridge=BR-CGNAT interface=sfp-sfpplus8
add bridge=BR-CGNAT interface=sfp-sfpplus9
add bridge=BR-CGNAT interface=sfp-sfpplus10


    


# CGNAT IP Configuration - Using Site Prefix 100.64.19.0/24
/ip address
add address=100.64.19.1/24 interface=BR-CGNAT

# CGNAT DHCP Pool

    /ip pool
    add name=cgnat-pool ranges=100.64.19.31-100.64.19.224

# CGNAT DHCP Server
/ip dhcp-server
add address-pool=cgnat-pool interface=BR-CGNAT name=CGNAT

# DHCP Network
/ip dhcp-server network
add address=100.64.19.0/24 gateway=100.64.19.1 dns-server=8.8.8.8

### System Notes
/system note
set show-at-login=no

