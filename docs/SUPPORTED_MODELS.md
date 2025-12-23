# Supported ASUS Laptop Models

This document lists ASUS laptop models that are known to work with ASUS Armoury Crate Linux, along with their supported features.

## Overview

ASUS Armoury Crate Linux requires the `asus-nb-wmi` or `asus-wmi` kernel module to function. Most modern ASUS laptops (2018+) with these modules should have at least partial support.

## Feature Support Legend

- ✅ Fully Supported
- ⚠️ Partially Supported
- ❌ Not Supported
- ❓ Untested

## ROG Series

### ROG Zephyrus

| Model | Performance Modes | GPU Switching | Fan Control | RGB Keyboard | Battery Limit | Notes |
|-------|------------------|---------------|-------------|--------------|---------------|-------|
| G14 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ | Full support with supergfxctl |
| G15 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ | Full support with supergfxctl |
| G16 (2023-2024) | ✅ | ✅ | ✅ | ✅ | ✅ | Full support |
| M16 (2022-2024) | ✅ | ✅ | ⚠️ | ✅ | ✅ | Fan curves may be limited |
| Duo 15/16 | ✅ | ✅ | ⚠️ | ✅ | ✅ | ScreenPad Plus not supported |

### ROG Strix

| Model | Performance Modes | GPU Switching | Fan Control | RGB Keyboard | Battery Limit | Notes |
|-------|------------------|---------------|-------------|--------------|---------------|-------|
| G15/G17 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ | Full support |
| SCAR 15/17 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ | Per-key RGB supported |
| G513/G713 Series | ✅ | ✅ | ✅ | ✅ | ✅ | Full support |

### ROG Flow

| Model | Performance Modes | GPU Switching | Fan Control | RGB Keyboard | Battery Limit | Notes |
|-------|------------------|---------------|-------------|--------------|---------------|-------|
| X13 (2021-2024) | ✅ | ✅ | ✅ | ✅ | ✅ | Full support |
| X16 (2022-2024) | ✅ | ✅ | ✅ | ✅ | ✅ | Full support |
| Z13 (2022-2024) | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | Tablet form factor, limited fan control |

## TUF Gaming Series

### TUF Gaming A-Series (AMD)

| Model | Performance Modes | GPU Switching | Fan Control | RGB Keyboard | Battery Limit | Notes |
|-------|------------------|---------------|-------------|--------------|---------------|-------|
| A15 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ | Full support |
| A17 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ | Full support |
| FA506/FA507 | ✅ | ✅ | ✅ | ✅ | ✅ | Full support |

### TUF Gaming F-Series (Intel)

| Model | Performance Modes | GPU Switching | Fan Control | RGB Keyboard | Battery Limit | Notes |
|-------|------------------|---------------|-------------|--------------|---------------|-------|
| F15 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ | Full support |
| F17 (2020-2024) | ✅ | ✅ | ✅ | ✅ | ✅ | Full support |
| FX505/FX506/FX507 | ✅ | ✅ | ✅ | ✅ | ✅ | Full support |

### TUF Dash

| Model | Performance Modes | GPU Switching | Fan Control | RGB Keyboard | Battery Limit | Notes |
|-------|------------------|---------------|-------------|--------------|---------------|-------|
| Dash F15 (2021-2024) | ✅ | ✅ | ✅ | ✅ | ✅ | Full support |

## ZenBook Series

| Model | Performance Modes | GPU Switching | Fan Control | RGB Keyboard | Battery Limit | Notes |
|-------|------------------|---------------|-------------|--------------|---------------|-------|
| ZenBook Pro 14/15 | ✅ | ⚠️ | ⚠️ | ❌ | ✅ | Limited gaming features |
| ZenBook Pro Duo | ✅ | ⚠️ | ⚠️ | ❌ | ✅ | ScreenPad Plus not supported |
| ZenBook 13/14/15 | ✅ | ❌ | ❌ | ❌ | ✅ | Basic support only |

## VivoBook Series

| Model | Performance Modes | GPU Switching | Fan Control | RGB Keyboard | Battery Limit | Notes |
|-------|------------------|---------------|-------------|--------------|---------------|-------|
| VivoBook Pro 14/15/16 | ✅ | ⚠️ | ⚠️ | ❌ | ✅ | Limited gaming features |
| VivoBook S14/S15 | ✅ | ❌ | ❌ | ❌ | ✅ | Basic support only |

## ProArt Series

| Model | Performance Modes | GPU Switching | Fan Control | RGB Keyboard | Battery Limit | Notes |
|-------|------------------|---------------|-------------|--------------|---------------|-------|
| ProArt StudioBook | ✅ | ⚠️ | ⚠️ | ❌ | ✅ | Professional workstation features |
| ProArt Studiobook Pro | ✅ | ⚠️ | ⚠️ | ❌ | ✅ | OLED dial not supported |

## Feature Details

### Performance Modes
- **Requirement**: Kernel 5.11+ with `platform_profile` support
- **Modes**: Silent, Balanced, Performance/Turbo
- **Works on**: Most ASUS laptops with asus-nb-wmi module

### GPU Switching
- **Requirement**: `supergfxctl` installed and configured
- **Modes**: Integrated, Hybrid, Dedicated, Compute
- **Works on**: Laptops with dual GPUs (typically gaming models)
- **Note**: Requires reboot/logout to take effect

### Fan Control
- **Requirement**: Fan curve support in asus-nb-wmi
- **Features**: Auto mode, custom fan curves
- **Works on**: Most ROG and TUF gaming laptops
- **Note**: Some models only support reading fan speeds

### RGB Keyboard
- **Requirement**: asus-nb-wmi LED support or USB HID control
- **Effects**: Static, Breathing, Rainbow, Wave, Spectrum, Reactive
- **Per-key RGB**: Only on select ROG models (Strix SCAR, some Zephyrus)
- **Works on**: Most gaming laptops, not on office/creator models

### Battery Charge Limit
- **Requirement**: `charge_control_end_threshold` support
- **Limits**: 60%, 80%, 100%
- **Works on**: Most modern ASUS laptops (2019+)
- **Note**: Helps extend battery lifespan

## Kernel Requirements

### Minimum Requirements
- Linux kernel 5.11+ (for platform_profile)
- `asus-nb-wmi` or `asus-wmi` module loaded

### Recommended
- Linux kernel 5.17+ (improved ASUS support)
- Latest kernel for newest models

## Checking Your Hardware Support

### 1. Check if asus-nb-wmi is loaded
```bash
lsmod | grep asus
```

### 2. Check platform profile support
```bash
cat /sys/firmware/acpi/platform_profile_choices
```

### 3. Check fan control
```bash
ls /sys/devices/platform/asus-nb-wmi/fan_curve*
```

### 4. Check RGB support
```bash
ls /sys/class/leds/ | grep asus
```

### 5. Check battery limit
```bash
cat /sys/class/power_supply/BAT0/charge_control_end_threshold
```

## Reporting Compatibility

If your ASUS laptop works or doesn't work with this software, please open an issue with:

1. Laptop model (exact model number from `sudo dmidecode -t system`)
2. Output of `lsmod | grep asus`
3. Output of `ls -la /sys/devices/platform/asus-nb-wmi/`
4. What features work and what don't

This helps us maintain this compatibility list and improve support.

## Known Issues

### Models with Limited Support
- **Older models (pre-2018)**: May lack WMI interface, limited features
- **Chromebooks**: Different hardware interface, not supported
- **Models with proprietary controllers**: Some RGB and fan features may not work

### Common Problems
- **Fan curves not applying**: Some models require specific kernel parameters
- **RGB not working**: May need USB HID support or different interface
- **GPU switching issues**: Ensure supergfxctl is properly configured

## Getting Help

For support with your specific model:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Visit [asus-linux.org](https://asus-linux.org/) for community support
3. Open an issue on GitHub with your hardware details

## Contributing

Know a model that works? Please submit a pull request to update this list!
