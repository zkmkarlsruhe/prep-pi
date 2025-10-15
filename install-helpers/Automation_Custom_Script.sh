#!/bin/bash

# Copyright © 2025 Hugo Dünger -  ZKM | Zentrum für Kunst und Medien Karlsruhe
# Lizenziert unter der MIT-Lizenz

#####################################################################
######### CONFIGURATION #############################################
#####################################################################

SSID="prep-pi"
PI_LOCAL_DOMAIN="prep.local"

#--------------------------------------------------------------------
# DO NOT EDIT BELOW THIS LINE
#--------------------------------------------------------------------

echo "Starting post-installation custom script..."

# --- 1. Preparations for Read-Only File System ---
echo "Preparing system for read-only file system..."
echo "Disabling cron..."
systemctl disable --now cron

echo "Moving dhclient lease file to RAM..."
# Ensure the target directory exists in RAM
mkdir -p /tmp/dhcp
rm -f /var/lib/dhcp/dhclient.eth0.leases
touch /tmp/dhcp/dhclient.eth0.leases
ln -sf /tmp/dhcp/dhclient.eth0.leases /var/lib/dhcp/dhclient.eth0.leases

echo "Making systemd journal write to RAM..."
sed -i 's/#Storage=auto/Storage=volatile/' /etc/systemd/journald.conf
systemctl restart systemd-journald
echo "Read-only file system preparations complete."


# --- 2. Custom Configurations ---
sudo systemctl stop isc-dhcp-server || true
sudo systemctl disable isc-dhcp-server || true

# 2.1 /etc/hosts Configuration
echo "Configuring /etc/hosts..."
PI_IP="192.168.42.1"
PI_HOSTNAME="prep-pi"
cat << EOF > /etc/hosts
127.0.0.1       localhost
127.0.1.1       $PI_HOSTNAME
$PI_IP          $PI_LOCAL_DOMAIN
EOF
echo "/etc/hosts configured."


# 2.2 Hotspot (hostapd) - Create Open Network
# DietPi creates a WPA2-secured hotspot by default. This overwrites the config
# to create an open (unsecured) network as specified in your original script.
echo "Configuring hostapd for an open hotspot..."
cat << EOF > /etc/hostapd/hostapd.conf
interface=wlan0
driver=nl80211
ssid=$SSID
country_code=DE
hw_mode=g
channel=3
ieee80211n=0
ieee80211ac=0
ieee80211ax=0
wmm_enabled=0
macaddr_acl=0
ignore_broadcast_ssid=0
EOF

echo "Disabling IPv6..."
sudo bash -c 'cat << "EOF" > /etc/sysctl.d/99-disable-ipv6.conf
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
EOF'
sudo sysctl -p
echo "IPv6 disabled."


# 2.3 dnsmasq Configuration
echo "Configuring dnsmasq..."
# Remove DietPi's default hotspot config to avoid conflicts
rm -f /etc/dnsmasq.d/dietpi-hotspot.conf

cat << "EOF" > /etc/dnsmasq.d/prep.conf
no-resolv
listen-address=127.0.0.1,192.168.42.1
local=/#/
address=/#/192.168.42.1
dhcp-authoritative
dhcp-range=192.168.42.10,192.168.42.250,255.255.255.0,15m
dhcp-option=option:router,192.168.42.1
dhcp-option=option:dns-server,192.168.42.1
dhcp-leasefile=/tmp/dnsmasq.leases
EOF
touch /tmp/dnsmasq.leases


# 2.4 lighttpd Configuration
echo "Configuring lighttpd..."
lighty-enable-mod rewrite

# Escape dots in the domain name for use in the regex pattern
PI_LOCAL_DOMAIN_REGEX=${PI_LOCAL_DOMAIN//./\\.}

# Overwrite the entire lighttpd.conf for your custom captive portal setup
cat << EOF > /etc/lighttpd/lighttpd.conf
server.modules = (
    "mod_indexfile", "mod_access", "mod_alias", "mod_redirect", "mod_rewrite"
)
server.document-root        = "/var/www/public"
server.upload-dirs          = ( "/var/cache/lighttpd/uploads" )
server.errorlog             = "/tmp/lighttpd-error.log"
server.pid-file             = "/run/lighttpd.pid"
server.username             = "www-data"
server.groupname            = "www-data"
server.port                 = 80
index-file.names            = ( "index.php", "index.html" )
url.access-deny             = ( "~", ".inc" )
static-file.exclude-extensions = ( ".php", ".pl", ".fcgi" )

include_shell "/usr/share/lighttpd/use-ipv6.pl " + server.port
include_shell "/usr/share/lighttpd/create-mime.conf.pl"
include "/etc/lighttpd/conf-enabled/*.conf"

# Captive portal and redirect logic
\$HTTP["host"] == "captive.apple.com" {
    # Handle any request for a non-existent file by serving index.html
    server.error-handler-404 = "/index.html"
} else \$HTTP["host"] !~ "^(${PI_LOCAL_DOMAIN_REGEX}|192\.168\.42\.1)$" {
    # Redirect any other hostname to the local domain
    url.redirect = ( ".*" => "http://$PI_LOCAL_DOMAIN%0" )
}
EOF
# Ensure the log file exists in RAM and has correct permissions
touch /tmp/lighttpd-error.log
chown www-data:www-data /tmp/lighttpd-error.log
# A public folder is needed for the document root
mkdir -p /var/www/public


# --- 3. Finalize Network and Services ---

# 3.1 Traffic Redirect (iptables)
echo "Configuring iptables for traffic redirection..."
iptables -F
iptables -t nat -F
iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j DNAT --to-destination 192.168.42.1:80
netfilter-persistent save
echo "iptables configured."

# 3.2 Restart Services
echo "Restarting services with new configurations..."
systemctl restart hostapd
systemctl restart dnsmasq
systemctl restart lighttpd

# --- 5. Set Filesystem to Read-Only (DietPi Optimized) ---
echo "Configuring filesystem for read-only mode..."

# 5.1 Add tmpfs mounts for volatile directories not covered by DietPi RAMlog.
# This prevents applications that write to /tmp or /var/tmp from failing.
cat << EOF >> /etc/fstab

# Mounts for read-only mode (added by automation script)
tmpfs /var/tmp tmpfs defaults,noatime,nosuid,size=100m 0 0
EOF

# 5.2 Set the root filesystem to read-only in fstab.
# This finds the root mount point (' / ') and adds the 'ro' (read-only)
# option, which will be applied on the next boot.
sed -i -E 's|^([^#].*[ \t]/[ \t].*)defaults(.*)|\1defaults,ro\2|' /etc/fstab

echo "Filesystem configured to mount as read-only on next boot."
echo "The system will be fully read-only after the first reboot."

echo "Custom automation script finished!"