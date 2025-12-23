# Contributing to ASUS Armoury Crate Linux

Thank you for your interest in contributing to ASUS Armoury Crate Linux! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## Getting Started

### Prerequisites

- Rust 1.70 or later
- GTK4 and libadwaita development libraries
- An ASUS laptop (for testing hardware features)

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/MrinallSamal-byte/Asus_Armercreate_Linux.git
cd Asus_Armercreate_Linux

# Install Rust dependencies
cargo build

# Run tests
cargo test

# Run clippy lints
cargo clippy

# Format code
cargo fmt
```

## Project Structure

```
├── src/
│   ├── common/          # Shared types and utilities
│   │   └── src/
│   │       ├── types.rs       # Data structures
│   │       ├── error.rs       # Error types
│   │       └── dbus_interface.rs
│   ├── daemon/          # Background service
│   │   └── src/
│   │       ├── main.rs        # Daemon entry point
│   │       ├── config.rs      # Configuration handling
│   │       ├── hardware/      # Hardware abstraction
│   │       ├── dbus_server.rs # D-Bus service
│   │       └── profiles.rs    # Profile management
│   └── gui/             # GTK4 application
│       └── src/
│           ├── main.rs        # GUI entry point
│           ├── window.rs      # Main window
│           ├── dbus_client.rs # D-Bus client
│           └── widgets/       # Custom widgets
├── systemd/             # Systemd service files
├── polkit/              # Polkit policy files
├── udev/                # Udev rules
├── data/                # Desktop entries, D-Bus config
├── docs/                # Documentation
└── scripts/             # Installation scripts
```

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Use the bug report template
3. Include:
   - System information (distro, kernel version, laptop model)
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs if applicable

### Suggesting Features

1. Check existing issues and discussions
2. Describe the feature and its use case
3. Consider implementation complexity

### Submitting Code

1. **Fork the repository**

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style guidelines below
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   cargo build
   cargo test
   cargo clippy
   cargo fmt --check
   ```

5. **Commit your changes**
   ```bash
   git commit -m "feat: add new feature description"
   ```
   Follow [Conventional Commits](https://www.conventionalcommits.org/) format:
   - `feat:` New features
   - `fix:` Bug fixes
   - `docs:` Documentation changes
   - `refactor:` Code refactoring
   - `test:` Test additions/changes
   - `chore:` Maintenance tasks

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style Guidelines

### Rust

- Follow [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- Use `cargo fmt` for formatting
- Use `cargo clippy` and fix warnings
- Document public APIs with doc comments
- Use meaningful variable and function names

```rust
/// Sets the performance mode for the CPU.
///
/// # Arguments
///
/// * `mode` - The target performance mode
///
/// # Errors
///
/// Returns an error if the hardware doesn't support the requested mode.
pub fn set_performance_mode(&mut self, mode: PerformanceMode) -> ArmouryResult<()> {
    // Implementation
}
```

### GTK/UI Code

- Follow GNOME Human Interface Guidelines
- Use libadwaita widgets where appropriate
- Support dark mode
- Ensure accessibility (proper labels, keyboard navigation)

## Testing

### Unit Tests

Add tests in the same file using `#[cfg(test)]` module:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rgb_color_from_hex() {
        let color = RgbColor::from_hex("#FF0000").unwrap();
        assert_eq!(color.r, 255);
        assert_eq!(color.g, 0);
        assert_eq!(color.b, 0);
    }
}
```

### Integration Tests

Place in `tests/` directory. Test daemon/GUI interaction, D-Bus communication, etc.

### Hardware Testing

If you have access to ASUS hardware:
1. Test all supported features
2. Verify graceful handling of unsupported features
3. Check for edge cases (missing sysfs nodes, permission errors)

## Adding Hardware Support

### Adding a New Feature

1. Add types to `src/common/src/types.rs`
2. Add sysfs paths/logic to `src/daemon/src/hardware/sysfs.rs`
3. Expose via D-Bus in `src/daemon/src/dbus_server.rs`
4. Add client methods in `src/gui/src/dbus_client.rs`
5. Add UI components as needed

### Supporting a New Laptop Model

1. Check what sysfs nodes exist on the hardware
2. Document findings in an issue or PR
3. Add detection logic if needed
4. Test all features and document results

## Documentation

- Update README.md for user-facing changes
- Update TROUBLESHOOTING.md for new issues/solutions
- Add doc comments to public APIs
- Update supported models list when adding hardware support

## Release Process

1. Version numbers follow [Semantic Versioning](https://semver.org/)
2. Update CHANGELOG.md
3. Update version in Cargo.toml files
4. Create a git tag
5. Build release binaries

## Getting Help

- Open a GitHub Discussion for questions
- Join the asus-linux community for general ASUS Linux support
- Ping maintainers in issues if no response after a week

## License

By contributing, you agree that your contributions will be licensed under the GPL-3.0 license.
