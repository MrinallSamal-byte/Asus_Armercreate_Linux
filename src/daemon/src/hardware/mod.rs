//! Hardware abstraction layer for ASUS laptops

use asus_armoury_common::{
    ArmouryResult, FanCurve, GpuMode, HardwareCapabilities, PerformanceMode,
    RgbSettings, SystemStatus,
};
use log::info;
use std::path::Path;

mod sysfs;
mod asusctl;

pub use sysfs::SysfsInterface;

/// Main hardware controller managing all hardware interactions
pub struct HardwareController {
    /// Detected hardware capabilities
    pub capabilities: HardwareCapabilities,
    /// Sysfs interface for direct hardware access
    sysfs: SysfsInterface,
    /// Current performance mode
    current_performance_mode: PerformanceMode,
    /// Current GPU mode
    current_gpu_mode: GpuMode,
}

impl HardwareController {
    /// Create a new hardware controller and detect capabilities
    pub fn new() -> ArmouryResult<Self> {
        let sysfs = SysfsInterface::new();
        let capabilities = Self::detect_capabilities(&sysfs);
        
        info!("Hardware controller initialized");
        
        Ok(Self {
            capabilities,
            sysfs,
            current_performance_mode: PerformanceMode::Balanced,
            current_gpu_mode: GpuMode::Hybrid,
        })
    }

    /// Create a dummy controller for systems without ASUS hardware
    pub fn dummy() -> Self {
        Self {
            capabilities: HardwareCapabilities::default(),
            sysfs: SysfsInterface::new(),
            current_performance_mode: PerformanceMode::Balanced,
            current_gpu_mode: GpuMode::Hybrid,
        }
    }

    /// Detect hardware capabilities
    fn detect_capabilities(sysfs: &SysfsInterface) -> HardwareCapabilities {
        let mut caps = HardwareCapabilities::default();

        // Detect model name
        caps.model_name = sysfs.read_model_name();

        // Check for ASUS WMI interface
        let asus_wmi_exists = Path::new("/sys/devices/platform/asus-nb-wmi").exists();
        
        if asus_wmi_exists {
            info!("ASUS WMI interface detected");
            
            // Check for platform_profile (performance modes)
            caps.performance_modes = Path::new("/sys/firmware/acpi/platform_profile").exists();
            
            // Check for fan control
            caps.fan_control = sysfs.has_fan_control();
            
            // Check for battery charge limit
            caps.battery_limit = sysfs.has_battery_limit();
            
            // Check for keyboard backlight/RGB
            caps.rgb_keyboard = sysfs.has_rgb_keyboard();
        }

        // Check for supergfxd (GPU switching)
        caps.gpu_switching = Self::check_supergfxd_available();

        // Check for anime matrix
        caps.anime_matrix = Path::new("/sys/devices/platform/asus-nb-wmi/anime_matrix").exists();

        caps
    }

    /// Check if supergfxd is available
    fn check_supergfxd_available() -> bool {
        // Check if supergfxd service exists
        Path::new("/usr/bin/supergfxctl").exists()
    }

    // ==================== Performance Mode ====================

    /// Get current performance mode
    pub fn get_performance_mode(&self) -> PerformanceMode {
        self.sysfs.read_platform_profile()
            .unwrap_or(self.current_performance_mode)
    }

    /// Set performance mode
    pub fn set_performance_mode(&mut self, mode: PerformanceMode) -> ArmouryResult<()> {
        if !self.capabilities.performance_modes {
            return Err(asus_armoury_common::ArmouryError::FeatureNotAvailable(
                "Performance modes not supported on this hardware".to_string()
            ));
        }

        self.sysfs.write_platform_profile(mode)?;
        self.current_performance_mode = mode;
        info!("Performance mode set to: {}", mode);
        Ok(())
    }

    // ==================== GPU Mode ====================

    /// Get current GPU mode
    pub fn get_gpu_mode(&self) -> GpuMode {
        self.current_gpu_mode
    }

    /// Set GPU mode (requires supergfxctl)
    pub fn set_gpu_mode(&mut self, mode: GpuMode) -> ArmouryResult<()> {
        if !self.capabilities.gpu_switching {
            return Err(asus_armoury_common::ArmouryError::FeatureNotAvailable(
                "GPU switching not supported (supergfxctl not found)".to_string()
            ));
        }

        // Use supergfxctl to switch GPU mode
        let mode_str = match mode {
            GpuMode::Integrated => "Integrated",
            GpuMode::Dedicated => "Dedicated",
            GpuMode::Hybrid => "Hybrid",
            GpuMode::Compute => "Compute",
        };

        let output = std::process::Command::new("supergfxctl")
            .args(["-m", mode_str])
            .output();

        match output {
            Ok(out) if out.status.success() => {
                self.current_gpu_mode = mode;
                info!("GPU mode set to: {}", mode);
                Ok(())
            }
            Ok(out) => {
                let stderr = String::from_utf8_lossy(&out.stderr);
                Err(asus_armoury_common::ArmouryError::HardwareError(
                    format!("Failed to set GPU mode: {}", stderr)
                ))
            }
            Err(e) => {
                Err(asus_armoury_common::ArmouryError::HardwareError(
                    format!("Failed to execute supergfxctl: {}", e)
                ))
            }
        }
    }

    // ==================== Fan Control ====================

    /// Get current fan speeds (CPU, GPU) in RPM
    pub fn get_fan_speeds(&self) -> (u32, u32) {
        self.sysfs.read_fan_speeds()
    }

    /// Set fan curve
    pub fn set_fan_curve(&mut self, curve: &FanCurve) -> ArmouryResult<()> {
        if !self.capabilities.fan_control {
            return Err(asus_armoury_common::ArmouryError::FeatureNotAvailable(
                "Fan control not supported on this hardware".to_string()
            ));
        }

        self.sysfs.write_fan_curve(curve)?;
        info!("Fan curve applied: {}", curve.name);
        Ok(())
    }

    /// Reset fan control to automatic
    pub fn reset_fan_auto(&mut self) -> ArmouryResult<()> {
        if !self.capabilities.fan_control {
            return Err(asus_armoury_common::ArmouryError::FeatureNotAvailable(
                "Fan control not supported on this hardware".to_string()
            ));
        }

        self.sysfs.reset_fan_auto()?;
        info!("Fan control reset to automatic");
        Ok(())
    }

    // ==================== Temperature ====================

    /// Get current temperatures (CPU, GPU) in Celsius
    pub fn get_temperatures(&self) -> (f32, f32) {
        self.sysfs.read_temperatures()
    }

    // ==================== RGB Keyboard ====================

    /// Get current RGB settings
    pub fn get_rgb_settings(&self) -> RgbSettings {
        // TODO: Read from hardware
        RgbSettings::default()
    }

    /// Set RGB settings
    pub fn set_rgb_settings(&mut self, settings: &RgbSettings) -> ArmouryResult<()> {
        if !self.capabilities.rgb_keyboard {
            return Err(asus_armoury_common::ArmouryError::FeatureNotAvailable(
                "RGB keyboard not supported on this hardware".to_string()
            ));
        }

        self.sysfs.write_rgb_settings(settings)?;
        info!("RGB settings applied: effect={}, brightness={}", settings.effect, settings.brightness);
        Ok(())
    }

    // ==================== Battery ====================

    /// Get current battery charge limit
    pub fn get_battery_limit(&self) -> u8 {
        self.sysfs.read_battery_limit().unwrap_or(100)
    }

    /// Set battery charge limit
    pub fn set_battery_limit(&mut self, limit: u8) -> ArmouryResult<()> {
        if !self.capabilities.battery_limit {
            return Err(asus_armoury_common::ArmouryError::FeatureNotAvailable(
                "Battery charge limit not supported on this hardware".to_string()
            ));
        }

        // Validate limit
        let valid_limits = [60, 80, 100];
        if !valid_limits.contains(&limit) {
            return Err(asus_armoury_common::ArmouryError::InvalidValue(
                format!("Invalid battery limit: {}. Valid values: 60, 80, 100", limit)
            ));
        }

        self.sysfs.write_battery_limit(limit)?;
        info!("Battery charge limit set to: {}%", limit);
        Ok(())
    }

    // ==================== System Status ====================

    /// Get comprehensive system status
    pub fn get_system_status(&self) -> SystemStatus {
        let (cpu_temp, gpu_temp) = self.get_temperatures();
        let (cpu_fan, gpu_fan) = self.get_fan_speeds();
        let (cpu_usage, gpu_usage) = self.sysfs.read_cpu_gpu_usage();
        let (battery_percent, ac_connected) = self.sysfs.read_battery_status();
        let power_draw = self.sysfs.read_power_draw();

        SystemStatus {
            cpu_temp,
            gpu_temp,
            cpu_usage,
            gpu_usage,
            cpu_fan_rpm: cpu_fan,
            gpu_fan_rpm: gpu_fan,
            battery_percent,
            ac_connected,
            power_draw,
        }
    }
}
