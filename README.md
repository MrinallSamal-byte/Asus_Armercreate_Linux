# ASUS Armoury Crate Linux

A Linux desktop application providing ASUS Armoury Crate functionality for ASUS laptops (TUF / ROG series). Control hardware performance, fans, RGB lighting, and more directly from Linux.

![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-green.svg)

## Features

### Hardware & Performance Control
- **CPU Performance Modes**: Silent / Balanced / Turbo / Manual
- **GPU Mode Switching**: Integrated / Hybrid / Dedicated (via supergfxctl)
- **Fan Control**: Automatic and custom fan curves
- **Temperature Monitoring**: Real-time CPU/GPU temperature display
- **Battery Management**: Charge limit control (60% / 80% / 100%)

### RGB Keyboard Control
- Multiple lighting effects (Static, Breathing, Rainbow, Wave, etc.)
- Custom color selection
- Brightness and speed adjustment
- Per-zone control (where supported)

### User Profiles
- Pre-configured profiles: Gaming, Work, Silent, Balanced
- Custom profile creation
- Quick profile switching

### Modern GUI
- GTK4/libadwaita based interface
- Dark mode support
- Dashboard with system metrics
- System tray integration (planned)

## Screenshots

*Coming soon*

## Supported Models

This application is designed to work with ASUS laptops that have the `asus-nb-wmi` kernel module. This includes:

### ROG Series
- ROG Zephyrus G14/G15/G16
- ROG Strix G15/G17
- ROG Flow X13/X16/Z13

### TUF Gaming Series
- TUF Gaming A15/A17
- TUF Gaming F15/F17
- TUF Dash F15

### Other ASUS Laptops
- Zenbook Pro
- VivoBook Pro
- ProArt StudioBook

> **Note**: Feature availability depends on your specific hardware model. Some features may not be available on all laptops.

## Installation

### Prerequisites

- Linux kernel 5.x or later with `asus-nb-wmi` module
- Rust 1.70+ (for building from source)
- GTK4 and libadwaita development libraries

### Ubuntu/Debian

```bash
# Install dependencies
sudo apt install build-essential pkg-config libgtk-4-dev libadwaita-1-dev

# Clone and build
git clone https://github.com/MrinallSamal-byte/Asus_Armercreate_Linux.git
cd Asus_Armercreate_Linux
cargo build --release

# Install
sudo ./scripts/install.sh
```

### Fedora

```bash
# Install dependencies
sudo dnf install gcc pkg-config gtk4-devel libadwaita-devel

# Clone and build
git clone https://github.com/MrinallSamal-byte/Asus_Armercreate_Linux.git
cd Asus_Armercreate_Linux
cargo build --release

# Install
sudo ./scripts/install.sh
```

### Arch Linux

```bash
# Install dependencies
sudo pacman -S base-devel gtk4 libadwaita

# Clone and build
git clone https://github.com/MrinallSamal-byte/Asus_Armercreate_Linux.git
cd Asus_Armercreate_Linux
cargo build --release

# Install
sudo ./scripts/install.sh
```

### Using with asusctl

This application can work alongside or as an alternative to [asusctl](https://gitlab.com/asus-linux/asusctl). If asusctl is installed, some features will use it for better hardware support.

```bash
# Arch Linux
sudo pacman -S asusctl

# Other distros - see asusctl documentation
```

## Usage

### Starting the Daemon

```bash
# Start the daemon service
sudo systemctl start asus-armoury-daemon

# Enable on boot
sudo systemctl enable asus-armoury-daemon
```

### Using the GUI

```bash
# Launch the GUI application
asus-armoury-gui
```

Or find "ASUS Armoury Crate" in your application menu.

### Command Line Interface (planned)

```bash
# Get current performance mode
asus-armoury-cli get-performance

# Set performance mode
asus-armoury-cli set-performance turbo

# Set battery limit
asus-armoury-cli set-battery-limit 80
```

## Configuration

Configuration files are stored in:
- Daemon config: `~/.config/armoury/daemon.json`
- User profiles: `~/.local/share/armoury/profiles/`

### Example Profile

```json
{
  "name": "Gaming",
  "performance_mode": "Turbo",
  "gpu_mode": "Dedicated",
  "fan_mode": "Auto",
  "rgb_settings": {
    "effect": "Rainbow",
    "color": {"r": 255, "g": 0, "b": 0},
    "brightness": 100,
    "speed": 75
  },
  "battery_settings": {
    "charge_limit": 100
  }
}
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      GUI Application                      │
│                    (GTK4/libadwaita)                      │
└─────────────────────────┬───────────────────────────────┘
                          │ D-Bus
┌─────────────────────────▼───────────────────────────────┐
│                    Daemon Service                         │
│              (Rust async, privileged)                     │
├─────────────────────────────────────────────────────────┤
│   Hardware Controller  │  Profile Manager  │  Config     │
└─────────────┬───────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────┐
│                  Linux Kernel Interfaces                  │
├──────────────┬──────────────┬──────────────┬────────────┤
│  asus-nb-wmi │    sysfs     │   hwmon      │  thermal   │
│    module    │  (platform   │  (fans,      │   zones    │
│              │   profile)   │   temps)     │            │
└──────────────┴──────────────┴──────────────┴────────────┘
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/MrinallSamal-byte/Asus_Armercreate_Linux.git
cd Asus_Armercreate_Linux

# Build in debug mode
cargo build

# Run tests
cargo test

# Run the daemon (requires root)
sudo cargo run --bin asus-armoury-daemon

# Run the GUI (in another terminal)
cargo run --bin asus-armoury-gui
```

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues and solutions.

### Quick Checks

1. **Check if asus-nb-wmi module is loaded:**
   ```bash
   lsmod | grep asus
   ```

2. **Check hardware capabilities:**
   ```bash
   ls -la /sys/devices/platform/asus-nb-wmi/
   ```

3. **Check daemon status:**
   ```bash
   systemctl status asus-armoury-daemon
   ```

## Related Projects

- [asusctl](https://gitlab.com/asus-linux/asusctl) - CLI tool for ASUS laptops
- [supergfxctl](https://gitlab.com/asus-linux/supergfxctl) - GPU switching utility
- [asus-linux](https://asus-linux.org/) - ASUS Linux community

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- The [asus-linux](https://asus-linux.org/) community for their excellent work on Linux support for ASUS laptops
- The GTK and GNOME teams for libadwaita
- All contributors to this project