"""
Profile manager for ASUS Armoury Crate Linux.

Manages performance profiles and their application.
"""

import os
import json
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, asdict
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.config import Config, PerformanceProfile, FanCurve, RGBConfig
from ..hardware.cpu_control import CPUController, CPUMode
from ..hardware.fan_control import FanController, FanCurvePoint
from ..hardware.rgb_control import RGBController, RGBMode, RGBColor
from ..hardware.battery_control import BatteryController


class ProfileManager:
    """
    Manages performance profiles and their application.
    
    Profiles combine CPU mode, fan curves, RGB settings, and battery limits
    into a single configuration that can be quickly applied.
    """
    
    # Profiles directory
    USER_PROFILES_DIR = "~/.config/asus-armoury/profiles"
    SYSTEM_PROFILES_DIR = "/etc/asus-armoury/profiles"
    
    def __init__(
        self,
        config: Optional[Config] = None,
        cpu_controller: Optional[CPUController] = None,
        fan_controller: Optional[FanController] = None,
        rgb_controller: Optional[RGBController] = None,
        battery_controller: Optional[BatteryController] = None
    ):
        """
        Initialize profile manager.
        
        Args:
            config: Configuration manager
            cpu_controller: CPU controller instance
            fan_controller: Fan controller instance
            rgb_controller: RGB controller instance
            battery_controller: Battery controller instance
        """
        self.logger = get_logger()
        
        self._config = config or Config()
        self._cpu = cpu_controller or CPUController()
        self._fan = fan_controller or FanController()
        self._rgb = rgb_controller or RGBController()
        self._battery = battery_controller or BatteryController()
        
        self._profiles: Dict[str, PerformanceProfile] = {}
        self._current_profile: Optional[str] = None
        self._listeners: List[Callable[[str], None]] = []
        
        self._load_profiles()
    
    def _load_profiles(self) -> None:
        """Load profiles from config and profile directories."""
        # Load from config
        self._profiles = self._config.get_all_profiles()
        
        # Load custom profiles from user directory
        user_dir = Path(self.USER_PROFILES_DIR).expanduser()
        if user_dir.exists():
            self._load_profiles_from_directory(user_dir)
        
        # Load system profiles
        system_dir = Path(self.SYSTEM_PROFILES_DIR)
        if system_dir.exists():
            self._load_profiles_from_directory(system_dir)
        
        self.logger.info(f"Loaded {len(self._profiles)} profiles")
    
    def _load_profiles_from_directory(self, directory: Path) -> None:
        """Load profile files from a directory."""
        for file_path in directory.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                profile = self._parse_profile_data(data)
                if profile and profile.name not in self._profiles:
                    self._profiles[profile.name] = profile
                    
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Failed to load profile {file_path}: {e}")
    
    def _parse_profile_data(self, data: dict) -> Optional[PerformanceProfile]:
        """Parse profile data from dictionary."""
        try:
            fan_curve_data = data.get('fan_curve', {})
            rgb_data = data.get('rgb_config', {})
            
            return PerformanceProfile(
                name=data.get('name', 'Custom'),
                cpu_mode=data.get('cpu_mode', 'balanced'),
                gpu_mode=data.get('gpu_mode', 'hybrid'),
                fan_curve=FanCurve(
                    name=fan_curve_data.get('name', 'Custom'),
                    points=fan_curve_data.get('points', [])
                ),
                rgb_config=RGBConfig(
                    mode=rgb_data.get('mode', 'static'),
                    color=rgb_data.get('color', '#FF0000'),
                    brightness=rgb_data.get('brightness', 100),
                    speed=rgb_data.get('speed', 50)
                ),
                battery_charge_limit=data.get('battery_charge_limit', 100)
            )
        except Exception as e:
            self.logger.error(f"Failed to parse profile data: {e}")
            return None
    
    @property
    def profiles(self) -> Dict[str, PerformanceProfile]:
        """Get all available profiles."""
        return self._profiles.copy()
    
    @property
    def profile_names(self) -> List[str]:
        """Get list of profile names."""
        return list(self._profiles.keys())
    
    @property
    def current_profile(self) -> Optional[str]:
        """Get name of currently active profile."""
        return self._current_profile
    
    def get_profile(self, name: str) -> Optional[PerformanceProfile]:
        """Get a profile by name."""
        return self._profiles.get(name)
    
    def add_profile(self, profile: PerformanceProfile) -> bool:
        """
        Add or update a profile.
        
        Args:
            profile: Profile to add
            
        Returns:
            True if successful
        """
        self._profiles[profile.name] = profile
        self._config.set_profile(profile.name, profile)
        return self._config.save()
    
    def remove_profile(self, name: str) -> bool:
        """
        Remove a profile.
        
        Args:
            name: Profile name to remove
            
        Returns:
            True if successful
        """
        if name in ['Silent', 'Balanced', 'Turbo', 'Gaming']:
            self.logger.warning(f"Cannot remove built-in profile: {name}")
            return False
        
        if name in self._profiles:
            del self._profiles[name]
            return True
        
        return False
    
    def apply_profile(self, name: str) -> bool:
        """
        Apply a profile.
        
        Args:
            name: Profile name to apply
            
        Returns:
            True if all settings applied successfully
        """
        profile = self._profiles.get(name)
        if not profile:
            self.logger.error(f"Profile not found: {name}")
            return False
        
        self.logger.info(f"Applying profile: {name}")
        
        success = True
        errors = []
        
        # Apply CPU mode
        try:
            cpu_mode = CPUMode(profile.cpu_mode)
            if self._cpu.is_available and not self._cpu.set_mode(cpu_mode):
                errors.append("CPU mode")
        except ValueError:
            errors.append("CPU mode (invalid)")
        
        # Apply fan curve
        if self._fan.is_available and profile.fan_curve.points:
            curve = [
                FanCurvePoint(p['temp'], p['speed']) 
                for p in profile.fan_curve.points
            ]
            if not self._fan.set_fan_curve(curve):
                errors.append("Fan curve")
        
        # Apply RGB settings
        if self._rgb.is_available:
            try:
                rgb_mode = RGBMode(profile.rgb_config.mode)
                color = RGBColor.from_hex(profile.rgb_config.color)
                
                if not self._rgb.apply_config(
                    mode=rgb_mode,
                    color=color,
                    brightness=profile.rgb_config.brightness,
                    speed=profile.rgb_config.speed
                ):
                    errors.append("RGB settings")
            except ValueError:
                errors.append("RGB settings (invalid)")
        
        # Apply battery charge limit
        if self._battery.is_available:
            if not self._battery.set_charge_limit(profile.battery_charge_limit):
                errors.append("Battery limit")
        
        if errors:
            self.logger.warning(f"Profile {name} applied with errors: {', '.join(errors)}")
            success = False
        else:
            self.logger.info(f"Profile {name} applied successfully")
        
        # Update current profile
        self._current_profile = name
        self._config.set_active_profile(name)
        self._config.save()
        
        # Notify listeners
        self._notify_profile_change(name)
        
        return success
    
    def save_current_as_profile(self, name: str) -> bool:
        """
        Save current settings as a new profile.
        
        Args:
            name: Name for the new profile
            
        Returns:
            True if successful
        """
        # Get current settings
        cpu_mode = self._cpu.get_current_mode()
        rgb_state = self._rgb.get_current_state()
        charge_limit = self._battery.get_charge_limit()
        fan_curve = self._fan.get_fan_curve()
        
        # Create profile
        profile = PerformanceProfile(
            name=name,
            cpu_mode=cpu_mode.value if cpu_mode else 'balanced',
            gpu_mode='hybrid',  # Default
            fan_curve=FanCurve(
                name=f"{name} Curve",
                points=[
                    {'temp': p.temperature, 'speed': p.speed_percent}
                    for p in fan_curve
                ] if fan_curve else []
            ),
            rgb_config=RGBConfig(
                mode=rgb_state.mode.value if rgb_state else 'static',
                color=rgb_state.color.to_hex() if rgb_state else '#FF0000',
                brightness=rgb_state.brightness if rgb_state else 100,
                speed=rgb_state.speed if rgb_state else 50
            ),
            battery_charge_limit=charge_limit or 100
        )
        
        return self.add_profile(profile)
    
    def export_profile(self, name: str, file_path: str) -> bool:
        """
        Export a profile to a file.
        
        Args:
            name: Profile name
            file_path: Path to export to
            
        Returns:
            True if successful
        """
        profile = self._profiles.get(name)
        if not profile:
            return False
        
        try:
            data = {
                'name': profile.name,
                'cpu_mode': profile.cpu_mode,
                'gpu_mode': profile.gpu_mode,
                'fan_curve': asdict(profile.fan_curve),
                'rgb_config': asdict(profile.rgb_config),
                'battery_charge_limit': profile.battery_charge_limit
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except IOError as e:
            self.logger.error(f"Failed to export profile: {e}")
            return False
    
    def import_profile(self, file_path: str) -> Optional[str]:
        """
        Import a profile from a file.
        
        Args:
            file_path: Path to import from
            
        Returns:
            Profile name if successful, None otherwise
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            profile = self._parse_profile_data(data)
            if profile:
                self.add_profile(profile)
                return profile.name
                
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Failed to import profile: {e}")
        
        return None
    
    def add_listener(self, callback: Callable[[str], None]) -> None:
        """
        Add a profile change listener.
        
        Args:
            callback: Function to call when profile changes
        """
        self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[str], None]) -> None:
        """Remove a profile change listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_profile_change(self, profile_name: str) -> None:
        """Notify listeners of profile change."""
        for listener in self._listeners:
            try:
                listener(profile_name)
            except Exception as e:
                self.logger.error(f"Profile listener error: {e}")
