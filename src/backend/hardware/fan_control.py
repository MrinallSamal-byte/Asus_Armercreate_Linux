"""
Fan control module for ASUS laptops.
"""

import os
import glob
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

from ..utils.helpers import read_sysfs, write_sysfs, run_command, clamp
from ..utils.logger import get_logger


@dataclass
class FanInfo:
    """Fan information and status."""
    fan_id: int
    name: str
    current_rpm: int
    pwm_value: int  # 0-255
    pwm_enabled: int  # 0=full, 1=manual, 2=auto
    min_rpm: Optional[int] = None
    max_rpm: Optional[int] = None


@dataclass 
class FanCurvePoint:
    """A point on a fan curve."""
    temperature: int
    speed_percent: int


class FanController:
    """
    Controls fan speeds on ASUS laptops.
    
    Supports direct hwmon control and asusctl integration.
    """
    
    def __init__(self):
        """Initialize fan controller."""
        self.logger = get_logger()
        self._hwmon_path: Optional[str] = None
        self._use_asusctl = False
        self._fan_count = 0
        
        self._detect_fan_control()
    
    def _detect_fan_control(self) -> None:
        """Detect available fan control method."""
        # Look for ASUS fan control in hwmon
        hwmon_base = '/sys/class/hwmon'
        
        if os.path.exists(hwmon_base):
            for hwmon_dir in os.listdir(hwmon_base):
                hwmon_path = os.path.join(hwmon_base, hwmon_dir)
                name_path = os.path.join(hwmon_path, 'name')
                name = read_sysfs(name_path)
                
                if name and 'asus' in name.lower():
                    # Check if fan control is available
                    if os.path.exists(os.path.join(hwmon_path, 'pwm1')):
                        self._hwmon_path = hwmon_path
                        
                        # Count fans
                        for i in range(1, 5):
                            if os.path.exists(os.path.join(hwmon_path, f'fan{i}_input')):
                                self._fan_count = i
                        
                        self.logger.debug(f"Found ASUS hwmon at {hwmon_path} with {self._fan_count} fans")
                        break
        
        # Check for asusctl as fallback
        if not self._hwmon_path:
            ret, _, _ = run_command(['which', 'asusctl'])
            if ret == 0:
                self._use_asusctl = True
                self._fan_count = 2  # Assume 2 fans (CPU + GPU) for asusctl
                self.logger.debug("Using asusctl for fan control")
    
    @property
    def is_available(self) -> bool:
        """Check if fan control is available."""
        return bool(self._hwmon_path) or self._use_asusctl
    
    @property
    def fan_count(self) -> int:
        """Get number of controllable fans."""
        return self._fan_count
    
    def get_fan_info(self, fan_id: int = 1) -> Optional[FanInfo]:
        """
        Get information about a specific fan.
        
        Args:
            fan_id: Fan number (1-indexed)
            
        Returns:
            FanInfo object or None
        """
        if not self.is_available or fan_id < 1 or fan_id > self._fan_count:
            return None
        
        if self._hwmon_path:
            rpm_path = os.path.join(self._hwmon_path, f'fan{fan_id}_input')
            pwm_path = os.path.join(self._hwmon_path, f'pwm{fan_id}')
            enable_path = os.path.join(self._hwmon_path, f'pwm{fan_id}_enable')
            
            rpm = read_sysfs(rpm_path)
            pwm = read_sysfs(pwm_path)
            enabled = read_sysfs(enable_path)
            
            # Get label if available
            label_path = os.path.join(self._hwmon_path, f'fan{fan_id}_label')
            label = read_sysfs(label_path) or f"Fan {fan_id}"
            
            return FanInfo(
                fan_id=fan_id,
                name=label,
                current_rpm=int(rpm) if rpm else 0,
                pwm_value=int(pwm) if pwm else 0,
                pwm_enabled=int(enabled) if enabled else 2
            )
        
        if self._use_asusctl:
            # Get fan info via asusctl
            ret, out, _ = run_command(['asusctl', 'fan-curve', '-g'])
            if ret == 0:
                # Parse output for fan RPM (if available)
                # Note: asusctl doesn't directly report RPM, use sensors instead
                rpm = self._get_rpm_from_sensors(fan_id)
                return FanInfo(
                    fan_id=fan_id,
                    name=f"Fan {fan_id}" if fan_id == 1 else "GPU Fan",
                    current_rpm=rpm or 0,
                    pwm_value=128,  # Placeholder
                    pwm_enabled=2   # Assume auto mode
                )
        
        return None
    
    def _get_rpm_from_sensors(self, fan_id: int) -> Optional[int]:
        """Try to get fan RPM from lm-sensors."""
        ret, out, _ = run_command(['sensors', '-u'])
        if ret == 0 and out:
            # Parse sensors output for fan RPM
            fan_key = f"fan{fan_id}_input"
            for line in out.split('\n'):
                if fan_key in line:
                    try:
                        value = line.split(':')[1].strip()
                        return int(float(value))
                    except (IndexError, ValueError):
                        pass
        return None
    
    def get_all_fans(self) -> List[FanInfo]:
        """
        Get information about all fans.
        
        Returns:
            List of FanInfo objects
        """
        fans = []
        for i in range(1, self._fan_count + 1):
            info = self.get_fan_info(i)
            if info:
                fans.append(info)
        return fans
    
    def set_fan_mode(self, mode: str, fan_id: int = 0) -> bool:
        """
        Set fan control mode.
        
        Args:
            mode: 'auto', 'manual', or 'full'
            fan_id: Fan number (0 = all fans)
            
        Returns:
            True if successful
        """
        mode_map = {
            'full': 0,
            'manual': 1,
            'auto': 2
        }
        
        if mode not in mode_map:
            self.logger.error(f"Invalid fan mode: {mode}")
            return False
        
        if self._hwmon_path:
            fans_to_set = range(1, self._fan_count + 1) if fan_id == 0 else [fan_id]
            
            success = True
            for fid in fans_to_set:
                enable_path = os.path.join(self._hwmon_path, f'pwm{fid}_enable')
                if not write_sysfs(enable_path, mode_map[mode]):
                    success = False
                    self.logger.error(f"Failed to set fan {fid} mode")
            
            return success
        
        if self._use_asusctl:
            # asusctl doesn't have direct mode control, but we can use fan curves
            self.logger.warning("Fan mode control via asusctl not directly supported")
            return False
        
        return False
    
    def set_fan_speed(self, speed_percent: int, fan_id: int = 0) -> bool:
        """
        Set fan speed (requires manual mode).
        
        Args:
            speed_percent: Speed as percentage (0-100)
            fan_id: Fan number (0 = all fans)
            
        Returns:
            True if successful
        """
        speed_percent = clamp(speed_percent, 0, 100)
        pwm_value = int(speed_percent * 255 / 100)
        
        self.logger.info(f"Setting fan {fan_id or 'all'} to {speed_percent}% (PWM: {pwm_value})")
        
        if self._hwmon_path:
            fans_to_set = range(1, self._fan_count + 1) if fan_id == 0 else [fan_id]
            
            success = True
            for fid in fans_to_set:
                # Ensure manual mode is enabled
                enable_path = os.path.join(self._hwmon_path, f'pwm{fid}_enable')
                pwm_path = os.path.join(self._hwmon_path, f'pwm{fid}')
                
                if not write_sysfs(enable_path, 1):  # Manual mode
                    self.logger.warning(f"Could not enable manual mode for fan {fid}")
                
                if not write_sysfs(pwm_path, pwm_value):
                    success = False
                    self.logger.error(f"Failed to set fan {fid} speed")
            
            return success
        
        return False
    
    def set_fan_curve(self, curve: List[FanCurvePoint], fan_id: int = 0) -> bool:
        """
        Set a custom fan curve.
        
        Args:
            curve: List of FanCurvePoint objects defining the curve
            fan_id: Fan number (0 = all fans, 1 = CPU, 2 = GPU typically)
            
        Returns:
            True if successful
        """
        if not curve:
            self.logger.error("Empty fan curve provided")
            return False
        
        # Sort curve by temperature
        curve = sorted(curve, key=lambda p: p.temperature)
        
        # Validate curve
        for point in curve:
            if not (0 <= point.temperature <= 100):
                self.logger.error(f"Invalid temperature in curve: {point.temperature}")
                return False
            if not (0 <= point.speed_percent <= 100):
                self.logger.error(f"Invalid speed in curve: {point.speed_percent}")
                return False
        
        self.logger.info(f"Setting fan curve with {len(curve)} points")
        
        if self._use_asusctl:
            # Format curve for asusctl
            # asusctl fan-curve expects format like: 30c:20%,50c:40%,70c:60%,90c:100%
            curve_str = ','.join([f"{p.temperature}c:{p.speed_percent}%" for p in curve])
            
            # Determine which fan
            if fan_id == 0 or fan_id == 1:
                ret, _, err = run_command(['asusctl', 'fan-curve', '-m', 'cpu', '-D', curve_str])
                if ret != 0:
                    self.logger.error(f"Failed to set CPU fan curve: {err}")
                    return False
            
            if fan_id == 0 or fan_id == 2:
                ret, _, err = run_command(['asusctl', 'fan-curve', '-m', 'gpu', '-D', curve_str])
                if ret != 0:
                    self.logger.error(f"Failed to set GPU fan curve: {err}")
                    return False
            
            return True
        
        # For direct hwmon, we can't set curves - would need to implement
        # a polling daemon that adjusts fan speed based on temperature
        self.logger.warning("Fan curves require asusctl or a background service")
        return False
    
    def reset_to_auto(self) -> bool:
        """
        Reset all fans to automatic control.
        
        Returns:
            True if successful
        """
        return self.set_fan_mode('auto', fan_id=0)
    
    def get_fan_curve(self, fan_id: int = 1) -> Optional[List[FanCurvePoint]]:
        """
        Get the current fan curve (if available).
        
        Args:
            fan_id: Fan number
            
        Returns:
            List of FanCurvePoint or None
        """
        if self._use_asusctl:
            fan_type = 'cpu' if fan_id == 1 else 'gpu'
            ret, out, _ = run_command(['asusctl', 'fan-curve', '-m', fan_type, '-g'])
            
            if ret == 0 and out:
                # Parse asusctl output
                # Output format may vary, this is a basic parser
                points = []
                for part in out.split(','):
                    match = part.strip().split(':')
                    if len(match) == 2:
                        try:
                            temp = int(match[0].replace('c', ''))
                            speed = int(match[1].replace('%', ''))
                            points.append(FanCurvePoint(temp, speed))
                        except ValueError:
                            continue
                
                if points:
                    return points
        
        return None
