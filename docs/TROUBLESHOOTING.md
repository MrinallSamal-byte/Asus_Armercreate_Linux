# Troubleshooting Guide

This guide covers common issues and their solutions when using ASUS Armoury Crate Linux.

## Prerequisites Check

Before troubleshooting specific issues, verify your system meets the requirements:

### 1. Kernel Module Check

```bash
# Check if asus-nb-wmi is loaded
lsmod | grep asus
```

Expected output should include `asus_nb_wmi` or `asus_wmi`.

If not loaded:
```bash
sudo modprobe asus-nb-wmi
```

### 2. Check Available Hardware Features

```bash
# List ASUS WMI sysfs interface
ls -la /sys/devices/platform/asus-nb-wmi/
```

### 3. Check Platform Profile Support

```bash
# Check if platform profile is available
cat /sys/firmware/acpi/platform_profile_choices
cat /sys/firmware/acpi/platform_profile
```

## Common Issues

### Daemon Won't Start

**Symptoms**: `systemctl status asus-armoury-daemon` shows failed state.

**Solutions**:

1. Check D-Bus configuration:
   ```bash
   ls -la /etc/dbus-1/system.d/org.asuslinux.Armoury.conf
   ```

2. Check permissions on sysfs:
   ```bash
   ls -la /sys/devices/platform/asus-nb-wmi/
   ```

3. View daemon logs:
   ```bash
   journalctl -u asus-armoury-daemon -f
   ```

### Performance Mode Not Changing

**Symptoms**: Setting performance mode has no effect.

**Possible causes**:
- Platform profile not supported by hardware
- Kernel too old
- Missing permissions

**Solutions**:

1. Check if platform profile exists:
   ```bash
   cat /sys/firmware/acpi/platform_profile
   ```

2. Try setting manually (as root):
   ```bash
   echo "performance" | sudo tee /sys/firmware/acpi/platform_profile
   ```

3. Check available choices:
   ```bash
   cat /sys/firmware/acpi/platform_profile_choices
   ```

### Fan Control Not Working

**Symptoms**: Fan speeds don't change, custom curves not applied.

**Possible causes**:
- Hardware doesn't support fan curve control
- Fan curve feature not exposed in sysfs

**Solutions**:

1. Check if fan curve control exists:
   ```bash
   ls -la /sys/devices/platform/asus-nb-wmi/fan_curve*
   ```

2. Check hwmon for fan sensors:
   ```bash
   find /sys/class/hwmon -name "fan*_input"
   ```

3. Try using asusctl instead (if installed):
   ```bash
   asusctl fan-curve --help
   ```

### Battery Charge Limit Not Working

**Symptoms**: Battery charges to 100% despite limit setting.

**Solutions**:

1. Check if charge limit is supported:
   ```bash
   cat /sys/class/power_supply/BAT0/charge_control_end_threshold
   # Or BAT1 on some systems
   cat /sys/class/power_supply/BAT1/charge_control_end_threshold
   ```

2. Set manually (as root):
   ```bash
   echo 80 | sudo tee /sys/class/power_supply/BAT0/charge_control_end_threshold
   ```

### RGB Keyboard Not Responding

**Symptoms**: Keyboard lighting doesn't change.

**Possible causes**:
- Keyboard uses USB HID instead of WMI
- Different RGB controller type

**Solutions**:

1. Check keyboard backlight:
   ```bash
   ls -la /sys/class/leds/ | grep asus
   ```

2. Try setting brightness manually:
   ```bash
   echo 2 | sudo tee /sys/class/leds/asus::kbd_backlight/brightness
   ```

3. Check if asusctl LED mode works:
   ```bash
   asusctl led-mode -l
   asusctl led-mode -s static
   ```

### GUI Won't Launch

**Symptoms**: Application crashes or shows blank window.

**Solutions**:

1. Check GTK4/libadwaita are installed:
   ```bash
   pkg-config --modversion gtk4
   pkg-config --modversion libadwaita-1
   ```

2. Run from terminal to see errors:
   ```bash
   asus-armoury-gui 2>&1
   ```

3. Check for Wayland issues (try with X11):
   ```bash
   GDK_BACKEND=x11 asus-armoury-gui
   ```

### GUI Can't Connect to Daemon

**Symptoms**: GUI shows "Service not running" or can't control hardware.

**Solutions**:

1. Verify daemon is running:
   ```bash
   systemctl status asus-armoury-daemon
   ```

2. Check D-Bus connection:
   ```bash
   busctl list | grep asuslinux
   ```

3. Test D-Bus interface:
   ```bash
   busctl call org.asuslinux.Armoury /org/asuslinux/Armoury org.asuslinux.Armoury Version
   ```

## GPU Mode Switching Issues

### Using supergfxctl

GPU mode switching requires supergfxctl:

```bash
# Check if installed
which supergfxctl

# Check current mode
supergfxctl -g

# Switch mode
supergfxctl -m Hybrid
```

### Common GPU Issues

1. **NVIDIA driver not loaded after switch**: Reboot may be required
2. **Display issues after switch**: Log out and back in
3. **Mode stuck**: Check supergfxctl status and logs

## Temperature/Sensor Issues

### No Temperature Readings

```bash
# List all thermal zones
ls /sys/class/thermal/

# Check hwmon sensors
sensors
```

### Incorrect Temperatures

Some sensors may report wrong values. Cross-reference with:
```bash
# CPU temperature
cat /sys/class/thermal/thermal_zone*/temp

# GPU temperature (NVIDIA)
nvidia-smi --query-gpu=temperature.gpu --format=csv
```

## Getting Help

If you're still having issues:

1. **Collect system information**:
   ```bash
   sudo dmidecode -t system | grep -E "Manufacturer|Product"
   uname -a
   cat /etc/os-release
   lsmod | grep asus
   ```

2. **Enable debug logging**:
   Edit daemon config and set `"debug": true`

3. **Open an issue** on GitHub with:
   - System info from step 1
   - Exact error messages
   - Steps to reproduce
   - Daemon logs (`journalctl -u asus-armoury-daemon`)

## Kernel Boot Parameters

Some hardware may need kernel parameters. Add to GRUB config:

```bash
# For some ASUS laptops with detection issues
asus_nb_wmi.wapf=1

# For fan curve issues
asus_nb_wmi.fan_boost_mode_mask=1
```

## Related Resources

- [asus-linux Wiki](https://asus-linux.org/wiki/)
- [Arch Linux ASUS Wiki](https://wiki.archlinux.org/title/ASUS)
- [Linux Kernel ASUS WMI Documentation](https://www.kernel.org/doc/html/latest/admin-guide/laptops/asus-nb-wmi.html)
