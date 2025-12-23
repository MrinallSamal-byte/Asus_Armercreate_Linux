#!/bin/bash
# ASUS Armoury Crate Linux Installation Script
#
# This script installs the compiled binaries, systemd service, polkit policies,
# udev rules, and D-Bus configuration.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
  exit 1
fi

echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ASUS Armoury Crate Linux Installer          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# Detect installation prefix
PREFIX="${PREFIX:-/usr}"
BIN_DIR="$PREFIX/bin"
SYSTEMD_DIR="/etc/systemd/system"
POLKIT_DIR="/usr/share/polkit-1/actions"
UDEV_DIR="/etc/udev/rules.d"
DBUS_DIR="/etc/dbus-1/system.d"
DESKTOP_DIR="/usr/share/applications"

# Check if binaries are built
if [ ! -f "target/release/asus-armoury-daemon" ] || [ ! -f "target/release/asus-armoury-gui" ]; then
  echo -e "${RED}Error: Binaries not found. Please run 'cargo build --release' first.${NC}"
  exit 1
fi

echo -e "${YELLOW}Installing binaries...${NC}"
install -Dm755 target/release/asus-armoury-daemon "$BIN_DIR/asus-armoury-daemon"
install -Dm755 target/release/asus-armoury-gui "$BIN_DIR/asus-armoury-gui"
echo -e "${GREEN}✓ Binaries installed to $BIN_DIR${NC}"

echo -e "${YELLOW}Installing systemd service...${NC}"
install -Dm644 systemd/asus-armoury-daemon.service "$SYSTEMD_DIR/asus-armoury-daemon.service"
echo -e "${GREEN}✓ Systemd service installed${NC}"

echo -e "${YELLOW}Installing polkit policies...${NC}"
install -Dm644 polkit/org.asuslinux.armoury.policy "$POLKIT_DIR/org.asuslinux.armoury.policy"
echo -e "${GREEN}✓ Polkit policies installed${NC}"

echo -e "${YELLOW}Installing udev rules...${NC}"
install -Dm644 udev/99-asus-armoury.rules "$UDEV_DIR/99-asus-armoury.rules"
echo -e "${GREEN}✓ Udev rules installed${NC}"

echo -e "${YELLOW}Installing D-Bus configuration...${NC}"
install -Dm644 data/org.asuslinux.Armoury.conf "$DBUS_DIR/org.asuslinux.Armoury.conf"
echo -e "${GREEN}✓ D-Bus configuration installed${NC}"

echo -e "${YELLOW}Installing desktop entry...${NC}"
install -Dm644 data/org.asuslinux.armoury.desktop "$DESKTOP_DIR/org.asuslinux.armoury.desktop"
echo -e "${GREEN}✓ Desktop entry installed${NC}"

echo ""
echo -e "${YELLOW}Reloading systemd daemon...${NC}"
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd daemon reloaded${NC}"

echo -e "${YELLOW}Reloading udev rules...${NC}"
udevadm control --reload-rules
udevadm trigger
echo -e "${GREEN}✓ Udev rules reloaded${NC}"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Installation Complete!                      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Start the daemon:"
echo "     sudo systemctl start asus-armoury-daemon"
echo ""
echo "  2. Enable on boot (optional):"
echo "     sudo systemctl enable asus-armoury-daemon"
echo ""
echo "  3. Launch the GUI application:"
echo "     asus-armoury-gui"
echo ""
echo -e "${YELLOW}Check daemon status with:${NC}"
echo "  sudo systemctl status asus-armoury-daemon"
echo ""
echo -e "${YELLOW}View logs with:${NC}"
echo "  sudo journalctl -u asus-armoury-daemon -f"
echo ""
