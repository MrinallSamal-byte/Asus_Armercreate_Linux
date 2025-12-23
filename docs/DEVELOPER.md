# Developer Guide

This guide is for developers who want to build, modify, or contribute to ASUS Armoury Crate Linux.

## Quick Start

### Prerequisites

- **Rust**: 1.70 or later
- **System Libraries**:
  - GTK4 development libraries
  - libadwaita development libraries
  - D-Bus development libraries
  
### Installing Dependencies

#### Ubuntu/Debian
```bash
sudo apt install \
    build-essential \
    pkg-config \
    libgtk-4-dev \
    libadwaita-1-dev \
    libdbus-1-dev
```

#### Fedora
```bash
sudo dnf install \
    gcc \
    pkg-config \
    gtk4-devel \
    libadwaita-devel \
    dbus-devel
```

#### Arch Linux
```bash
sudo pacman -S \
    base-devel \
    gtk4 \
    libadwaita \
    dbus
```

### Building

```bash
# Clone the repository
git clone https://github.com/MrinallSamal-byte/Asus_Armercreate_Linux.git
cd Asus_Armercreate_Linux

# Build in debug mode
cargo build

# Build in release mode
cargo build --release

# Run tests
cargo test

# Run linter
cargo clippy

# Format code
cargo fmt
```

### Running from Source

#### Run the Daemon (requires root)
```bash
# In one terminal
sudo target/debug/asus-armoury-daemon
```

#### Run the GUI
```bash
# In another terminal
target/debug/asus-armoury-gui
```

### Development Workflow

1. **Make Changes**: Edit source files in `src/`
2. **Check Syntax**: Run `cargo check`
3. **Test Changes**: Run `cargo test`
4. **Lint Code**: Run `cargo clippy`
5. **Format Code**: Run `cargo fmt`
6. **Build**: Run `cargo build`
7. **Test Manually**: Run daemon and GUI

## Project Structure

```
Asus_Armercreate_Linux/
├── src/
│   ├── common/              # Shared types and utilities
│   │   ├── src/
│   │   │   ├── types.rs     # Data structures (Profile, RGB, etc.)
│   │   │   ├── error.rs     # Error types
│   │   │   └── dbus_interface.rs  # D-Bus constants
│   │   └── Cargo.toml
│   │
│   ├── daemon/              # Background service
│   │   ├── src/
│   │   │   ├── main.rs              # Entry point
│   │   │   ├── config.rs            # Configuration management
│   │   │   ├── profiles.rs          # Profile management
│   │   │   ├── dbus_server.rs       # D-Bus service
│   │   │   └── hardware/            # Hardware abstraction
│   │   │       ├── mod.rs           # Hardware controller
│   │   │       ├── sysfs.rs         # Linux sysfs interface
│   │   │       └── asusctl.rs       # asusctl integration
│   │   └── Cargo.toml
│   │
│   └── gui/                 # GTK4 GUI application
│       ├── src/
│       │   ├── main.rs              # Entry point
│       │   ├── window.rs            # Main window
│       │   ├── dbus_client.rs       # D-Bus client
│       │   └── widgets/             # Custom widgets
│       │       ├── mod.rs
│       │       ├── fan_curve.rs     # Fan curve editor
│       │       └── rgb_picker.rs    # RGB color picker
│       └── Cargo.toml
│
├── systemd/                 # Systemd service files
├── polkit/                  # Polkit policy files
├── udev/                    # Udev rules
├── data/                    # Desktop entries, D-Bus config
├── docs/                    # Documentation
│   ├── CONTRIBUTING.md
│   ├── TROUBLESHOOTING.md
│   └── SUPPORTED_MODELS.md
├── scripts/                 # Installation scripts
│   ├── install.sh
│   ├── uninstall.sh
│   └── build-test.sh
├── Cargo.toml               # Workspace configuration
└── README.md
```

## Architecture

### Component Communication

```
┌─────────────────────────────────────────┐
│         GUI (asus-armoury-gui)          │
│         GTK4 + libadwaita               │
└──────────────┬──────────────────────────┘
               │ D-Bus IPC
               │
┌──────────────▼──────────────────────────┐
│       Daemon (asus-armoury-daemon)       │
│       Rust async + tokio                 │
├──────────────────────────────────────────┤
│  Hardware    │  Profile   │  Config      │
│  Controller  │  Manager   │  Manager     │
└──────┬───────┴────────────┴──────────────┘
       │
┌──────▼───────────────────────────────────┐
│    Linux Kernel Interfaces               │
│  sysfs / platform_profile / hwmon        │
└──────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: GUI and daemon are separate processes
2. **Safety First**: Never exceed safe hardware limits
3. **Graceful Degradation**: Features work independently
4. **User Privacy**: No telemetry, all data stays local
5. **Linux Native**: Uses standard Linux interfaces

## Adding New Features

### Adding a New Hardware Feature

1. **Add Type** to `src/common/src/types.rs`
   ```rust
   pub struct NewFeature {
       pub setting: String,
   }
   ```

2. **Add Sysfs Support** to `src/daemon/src/hardware/sysfs.rs`
   ```rust
   pub fn read_new_feature(&self) -> Option<NewFeature> {
       // Read from sysfs
   }
   
   pub fn write_new_feature(&self, feature: &NewFeature) -> ArmouryResult<()> {
       // Write to sysfs
   }
   ```

3. **Add to Hardware Controller** in `src/daemon/src/hardware/mod.rs`
   ```rust
   pub fn get_new_feature(&self) -> NewFeature {
       self.sysfs.read_new_feature().unwrap_or_default()
   }
   
   pub fn set_new_feature(&mut self, feature: &NewFeature) -> ArmouryResult<()> {
       self.sysfs.write_new_feature(feature)
   }
   ```

4. **Expose via D-Bus** in `src/daemon/src/dbus_server.rs`
   ```rust
   async fn get_new_feature(&self) -> String {
       let state = self.state.read().await;
       serde_json::to_string(&state.hardware.get_new_feature())
           .unwrap_or_default()
   }
   
   async fn set_new_feature(&self, feature_json: &str) -> bool {
       // Parse and set feature
   }
   ```

5. **Add Client Method** in `src/gui/src/dbus_client.rs`
   ```rust
   pub async fn get_new_feature(&self) -> Option<NewFeature> {
       // Call D-Bus method
   }
   ```

6. **Add UI** in `src/gui/src/window.rs` or new widget

### Testing Hardware Features

Always test on real hardware when adding features that interact with hardware:

1. Check if sysfs nodes exist
2. Test reading current values
3. Test writing values (carefully!)
4. Verify changes take effect
5. Test error handling
6. Document hardware requirements

## Debugging

### Enable Debug Logging

#### Daemon
```bash
RUST_LOG=debug sudo target/debug/asus-armoury-daemon
```

#### GUI
```bash
RUST_LOG=debug target/debug/asus-armoury-gui
```

### View D-Bus Traffic

```bash
# Monitor D-Bus messages
dbus-monitor --system "sender='org.asuslinux.Armoury'"
```

### Check sysfs Values

```bash
# List available hardware interfaces
ls -la /sys/devices/platform/asus-nb-wmi/

# Read current platform profile
cat /sys/firmware/acpi/platform_profile

# Check fan sensors
find /sys/class/hwmon -name "fan*_input"
```

## Testing

### Unit Tests

```bash
# Run all tests
cargo test

# Run tests for a specific module
cargo test --package asus-armoury-daemon

# Run a specific test
cargo test test_rgb_color_from_hex
```

### Integration Testing

1. Build and install the software
2. Start the daemon: `sudo systemctl start asus-armoury-daemon`
3. Check status: `sudo systemctl status asus-armoury-daemon`
4. View logs: `sudo journalctl -u asus-armoury-daemon -f`
5. Launch GUI and test features
6. Monitor D-Bus with `dbus-monitor`

## Code Style

### Rust Guidelines

- Follow [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- Use `cargo fmt` for consistent formatting
- Run `cargo clippy` and fix all warnings
- Document public APIs with doc comments
- Use meaningful variable and function names

### GTK/UI Guidelines

- Follow [GNOME Human Interface Guidelines](https://developer.gnome.org/hig/)
- Use libadwaita widgets where appropriate
- Ensure dark mode compatibility
- Add tooltips for complex features
- Support keyboard navigation

## Contributing

See [CONTRIBUTING.md](../docs/CONTRIBUTING.md) for contribution guidelines.

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

Example:
```
feat: add support for per-key RGB control

- Detect per-key RGB capable keyboards
- Add key mapping configuration
- Update UI with per-key color picker
```

## Resources

- [asus-linux.org](https://asus-linux.org/) - ASUS Linux community
- [Rust Book](https://doc.rust-lang.org/book/)
- [GTK4 Documentation](https://docs.gtk.org/gtk4/)
- [libadwaita Documentation](https://gnome.pages.gitlab.gnome.org/libadwaita/)
- [D-Bus Specification](https://dbus.freedesktop.org/doc/dbus-specification.html)

## Getting Help

- Open an issue on GitHub
- Ask in GitHub Discussions
- Join the asus-linux community

## License

GPL-3.0 - See [LICENSE](../LICENSE) for details
