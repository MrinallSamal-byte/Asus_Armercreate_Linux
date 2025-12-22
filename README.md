# ASUS Armoury Crate Linux

A Linux desktop application that provides the same functionality as ASUS Armoury Crate on Windows, specifically designed for ASUS laptops (especially TUF / ROG series). This software allows ASUS users on Linux to fully control hardware and performance features that are otherwise only available on Windows.

![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![GTK](https://img.shields.io/badge/GTK-4.0-orange.svg)

## Features

### Hardware & Performance Control
- **CPU Performance Modes**: Silent / Balanced / Turbo / Manual
- **GPU Mode Switching**: Integrated / Dedicated / Hybrid (where supported)
- **Fan Speed Control**: Automatic and manual fan curves
- **Temperature Monitoring**: Real-time CPU and GPU temperature display
- **Power Limits**: Thermal policy control

### ASUS-Specific Features
- **RGB Keyboard Control**: Static, breathing, rainbow, and custom colors
- **Battery Charge Limit**: Set maximum charge level (60%, 80%, 100%)
- **Panel Overdrive**: Display refresh rate control (where supported)
- **Anime Matrix Support**: LED panel control (for supported devices)

### System Integration
- Works on major Linux distributions (Ubuntu, Fedora, Arch)
- D-Bus integration for system-level control
- Polkit rules for privileged operations
- udev rules for hardware access
- Background daemon with GUI frontend

## Screenshots

*Coming soon*

## Installation

### Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/asus-armoury-linux/asus-armoury-crate.git
cd asus-armoury-crate

# Run the installer
sudo ./install.sh
```

### Manual Installation

See the [Installation Guide](docs/INSTALLATION.md) for detailed instructions.

### Dependencies

- Python 3.9+
- GTK4
- libadwaita 1.0+
- PyGObject (python3-gi)
- lm-sensors

**Optional:**
- asusctl (for enhanced ASUS support)
- supergfxctl (for GPU switching)
- OpenRGB (for additional RGB support)

## Usage

### GUI Application

Launch from your application menu or run:
```bash
asus-armoury-gui
```

### Command Line

```bash
# Run hardware detection
asus-armoury-daemon --detect

# Start the daemon manually
sudo asus-armoury-daemon

# With debug output
sudo asus-armoury-daemon --debug
```

### Profiles

The application includes several built-in profiles:

| Profile | CPU Mode | Fan Curve | RGB | Battery Limit |
|---------|----------|-----------|-----|---------------|
| Silent | Silent | Quiet | Off | 60% |
| Balanced | Balanced | Normal | Green | 80% |
| Turbo | Turbo | Aggressive | Rainbow | 100% |
| Gaming | Turbo | Performance | Red Breathing | 100% |

You can create custom profiles combining any settings.

## Supported Models

### Fully Supported
- ASUS ROG Zephyrus G14/G15/G16
- ASUS ROG Strix G15/G17
- ASUS TUF Gaming A15/A17
- ASUS TUF Gaming F15/F17

### Partially Supported
- ASUS ROG Flow X13/Z13
- ASUS VivoBook Pro
- ASUS ZenBook Pro

See [Supported Models](docs/SUPPORTED_MODELS.md) for a complete list.

## Troubleshooting

### Common Issues

**No ASUS hardware detected**
- Ensure you're running on an ASUS laptop
- Check if asus-nb-wmi module is loaded: `lsmod | grep asus`

**Permission denied errors**
- Add your user to the `asus-armoury` group: `sudo usermod -aG asus-armoury $USER`
- Log out and back in for changes to take effect

See [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for more solutions.

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/asus-armoury-linux/asus-armoury-crate.git
cd asus-armoury-crate

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Project Structure

```
asus-armoury-crate/
├── src/
│   ├── backend/           # Hardware control modules
│   │   ├── hardware/      # CPU, fan, RGB, battery controllers
│   │   ├── services/      # D-Bus service, daemon, profiles
│   │   └── utils/         # Logging, config, helpers
│   └── frontend/          # GTK4/libadwaita GUI
│       └── ui/            # Application windows
├── data/                  # Desktop entry, icons, profiles
├── systemd/               # Systemd service file
├── polkit/                # Polkit policy rules
├── udev/                  # udev rules
├── docs/                  # Documentation
└── tests/                 # Test suite
```

See [Contributing Guide](docs/CONTRIBUTING.md) for development instructions.

## Related Projects

- [asusctl](https://gitlab.com/asus-linux/asusctl) - ASUS Linux control daemon
- [supergfxctl](https://gitlab.com/asus-linux/supergfxctl) - GPU switching
- [OpenRGB](https://openrgb.org/) - RGB lighting control

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- The ASUS Linux community for kernel driver development
- asusctl developers for the reference implementation
- All contributors to the Linux kernel ASUS WMI modules