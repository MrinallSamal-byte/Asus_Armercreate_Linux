//! Sysfs interface for direct hardware access
//!
//! This module provides low-level access to ASUS hardware through the Linux sysfs interface.

use asus_armoury_common::{ArmouryResult, ArmouryError, FanCurve, PerformanceMode, RgbSettings};
use log::{debug, warn};
use std::fs;
use std::path::Path;

// ASUS-specific sysfs paths
const PLATFORM_PROFILE: &str = "/sys/firmware/acpi/platform_profile";
const PLATFORM_PROFILE_CHOICES: &str = "/sys/firmware/acpi/platform_profile_choices";
const ASUS_WMI_PATH: &str = "/sys/devices/platform/asus-nb-wmi";
const BATTERY_LIMIT_PATH: &str = "/sys/class/power_supply/BAT0/charge_control_end_threshold";
const BATTERY_LIMIT_PATH_ALT: &str = "/sys/class/power_supply/BAT1/charge_control_end_threshold";

// Thermal zone paths for temperature reading
const THERMAL_ZONE_BASE: &str = "/sys/class/thermal/thermal_zone";
const HWMON_PATH: &str = "/sys/class/hwmon";

/// Interface for reading/writing sysfs values
pub struct SysfsInterface {
    /// Cached battery limit path (BAT0 or BAT1)
    battery_limit_path: Option<String>,
}

impl SysfsInterface {
    pub fn new() -> Self {
        // Determine which battery path exists
        let battery_limit_path = if Path::new(BATTERY_LIMIT_PATH).exists() {
            Some(BATTERY_LIMIT_PATH.to_string())
        } else if Path::new(BATTERY_LIMIT_PATH_ALT).exists() {
            Some(BATTERY_LIMIT_PATH_ALT.to_string())
        } else {
            None
        };

        Self { battery_limit_path }
    }

    // ==================== Model Detection ====================

    /// Read the laptop model name
    pub fn read_model_name(&self) -> Option<String> {
        // Try DMI product name
        if let Ok(name) = fs::read_to_string("/sys/class/dmi/id/product_name") {
            let name = name.trim().to_string();
            if !name.is_empty() {
                return Some(name);
            }
        }
        
        // Try ASUS WMI
        let wmi_path = format!("{}/product_name", ASUS_WMI_PATH);
        if let Ok(name) = fs::read_to_string(&wmi_path) {
            let name = name.trim().to_string();
            if !name.is_empty() {
                return Some(name);
            }
        }

        None
    }

    // ==================== Capability Detection ====================

    /// Check if fan control is available
    pub fn has_fan_control(&self) -> bool {
        let fan_curve_path = format!("{}/fan_curve", ASUS_WMI_PATH);
        Path::new(&fan_curve_path).exists() || self.find_hwmon_fan().is_some()
    }

    /// Check if battery limit control is available
    pub fn has_battery_limit(&self) -> bool {
        self.battery_limit_path.is_some()
    }

    /// Check if RGB keyboard control is available
    pub fn has_rgb_keyboard(&self) -> bool {
        // Check for ASUS keyboard backlight
        let kbd_backlight = "/sys/class/leds/asus::kbd_backlight";
        if Path::new(kbd_backlight).exists() {
            return true;
        }

        // Check for aura_keyboard
        let aura_path = format!("{}/leds", ASUS_WMI_PATH);
        if Path::new(&aura_path).exists() {
            return true;
        }

        // Check for TUF RGB
        let tuf_rgb = "/sys/devices/platform/asus-nb-wmi/leds/asus::kbd_backlight";
        Path::new(tuf_rgb).exists()
    }

    // ==================== Platform Profile ====================

    /// Read current platform profile (performance mode)
    pub fn read_platform_profile(&self) -> Option<PerformanceMode> {
        let content = fs::read_to_string(PLATFORM_PROFILE).ok()?;
        let profile = content.trim();
        
        match profile {
            "quiet" | "silent" => Some(PerformanceMode::Silent),
            "balanced" | "balanced-performance" => Some(PerformanceMode::Balanced),
            "performance" | "turbo" => Some(PerformanceMode::Turbo),
            _ => {
                warn!("Unknown platform profile: {}", profile);
                None
            }
        }
    }

    /// Write platform profile (performance mode)
    pub fn write_platform_profile(&self, mode: PerformanceMode) -> ArmouryResult<()> {
        let profile = match mode {
            PerformanceMode::Silent => "quiet",
            PerformanceMode::Balanced => "balanced",
            PerformanceMode::Turbo => "performance",
            PerformanceMode::Manual => "balanced", // Manual uses balanced as base
        };

        fs::write(PLATFORM_PROFILE, profile).map_err(|e| {
            if e.kind() == std::io::ErrorKind::PermissionDenied {
                ArmouryError::PermissionDenied("Cannot write platform profile (root required)".to_string())
            } else {
                ArmouryError::IoError(e)
            }
        })
    }

    // ==================== Temperature Reading ====================

    /// Read CPU and GPU temperatures
    pub fn read_temperatures(&self) -> (f32, f32) {
        let cpu_temp = self.read_cpu_temperature().unwrap_or(0.0);
        let gpu_temp = self.read_gpu_temperature().unwrap_or(0.0);
        (cpu_temp, gpu_temp)
    }

    fn read_cpu_temperature(&self) -> Option<f32> {
        // Try thermal zones
        for i in 0..20 {
            let type_path = format!("{}{}/type", THERMAL_ZONE_BASE, i);
            let temp_path = format!("{}{}/temp", THERMAL_ZONE_BASE, i);
            
            if let Ok(zone_type) = fs::read_to_string(&type_path) {
                let zone_type = zone_type.trim().to_lowercase();
                if zone_type.contains("cpu") || zone_type.contains("x86_pkg") || zone_type == "acpitz" {
                    if let Ok(temp_str) = fs::read_to_string(&temp_path) {
                        if let Ok(temp) = temp_str.trim().parse::<f32>() {
                            return Some(temp / 1000.0); // Convert from millidegrees
                        }
                    }
                }
            }
        }

        // Try hwmon
        if let Some(hwmon) = self.find_hwmon_cpu() {
            if let Ok(temp_str) = fs::read_to_string(format!("{}/temp1_input", hwmon)) {
                if let Ok(temp) = temp_str.trim().parse::<f32>() {
                    return Some(temp / 1000.0);
                }
            }
        }

        None
    }

    fn read_gpu_temperature(&self) -> Option<f32> {
        // Try NVIDIA GPU
        if let Some(hwmon) = self.find_hwmon_gpu() {
            if let Ok(temp_str) = fs::read_to_string(format!("{}/temp1_input", hwmon)) {
                if let Ok(temp) = temp_str.trim().parse::<f32>() {
                    return Some(temp / 1000.0);
                }
            }
        }

        // Try AMD GPU via thermal zone
        for i in 0..20 {
            let type_path = format!("{}{}/type", THERMAL_ZONE_BASE, i);
            let temp_path = format!("{}{}/temp", THERMAL_ZONE_BASE, i);
            
            if let Ok(zone_type) = fs::read_to_string(&type_path) {
                let zone_type = zone_type.trim().to_lowercase();
                if zone_type.contains("gpu") || zone_type.contains("amdgpu") {
                    if let Ok(temp_str) = fs::read_to_string(&temp_path) {
                        if let Ok(temp) = temp_str.trim().parse::<f32>() {
                            return Some(temp / 1000.0);
                        }
                    }
                }
            }
        }

        None
    }

    // ==================== Fan Control ====================

    /// Read fan speeds (CPU, GPU) in RPM
    pub fn read_fan_speeds(&self) -> (u32, u32) {
        let cpu_fan = self.read_fan_rpm(1).unwrap_or(0);
        let gpu_fan = self.read_fan_rpm(2).unwrap_or(0);
        (cpu_fan, gpu_fan)
    }

    fn read_fan_rpm(&self, fan_num: u8) -> Option<u32> {
        if let Some(hwmon) = self.find_hwmon_fan() {
            let path = format!("{}/fan{}_input", hwmon, fan_num);
            if let Ok(rpm_str) = fs::read_to_string(&path) {
                if let Ok(rpm) = rpm_str.trim().parse::<u32>() {
                    return Some(rpm);
                }
            }
        }
        None
    }

    /// Write fan curve to hardware
    pub fn write_fan_curve(&self, curve: &FanCurve) -> ArmouryResult<()> {
        let fan_curve_path = format!("{}/fan_curve", ASUS_WMI_PATH);
        
        if !Path::new(&fan_curve_path).exists() {
            return Err(ArmouryError::FeatureNotAvailable(
                "Fan curve control not available".to_string()
            ));
        }

        // Format fan curve for ASUS WMI
        // Format: temp1:speed1,temp2:speed2,...
        let curve_str: String = curve.points
            .iter()
            .map(|p| format!("{}:{}", p.temperature, p.fan_percent))
            .collect::<Vec<_>>()
            .join(",");

        fs::write(&fan_curve_path, &curve_str).map_err(|e| {
            if e.kind() == std::io::ErrorKind::PermissionDenied {
                ArmouryError::PermissionDenied("Cannot write fan curve (root required)".to_string())
            } else {
                ArmouryError::IoError(e)
            }
        })
    }

    /// Reset fan to automatic control
    pub fn reset_fan_auto(&self) -> ArmouryResult<()> {
        let fan_curve_path = format!("{}/fan_curve", ASUS_WMI_PATH);
        
        if Path::new(&fan_curve_path).exists() {
            fs::write(&fan_curve_path, "auto").map_err(|e| {
                if e.kind() == std::io::ErrorKind::PermissionDenied {
                    ArmouryError::PermissionDenied("Cannot reset fan control (root required)".to_string())
                } else {
                    ArmouryError::IoError(e)
                }
            })
        } else {
            Ok(()) // No fan curve support, nothing to reset
        }
    }

    // ==================== RGB Keyboard ====================

    /// Write RGB settings to hardware
    pub fn write_rgb_settings(&self, settings: &RgbSettings) -> ArmouryResult<()> {
        // Try ASUS keyboard backlight brightness
        let kbd_backlight = "/sys/class/leds/asus::kbd_backlight/brightness";
        if Path::new(kbd_backlight).exists() {
            // Scale brightness to 0-3 range (typical for ASUS keyboards)
            let brightness_value = (settings.brightness as u32 * 3 / 100).min(3);
            fs::write(kbd_backlight, brightness_value.to_string()).map_err(|e| {
                if e.kind() == std::io::ErrorKind::PermissionDenied {
                    ArmouryError::PermissionDenied("Cannot write keyboard brightness (root required)".to_string())
                } else {
                    ArmouryError::IoError(e)
                }
            })?;
        }

        // Note: Full RGB control typically requires kernel module or USB HID access
        // This is a basic implementation - full Aura support would need aura-read/aura-write utilities

        Ok(())
    }

    // ==================== Battery ====================

    /// Read battery charge limit
    pub fn read_battery_limit(&self) -> Option<u8> {
        let path = self.battery_limit_path.as_ref()?;
        let content = fs::read_to_string(path).ok()?;
        content.trim().parse::<u8>().ok()
    }

    /// Write battery charge limit
    pub fn write_battery_limit(&self, limit: u8) -> ArmouryResult<()> {
        let path = self.battery_limit_path.as_ref()
            .ok_or_else(|| ArmouryError::FeatureNotAvailable(
                "Battery charge limit not available".to_string()
            ))?;

        fs::write(path, limit.to_string()).map_err(|e| {
            if e.kind() == std::io::ErrorKind::PermissionDenied {
                ArmouryError::PermissionDenied("Cannot write battery limit (root required)".to_string())
            } else {
                ArmouryError::IoError(e)
            }
        })
    }

    /// Read battery status (percentage, AC connected)
    pub fn read_battery_status(&self) -> (u8, bool) {
        let capacity = fs::read_to_string("/sys/class/power_supply/BAT0/capacity")
            .or_else(|_| fs::read_to_string("/sys/class/power_supply/BAT1/capacity"))
            .ok()
            .and_then(|s| s.trim().parse::<u8>().ok())
            .unwrap_or(0);

        let ac_online = fs::read_to_string("/sys/class/power_supply/AC0/online")
            .or_else(|_| fs::read_to_string("/sys/class/power_supply/ADP0/online"))
            .or_else(|_| fs::read_to_string("/sys/class/power_supply/ADP1/online"))
            .ok()
            .map(|s| s.trim() == "1")
            .unwrap_or(false);

        (capacity, ac_online)
    }

    // ==================== System Usage ====================

    /// Read CPU and GPU usage percentages
    pub fn read_cpu_gpu_usage(&self) -> (f32, f32) {
        // CPU usage requires reading /proc/stat and calculating delta
        // For simplicity, we'll read load average as an approximation
        let cpu_usage = self.read_cpu_usage_simple().unwrap_or(0.0);
        let gpu_usage = self.read_gpu_usage().unwrap_or(0.0);
        (cpu_usage, gpu_usage)
    }

    fn read_cpu_usage_simple(&self) -> Option<f32> {
        // Read load average as simple CPU usage indicator
        let loadavg = fs::read_to_string("/proc/loadavg").ok()?;
        let load: f32 = loadavg.split_whitespace().next()?.parse().ok()?;
        
        // Get number of CPUs
        let cpus = std::thread::available_parallelism()
            .map(|n| n.get() as f32)
            .unwrap_or(1.0);
        
        // Convert load to percentage (capped at 100%)
        Some((load / cpus * 100.0).min(100.0))
    }

    fn read_gpu_usage(&self) -> Option<f32> {
        // Try NVIDIA GPU
        if let Some(hwmon) = self.find_hwmon_gpu() {
            // Some NVIDIA drivers expose GPU utilization
            let util_path = format!("{}/gpu_busy_percent", hwmon);
            if let Ok(util_str) = fs::read_to_string(&util_path) {
                if let Ok(util) = util_str.trim().parse::<f32>() {
                    return Some(util);
                }
            }
        }

        // Try AMD GPU
        let amd_util_path = "/sys/class/drm/card0/device/gpu_busy_percent";
        if let Ok(util_str) = fs::read_to_string(amd_util_path) {
            if let Ok(util) = util_str.trim().parse::<f32>() {
                return Some(util);
            }
        }

        None
    }

    /// Read power draw in watts
    pub fn read_power_draw(&self) -> f32 {
        // Try to read from battery power_now (in microwatts)
        if let Ok(power_str) = fs::read_to_string("/sys/class/power_supply/BAT0/power_now") {
            if let Ok(power) = power_str.trim().parse::<f64>() {
                return (power / 1_000_000.0) as f32; // Convert to watts
            }
        }

        // Try energy_now approach
        if let Ok(energy_str) = fs::read_to_string("/sys/class/power_supply/BAT0/energy_now") {
            if let Ok(voltage_str) = fs::read_to_string("/sys/class/power_supply/BAT0/voltage_now") {
                if let (Ok(energy), Ok(voltage)) = (
                    energy_str.trim().parse::<f64>(),
                    voltage_str.trim().parse::<f64>()
                ) {
                    // This is approximate - actual power draw requires time delta
                    return ((energy * voltage) / 1e12) as f32;
                }
            }
        }

        0.0
    }

    // ==================== Helper Functions ====================

    fn find_hwmon_cpu(&self) -> Option<String> {
        self.find_hwmon_by_name(&["coretemp", "k10temp", "zenpower", "acpitz"])
    }

    fn find_hwmon_gpu(&self) -> Option<String> {
        self.find_hwmon_by_name(&["nvidia", "amdgpu", "nouveau", "radeon"])
    }

    fn find_hwmon_fan(&self) -> Option<String> {
        self.find_hwmon_by_name(&["asus-nb-wmi", "asus_fan", "thinkpad"])
    }

    fn find_hwmon_by_name(&self, names: &[&str]) -> Option<String> {
        let hwmon_dir = Path::new(HWMON_PATH);
        if !hwmon_dir.exists() {
            return None;
        }

        if let Ok(entries) = fs::read_dir(hwmon_dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                let name_path = path.join("name");
                if let Ok(name) = fs::read_to_string(&name_path) {
                    let name = name.trim().to_lowercase();
                    if names.iter().any(|n| name.contains(n)) {
                        return Some(path.to_string_lossy().to_string());
                    }
                }
            }
        }

        None
    }
}
