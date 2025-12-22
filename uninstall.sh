#!/bin/bash
#
# ASUS Armoury Crate Linux - Uninstall Script
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    exit 1
fi

echo -e "${BLUE}Uninstalling ASUS Armoury Crate Linux...${NC}"

# Stop and disable service
if systemctl is-active --quiet asus-armoury-daemon; then
    systemctl stop asus-armoury-daemon
fi

if systemctl is-enabled --quiet asus-armoury-daemon 2>/dev/null; then
    systemctl disable asus-armoury-daemon
fi

# Remove system files
rm -f /etc/systemd/system/asus-armoury-daemon.service
rm -f /usr/share/polkit-1/actions/org.asus.armoury.policy
rm -f /etc/udev/rules.d/99-asus-armoury.rules
rm -f /usr/share/applications/org.asus.armoury.desktop
rm -f /usr/share/icons/hicolor/scalable/apps/org.asus.armoury.svg

# Reload systemd and udev
systemctl daemon-reload
udevadm control --reload-rules

# Remove Python package
pip3 uninstall -y asus-armoury-crate 2>/dev/null || true

# Optionally remove config and logs
read -p "Remove configuration and logs? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf /etc/asus-armoury
    rm -rf /var/log/asus-armoury
    rm -rf ~/.config/asus-armoury
    echo -e "${GREEN}Configuration and logs removed${NC}"
fi

# Note about group
echo ""
echo -e "${GREEN}Uninstallation complete!${NC}"
echo ""
echo "Note: The 'asus-armoury' group was not removed."
echo "To remove it manually: sudo groupdel asus-armoury"
