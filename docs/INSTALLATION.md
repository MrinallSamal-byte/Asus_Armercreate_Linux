# Installation Guide

This guide provides detailed instructions for installing ASUS Armoury Crate Linux on various distributions.

## Prerequisites

Before installing, ensure your system meets these requirements:

- Linux kernel 5.4 or later (for ASUS WMI support)
- An ASUS laptop (TUF/ROG/VivoBook/ZenBook)
- Python 3.9 or later
- GTK4 and libadwaita

## Quick Installation

The easiest way to install is using the provided installer script:

```bash
git clone https://github.com/asus-armoury-linux/asus-armoury-crate.git
cd asus-armoury-crate
sudo ./install.sh
```

The installer will:
1. Detect your distribution
2. Install required dependencies
3. Install the Python package
4. Set up systemd service
5. Configure udev rules and polkit

## Distribution-Specific Instructions

### Ubuntu / Debian / Linux Mint

```bash
# Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-gi python3-gi-cairo \
    gir1.2-gtk-4.0 gir1.2-adw-1 libadwaita-1-0 lm-sensors

# Install the package
sudo pip3 install .

# Install system files
sudo cp systemd/asus-armoury-daemon.service /etc/systemd/system/
sudo cp polkit/org.asus.armoury.policy /usr/share/polkit-1/actions/
sudo cp udev/99-asus-armoury.rules /etc/udev/rules.d/

# Create user group
sudo groupadd asus-armoury
sudo usermod -aG asus-armoury $USER

# Enable and start service
sudo systemctl daemon-reload
sudo udevadm control --reload-rules
sudo systemctl enable --now asus-armoury-daemon
```

### Fedora

```bash
# Install dependencies
sudo dnf install -y python3 python3-pip python3-gobject gtk4 libadwaita lm_sensors

# Install the package
sudo pip3 install .

# Follow the same system file installation steps as Ubuntu
```

### Arch Linux / Manjaro

```bash
# Install dependencies
sudo pacman -S python python-pip python-gobject gtk4 libadwaita lm_sensors

# Or use an AUR helper (if available)
# yay -S asus-armoury-crate

# Install from source
sudo pip3 install .

# Follow the same system file installation steps
```

### openSUSE

```bash
# Install dependencies
sudo zypper install python3 python3-pip python3-gobject gtk4 libadwaita sensors

# Install the package
sudo pip3 install .
```

## Optional Components

### asusctl (Recommended)

asusctl provides enhanced ASUS hardware support:

```bash
# Ubuntu (PPA)
sudo add-apt-repository ppa:asus-linux/asus-linux
sudo apt update
sudo apt install asusctl

# Fedora (COPR)
sudo dnf copr enable lukenukem/asus-linux
sudo dnf install asusctl

# Arch Linux (AUR)
yay -S asusctl
```

### supergfxctl (For GPU Switching)

```bash
# Install via the same repositories as asusctl
sudo apt install supergfxctl  # Ubuntu
sudo dnf install supergfxctl  # Fedora
yay -S supergfxctl            # Arch
```

## Post-Installation

1. **Log out and log back in** to apply group membership changes

2. **Verify the daemon is running:**
   ```bash
   systemctl status asus-armoury-daemon
   ```

3. **Launch the application:**
   - From application menu: Search for "ASUS Armoury Crate"
   - From terminal: `asus-armoury-gui`

4. **Check hardware detection:**
   ```bash
   asus-armoury-daemon --detect
   ```

## Troubleshooting Installation

### GTK4 not found

If GTK4 packages are not available on older distributions, you may need to:
- Upgrade your distribution
- Use a Flatpak version (when available)
- Build GTK4 from source

### Permission Errors

If you get permission errors:
```bash
# Ensure you're in the asus-armoury group
groups $USER

# If not, add yourself and re-login
sudo usermod -aG asus-armoury $USER
```

### Kernel Module Issues

Ensure ASUS WMI module is loaded:
```bash
lsmod | grep asus
# Should show: asus_nb_wmi, asus_wmi

# If not loaded, try:
sudo modprobe asus-nb-wmi
```

### Service Won't Start

Check logs for errors:
```bash
journalctl -u asus-armoury-daemon -b
```

## Uninstallation

To remove ASUS Armoury Crate:

```bash
sudo ./uninstall.sh
```

Or manually:
```bash
sudo systemctl stop asus-armoury-daemon
sudo systemctl disable asus-armoury-daemon
sudo pip3 uninstall asus-armoury-crate
sudo rm /etc/systemd/system/asus-armoury-daemon.service
sudo rm /usr/share/polkit-1/actions/org.asus.armoury.policy
sudo rm /etc/udev/rules.d/99-asus-armoury.rules
```
