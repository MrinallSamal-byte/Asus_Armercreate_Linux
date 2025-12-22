"""
Hardware control modules for ASUS laptops.
"""

from .detector import HardwareDetector
from .cpu_control import CPUController
from .fan_control import FanController
from .rgb_control import RGBController
from .battery_control import BatteryController
from .thermal_monitor import ThermalMonitor

__all__ = [
    'HardwareDetector',
    'CPUController',
    'FanController',
    'RGBController',
    'BatteryController',
    'ThermalMonitor'
]
