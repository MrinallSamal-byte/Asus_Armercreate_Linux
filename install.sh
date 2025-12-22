#!/bin/bash
#
# ASUS Armoury Crate Linux - Installation Script
#
# This script installs the application and its system components.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}Error: This script must be run as root${NC}"
        echo "Please run: sudo $0"
        exit 1
    fi
}

# Detect distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        DISTRO_VERSION=$VERSION_ID
    else
        DISTRO="unknown"
    fi
    echo -e "${BLUE}Detected distribution: $DISTRO${NC}"
}

# Install dependencies based on distribution
install_dependencies() {
    echo -e "${BLUE}Installing dependencies...${NC}"
    
    case $DISTRO in
        ubuntu|debian|linuxmint|pop)
            apt-get update
            apt-get install -y python3 python3-pip python3-gi python3-gi-cairo \
                gir1.2-gtk-4.0 gir1.2-adw-1 libadwaita-1-0 \
                python3-dbus lm-sensors
            ;;
        fedora)
            dnf install -y python3 python3-pip python3-gobject gtk4 libadwaita \
                python3-dbus lm_sensors
            ;;
        arch|manjaro|endeavouros)
            pacman -Sy --noconfirm python python-pip python-gobject gtk4 libadwaita \
                python-dbus lm_sensors
            ;;
        opensuse*)
            zypper install -y python3 python3-pip python3-gobject gtk4 libadwaita \
                python3-dbus sensors
            ;;
        *)
            echo -e "${YELLOW}Warning: Unknown distribution. Please install dependencies manually:${NC}"
            echo "  - Python 3.9+"
            echo "  - GTK4"
            echo "  - libadwaita"
            echo "  - PyGObject"
            echo "  - lm-sensors"
            ;;
    esac
}

# Install Python package
install_python_package() {
    echo -e "${BLUE}Installing Python package...${NC}"
    
    # Install in system Python
    pip3 install --system .
}

# Install system files
install_system_files() {
    echo -e "${BLUE}Installing system files...${NC}"
    
    # Create group for hardware access
    if ! getent group asus-armoury > /dev/null 2>&1; then
        groupadd asus-armoury
        echo -e "${GREEN}Created 'asus-armoury' group${NC}"
    fi
    
    # Add current user to group
    if [ -n "$SUDO_USER" ]; then
        usermod -aG asus-armoury "$SUDO_USER"
        echo -e "${GREEN}Added $SUDO_USER to 'asus-armoury' group${NC}"
    fi
    
    # Install systemd service
    if [ -d /etc/systemd/system ]; then
        cp systemd/asus-armoury-daemon.service /etc/systemd/system/
        systemctl daemon-reload
        echo -e "${GREEN}Installed systemd service${NC}"
    fi
    
    # Install polkit policy
    if [ -d /usr/share/polkit-1/actions ]; then
        cp polkit/org.asus.armoury.policy /usr/share/polkit-1/actions/
        echo -e "${GREEN}Installed polkit policy${NC}"
    fi
    
    # Install udev rules
    if [ -d /etc/udev/rules.d ]; then
        cp udev/99-asus-armoury.rules /etc/udev/rules.d/
        udevadm control --reload-rules
        udevadm trigger
        echo -e "${GREEN}Installed udev rules${NC}"
    fi
    
    # Install desktop file
    if [ -d /usr/share/applications ]; then
        cp data/org.asus.armoury.desktop /usr/share/applications/
        echo -e "${GREEN}Installed desktop entry${NC}"
    fi
    
    # Install icon
    if [ -d /usr/share/icons/hicolor/scalable/apps ]; then
        cp data/icons/org.asus.armoury.svg /usr/share/icons/hicolor/scalable/apps/
        gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
        echo -e "${GREEN}Installed application icon${NC}"
    fi
    
    # Create log directory
    mkdir -p /var/log/asus-armoury
    chmod 755 /var/log/asus-armoury
    
    # Create config directory
    mkdir -p /etc/asus-armoury
    chmod 755 /etc/asus-armoury
}

# Enable and start service
enable_service() {
    echo -e "${BLUE}Enabling daemon service...${NC}"
    
    systemctl enable asus-armoury-daemon.service
    systemctl start asus-armoury-daemon.service
    
    if systemctl is-active --quiet asus-armoury-daemon; then
        echo -e "${GREEN}Daemon service is running${NC}"
    else
        echo -e "${YELLOW}Warning: Daemon service failed to start${NC}"
        echo "Check logs with: journalctl -u asus-armoury-daemon"
    fi
}

# Print post-installation message
print_post_install() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Installation completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "To start using ASUS Armoury Crate:"
    echo "  1. Log out and log back in (to apply group membership)"
    echo "  2. Launch 'ASUS Armoury Crate' from your application menu"
    echo ""
    echo "Or run from terminal:"
    echo "  asus-armoury-gui"
    echo ""
    echo "For daemon status:"
    echo "  systemctl status asus-armoury-daemon"
    echo ""
    echo "For troubleshooting, see:"
    echo "  /var/log/asus-armoury/asus-armoury.log"
    echo "  journalctl -u asus-armoury-daemon"
    echo ""
}

# Main installation
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}ASUS Armoury Crate Linux - Installation${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    check_root
    detect_distro
    install_dependencies
    install_python_package
    install_system_files
    enable_service
    print_post_install
}

# Run main function
main "$@"
