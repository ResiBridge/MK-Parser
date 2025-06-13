# 2025-06-13 10:29:19 by RouterOS 7.14.2
# software id = 54EE-CKWV
#
# model = CCR2004-1G-12S+2XS
# serial number = HGJ09VSEZSG
/interface bridge
add name=BR-CGNAT
add name=BR-WAN
/interface ethernet
set [ find default-name=sfp-sfpplus1 ] advertise="1G-baseT-half,1G-baseT-full,\
    1G-baseX,2.5G-baseT,2.5G-baseX,5G-baseT,10G-baseT,10G-baseSR-LR,10G-baseCR\
    "
/ip pool
add name=cgnat-pool ranges=100.64.19.31-100.64.19.224
/ip dhcp-server
add address-pool=cgnat-pool interface=BR-CGNAT name=CGNAT
/port
set 0 name=serial0
set 1 name=serial1
/interface ovpn-client
add certificate=splynx_1 cipher=aes192-cbc connect-to=crm.resibridge.com \
    mac-address=02:83:B2:CC:65:E0 name=splynx profile=default-encryption \
    user=longwood
/system logging action
set 3 bsd-syslog=yes remote=54.221.91.223 syslog-facility=local0
/user group
add name=mktxp_group policy="ssh,read,api,!local,!telnet,!ftp,!reboot,!write,!\
    policy,!test,!winbox,!password,!web,!sniff,!sensitive,!romon,!rest-api"
add name=oxidized policy="ssh,read,password,sensitive,!local,!telnet,!ftp,!reb\
    oot,!write,!policy,!test,!winbox,!web,!sniff,!api,!romon,!rest-api"
/zerotier
set zt1 comment="ZeroTier Central controller - mgmt" name=zt1 port=9993
/zerotier interface
add allow-default=no allow-global=no allow-managed=yes disabled=no instance=\
    zt1 name=zerotier1 network=52b337794fb794fc
/interface bridge port
add bridge=BR-WAN interface=sfp-sfpplus1
add bridge=BR-WAN interface=sfp28-1
add bridge=BR-CGNAT interface=sfp-sfpplus2
add bridge=BR-CGNAT interface=sfp-sfpplus3
add bridge=BR-CGNAT interface=sfp-sfpplus4
add bridge=BR-CGNAT interface=sfp-sfpplus5
add bridge=BR-CGNAT interface=sfp-sfpplus6
add bridge=BR-CGNAT interface=sfp-sfpplus7
add bridge=BR-CGNAT interface=sfp-sfpplus8
add bridge=BR-CGNAT interface=sfp-sfpplus9
add bridge=BR-CGNAT interface=sfp-sfpplus10
add bridge=BR-WAN interface=ether1
/ip address
add address=192.168.88.1/24 comment=defconf interface=ether1 network=\
    192.168.88.0
add address=208.217.64.178/29 comment=WAN interface=BR-WAN network=\
    208.217.64.176
add address=100.64.19.1/24 interface=BR-CGNAT network=100.64.19.0
/ip arp
add address=100.64.19.224 interface=BR-CGNAT mac-address=A8:6E:84:00:A2:A4
/ip dhcp-server lease
add address=100.64.19.224 client-id=1:a8:6e:84:0:a2:a4 mac-address=\
    A8:6E:84:00:A2:A4 server=CGNAT
/ip dhcp-server network
add address=100.64.19.0/24 dns-server=8.8.8.8 gateway=100.64.19.1
/ip dns
set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4
/ip firewall address-list
add address=54.221.91.223 comment=grafana list=ResiCore
add address=44.207.189.240 comment=jump_a list=ResiCore
add address=52.0.162.201 comment=jump_b list=ResiCore
add address=98.82.104.1 comment=netbox list=ResiCore
/ip firewall filter
add chain=forward comment="Splynx Blocking Rules - begin" disabled=yes
add action=jump chain=forward comment=SpBlockingRule-2751605989 \
    dst-address-list=!splynx-allowed-resources jump-target=splynx-blocked \
    src-address-list=SpLBL_blocked
add action=jump chain=forward comment=SpBlockingRule-2673675484 \
    dst-address-list=!splynx-allowed-resources jump-target=splynx-blocked \
    src-address-list=SpLBL_new
add action=jump chain=forward comment=SpBlockingRule-3109596403 \
    dst-address-list=!splynx-allowed-resources jump-target=splynx-blocked \
    src-address-list=SpLBL_disabled
add action=jump chain=forward comment=SpBlockingRule-2815368063 \
    dst-address-list=!splynx-allowed-resources jump-target=splynx-blocked \
    src-address-list=Reject_0
add action=jump chain=forward comment=SpBlockingRule-3502779369 \
    dst-address-list=!splynx-allowed-resources jump-target=splynx-blocked \
    src-address-list=Reject_1
add action=jump chain=forward comment=SpBlockingRule-1237416531 \
    dst-address-list=!splynx-allowed-resources jump-target=splynx-blocked \
    src-address-list=Reject_2
add action=jump chain=forward comment=SpBlockingRule-1053182661 \
    dst-address-list=!splynx-allowed-resources jump-target=splynx-blocked \
    src-address-list=Reject_3
add action=jump chain=forward comment=SpBlockingRule-2695028582 \
    dst-address-list=!splynx-allowed-resources jump-target=splynx-blocked \
    src-address-list=Reject_4
add action=accept chain=splynx-blocked comment=SpBlockingRule-3053659851 \
    dst-limit=2,0,src-address/1m40s dst-port=53 protocol=udp
add action=accept chain=splynx-blocked comment=SpBlockingRule-3728159901 \
    dst-address=159.65.88.239 dst-port=80,443,8101,8102,8103,8104 protocol=\
    tcp
add action=reject chain=splynx-blocked comment=SpBlockingRule-3070586937 \
    dst-limit=10,0,src-address/1m40s reject-with=icmp-admin-prohibited
add action=drop chain=splynx-blocked comment=SpBlockingRule-496360353
add chain=forward comment="Splynx Blocking Rules - end" disabled=yes
add action=accept chain=forward in-interface=zerotier1
add action=accept chain=input in-interface=zerotier1
add action=accept chain=forward comment="Allow ResiBridge Core IPs" \
    src-address-list=ResiCore
add action=accept chain=input comment="Allow ResiBridge Core IPs" \
    src-address-list=ResiCore
add action=drop chain=input comment="Drop SSH brute forcers" dst-port=22 \
    protocol=tcp src-address-list=ssh_blacklist
add action=add-src-to-address-list address-list=ssh_blacklist \
    address-list-timeout=1w3d chain=input comment=\
    "Move persistent offenders to blacklist" connection-state=new dst-port=22 \
    protocol=tcp src-address-list=ssh_stage3
add action=add-src-to-address-list address-list=ssh_stage3 \
    address-list-timeout=1m chain=input comment="Escalate to stage 3" \
    connection-state=new dst-port=22 protocol=tcp src-address-list=ssh_stage2
add action=add-src-to-address-list address-list=ssh_stage2 \
    address-list-timeout=1m chain=input comment="Escalate to stage 2" \
    connection-state=new dst-port=22 protocol=tcp src-address-list=ssh_stage1
add action=add-src-to-address-list address-list=ssh_stage1 \
    address-list-timeout=1m chain=input comment=\
    "Initial detection - Add to stage 1" connection-state=new dst-port=22 \
    protocol=tcp
/ip firewall nat
add action=dst-nat chain=dstnat comment="HTTPS Port Forward to 100.64.19.224" \
    dst-port=1099 in-interface=BR-WAN protocol=tcp to-addresses=100.64.19.224 \
    to-ports=443
/ip route
add disabled=no distance=1 dst-address=0.0.0.0/0 gateway=208.217.64.177 \
    pref-src="" routing-table=main scope=30 suppress-hw-offload=no \
    target-scope=10
/ip service
set telnet disabled=yes
set ftp disabled=yes
set www disabled=yes
set ssh address="192.168.100.0/24,10.0.0.0/8,54.221.91.223/32,44.207.189.240/3\
    2,52.0.162.201/32,98.82.104.1/32,172.27.0.0/16"
set api address="192.168.100.0/24,10.0.0.0/8,54.221.91.223/32,44.207.189.240/3\
    2,52.0.162.201/32,98.82.104.1/32,172.27.0.0/16"
set winbox address=192.168.100.0/24,10.0.0.0/8,68.173.179.95/32,172.27.0.0/16
/radius
add address=10.250.32.1 service=ppp,login,dhcp src-address=10.250.32.9
add address=172.27.209.248 service=login
/radius incoming
set accept=yes
/snmp
set enabled=yes trap-version=2
/system clock
set time-zone-name=America/Chicago
/system identity
set name=000012-R1
/system logging
set 0 action=remote prefix=:info
set 1 action=remote prefix=:Error
set 2 action=remote prefix=:Warning
set 3 action=remote prefix=:Critical topics=interface
add action=remote prefix=:Firewall topics=firewall
add action=remote prefix=:pppoe topics=pppoe,info
add topics=queue
add topics=radius
add topics=debug
/system note
set show-at-login=no
/system routerboard settings
set enter-setup-on=delete-key
/tool netwatch
add comment=test disabled=no host=1.1.1.1 type=icmp
add comment="Grafana Instance" disabled=no host=54.221.91.223 type=simple
add comment="Netbox Instance" disabled=no host=98.82.104.1 type=icmp
/user aaa
set default-group=full use-radius=yes
