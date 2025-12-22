"""
CPU performance mode control for ASUS laptops.
"""

import os
from enum import Enum
from typing import Optional, List

from ..utils.helpers import read_sysfs, write_sysfs, run_command, find_asus_wmi_paths
from ..utils.logger import get_logger


class CPUMode(Enum):
    """CPU performance modes."""
    SILENT = "silent"
    BALANCED = "balanced"
    TURBO = "turbo"
    MANUAL = "manual"


class CPUController:
    """
    Controls CPU performance modes on ASUS laptops.
    
    Supports both direct sysfs control and asusctl integration.
    """
    
    # Throttle thermal policy values
    THERMAL_POLICY = {
        CPUMode.BALANCED: 0,
        CPUMode.TURBO: 1,
        CPUMode.SILENT: 2
    }
    
    def __init__(self):
        """Initialize CPU controller."""
        self.logger = get_logger()
        self._paths = find_asus_wmi_paths()
        self._throttle_path = self._paths.get('throttle_thermal_policy')
        self._use_asusctl = False
        
        # Check if asusctl is available
        if not self._throttle_path:
            ret, _, _ = run_command(['which', 'asusctl'])
            self._use_asusctl = (ret == 0)
        
        self.logger.debug(f"CPU Controller initialized (asusctl: {self._use_asusctl})")
    
    @property
    def is_available(self) -> bool:
        """Check if CPU mode control is available."""
        return bool(self._throttle_path) or self._use_asusctl
    
    def get_current_mode(self) -> Optional[CPUMode]:
        """
        Get the current CPU performance mode.
        
        Returns:
            Current CPUMode or None if unable to determine
        """
        if self._throttle_path:
            value = read_sysfs(self._throttle_path)
            if value is not None:
                try:
                    policy = int(value)
                    for mode, val in self.THERMAL_POLICY.items():
                        if val == policy:
                            return mode
                except ValueError:
                    pass
        
        if self._use_asusctl:
            ret, out, _ = run_command(['asusctl', 'profile', '-p'])
            if ret == 0 and out:
                out_lower = out.lower()
                if 'silent' in out_lower or 'quiet' in out_lower:
                    return CPUMode.SILENT
                elif 'performance' in out_lower or 'turbo' in out_lower:
                    return CPUMode.TURBO
                elif 'balanced' in out_lower:
                    return CPUMode.BALANCED
        
        return None
    
    def set_mode(self, mode: CPUMode) -> bool:
        """
        Set the CPU performance mode.
        
        Args:
            mode: Desired CPUMode
            
        Returns:
            True if mode was set successfully
        """
        if mode == CPUMode.MANUAL:
            self.logger.warning("Manual mode not yet implemented")
            return False
        
        self.logger.info(f"Setting CPU mode to: {mode.value}")
        
        # Try sysfs first
        if self._throttle_path:
            policy = self.THERMAL_POLICY.get(mode)
            if policy is not None:
                if write_sysfs(self._throttle_path, policy):
                    self.logger.info(f"CPU mode set to {mode.value} via sysfs")
                    return True
                else:
                    self.logger.warning("Failed to write to sysfs, trying asusctl")
        
        # Fallback to asusctl
        if self._use_asusctl:
            mode_map = {
                CPUMode.SILENT: 'Quiet',
                CPUMode.BALANCED: 'Balanced', 
                CPUMode.TURBO: 'Performance'
            }
            asusctl_mode = mode_map.get(mode, 'Balanced')
            
            ret, _, err = run_command(['asusctl', 'profile', '-P', asusctl_mode])
            if ret == 0:
                self.logger.info(f"CPU mode set to {mode.value} via asusctl")
                return True
            else:
                self.logger.error(f"Failed to set CPU mode: {err}")
        
        return False
    
    def get_available_modes(self) -> List[CPUMode]:
        """
        Get list of available CPU modes.
        
        Returns:
            List of available CPUMode values
        """
        if not self.is_available:
            return []
        
        # Most ASUS laptops support these three modes
        return [CPUMode.SILENT, CPUMode.BALANCED, CPUMode.TURBO]
    
    def cycle_mode(self) -> Optional[CPUMode]:
        """
        Cycle to the next performance mode.
        
        Returns:
            The new mode, or None if cycling failed
        """
        current = self.get_current_mode()
        modes = self.get_available_modes()
        
        if not current or not modes:
            return None
        
        try:
            current_idx = modes.index(current)
            next_idx = (current_idx + 1) % len(modes)
            next_mode = modes[next_idx]
            
            if self.set_mode(next_mode):
                return next_mode
        except ValueError:
            # Current mode not in list, set to balanced
            if self.set_mode(CPUMode.BALANCED):
                return CPUMode.BALANCED
        
        return None
    
    def get_cpu_frequency_info(self) -> dict:
        """
        Get current CPU frequency information.
        
        Returns:
            Dictionary with frequency info
        """
        info = {
            'current_freq_mhz': None,
            'min_freq_mhz': None,
            'max_freq_mhz': None,
            'governor': None,
            'scaling_driver': None
        }
        
        cpu0_path = '/sys/devices/system/cpu/cpu0/cpufreq'
        
        if os.path.exists(cpu0_path):
            # Current frequency
            cur_freq = read_sysfs(os.path.join(cpu0_path, 'scaling_cur_freq'))
            if cur_freq:
                info['current_freq_mhz'] = int(cur_freq) / 1000
            
            # Min frequency
            min_freq = read_sysfs(os.path.join(cpu0_path, 'scaling_min_freq'))
            if min_freq:
                info['min_freq_mhz'] = int(min_freq) / 1000
            
            # Max frequency
            max_freq = read_sysfs(os.path.join(cpu0_path, 'scaling_max_freq'))
            if max_freq:
                info['max_freq_mhz'] = int(max_freq) / 1000
            
            # Governor
            governor = read_sysfs(os.path.join(cpu0_path, 'scaling_governor'))
            if governor:
                info['governor'] = governor
            
            # Driver
            driver = read_sysfs(os.path.join(cpu0_path, 'scaling_driver'))
            if driver:
                info['scaling_driver'] = driver
        
        return info
    
    def get_cpu_usage(self) -> Optional[float]:
        """
        Get current CPU usage percentage.
        
        Returns:
            CPU usage as percentage (0-100) or None
        """
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
            
            if line.startswith('cpu '):
                values = line.split()[1:]
                values = [int(v) for v in values[:7]]
                
                # user, nice, system, idle, iowait, irq, softirq
                idle = values[3] + values[4]
                total = sum(values)
                
                # This is a snapshot - for accurate usage, need to compare over time
                if total > 0:
                    return round(100 * (1 - idle / total), 1)
        except Exception:
            pass
        
        return None
