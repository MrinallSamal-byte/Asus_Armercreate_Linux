# Contributing Guide

Thank you for your interest in contributing to ASUS Armoury Crate Linux! This guide will help you get started.

## Ways to Contribute

### 1. Bug Reports

Found a bug? Please open an issue with:
- Your ASUS laptop model
- Linux distribution and version
- Steps to reproduce
- Expected vs actual behavior
- Logs (see Troubleshooting guide)

### 2. Feature Requests

Have an idea? Open an issue describing:
- The feature you'd like
- Use case / why it's needed
- Any implementation ideas

### 3. Code Contributions

Ready to code? Here's how:

## Development Setup

### Prerequisites

- Python 3.9+
- GTK4 and libadwaita
- Git

### Setting Up

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/asus-armoury-crate.git
cd asus-armoury-crate

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_cpu_control.py
```

### Code Style

We use:
- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking

```bash
# Format code
black src/

# Check linting
flake8 src/

# Type checking
mypy src/
```

### Running the Application

```bash
# Run the GUI (without installation)
python -m frontend.ui.application

# Run the daemon in debug mode
sudo python -m backend.services.daemon --debug --session
```

## Project Structure

```
src/
├── backend/
│   ├── hardware/
│   │   ├── detector.py      # Hardware detection
│   │   ├── cpu_control.py   # CPU mode control
│   │   ├── fan_control.py   # Fan speed control
│   │   ├── rgb_control.py   # RGB keyboard control
│   │   ├── battery_control.py # Battery management
│   │   └── thermal_monitor.py # Temperature monitoring
│   ├── services/
│   │   ├── dbus_service.py  # D-Bus interface
│   │   ├── profile_manager.py # Profile management
│   │   └── daemon.py        # Background daemon
│   └── utils/
│       ├── logger.py        # Logging utilities
│       ├── config.py        # Configuration management
│       └── helpers.py       # Helper functions
└── frontend/
    └── ui/
        ├── application.py   # GTK application
        └── main_window.py   # Main window
```

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(rgb): add per-key RGB support
fix(fan): correct PWM calculation for ASUS hwmon
docs: update supported models list
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all tests pass and code is formatted
4. Update documentation if needed
5. Open a PR with clear description
6. Respond to review feedback

## Adding Hardware Support

### Supporting a New Model

1. Check if ASUS WMI provides the necessary interfaces
2. Add model to detection in `detector.py`
3. Test all features on the hardware
4. Update `SUPPORTED_MODELS.md`

### Adding a New Feature

1. Create control module in `backend/hardware/`
2. Add D-Bus interface methods
3. Add GUI controls in frontend
4. Write tests
5. Update documentation

## Testing on Hardware

### Before Submitting

Test on actual ASUS hardware:
- Run hardware detection
- Test each feature you modified
- Check logs for errors
- Verify no regressions

### Testing Without ASUS Hardware

Some testing is possible:
- Unit tests with mocked sysfs
- GUI testing on any system
- Code style/lint checks

## Documentation

Update documentation when:
- Adding new features
- Changing configuration
- Adding supported models
- Changing installation steps

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn

## Questions?

- Open a GitHub discussion
- Check existing issues
- Read the troubleshooting guide

Thank you for contributing!
