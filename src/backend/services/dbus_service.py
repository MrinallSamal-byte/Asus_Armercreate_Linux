"""
D-Bus service for ASUS Armoury Crate Linux.

Provides system-level control interface via D-Bus.
"""

import os
from typing import Optional, Dict, Any, Callable
import json

# D-Bus support - we use dasbus as it's the modern replacement for dbus-python
# If not available, we provide a fallback

try:
    from dasbus.connection import SystemMessageBus, SessionMessageBus
    from dasbus.server.interface import dbus_interface
    from dasbus.typing import Str, Int, Bool, Double, List as DBusList
    from dasbus.loop import EventLoop
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False
    # Provide stub classes
    def dbus_interface(name):
        def decorator(cls):
            return cls
        return decorator
    
    Str = str
    Int = int
    Bool = bool
    Double = float
    DBusList = list

from ..utils.logger import get_logger
from ..hardware.cpu_control import CPUController, CPUMode
from ..hardware.fan_control import FanController
from ..hardware.rgb_control import RGBController, RGBMode, RGBColor
from ..hardware.battery_control import BatteryController
from ..hardware.thermal_monitor import ThermalMonitor


# D-Bus service name and paths
DBUS_SERVICE_NAME = "org.asus.armoury"
DBUS_OBJECT_PATH = "/org/asus/armoury"


@dbus_interface(DBUS_SERVICE_NAME)
class ArmouryDBusInterface:
    """
    D-Bus interface for ASUS Armoury Crate Linux.
    
    This interface is exposed on the system bus and provides
    privileged hardware control operations.
    """
    
    def __init__(
        self,
        cpu_controller: CPUController,
        fan_controller: FanController,
        rgb_controller: RGBController,
        battery_controller: BatteryController,
        thermal_monitor: ThermalMonitor
    ):
        """Initialize D-Bus interface with controllers."""
        self._cpu = cpu_controller
        self._fan = fan_controller
        self._rgb = rgb_controller
        self._battery = battery_controller
        self._thermal = thermal_monitor
        self._logger = get_logger()
    
    # CPU Control Methods
    
    def GetCPUMode(self) -> Str:
        """Get current CPU performance mode."""
        mode = self._cpu.get_current_mode()
        return mode.value if mode else "unknown"
    
    def SetCPUMode(self, mode: Str) -> Bool:
        """Set CPU performance mode."""
        try:
            cpu_mode = CPUMode(mode)
            return self._cpu.set_mode(cpu_mode)
        except ValueError:
            self._logger.error(f"Invalid CPU mode: {mode}")
            return False
    
    def GetAvailableCPUModes(self) -> DBusList:
        """Get list of available CPU modes."""
        modes = self._cpu.get_available_modes()
        return [m.value for m in modes]
    
    def CycleCPUMode(self) -> Str:
        """Cycle to next CPU mode."""
        mode = self._cpu.cycle_mode()
        return mode.value if mode else "unknown"
    
    # Fan Control Methods
    
    def GetFanCount(self) -> Int:
        """Get number of controllable fans."""
        return self._fan.fan_count
    
    def GetFanRPM(self, fan_id: Int) -> Int:
        """Get current fan RPM."""
        info = self._fan.get_fan_info(fan_id)
        return info.current_rpm if info else 0
    
    def SetFanMode(self, mode: Str, fan_id: Int) -> Bool:
        """Set fan control mode (auto/manual/full)."""
        return self._fan.set_fan_mode(mode, fan_id)
    
    def SetFanSpeed(self, speed_percent: Int, fan_id: Int) -> Bool:
        """Set fan speed percentage."""
        return self._fan.set_fan_speed(speed_percent, fan_id)
    
    def SetFanCurve(self, curve_json: Str, fan_id: Int) -> Bool:
        """Set fan curve from JSON string."""
        try:
            from ..hardware.fan_control import FanCurvePoint
            curve_data = json.loads(curve_json)
            curve = [FanCurvePoint(p['temp'], p['speed']) for p in curve_data]
            return self._fan.set_fan_curve(curve, fan_id)
        except (json.JSONDecodeError, KeyError) as e:
            self._logger.error(f"Invalid fan curve JSON: {e}")
            return False
    
    def ResetFansToAuto(self) -> Bool:
        """Reset all fans to automatic control."""
        return self._fan.reset_to_auto()
    
    # RGB Control Methods
    
    def GetRGBMode(self) -> Str:
        """Get current RGB mode."""
        state = self._rgb.get_current_state()
        return state.mode.value if state else "unknown"
    
    def SetRGBMode(self, mode: Str) -> Bool:
        """Set RGB lighting mode."""
        try:
            rgb_mode = RGBMode(mode)
            return self._rgb.set_mode(rgb_mode)
        except ValueError:
            self._logger.error(f"Invalid RGB mode: {mode}")
            return False
    
    def SetRGBColor(self, hex_color: Str) -> Bool:
        """Set RGB color from hex string."""
        color = RGBColor.from_hex(hex_color)
        return self._rgb.set_color(color)
    
    def SetRGBBrightness(self, brightness: Int) -> Bool:
        """Set RGB brightness (0-100)."""
        return self._rgb.set_brightness(brightness)
    
    def GetSupportedRGBModes(self) -> DBusList:
        """Get list of supported RGB modes."""
        modes = self._rgb.supported_modes
        return [m.value for m in modes]
    
    def TurnOffRGB(self) -> Bool:
        """Turn off RGB lighting."""
        return self._rgb.turn_off()
    
    # Battery Control Methods
    
    def GetBatteryChargeLimit(self) -> Int:
        """Get current battery charge limit."""
        limit = self._battery.get_charge_limit()
        return limit if limit is not None else 100
    
    def SetBatteryChargeLimit(self, limit: Int) -> Bool:
        """Set battery charge limit (20-100)."""
        return self._battery.set_charge_limit(limit)
    
    def GetBatteryInfo(self) -> Str:
        """Get battery info as JSON string."""
        info = self._battery.get_battery_info()
        return json.dumps(info)
    
    def IsACConnected(self) -> Bool:
        """Check if AC power is connected."""
        return self._battery.get_ac_status()
    
    # Thermal Monitoring Methods
    
    def GetCPUTemperature(self) -> Double:
        """Get CPU package temperature."""
        temp = self._thermal.get_cpu_package_temp()
        return temp if temp is not None else 0.0
    
    def GetGPUTemperature(self) -> Double:
        """Get GPU temperature."""
        temp = self._thermal.get_gpu_temperature()
        return temp if temp is not None else 0.0
    
    def GetAllTemperatures(self) -> Str:
        """Get all temperatures as JSON string."""
        temps = self._thermal.get_all_temperatures()
        return json.dumps(temps)
    
    def GetThermalStatus(self) -> Str:
        """Get thermal status (Cool/Normal/Warm/Hot/Critical)."""
        return self._thermal.get_thermal_status()
    
    def IsThermalThrottling(self) -> Bool:
        """Check if system is thermal throttling."""
        return self._thermal.is_thermal_throttling()
    
    # System Methods
    
    def GetServiceVersion(self) -> Str:
        """Get service version."""
        from .. import __version__
        return __version__
    
    def Ping(self) -> Str:
        """Ping the service."""
        return "pong"


class DBusService:
    """
    D-Bus service manager for ASUS Armoury Crate Linux.
    
    Manages the lifecycle of the D-Bus service.
    """
    
    def __init__(self):
        """Initialize D-Bus service."""
        self.logger = get_logger()
        self._interface: Optional[ArmouryDBusInterface] = None
        self._loop = None
        self._bus = None
        
        # Initialize controllers
        self._cpu = CPUController()
        self._fan = FanController()
        self._rgb = RGBController()
        self._battery = BatteryController()
        self._thermal = ThermalMonitor()
    
    @property
    def is_available(self) -> bool:
        """Check if D-Bus is available."""
        return DBUS_AVAILABLE
    
    def start(self, use_session_bus: bool = False) -> bool:
        """
        Start the D-Bus service.
        
        Args:
            use_session_bus: Use session bus instead of system bus
            
        Returns:
            True if service started successfully
        """
        if not DBUS_AVAILABLE:
            self.logger.error("D-Bus library not available")
            return False
        
        try:
            # Create interface
            self._interface = ArmouryDBusInterface(
                self._cpu,
                self._fan,
                self._rgb,
                self._battery,
                self._thermal
            )
            
            # Connect to bus
            if use_session_bus:
                self._bus = SessionMessageBus()
            else:
                self._bus = SystemMessageBus()
            
            # Publish interface
            self._bus.publish_object(DBUS_OBJECT_PATH, self._interface)
            self._bus.register_service(DBUS_SERVICE_NAME)
            
            self.logger.info(f"D-Bus service started on {DBUS_SERVICE_NAME}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start D-Bus service: {e}")
            return False
    
    def run(self) -> None:
        """Run the D-Bus event loop."""
        if not DBUS_AVAILABLE:
            return
        
        try:
            self._loop = EventLoop()
            self._loop.run()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self) -> None:
        """Stop the D-Bus service."""
        if self._loop:
            self._loop.quit()
        
        self.logger.info("D-Bus service stopped")


class DBusClient:
    """
    D-Bus client for communicating with the service.
    
    Used by the GUI to communicate with the privileged daemon.
    """
    
    def __init__(self, use_session_bus: bool = False):
        """Initialize D-Bus client."""
        self.logger = get_logger()
        self._proxy = None
        self._use_session_bus = use_session_bus
        
        if DBUS_AVAILABLE:
            self._connect()
    
    def _connect(self) -> bool:
        """Connect to the D-Bus service."""
        if not DBUS_AVAILABLE:
            return False
        
        try:
            if self._use_session_bus:
                bus = SessionMessageBus()
            else:
                bus = SystemMessageBus()
            
            self._proxy = bus.get_proxy(DBUS_SERVICE_NAME, DBUS_OBJECT_PATH)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to D-Bus service: {e}")
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to service."""
        if not self._proxy:
            return False
        
        try:
            self._proxy.Ping()
            return True
        except Exception:
            return False
    
    def call(self, method: str, *args) -> Any:
        """
        Call a D-Bus method.
        
        Args:
            method: Method name
            *args: Method arguments
            
        Returns:
            Method return value
        """
        if not self._proxy:
            self.logger.error("Not connected to D-Bus service")
            return None
        
        try:
            func = getattr(self._proxy, method)
            return func(*args)
        except Exception as e:
            self.logger.error(f"D-Bus call failed: {e}")
            return None
    
    # Convenience methods
    
    def get_cpu_mode(self) -> Optional[str]:
        """Get current CPU mode."""
        return self.call("GetCPUMode")
    
    def set_cpu_mode(self, mode: str) -> bool:
        """Set CPU mode."""
        result = self.call("SetCPUMode", mode)
        return result is True
    
    def get_temperatures(self) -> Dict[str, float]:
        """Get all temperatures."""
        result = self.call("GetAllTemperatures")
        if result:
            return json.loads(result)
        return {}
    
    def get_battery_info(self) -> Dict[str, Any]:
        """Get battery information."""
        result = self.call("GetBatteryInfo")
        if result:
            return json.loads(result)
        return {}
