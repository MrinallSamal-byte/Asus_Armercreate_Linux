"""
Battery charge limit control for ASUS laptops.
"""

import os
from typing import Optional

from ..utils.helpers import read_sysfs, write_sysfs, find_asus_wmi_paths
from ..utils.logger import get_logger


class BatteryController:
    """
    Controls battery charge limit on ASUS laptops.
    
    This feature allows setting a maximum charge level to extend battery longevity.
    """
    
    # Common charge limit paths
    CHARGE_LIMIT_PATHS = [
        '/sys/class/power_supply/BAT0/charge_control_end_threshold',
        '/sys/class/power_supply/BAT1/charge_control_end_threshold',
        '/sys/class/power_supply/BATC/charge_control_end_threshold',
    ]
    
    # Common presets
    PRESETS = {
        'max_lifespan': 60,   # Best for always plugged in
        'balanced': 80,       # Good balance
        'full_charge': 100    # Maximum capacity
    }
    
    def __init__(self):
        """Initialize battery controller."""
        self.logger = get_logger()
        self._charge_limit_path: Optional[str] = None
        self._battery_path: Optional[str] = None
        
        self._detect_battery()
    
    def _detect_battery(self) -> None:
        """Detect battery and charge limit control paths."""
        # First check ASUS WMI paths
        paths = find_asus_wmi_paths()
        asus_path = paths.get('charge_control_end_threshold')
        
        if asus_path and os.path.exists(asus_path):
            self._charge_limit_path = asus_path
            self.logger.debug(f"Found charge limit control at {asus_path}")
        else:
            # Check standard paths
            for path in self.CHARGE_LIMIT_PATHS:
                if os.path.exists(path):
                    self._charge_limit_path = path
                    self.logger.debug(f"Found charge limit control at {path}")
                    break
        
        # Find battery info path
        battery_paths = [
            '/sys/class/power_supply/BAT0',
            '/sys/class/power_supply/BAT1',
            '/sys/class/power_supply/BATC'
        ]
        
        for path in battery_paths:
            if os.path.exists(path):
                self._battery_path = path
                break
    
    @property
    def is_available(self) -> bool:
        """Check if charge limit control is available."""
        return bool(self._charge_limit_path)
    
    def get_charge_limit(self) -> Optional[int]:
        """
        Get current charge limit.
        
        Returns:
            Current charge limit percentage (20-100) or None
        """
        if not self._charge_limit_path:
            return None
        
        value = read_sysfs(self._charge_limit_path)
        if value is not None:
            try:
                return int(value)
            except ValueError:
                pass
        
        return None
    
    def set_charge_limit(self, limit: int) -> bool:
        """
        Set battery charge limit.
        
        Args:
            limit: Charge limit percentage (20-100)
            
        Returns:
            True if successful
        """
        if not self._charge_limit_path:
            self.logger.error("Charge limit control not available")
            return False
        
        # Validate limit
        limit = max(20, min(100, limit))
        
        self.logger.info(f"Setting charge limit to: {limit}%")
        
        if write_sysfs(self._charge_limit_path, limit):
            self.logger.info(f"Charge limit set to {limit}%")
            return True
        
        self.logger.error("Failed to set charge limit (insufficient permissions?)")
        return False
    
    def apply_preset(self, preset: str) -> bool:
        """
        Apply a charge limit preset.
        
        Args:
            preset: Preset name ('max_lifespan', 'balanced', 'full_charge')
            
        Returns:
            True if successful
        """
        if preset not in self.PRESETS:
            self.logger.error(f"Unknown preset: {preset}")
            return False
        
        return self.set_charge_limit(self.PRESETS[preset])
    
    def get_battery_info(self) -> dict:
        """
        Get battery status information.
        
        Returns:
            Dictionary with battery information
        """
        info = {
            'present': False,
            'status': 'Unknown',
            'capacity': None,
            'capacity_level': 'Unknown',
            'charge_limit': None,
            'voltage_now': None,
            'power_now': None,
            'energy_now': None,
            'energy_full': None,
            'energy_full_design': None,
            'health': None,
            'cycle_count': None,
            'technology': 'Unknown',
            'manufacturer': 'Unknown',
            'model_name': 'Unknown'
        }
        
        if not self._battery_path:
            return info
        
        # Check if battery is present
        present = read_sysfs(os.path.join(self._battery_path, 'present'))
        if present == '1':
            info['present'] = True
        else:
            return info
        
        # Read battery attributes
        attributes = {
            'status': 'status',
            'capacity': 'capacity',
            'capacity_level': 'capacity_level',
            'voltage_now': 'voltage_now',
            'power_now': 'power_now',
            'energy_now': 'energy_now',
            'energy_full': 'energy_full',
            'energy_full_design': 'energy_full_design',
            'cycle_count': 'cycle_count',
            'technology': 'technology',
            'manufacturer': 'manufacturer',
            'model_name': 'model_name'
        }
        
        for key, attr in attributes.items():
            value = read_sysfs(os.path.join(self._battery_path, attr))
            if value is not None:
                # Convert numeric values
                if key in ['capacity', 'voltage_now', 'power_now', 
                          'energy_now', 'energy_full', 'energy_full_design', 'cycle_count']:
                    try:
                        info[key] = int(value)
                    except ValueError:
                        info[key] = value
                else:
                    info[key] = value
        
        # Get charge limit
        info['charge_limit'] = self.get_charge_limit()
        
        # Calculate battery health
        if info['energy_full'] and info['energy_full_design']:
            health = (info['energy_full'] / info['energy_full_design']) * 100
            info['health'] = round(health, 1)
        
        # Convert voltage and power to user-friendly units
        if info['voltage_now']:
            info['voltage_v'] = round(info['voltage_now'] / 1000000, 2)
        
        if info['power_now']:
            info['power_w'] = round(info['power_now'] / 1000000, 2)
        
        if info['energy_now']:
            info['energy_wh'] = round(info['energy_now'] / 1000000, 2)
        
        if info['energy_full']:
            info['energy_full_wh'] = round(info['energy_full'] / 1000000, 2)
        
        return info
    
    def get_ac_status(self) -> bool:
        """
        Check if AC power is connected.
        
        Returns:
            True if AC power is connected
        """
        ac_paths = [
            '/sys/class/power_supply/AC0/online',
            '/sys/class/power_supply/AC/online',
            '/sys/class/power_supply/ADP0/online',
            '/sys/class/power_supply/ADP1/online'
        ]
        
        for path in ac_paths:
            value = read_sysfs(path)
            if value == '1':
                return True
        
        return False
    
    def estimate_time_remaining(self) -> Optional[int]:
        """
        Estimate battery time remaining in minutes.
        
        Returns:
            Estimated minutes remaining or None
        """
        info = self.get_battery_info()
        
        if not info['present']:
            return None
        
        # If charging, return None (would need charge rate estimation)
        if info['status'] == 'Charging':
            return None
        
        # Calculate time remaining
        if info.get('power_now') and info.get('energy_now') and info['power_now'] > 0:
            hours = info['energy_now'] / info['power_now']
            return int(hours * 60)
        
        return None
