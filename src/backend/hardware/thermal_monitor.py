"""
Thermal monitoring module for ASUS laptops.
"""

import os
import glob
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum

from ..utils.helpers import read_sysfs, run_command
from ..utils.logger import get_logger


class ThermalZone(Enum):
    """Thermal zone types."""
    CPU = "cpu"
    GPU = "gpu"
    MOTHERBOARD = "motherboard"
    BATTERY = "battery"
    CHARGER = "charger"
    UNKNOWN = "unknown"


@dataclass
class ThermalReading:
    """A thermal sensor reading."""
    zone_id: int
    zone_type: ThermalZone
    name: str
    temperature_c: float
    critical_temp_c: Optional[float] = None
    trip_points: Optional[List[float]] = None


@dataclass
class CPUCoreTemp:
    """CPU core temperature reading."""
    core_id: int
    temperature_c: float
    high_temp_c: Optional[float] = None
    critical_temp_c: Optional[float] = None


class ThermalMonitor:
    """
    Monitors thermal sensors on ASUS laptops.
    
    Provides temperature readings for CPU, GPU, and other components.
    """
    
    # Known thermal zone type mappings
    ZONE_TYPE_MAP = {
        'acpitz': ThermalZone.MOTHERBOARD,
        'x86_pkg_temp': ThermalZone.CPU,
        'pch_cannonlake': ThermalZone.MOTHERBOARD,
        'pch_skylake': ThermalZone.MOTHERBOARD,
        'iwlwifi': ThermalZone.UNKNOWN,
        'nvme': ThermalZone.UNKNOWN,
        'amdgpu': ThermalZone.GPU,
        'coretemp': ThermalZone.CPU,
        'k10temp': ThermalZone.CPU,
        'nvidia': ThermalZone.GPU,
    }
    
    def __init__(self):
        """Initialize thermal monitor."""
        self.logger = get_logger()
        self._thermal_zones: List[str] = []
        self._hwmon_sensors: Dict[str, str] = {}
        
        self._detect_thermal_zones()
        self._detect_hwmon_sensors()
    
    def _detect_thermal_zones(self) -> None:
        """Detect available thermal zones."""
        thermal_base = '/sys/class/thermal'
        
        if os.path.exists(thermal_base):
            for item in os.listdir(thermal_base):
                if item.startswith('thermal_zone'):
                    self._thermal_zones.append(os.path.join(thermal_base, item))
        
        self.logger.debug(f"Found {len(self._thermal_zones)} thermal zones")
    
    def _detect_hwmon_sensors(self) -> None:
        """Detect hwmon temperature sensors."""
        hwmon_base = '/sys/class/hwmon'
        
        if not os.path.exists(hwmon_base):
            return
        
        for hwmon_dir in os.listdir(hwmon_base):
            hwmon_path = os.path.join(hwmon_base, hwmon_dir)
            name_path = os.path.join(hwmon_path, 'name')
            name = read_sysfs(name_path)
            
            if name:
                # Check for temperature inputs
                temp_inputs = glob.glob(os.path.join(hwmon_path, 'temp*_input'))
                if temp_inputs:
                    self._hwmon_sensors[name] = hwmon_path
        
        self.logger.debug(f"Found hwmon sensors: {list(self._hwmon_sensors.keys())}")
    
    def get_thermal_zones(self) -> List[ThermalReading]:
        """
        Get readings from all thermal zones.
        
        Returns:
            List of ThermalReading objects
        """
        readings = []
        
        for idx, zone_path in enumerate(self._thermal_zones):
            reading = self._read_thermal_zone(idx, zone_path)
            if reading:
                readings.append(reading)
        
        return readings
    
    def _read_thermal_zone(self, zone_id: int, zone_path: str) -> Optional[ThermalReading]:
        """Read a thermal zone."""
        temp_path = os.path.join(zone_path, 'temp')
        type_path = os.path.join(zone_path, 'type')
        
        temp_str = read_sysfs(temp_path)
        type_str = read_sysfs(type_path) or 'unknown'
        
        if temp_str is None:
            return None
        
        try:
            # Temperature is in millidegrees
            temp_c = int(temp_str) / 1000
        except ValueError:
            return None
        
        # Determine zone type
        zone_type = self.ZONE_TYPE_MAP.get(type_str.lower(), ThermalZone.UNKNOWN)
        
        # Read critical temperature if available
        crit_temp = None
        crit_path = glob.glob(os.path.join(zone_path, 'trip_point_*_temp'))
        for trip_path in crit_path:
            trip_type_path = trip_path.replace('_temp', '_type')
            trip_type = read_sysfs(trip_type_path)
            if trip_type and 'critical' in trip_type.lower():
                trip_temp = read_sysfs(trip_path)
                if trip_temp:
                    try:
                        crit_temp = int(trip_temp) / 1000
                    except ValueError:
                        pass
                break
        
        return ThermalReading(
            zone_id=zone_id,
            zone_type=zone_type,
            name=type_str,
            temperature_c=temp_c,
            critical_temp_c=crit_temp
        )
    
    def get_cpu_temperatures(self) -> List[CPUCoreTemp]:
        """
        Get CPU core temperatures.
        
        Returns:
            List of CPUCoreTemp objects
        """
        temps = []
        
        # Check for coretemp (Intel) or k10temp (AMD)
        for sensor_name, hwmon_path in self._hwmon_sensors.items():
            if sensor_name in ['coretemp', 'k10temp']:
                temps.extend(self._read_cpu_temps(hwmon_path))
                break
        
        return temps
    
    def _read_cpu_temps(self, hwmon_path: str) -> List[CPUCoreTemp]:
        """Read CPU core temperatures from hwmon."""
        temps = []
        
        temp_inputs = glob.glob(os.path.join(hwmon_path, 'temp*_input'))
        
        for temp_path in sorted(temp_inputs):
            # Extract sensor number
            base_name = os.path.basename(temp_path)
            sensor_num = base_name.replace('temp', '').replace('_input', '')
            
            try:
                sensor_idx = int(sensor_num)
            except ValueError:
                continue
            
            # Skip temp1 which is usually the package temp
            if sensor_idx == 1:
                continue
            
            temp_str = read_sysfs(temp_path)
            if temp_str is None:
                continue
            
            try:
                temp_c = int(temp_str) / 1000
            except ValueError:
                continue
            
            # Read high and critical temps
            high_temp = None
            crit_temp = None
            
            high_path = temp_path.replace('_input', '_max')
            crit_path = temp_path.replace('_input', '_crit')
            
            high_str = read_sysfs(high_path)
            crit_str = read_sysfs(crit_path)
            
            if high_str:
                try:
                    high_temp = int(high_str) / 1000
                except ValueError:
                    pass
            
            if crit_str:
                try:
                    crit_temp = int(crit_str) / 1000
                except ValueError:
                    pass
            
            temps.append(CPUCoreTemp(
                core_id=sensor_idx - 2,  # Adjust for 0-based indexing
                temperature_c=temp_c,
                high_temp_c=high_temp,
                critical_temp_c=crit_temp
            ))
        
        return temps
    
    def get_cpu_package_temp(self) -> Optional[float]:
        """
        Get CPU package temperature.
        
        Returns:
            Package temperature in Celsius or None
        """
        for sensor_name, hwmon_path in self._hwmon_sensors.items():
            if sensor_name in ['coretemp', 'k10temp']:
                temp_path = os.path.join(hwmon_path, 'temp1_input')
                temp_str = read_sysfs(temp_path)
                if temp_str:
                    try:
                        return int(temp_str) / 1000
                    except ValueError:
                        pass
        
        # Fallback to thermal zone
        for reading in self.get_thermal_zones():
            if reading.zone_type == ThermalZone.CPU:
                return reading.temperature_c
        
        return None
    
    def get_gpu_temperature(self) -> Optional[float]:
        """
        Get GPU temperature.
        
        Returns:
            GPU temperature in Celsius or None
        """
        # Check hwmon for GPU sensors
        for sensor_name, hwmon_path in self._hwmon_sensors.items():
            if 'amdgpu' in sensor_name or 'nvidia' in sensor_name:
                temp_path = os.path.join(hwmon_path, 'temp1_input')
                temp_str = read_sysfs(temp_path)
                if temp_str:
                    try:
                        return int(temp_str) / 1000
                    except ValueError:
                        pass
        
        # Try nvidia-smi for NVIDIA GPUs
        ret, out, _ = run_command(['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'])
        if ret == 0 and out:
            try:
                return float(out.strip())
            except ValueError:
                pass
        
        # Fallback to thermal zone
        for reading in self.get_thermal_zones():
            if reading.zone_type == ThermalZone.GPU:
                return reading.temperature_c
        
        return None
    
    def get_all_temperatures(self) -> Dict[str, float]:
        """
        Get all available temperatures.
        
        Returns:
            Dictionary mapping sensor names to temperatures
        """
        temps = {}
        
        # CPU package
        cpu_pkg = self.get_cpu_package_temp()
        if cpu_pkg is not None:
            temps['CPU Package'] = cpu_pkg
        
        # CPU cores
        for core in self.get_cpu_temperatures():
            temps[f'CPU Core {core.core_id}'] = core.temperature_c
        
        # GPU
        gpu_temp = self.get_gpu_temperature()
        if gpu_temp is not None:
            temps['GPU'] = gpu_temp
        
        # Other thermal zones
        for reading in self.get_thermal_zones():
            if reading.zone_type not in [ThermalZone.CPU, ThermalZone.GPU]:
                temps[reading.name] = reading.temperature_c
        
        return temps
    
    def get_max_cpu_temp(self) -> Optional[float]:
        """Get the maximum CPU temperature."""
        temps = []
        
        cpu_pkg = self.get_cpu_package_temp()
        if cpu_pkg is not None:
            temps.append(cpu_pkg)
        
        for core in self.get_cpu_temperatures():
            temps.append(core.temperature_c)
        
        return max(temps) if temps else None
    
    def is_thermal_throttling(self) -> bool:
        """
        Check if system is thermal throttling.
        
        Returns:
            True if thermal throttling is detected
        """
        # Check for throttling via thermal zones
        for reading in self.get_thermal_zones():
            if reading.critical_temp_c and reading.temperature_c:
                if reading.temperature_c >= reading.critical_temp_c * 0.95:
                    return True
        
        # Check CPU core temps
        for core in self.get_cpu_temperatures():
            if core.critical_temp_c and core.temperature_c >= core.critical_temp_c * 0.95:
                return True
            if core.high_temp_c and core.temperature_c >= core.high_temp_c:
                return True
        
        return False
    
    def get_thermal_status(self) -> str:
        """
        Get human-readable thermal status.
        
        Returns:
            Status string ('Cool', 'Normal', 'Warm', 'Hot', 'Critical')
        """
        max_temp = self.get_max_cpu_temp()
        
        if max_temp is None:
            return 'Unknown'
        
        if max_temp < 50:
            return 'Cool'
        elif max_temp < 70:
            return 'Normal'
        elif max_temp < 85:
            return 'Warm'
        elif max_temp < 95:
            return 'Hot'
        else:
            return 'Critical'
