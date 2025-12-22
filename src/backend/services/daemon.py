"""
Background daemon for ASUS Armoury Crate Linux.

Runs as a system service to provide continuous hardware monitoring
and control.
"""

import os
import sys
import signal
import time
import threading
from typing import Optional, Dict, Any, Callable
import json

from ..utils.logger import get_logger, init_default_logger
from ..utils.config import Config
from ..hardware.detector import HardwareDetector
from ..hardware.cpu_control import CPUController
from ..hardware.fan_control import FanController
from ..hardware.rgb_control import RGBController
from ..hardware.battery_control import BatteryController
from ..hardware.thermal_monitor import ThermalMonitor
from .profile_manager import ProfileManager
from .dbus_service import DBusService


class AsusControlDaemon:
    """
    Background daemon for ASUS laptop control.
    
    Provides:
    - D-Bus interface for GUI communication
    - Hardware monitoring and polling
    - Automatic profile switching
    - Fan curve management
    - Event handling (Fn keys, AC power, etc.)
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the daemon.
        
        Args:
            debug: Enable debug mode
        """
        self.logger = init_default_logger(debug_mode=debug)
        self.logger.info("Initializing ASUS Control Daemon...")
        
        self._running = False
        self._debug = debug
        self._poll_interval = 1.0  # seconds
        
        # Initialize components
        self._config = Config()
        self._detector = HardwareDetector()
        self._cpu = CPUController()
        self._fan = FanController()
        self._rgb = RGBController()
        self._battery = BatteryController()
        self._thermal = ThermalMonitor()
        
        self._profile_manager = ProfileManager(
            config=self._config,
            cpu_controller=self._cpu,
            fan_controller=self._fan,
            rgb_controller=self._rgb,
            battery_controller=self._battery
        )
        
        self._dbus_service = DBusService()
        
        # State tracking
        self._last_ac_state: Optional[bool] = None
        self._last_temps: Dict[str, float] = {}
        
        # Callbacks
        self._callbacks: Dict[str, list] = {
            'temperature': [],
            'fan_speed': [],
            'ac_power': [],
            'profile': []
        }
        
        # Background threads
        self._monitor_thread: Optional[threading.Thread] = None
        self._dbus_thread: Optional[threading.Thread] = None
    
    def detect_hardware(self) -> Dict[str, Any]:
        """
        Run hardware detection and return capabilities.
        
        Returns:
            Dictionary of detected capabilities
        """
        caps = self._detector.detect()
        
        return {
            'is_asus': caps.is_asus,
            'model_name': caps.model_name,
            'model_family': caps.model_family,
            'cpu_model': caps.cpu_model,
            'cpu_cores': caps.cpu_cores,
            'has_dgpu': caps.has_dgpu,
            'features': {
                'performance_modes': caps.has_performance_modes,
                'fan_control': caps.has_fan_control,
                'rgb_keyboard': caps.has_rgb_keyboard,
                'battery_limit': caps.has_battery_charge_limit,
                'gpu_switching': caps.has_gpu_switching,
                'panel_overdrive': caps.has_panel_overdrive,
                'anime_matrix': caps.has_anime_matrix
            }
        }
    
    def start(self, use_session_bus: bool = False) -> bool:
        """
        Start the daemon.
        
        Args:
            use_session_bus: Use session D-Bus instead of system bus
            
        Returns:
            True if started successfully
        """
        if self._running:
            self.logger.warning("Daemon already running")
            return False
        
        self.logger.info("Starting ASUS Control Daemon...")
        
        # Detect hardware
        caps = self._detector.detect()
        
        if not caps.is_asus:
            self.logger.warning("Not running on ASUS hardware - limited functionality")
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        self._running = True
        
        # Start D-Bus service in background thread
        if self._dbus_service.is_available:
            self._dbus_thread = threading.Thread(
                target=self._run_dbus_service,
                args=(use_session_bus,),
                daemon=True
            )
            self._dbus_thread.start()
        else:
            self.logger.warning("D-Bus not available - running without D-Bus interface")
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitor_thread.start()
        
        # Apply last active profile
        active_profile = self._config.get('active_profile')
        if active_profile:
            self.logger.info(f"Restoring profile: {active_profile}")
            self._profile_manager.apply_profile(active_profile)
        
        self.logger.info("Daemon started successfully")
        return True
    
    def _run_dbus_service(self, use_session_bus: bool) -> None:
        """Run D-Bus service in background."""
        if self._dbus_service.start(use_session_bus):
            self._dbus_service.run()
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        self.logger.debug("Starting monitoring loop")
        
        while self._running:
            try:
                self._poll_hardware()
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
            
            time.sleep(self._poll_interval)
    
    def _poll_hardware(self) -> None:
        """Poll hardware status."""
        # Check temperatures
        temps = self._thermal.get_all_temperatures()
        if temps != self._last_temps:
            self._last_temps = temps
            self._emit_event('temperature', temps)
            
            # Check for thermal throttling
            if self._thermal.is_thermal_throttling():
                self.logger.warning("Thermal throttling detected!")
        
        # Check AC power state
        ac_state = self._battery.get_ac_status()
        if ac_state != self._last_ac_state:
            self._last_ac_state = ac_state
            self._emit_event('ac_power', {'connected': ac_state})
            
            # Could implement auto profile switching here
            # e.g., switch to Silent when on battery
    
    def _emit_event(self, event_type: str, data: Any) -> None:
        """Emit an event to registered callbacks."""
        for callback in self._callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
    
    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register an event callback."""
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
    
    def unregister_callback(self, event_type: str, callback: Callable) -> None:
        """Unregister an event callback."""
        if event_type in self._callbacks and callback in self._callbacks[event_type]:
            self._callbacks[event_type].remove(callback)
    
    def stop(self) -> None:
        """Stop the daemon."""
        self.logger.info("Stopping daemon...")
        self._running = False
        
        # Stop D-Bus service
        if self._dbus_service:
            self._dbus_service.stop()
        
        # Wait for threads
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        
        self.logger.info("Daemon stopped")
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle system signals."""
        self.logger.info(f"Received signal {signum}")
        self.stop()
    
    def run_forever(self) -> None:
        """Run the daemon until stopped."""
        if not self._running:
            self.start()
        
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    # API methods for direct control
    
    def set_cpu_mode(self, mode: str) -> bool:
        """Set CPU performance mode."""
        from ..hardware.cpu_control import CPUMode
        try:
            cpu_mode = CPUMode(mode)
            return self._cpu.set_mode(cpu_mode)
        except ValueError:
            return False
    
    def set_fan_speed(self, speed: int, fan_id: int = 0) -> bool:
        """Set fan speed percentage."""
        return self._fan.set_fan_speed(speed, fan_id)
    
    def set_rgb_mode(self, mode: str, color: Optional[str] = None) -> bool:
        """Set RGB mode and optionally color."""
        from ..hardware.rgb_control import RGBMode, RGBColor
        try:
            rgb_mode = RGBMode(mode)
            if color:
                rgb_color = RGBColor.from_hex(color)
                return self._rgb.apply_config(rgb_mode, rgb_color)
            return self._rgb.set_mode(rgb_mode)
        except ValueError:
            return False
    
    def set_charge_limit(self, limit: int) -> bool:
        """Set battery charge limit."""
        return self._battery.set_charge_limit(limit)
    
    def apply_profile(self, name: str) -> bool:
        """Apply a performance profile."""
        return self._profile_manager.apply_profile(name)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'cpu_mode': self._cpu.get_current_mode().value if self._cpu.get_current_mode() else None,
            'temperatures': self._thermal.get_all_temperatures(),
            'thermal_status': self._thermal.get_thermal_status(),
            'battery': self._battery.get_battery_info(),
            'ac_connected': self._battery.get_ac_status(),
            'active_profile': self._profile_manager.current_profile,
            'rgb_state': self._rgb.get_current_state()
        }


def main():
    """Main entry point for the daemon."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ASUS Armoury Crate Linux Daemon')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--session', action='store_true', help='Use session D-Bus')
    parser.add_argument('--detect', action='store_true', help='Run hardware detection and exit')
    
    args = parser.parse_args()
    
    daemon = AsusControlDaemon(debug=args.debug)
    
    if args.detect:
        # Just run detection and print results
        caps = daemon.detect_hardware()
        print(json.dumps(caps, indent=2))
        return
    
    # Run daemon
    daemon.start(use_session_bus=args.session)
    daemon.run_forever()


if __name__ == '__main__':
    main()
