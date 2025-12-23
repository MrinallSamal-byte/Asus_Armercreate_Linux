#!/bin/bash
# ASUS Armoury Crate Linux Uninstall Script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
  exit 1
fi

echo -e "${YELLOW}Uninstalling ASUS Armoury Crate Linux...${NC}"

# Stop and disable the service
if systemctl is-active --quiet asus-armoury-daemon; then
  echo -e "${YELLOW}Stopping daemon...${NC}"
  systemctl stop asus-armoury-daemon
fi

if systemctl is-enabled --quiet asus-armoury-daemon 2>/dev/null; then
  echo -e "${YELLOW}Disabling daemon...${NC}"
  systemctl disable asus-armoury-daemon
fi

PREFIX="${PREFIX:-/usr}"

echo -e "${YELLOW}Removing files...${NC}"
rm -f "$PREFIX/bin/asus-armoury-daemon"
rm -f "$PREFIX/bin/asus-armoury-gui"
rm -f "/etc/systemd/system/asus-armoury-daemon.service"
rm -f "/usr/share/polkit-1/actions/org.asuslinux.armoury.policy"
rm -f "/etc/udev/rules.d/99-asus-armoury.rules"
rm -f "/etc/dbus-1/system.d/org.asuslinux.Armoury.conf"
rm -f "/usr/share/applications/org.asuslinux.armoury.desktop"

echo -e "${YELLOW}Reloading system services...${NC}"
systemctl daemon-reload
udevadm control --reload-rules
udevadm trigger

echo -e "${GREEN}✓ Uninstallation complete${NC}"
echo ""
echo -e "${YELLOW}Note: Configuration files in ~/.config/armoury/ and ~/.local/share/armoury/ were preserved.${NC}"
echo "  To remove them, run: rm -rf ~/.config/armoury ~/.local/share/armoury"
