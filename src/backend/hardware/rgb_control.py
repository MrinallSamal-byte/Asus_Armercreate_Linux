"""
RGB keyboard control module for ASUS laptops.
"""

import os
from enum import Enum
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

from ..utils.helpers import read_sysfs, write_sysfs, run_command, find_asus_wmi_paths
from ..utils.logger import get_logger


class RGBMode(Enum):
    """RGB lighting modes."""
    OFF = "off"
    STATIC = "static"
    BREATHING = "breathing"
    COLOR_CYCLE = "color_cycle"
    RAINBOW = "rainbow"
    STROBE = "strobe"
    COMET = "comet"
    FLASH = "flash"
    MULTI_STATIC = "multi_static"


@dataclass
class RGBColor:
    """RGB color representation."""
    red: int
    green: int
    blue: int
    
    def __post_init__(self):
        """Validate color values."""
        self.red = max(0, min(255, self.red))
        self.green = max(0, min(255, self.green))
        self.blue = max(0, min(255, self.blue))
    
    def to_hex(self) -> str:
        """Convert to hex string."""
        return f"#{self.red:02X}{self.green:02X}{self.blue:02X}"
    
    @classmethod
    def from_hex(cls, hex_color: str) -> 'RGBColor':
        """Create from hex string."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return cls(r, g, b)
        return cls(255, 255, 255)
    
    def to_tuple(self) -> Tuple[int, int, int]:
        """Convert to tuple."""
        return (self.red, self.green, self.blue)


@dataclass
class RGBState:
    """Current RGB keyboard state."""
    mode: RGBMode
    color: RGBColor
    brightness: int  # 0-100
    speed: int  # 0-100
    enabled: bool


class RGBController:
    """
    Controls RGB keyboard lighting on ASUS laptops.
    
    Supports asusctl (aura) and direct sysfs control.
    """
    
    # Mode mapping for asusctl
    ASUSCTL_MODES = {
        RGBMode.OFF: 'Off',
        RGBMode.STATIC: 'Static',
        RGBMode.BREATHING: 'Breathe',
        RGBMode.COLOR_CYCLE: 'Spectrum',
        RGBMode.RAINBOW: 'Rainbow',
        RGBMode.STROBE: 'Strobe',
        RGBMode.COMET: 'Comet',
        RGBMode.FLASH: 'Flash',
        RGBMode.MULTI_STATIC: 'MultiStatic'
    }
    
    def __init__(self):
        """Initialize RGB controller."""
        self.logger = get_logger()
        self._paths = find_asus_wmi_paths()
        self._kbd_rgb_path = self._paths.get('kbd_rgb_mode')
        self._use_asusctl = False
        self._use_openrgb = False
        self._supported_modes: List[RGBMode] = []
        
        self._detect_rgb_control()
    
    def _detect_rgb_control(self) -> None:
        """Detect available RGB control method."""
        # Check for asusctl
        ret, _, _ = run_command(['which', 'asusctl'])
        if ret == 0:
            # Check if aura is supported
            ret, out, _ = run_command(['asusctl', 'led-mode', '-s'])
            if ret == 0:
                self._use_asusctl = True
                self._parse_supported_modes(out)
                self.logger.debug("Using asusctl for RGB control")
                return
        
        # Check for direct sysfs control
        if self._kbd_rgb_path and os.path.exists(self._kbd_rgb_path):
            self._supported_modes = [RGBMode.STATIC, RGBMode.OFF]
            self.logger.debug("Using sysfs for RGB control")
            return
        
        # Check for OpenRGB
        ret, _, _ = run_command(['which', 'openrgb'])
        if ret == 0:
            self._use_openrgb = True
            self._supported_modes = list(RGBMode)
            self.logger.debug("Using OpenRGB for RGB control")
    
    def _parse_supported_modes(self, asusctl_output: str) -> None:
        """Parse supported modes from asusctl output."""
        self._supported_modes = []
        
        reverse_map = {v.lower(): k for k, v in self.ASUSCTL_MODES.items()}
        
        for line in asusctl_output.lower().split('\n'):
            for mode_name, mode in reverse_map.items():
                if mode_name in line:
                    if mode not in self._supported_modes:
                        self._supported_modes.append(mode)
        
        # Always include OFF
        if RGBMode.OFF not in self._supported_modes:
            self._supported_modes.insert(0, RGBMode.OFF)
        
        if not self._supported_modes:
            # Default modes if parsing fails
            self._supported_modes = [
                RGBMode.OFF, RGBMode.STATIC, RGBMode.BREATHING,
                RGBMode.COLOR_CYCLE, RGBMode.RAINBOW
            ]
    
    @property
    def is_available(self) -> bool:
        """Check if RGB control is available."""
        return (
            self._use_asusctl or 
            self._use_openrgb or 
            bool(self._kbd_rgb_path)
        )
    
    @property
    def supported_modes(self) -> List[RGBMode]:
        """Get list of supported RGB modes."""
        return self._supported_modes.copy()
    
    def get_current_state(self) -> Optional[RGBState]:
        """
        Get current RGB keyboard state.
        
        Returns:
            RGBState object or None
        """
        if self._use_asusctl:
            ret, out, _ = run_command(['asusctl', 'led-mode', '-c'])
            if ret == 0 and out:
                return self._parse_asusctl_state(out)
        
        # Default state if unable to read
        return RGBState(
            mode=RGBMode.STATIC,
            color=RGBColor(255, 0, 0),
            brightness=100,
            speed=50,
            enabled=True
        )
    
    def _parse_asusctl_state(self, output: str) -> RGBState:
        """Parse RGB state from asusctl output."""
        mode = RGBMode.STATIC
        color = RGBColor(255, 0, 0)
        brightness = 100
        speed = 50
        enabled = True
        
        lines = output.lower()
        
        # Parse mode
        reverse_map = {v.lower(): k for k, v in self.ASUSCTL_MODES.items()}
        for mode_name, mode_enum in reverse_map.items():
            if mode_name in lines:
                mode = mode_enum
                break
        
        # Parse color (look for hex color)
        import re
        hex_match = re.search(r'#([0-9a-f]{6})', output, re.IGNORECASE)
        if hex_match:
            color = RGBColor.from_hex(f"#{hex_match.group(1)}")
        
        # Parse brightness
        bright_match = re.search(r'brightness[:\s]*(\d+)', output, re.IGNORECASE)
        if bright_match:
            brightness = min(100, int(bright_match.group(1)))
        
        # Check if off
        if 'off' in lines and mode != RGBMode.OFF:
            enabled = False
        
        return RGBState(mode, color, brightness, speed, enabled)
    
    def set_mode(self, mode: RGBMode) -> bool:
        """
        Set RGB lighting mode.
        
        Args:
            mode: Desired RGBMode
            
        Returns:
            True if successful
        """
        if mode not in self._supported_modes:
            self.logger.warning(f"Mode {mode.value} not supported")
            return False
        
        self.logger.info(f"Setting RGB mode to: {mode.value}")
        
        if self._use_asusctl:
            asusctl_mode = self.ASUSCTL_MODES.get(mode, 'Static')
            ret, _, err = run_command(['asusctl', 'led-mode', '-s', asusctl_mode])
            if ret == 0:
                return True
            self.logger.error(f"Failed to set RGB mode: {err}")
        
        if self._use_openrgb:
            # OpenRGB mode setting
            mode_idx = list(RGBMode).index(mode)
            ret, _, err = run_command(['openrgb', '-m', str(mode_idx)])
            if ret == 0:
                return True
            self.logger.error(f"Failed to set RGB mode via OpenRGB: {err}")
        
        return False
    
    def set_color(self, color: RGBColor) -> bool:
        """
        Set RGB color.
        
        Args:
            color: RGBColor object
            
        Returns:
            True if successful
        """
        self.logger.info(f"Setting RGB color to: {color.to_hex()}")
        
        if self._use_asusctl:
            hex_color = color.to_hex().lstrip('#')
            ret, _, err = run_command(['asusctl', 'led-mode', 'static', '-c', hex_color])
            if ret == 0:
                return True
            self.logger.error(f"Failed to set RGB color: {err}")
        
        if self._use_openrgb:
            r, g, b = color.to_tuple()
            ret, _, err = run_command(['openrgb', '-c', f'{r:02X}{g:02X}{b:02X}'])
            if ret == 0:
                return True
            self.logger.error(f"Failed to set RGB color via OpenRGB: {err}")
        
        return False
    
    def set_brightness(self, brightness: int) -> bool:
        """
        Set RGB brightness.
        
        Args:
            brightness: Brightness level (0-100)
            
        Returns:
            True if successful
        """
        brightness = max(0, min(100, brightness))
        self.logger.info(f"Setting RGB brightness to: {brightness}%")
        
        if self._use_asusctl:
            # asusctl brightness is 0-3
            asusctl_brightness = min(3, brightness // 25)
            ret, _, err = run_command(['asusctl', 'led-mode', '-b', str(asusctl_brightness)])
            if ret == 0:
                return True
            self.logger.error(f"Failed to set brightness: {err}")
        
        if self._use_openrgb:
            ret, _, err = run_command(['openrgb', '-b', str(brightness)])
            if ret == 0:
                return True
        
        return False
    
    def set_speed(self, speed: int) -> bool:
        """
        Set animation speed for animated modes.
        
        Args:
            speed: Speed level (0-100)
            
        Returns:
            True if successful
        """
        speed = max(0, min(100, speed))
        self.logger.info(f"Setting RGB speed to: {speed}%")
        
        if self._use_asusctl:
            # asusctl speed is 0-2 (slow, medium, fast)
            asusctl_speed = min(2, speed // 34)
            ret, _, err = run_command(['asusctl', 'led-mode', '--speed', str(asusctl_speed)])
            if ret == 0:
                return True
        
        return False
    
    def apply_config(
        self,
        mode: RGBMode,
        color: Optional[RGBColor] = None,
        brightness: Optional[int] = None,
        speed: Optional[int] = None
    ) -> bool:
        """
        Apply a complete RGB configuration.
        
        Args:
            mode: RGB mode
            color: Optional color
            brightness: Optional brightness
            speed: Optional animation speed
            
        Returns:
            True if all settings applied successfully
        """
        success = True
        
        if not self.set_mode(mode):
            success = False
        
        if color and mode not in [RGBMode.OFF, RGBMode.RAINBOW, RGBMode.COLOR_CYCLE]:
            if not self.set_color(color):
                success = False
        
        if brightness is not None:
            if not self.set_brightness(brightness):
                success = False
        
        if speed is not None and mode in [
            RGBMode.BREATHING, RGBMode.COLOR_CYCLE, 
            RGBMode.RAINBOW, RGBMode.STROBE, RGBMode.COMET
        ]:
            if not self.set_speed(speed):
                success = False
        
        return success
    
    def turn_off(self) -> bool:
        """Turn off RGB lighting."""
        return self.set_mode(RGBMode.OFF)
    
    def turn_on(self) -> bool:
        """Turn on RGB lighting with last settings."""
        return self.set_mode(RGBMode.STATIC)
    
    def get_preset_colors(self) -> Dict[str, RGBColor]:
        """Get preset colors."""
        return {
            'Red': RGBColor(255, 0, 0),
            'Green': RGBColor(0, 255, 0),
            'Blue': RGBColor(0, 0, 255),
            'Cyan': RGBColor(0, 255, 255),
            'Magenta': RGBColor(255, 0, 255),
            'Yellow': RGBColor(255, 255, 0),
            'Orange': RGBColor(255, 128, 0),
            'Purple': RGBColor(128, 0, 255),
            'Pink': RGBColor(255, 128, 192),
            'White': RGBColor(255, 255, 255),
            'ROG Red': RGBColor(255, 0, 50),
            'TUF Orange': RGBColor(255, 85, 0)
        }
