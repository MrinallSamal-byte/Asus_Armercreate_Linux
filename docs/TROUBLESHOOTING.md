# Troubleshooting Guide

This guide helps resolve common issues with ASUS Armoury Crate Linux.

## Quick Diagnostics

Run these commands to gather diagnostic information:

```bash
# Check hardware detection
asus-armoury-daemon --detect

# Check daemon status
systemctl status asus-armoury-daemon

# View daemon logs
journalctl -u asus-armoury-daemon -b

# Check ASUS WMI module
lsmod | grep asus

# Check sysfs entries
ls -la /sys/devices/platform/asus-nb-wmi/
```

## Common Issues

### Application Won't Start

**Symptom**: GUI doesn't launch or crashes immediately

**Solutions**:

1. Check GTK4/libadwaita is installed:
   ```bash
   python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1')"
   ```

2. Run from terminal to see errors:
   ```bash
   asus-armoury-gui
   ```

3. Check for missing dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
   
   # Fedora
   sudo dnf install python3-gobject gtk4 libadwaita
   ```

### "Not an ASUS System"

**Symptom**: Hardware detection shows "Not an ASUS system"

**Solutions**:

1. Check DMI information:
   ```bash
   cat /sys/class/dmi/id/sys_vendor
   # Should contain "ASUSTeK" or "ASUS"
   ```

2. If running in a VM, this is expected behavior

3. Check for custom BIOS that may have altered vendor strings

### No Performance Modes

**Symptom**: Can't change between Silent/Balanced/Turbo modes

**Solutions**:

1. Check for throttle policy support:
   ```bash
   cat /sys/devices/platform/asus-nb-wmi/throttle_thermal_policy
   ```

2. Try loading the ASUS WMI module:
   ```bash
   sudo modprobe asus-nb-wmi
   ```

3. Check if asusctl is available as fallback:
   ```bash
   which asusctl
   asusctl profile -p
   ```

4. Some older models may not support this feature

### Fan Control Not Working

**Symptom**: Can't read or set fan speeds

**Solutions**:

1. Check hwmon sensors:
   ```bash
   sensors
   ls /sys/class/hwmon/
   ```

2. Look for ASUS fan control:
   ```bash
   for hwmon in /sys/class/hwmon/hwmon*; do
       name=$(cat $hwmon/name 2>/dev/null)
       echo "$hwmon: $name"
   done
   ```

3. Some models require the faustus driver:
   ```bash
   # Check if faustus is loaded
   lsmod | grep faustus
   
   # Install faustus (Arch AUR)
   yay -S faustus-dkms
   ```

4. Ensure you're in the asus-armoury group:
   ```bash
   groups $USER | grep asus-armoury
   ```

### RGB Keyboard Not Responding

**Symptom**: Can't change keyboard lighting

**Solutions**:

1. Check for RGB control paths:
   ```bash
   ls /sys/devices/platform/asus-nb-wmi/kbd_rgb*
   ```

2. Install asusctl for RGB support:
   ```bash
   # Check asusctl LED mode support
   asusctl led-mode -s
   ```

3. Try OpenRGB as alternative:
   ```bash
   # Install OpenRGB
   sudo apt install openrgb  # or equivalent
   
   # Detect devices
   openrgb --list-devices
   ```

4. Some keyboard RGB is controlled via USB HID:
   ```bash
   lsusb | grep ASUS
   ```

### Battery Charge Limit Not Working

**Symptom**: Can't set charge limit

**Solutions**:

1. Check for charge limit support:
   ```bash
   cat /sys/class/power_supply/BAT0/charge_control_end_threshold
   # or
   cat /sys/class/power_supply/BAT1/charge_control_end_threshold
   ```

2. Test write permissions:
   ```bash
   # As root
   echo 80 | sudo tee /sys/class/power_supply/BAT0/charge_control_end_threshold
   ```

3. Older kernels (< 5.4) may not support this feature

### GPU Switching Fails

**Symptom**: Can't switch between integrated and dedicated GPU

**Solutions**:

1. Check GPU MUX support:
   ```bash
   cat /sys/devices/platform/asus-nb-wmi/gpu_mux_mode
   ```

2. Install supergfxctl:
   ```bash
   # Check GPU mode
   supergfxctl -g
   
   # Switch mode
   supergfxctl -m hybrid
   ```

3. GPU switching may require a reboot on some models

### Permission Denied Errors

**Symptom**: Various operations fail with permission errors

**Solutions**:

1. Add user to asus-armoury group:
   ```bash
   sudo usermod -aG asus-armoury $USER
   # Log out and back in
   ```

2. Check udev rules are installed:
   ```bash
   cat /etc/udev/rules.d/99-asus-armoury.rules
   ```

3. Reload udev rules:
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

4. Ensure daemon is running as root:
   ```bash
   ps aux | grep asus-armoury
   ```

### Daemon Won't Start

**Symptom**: systemd service fails to start

**Solutions**:

1. Check service logs:
   ```bash
   journalctl -u asus-armoury-daemon -b --no-pager
   ```

2. Try running manually:
   ```bash
   sudo asus-armoury-daemon --debug
   ```

3. Check Python is available:
   ```bash
   which python3
   python3 --version
   ```

4. Verify installation:
   ```bash
   pip3 show asus-armoury-crate
   ```

## Debug Mode

Run the daemon with debug output:

```bash
sudo asus-armoury-daemon --debug
```

This will show:
- Detailed hardware detection
- All sysfs paths being accessed
- D-Bus communication logs
- Error details

## Collecting Logs for Bug Reports

When reporting issues, please include:

```bash
# System information
uname -a
cat /etc/os-release
cat /sys/class/dmi/id/product_name

# Hardware detection
asus-armoury-daemon --detect 2>&1

# Kernel modules
lsmod | grep -E "(asus|wmi)"

# sysfs entries
ls -la /sys/devices/platform/asus-nb-wmi/ 2>&1

# Daemon logs
journalctl -u asus-armoury-daemon -b --no-pager

# Sensors
sensors 2>&1
```

## Getting Help

If you can't resolve your issue:

1. Search existing [GitHub issues](https://github.com/asus-armoury-linux/asus-armoury-crate/issues)
2. Check the [ASUS Linux community](https://asus-linux.org/)
3. Open a new issue with diagnostic information
