"""
Helper utilities for hardware interaction.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Union, List


def read_sysfs(path: str) -> Optional[str]:
    """
    Read a value from a sysfs file.
    
    Args:
        path: Path to the sysfs file
        
    Returns:
        File contents as string, or None if read fails
    """
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except (IOError, PermissionError):
        return None


def write_sysfs(path: str, value: Union[str, int]) -> bool:
    """
    Write a value to a sysfs file.
    
    Args:
        path: Path to the sysfs file
        value: Value to write
        
    Returns:
        True if write succeeded, False otherwise
    """
    try:
        with open(path, 'w') as f:
            f.write(str(value))
        return True
    except (IOError, PermissionError):
        return False


def check_permissions(path: str) -> dict:
    """
    Check permissions for a file or directory.
    
    Args:
        path: Path to check
        
    Returns:
        Dictionary with permission information
    """
    result = {
        'exists': False,
        'readable': False,
        'writable': False,
        'executable': False,
        'owner': None,
        'group': None,
        'mode': None
    }
    
    try:
        p = Path(path)
        if p.exists():
            result['exists'] = True
            result['readable'] = os.access(path, os.R_OK)
            result['writable'] = os.access(path, os.W_OK)
            result['executable'] = os.access(path, os.X_OK)
            
            stat_info = p.stat()
            result['owner'] = stat_info.st_uid
            result['group'] = stat_info.st_gid
            result['mode'] = oct(stat_info.st_mode)[-3:]
    except Exception:
        pass
    
    return result


def run_command(
    cmd: List[str],
    check: bool = False,
    capture_output: bool = True,
    timeout: Optional[int] = None
) -> tuple:
    """
    Run a shell command safely.
    
    Args:
        cmd: Command and arguments as list
        check: Raise exception on non-zero exit
        capture_output: Capture stdout and stderr
        timeout: Command timeout in seconds
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        return (result.returncode, result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        return (-1, "", "Command timed out")
    except subprocess.CalledProcessError as e:
        return (e.returncode, e.stdout or "", e.stderr or "")
    except FileNotFoundError:
        return (-1, "", f"Command not found: {cmd[0]}")


def is_root() -> bool:
    """Check if running as root."""
    return os.geteuid() == 0


def find_asus_wmi_paths() -> dict:
    """
    Find ASUS WMI sysfs paths.
    
    Returns:
        Dictionary of available ASUS WMI paths
    """
    paths = {
        'platform': None,
        'throttle_thermal_policy': None,
        'charge_control_end_threshold': None,
        'kbd_rgb_mode': None,
        'gpu_mux_mode': None,
        'dgpu_disable': None,
        'egpu_enable': None,
        'panel_od': None,
    }
    
    # ASUS WMI platform paths
    asus_platform_paths = [
        '/sys/devices/platform/asus-nb-wmi',
        '/sys/devices/platform/asus_nb_wmi',
        '/sys/bus/platform/devices/asus-nb-wmi'
    ]
    
    for path in asus_platform_paths:
        if os.path.exists(path):
            paths['platform'] = path
            
            # Check for available attributes
            attrs = [
                ('throttle_thermal_policy', 'throttle_thermal_policy'),
                ('charge_control_end_threshold', 'charge_control_end_threshold'),
                ('kbd_rgb_mode', 'kbd_rgb_mode'),
                ('gpu_mux_mode', 'gpu_mux_mode'),
                ('dgpu_disable', 'dgpu_disable'),
                ('egpu_enable', 'egpu_enable'),
                ('panel_od', 'panel_od'),
            ]
            
            for key, attr in attrs:
                attr_path = os.path.join(path, attr)
                if os.path.exists(attr_path):
                    paths[key] = attr_path
            
            break
    
    # Alternative paths for battery charge limit
    if not paths['charge_control_end_threshold']:
        alt_battery_paths = [
            '/sys/class/power_supply/BAT0/charge_control_end_threshold',
            '/sys/class/power_supply/BAT1/charge_control_end_threshold',
            '/sys/class/power_supply/BATC/charge_control_end_threshold'
        ]
        for path in alt_battery_paths:
            if os.path.exists(path):
                paths['charge_control_end_threshold'] = path
                break
    
    return paths


def get_dmi_info() -> dict:
    """
    Get DMI system information.
    
    Returns:
        Dictionary with DMI information
    """
    dmi_info = {
        'vendor': None,
        'product_name': None,
        'product_family': None,
        'board_name': None,
        'board_vendor': None,
        'bios_version': None
    }
    
    dmi_paths = {
        'vendor': '/sys/class/dmi/id/sys_vendor',
        'product_name': '/sys/class/dmi/id/product_name',
        'product_family': '/sys/class/dmi/id/product_family',
        'board_name': '/sys/class/dmi/id/board_name',
        'board_vendor': '/sys/class/dmi/id/board_vendor',
        'bios_version': '/sys/class/dmi/id/bios_version'
    }
    
    for key, path in dmi_paths.items():
        value = read_sysfs(path)
        if value:
            dmi_info[key] = value
    
    return dmi_info


def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))
