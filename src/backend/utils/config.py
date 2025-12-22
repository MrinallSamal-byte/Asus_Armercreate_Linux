"""
Configuration management for ASUS Armoury Crate Linux.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class FanCurve:
    """Fan curve configuration."""
    name: str = "Default"
    points: list = field(default_factory=lambda: [
        {"temp": 30, "speed": 20},
        {"temp": 50, "speed": 40},
        {"temp": 70, "speed": 60},
        {"temp": 80, "speed": 80},
        {"temp": 90, "speed": 100}
    ])


@dataclass
class RGBConfig:
    """RGB keyboard configuration."""
    mode: str = "static"
    color: str = "#FF0000"
    brightness: int = 100
    speed: int = 50


@dataclass
class PerformanceProfile:
    """Performance profile configuration."""
    name: str = "Balanced"
    cpu_mode: str = "balanced"
    gpu_mode: str = "hybrid"
    fan_curve: FanCurve = field(default_factory=FanCurve)
    rgb_config: RGBConfig = field(default_factory=RGBConfig)
    battery_charge_limit: int = 100


class Config:
    """
    Application configuration manager.
    
    Handles loading, saving, and accessing configuration settings.
    """
    
    DEFAULT_CONFIG_PATH = "~/.config/asus-armoury/config.json"
    SYSTEM_CONFIG_PATH = "/etc/asus-armoury/config.json"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        if config_path:
            self.config_path = Path(config_path).expanduser()
        else:
            # Use user config if exists, otherwise system config
            user_path = Path(self.DEFAULT_CONFIG_PATH).expanduser()
            system_path = Path(self.SYSTEM_CONFIG_PATH)
            
            if user_path.exists():
                self.config_path = user_path
            elif system_path.exists():
                self.config_path = system_path
            else:
                self.config_path = user_path
        
        self._config: Dict[str, Any] = {}
        self._profiles: Dict[str, PerformanceProfile] = {}
        self._load_defaults()
        self.load()
    
    def _load_defaults(self) -> None:
        """Load default configuration values."""
        self._config = {
            "version": "1.0.0",
            "auto_start": True,
            "minimize_to_tray": True,
            "check_updates": True,
            "dark_mode": True,
            "active_profile": "Balanced",
            "temperature_unit": "celsius",
            "polling_interval": 1000,  # milliseconds
            "enable_notifications": True,
            "safe_mode": True,  # Prevent unsafe hardware operations
        }
        
        # Default profiles
        self._profiles = {
            "Silent": PerformanceProfile(
                name="Silent",
                cpu_mode="silent",
                gpu_mode="integrated",
                fan_curve=FanCurve(
                    name="Silent",
                    points=[
                        {"temp": 30, "speed": 10},
                        {"temp": 50, "speed": 20},
                        {"temp": 70, "speed": 40},
                        {"temp": 80, "speed": 60},
                        {"temp": 90, "speed": 80}
                    ]
                ),
                rgb_config=RGBConfig(mode="off", brightness=0),
                battery_charge_limit=60
            ),
            "Balanced": PerformanceProfile(
                name="Balanced",
                cpu_mode="balanced",
                gpu_mode="hybrid",
                fan_curve=FanCurve(
                    name="Balanced",
                    points=[
                        {"temp": 30, "speed": 20},
                        {"temp": 50, "speed": 40},
                        {"temp": 70, "speed": 60},
                        {"temp": 80, "speed": 80},
                        {"temp": 90, "speed": 100}
                    ]
                ),
                rgb_config=RGBConfig(mode="static", color="#00FF00", brightness=75),
                battery_charge_limit=80
            ),
            "Turbo": PerformanceProfile(
                name="Turbo",
                cpu_mode="turbo",
                gpu_mode="dedicated",
                fan_curve=FanCurve(
                    name="Turbo",
                    points=[
                        {"temp": 30, "speed": 40},
                        {"temp": 50, "speed": 60},
                        {"temp": 70, "speed": 80},
                        {"temp": 80, "speed": 100},
                        {"temp": 90, "speed": 100}
                    ]
                ),
                rgb_config=RGBConfig(mode="rainbow", brightness=100, speed=70),
                battery_charge_limit=100
            ),
            "Gaming": PerformanceProfile(
                name="Gaming",
                cpu_mode="turbo",
                gpu_mode="dedicated",
                fan_curve=FanCurve(
                    name="Gaming",
                    points=[
                        {"temp": 30, "speed": 30},
                        {"temp": 50, "speed": 50},
                        {"temp": 70, "speed": 75},
                        {"temp": 80, "speed": 90},
                        {"temp": 90, "speed": 100}
                    ]
                ),
                rgb_config=RGBConfig(mode="breathing", color="#FF0000", brightness=100, speed=50),
                battery_charge_limit=100
            )
        }
    
    def load(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                # Merge loaded config with defaults
                self._config.update(data.get('settings', {}))
                
                # Load profiles
                for name, profile_data in data.get('profiles', {}).items():
                    fan_curve_data = profile_data.get('fan_curve', {})
                    rgb_data = profile_data.get('rgb_config', {})
                    
                    self._profiles[name] = PerformanceProfile(
                        name=profile_data.get('name', name),
                        cpu_mode=profile_data.get('cpu_mode', 'balanced'),
                        gpu_mode=profile_data.get('gpu_mode', 'hybrid'),
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
                        battery_charge_limit=profile_data.get('battery_charge_limit', 100)
                    )
                
                return True
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
        
        return False
    
    def save(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'settings': self._config,
                'profiles': {}
            }
            
            for name, profile in self._profiles.items():
                data['profiles'][name] = {
                    'name': profile.name,
                    'cpu_mode': profile.cpu_mode,
                    'gpu_mode': profile.gpu_mode,
                    'fan_curve': asdict(profile.fan_curve),
                    'rgb_config': asdict(profile.rgb_config),
                    'battery_charge_limit': profile.battery_charge_limit
                }
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
        
        return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
    
    def get_profile(self, name: str) -> Optional[PerformanceProfile]:
        """Get a performance profile by name."""
        return self._profiles.get(name)
    
    def set_profile(self, name: str, profile: PerformanceProfile) -> None:
        """Set or create a performance profile."""
        self._profiles[name] = profile
    
    def get_all_profiles(self) -> Dict[str, PerformanceProfile]:
        """Get all performance profiles."""
        return self._profiles.copy()
    
    def get_active_profile(self) -> Optional[PerformanceProfile]:
        """Get the currently active profile."""
        active_name = self.get('active_profile', 'Balanced')
        return self.get_profile(active_name)
    
    def set_active_profile(self, name: str) -> bool:
        """Set the active profile by name."""
        if name in self._profiles:
            self.set('active_profile', name)
            return True
        return False
