"""
Hardware detection module for ASUS laptops.

Detects hardware capabilities and determines which features are available.
"""

import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ..utils.helpers import (
    read_sysfs, 
    find_asus_wmi_paths, 
    get_dmi_info,
    run_command
)
from ..utils.logger import get_logger


@dataclass
class HardwareCapabilities:
    """Detected hardware capabilities."""
    is_asus: bool = False
    model_name: str = ""
    model_family: str = ""
    
    # Feature availability
    has_performance_modes: bool = False
    has_fan_control: bool = False
    has_rgb_keyboard: bool = False
    has_battery_charge_limit: bool = False
    has_gpu_switching: bool = False
    has_panel_overdrive: bool = False
    has_anime_matrix: bool = False
    
    # Available performance modes
    performance_modes: List[str] = field(default_factory=list)
    
    # CPU info
    cpu_model: str = ""
    cpu_cores: int = 0
    
    # GPU info
    has_dgpu: bool = False
    igpu_name: str = ""
    dgpu_name: str = ""
    
    # System paths
    sysfs_paths: Dict[str, Optional[str]] = field(default_factory=dict)


class HardwareDetector:
    """
    Detects ASUS laptop hardware and available features.
    
    This class probes the system to determine which hardware features
    are available and can be controlled.
    """
    
    # Known ASUS laptop families
    KNOWN_FAMILIES = [
        'ROG', 'TUF', 'Zephyrus', 'Strix', 'Flow', 
        'VivoBook', 'ZenBook', 'ExpertBook', 'ProArt'
    ]
    
    # Performance mode names
    PERFORMANCE_MODES = {
        0: 'balanced',
        1: 'turbo',  # Also called "Performance" 
        2: 'silent'
    }
    
    def __init__(self):
        """Initialize hardware detector."""
        self.logger = get_logger()
        self._capabilities: Optional[HardwareCapabilities] = None
    
    def detect(self) -> HardwareCapabilities:
        """
        Perform full hardware detection.
        
        Returns:
            HardwareCapabilities object with detected features
        """
        self.logger.info("Starting hardware detection...")
        
        caps = HardwareCapabilities()
        
        # Get DMI info
        dmi = get_dmi_info()
        
        # Check if ASUS system
        vendor = dmi.get('vendor', '').lower()
        caps.is_asus = 'asus' in vendor or 'asustek' in vendor
        
        if not caps.is_asus:
            self.logger.warning("Not an ASUS system detected")
            self._capabilities = caps
            return caps
        
        caps.model_name = dmi.get('product_name', 'Unknown')
        caps.model_family = self._detect_family(dmi)
        
        self.logger.info(f"Detected ASUS {caps.model_family}: {caps.model_name}")
        
        # Get sysfs paths
        caps.sysfs_paths = find_asus_wmi_paths()
        
        # Detect features
        self._detect_performance_modes(caps)
        self._detect_fan_control(caps)
        self._detect_rgb_keyboard(caps)
        self._detect_battery_control(caps)
        self._detect_gpu(caps)
        self._detect_panel_features(caps)
        self._detect_anime_matrix(caps)
        self._detect_cpu_info(caps)
        
        self._capabilities = caps
        self._log_capabilities(caps)
        
        return caps
    
    def _detect_family(self, dmi: Dict[str, Any]) -> str:
        """Detect ASUS laptop family from DMI info."""
        product_name = dmi.get('product_name', '')
        product_family = dmi.get('product_family', '')
        
        combined = f"{product_name} {product_family}"
        
        for family in self.KNOWN_FAMILIES:
            if family.lower() in combined.lower():
                return family
        
        return "Unknown"
    
    def _detect_performance_modes(self, caps: HardwareCapabilities) -> None:
        """Detect available performance/thermal modes."""
        throttle_path = caps.sysfs_paths.get('throttle_thermal_policy')
        
        if throttle_path and os.path.exists(throttle_path):
            caps.has_performance_modes = True
            caps.performance_modes = ['silent', 'balanced', 'turbo']
            self.logger.debug(f"Found throttle_thermal_policy at {throttle_path}")
        else:
            # Check for asusctl support
            ret, out, _ = run_command(['which', 'asusctl'])
            if ret == 0:
                caps.has_performance_modes = True
                caps.performance_modes = ['silent', 'balanced', 'turbo']
                self.logger.debug("Performance modes available via asusctl")
    
    def _detect_fan_control(self, caps: HardwareCapabilities) -> None:
        """Detect fan control capabilities."""
        # Check for ASUS fan control via hwmon
        hwmon_path = '/sys/class/hwmon'
        
        if os.path.exists(hwmon_path):
            for hwmon_dir in os.listdir(hwmon_path):
                name_path = os.path.join(hwmon_path, hwmon_dir, 'name')
                name = read_sysfs(name_path)
                
                if name and 'asus' in name.lower():
                    # Check for fan control files
                    fan_path = os.path.join(hwmon_path, hwmon_dir)
                    if os.path.exists(os.path.join(fan_path, 'pwm1')):
                        caps.has_fan_control = True
                        self.logger.debug(f"Found ASUS fan control at {fan_path}")
                        break
        
        # Also check for faustus or asus-fan-control modules
        if not caps.has_fan_control:
            kernel_modules = read_sysfs('/proc/modules') or ''
            if 'faustus' in kernel_modules or 'asus_fan' in kernel_modules:
                caps.has_fan_control = True
                self.logger.debug("Fan control available via kernel module")
    
    def _detect_rgb_keyboard(self, caps: HardwareCapabilities) -> None:
        """Detect RGB keyboard support."""
        # Check for ASUS keyboard RGB via sysfs
        kbd_path = caps.sysfs_paths.get('kbd_rgb_mode')
        
        if kbd_path and os.path.exists(kbd_path):
            caps.has_rgb_keyboard = True
            self.logger.debug(f"Found RGB keyboard control at {kbd_path}")
            return
        
        # Check for aura support via asusctl
        ret, out, _ = run_command(['which', 'asusctl'])
        if ret == 0:
            ret, out, _ = run_command(['asusctl', 'led-mode', '-s'])
            if ret == 0 and out:
                caps.has_rgb_keyboard = True
                self.logger.debug("RGB keyboard available via asusctl")
                return
        
        # Check for OpenRGB support
        ret, _, _ = run_command(['which', 'openrgb'])
        if ret == 0:
            caps.has_rgb_keyboard = True
            self.logger.debug("RGB control available via OpenRGB")
    
    def _detect_battery_control(self, caps: HardwareCapabilities) -> None:
        """Detect battery charge limit control."""
        charge_path = caps.sysfs_paths.get('charge_control_end_threshold')
        
        if charge_path and os.path.exists(charge_path):
            caps.has_battery_charge_limit = True
            self.logger.debug(f"Found battery charge limit at {charge_path}")
    
    def _detect_gpu(self, caps: HardwareCapabilities) -> None:
        """Detect GPU information and switching capability."""
        # Check for dGPU
        ret, out, _ = run_command(['lspci', '-nn'])
        if ret == 0 and out:
            lines = out.split('\n')
            for line in lines:
                lower_line = line.lower()
                if 'vga' in lower_line or '3d' in lower_line:
                    if 'nvidia' in lower_line:
                        caps.has_dgpu = True
                        caps.dgpu_name = self._extract_gpu_name(line)
                    elif 'amd' in lower_line and 'radeon' in lower_line:
                        if 'integrated' not in lower_line:
                            caps.has_dgpu = True
                            caps.dgpu_name = self._extract_gpu_name(line)
                        else:
                            caps.igpu_name = self._extract_gpu_name(line)
                    elif 'intel' in lower_line:
                        caps.igpu_name = self._extract_gpu_name(line)
        
        # Check for GPU MUX switch
        mux_path = caps.sysfs_paths.get('gpu_mux_mode')
        dgpu_path = caps.sysfs_paths.get('dgpu_disable')
        
        if mux_path or dgpu_path:
            caps.has_gpu_switching = True
            self.logger.debug("GPU switching available via ASUS WMI")
        else:
            # Check for supergfxctl
            ret, _, _ = run_command(['which', 'supergfxctl'])
            if ret == 0:
                caps.has_gpu_switching = True
                self.logger.debug("GPU switching available via supergfxctl")
    
    def _extract_gpu_name(self, lspci_line: str) -> str:
        """Extract GPU name from lspci output line."""
        # Try to extract the GPU name from the line
        match = re.search(r'\[([^\]]+)\]$', lspci_line)
        if match:
            return match.group(1)
        
        # Fallback: get everything after the first colon
        parts = lspci_line.split(':', 2)
        if len(parts) >= 3:
            return parts[2].strip()[:50]  # Limit length
        
        return "Unknown GPU"
    
    def _detect_panel_features(self, caps: HardwareCapabilities) -> None:
        """Detect panel overdrive and other display features."""
        panel_od_path = caps.sysfs_paths.get('panel_od')
        
        if panel_od_path and os.path.exists(panel_od_path):
            caps.has_panel_overdrive = True
            self.logger.debug(f"Found panel overdrive at {panel_od_path}")
    
    def _detect_anime_matrix(self, caps: HardwareCapabilities) -> None:
        """Detect Anime Matrix LED support."""
        # Check for anime matrix device
        anime_paths = [
            '/sys/class/leds/asus::anime_matrix',
            '/dev/asusd-anime'
        ]
        
        for path in anime_paths:
            if os.path.exists(path):
                caps.has_anime_matrix = True
                self.logger.debug(f"Found Anime Matrix at {path}")
                return
        
        # Check via asusctl
        ret, out, _ = run_command(['asusctl', 'anime', '-h'])
        if ret == 0 and 'error' not in out.lower():
            caps.has_anime_matrix = True
            self.logger.debug("Anime Matrix available via asusctl")
    
    def _detect_cpu_info(self, caps: HardwareCapabilities) -> None:
        """Detect CPU information."""
        cpuinfo = read_sysfs('/proc/cpuinfo')
        
        if cpuinfo:
            for line in cpuinfo.split('\n'):
                if line.startswith('model name'):
                    caps.cpu_model = line.split(':')[1].strip()
                    break
            
            # Count physical cores
            cores = set()
            current_physical = None
            for line in cpuinfo.split('\n'):
                if line.startswith('physical id'):
                    current_physical = line.split(':')[1].strip()
                elif line.startswith('core id') and current_physical is not None:
                    core_id = line.split(':')[1].strip()
                    cores.add(f"{current_physical}:{core_id}")
            
            caps.cpu_cores = len(cores) if cores else 1
    
    def _log_capabilities(self, caps: HardwareCapabilities) -> None:
        """Log detected capabilities."""
        self.logger.info("=== Hardware Detection Results ===")
        self.logger.info(f"Model: {caps.model_name}")
        self.logger.info(f"Family: {caps.model_family}")
        self.logger.info(f"CPU: {caps.cpu_model} ({caps.cpu_cores} cores)")
        
        if caps.has_dgpu:
            self.logger.info(f"iGPU: {caps.igpu_name}")
            self.logger.info(f"dGPU: {caps.dgpu_name}")
        else:
            self.logger.info(f"GPU: {caps.igpu_name}")
        
        features = []
        if caps.has_performance_modes:
            features.append("Performance Modes")
        if caps.has_fan_control:
            features.append("Fan Control")
        if caps.has_rgb_keyboard:
            features.append("RGB Keyboard")
        if caps.has_battery_charge_limit:
            features.append("Battery Limit")
        if caps.has_gpu_switching:
            features.append("GPU Switching")
        if caps.has_panel_overdrive:
            features.append("Panel Overdrive")
        if caps.has_anime_matrix:
            features.append("Anime Matrix")
        
        self.logger.info(f"Available Features: {', '.join(features) if features else 'None detected'}")
    
    @property
    def capabilities(self) -> HardwareCapabilities:
        """Get detected capabilities, running detection if needed."""
        if self._capabilities is None:
            self.detect()
        return self._capabilities
    
    def refresh(self) -> HardwareCapabilities:
        """Re-run hardware detection."""
        return self.detect()
