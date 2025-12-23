//! Integration tests for ASUS Armoury Crate Linux
//!
//! These tests verify basic functionality without requiring actual hardware.

use asus_armoury_common::*;

#[test]
fn test_performance_mode_conversions() {
    let mode = PerformanceMode::Silent;
    assert_eq!(mode.to_string(), "Silent");
    
    let mode = PerformanceMode::Balanced;
    assert_eq!(mode.to_string(), "Balanced");
    
    let mode = PerformanceMode::Turbo;
    assert_eq!(mode.to_string(), "Turbo");
}

#[test]
fn test_rgb_color_from_hex() {
    let color = RgbColor::from_hex("#FF0000").unwrap();
    assert_eq!(color.r, 255);
    assert_eq!(color.g, 0);
    assert_eq!(color.b, 0);
    
    let color = RgbColor::from_hex("#00FF00").unwrap();
    assert_eq!(color.r, 0);
    assert_eq!(color.g, 255);
    assert_eq!(color.b, 0);
    
    let color = RgbColor::from_hex("0000FF").unwrap();
    assert_eq!(color.r, 0);
    assert_eq!(color.g, 0);
    assert_eq!(color.b, 255);
}

#[test]
fn test_rgb_color_to_hex() {
    let color = RgbColor::new(255, 0, 0);
    assert_eq!(color.to_hex(), "#FF0000");
    
    let color = RgbColor::new(128, 128, 128);
    assert_eq!(color.to_hex(), "#808080");
}

#[test]
fn test_fan_curve_default() {
    let curve = FanCurve::default();
    assert_eq!(curve.name, "Default");
    assert!(!curve.points.is_empty());
    
    // Verify points are in ascending temperature order
    let mut last_temp = 0;
    for point in &curve.points {
        assert!(point.temperature >= last_temp);
        assert!(point.fan_percent <= 100);
        last_temp = point.temperature;
    }
}

#[test]
fn test_profile_serialization() {
    let profile = Profile::default();
    
    // Test serialization
    let json = serde_json::to_string(&profile).unwrap();
    assert!(json.contains("Default"));
    
    // Test deserialization
    let deserialized: Profile = serde_json::from_str(&json).unwrap();
    assert_eq!(deserialized.name, profile.name);
    assert_eq!(deserialized.performance_mode, profile.performance_mode);
}

#[test]
fn test_system_status_default() {
    let status = SystemStatus::default();
    assert_eq!(status.cpu_temp, 0.0);
    assert_eq!(status.gpu_temp, 0.0);
    assert_eq!(status.battery_percent, 0);
}

#[test]
fn test_battery_settings_valid_limits() {
    let settings = BatterySettings { charge_limit: 60 };
    assert_eq!(settings.charge_limit, 60);
    
    let settings = BatterySettings { charge_limit: 80 };
    assert_eq!(settings.charge_limit, 80);
    
    let settings = BatterySettings { charge_limit: 100 };
    assert_eq!(settings.charge_limit, 100);
}

#[test]
fn test_rgb_settings_default() {
    let settings = RgbSettings::default();
    assert_eq!(settings.effect, RgbEffect::Static);
    assert_eq!(settings.brightness, 100);
    assert!(settings.color_secondary.is_none());
}

#[test]
fn test_hardware_capabilities_default() {
    let caps = HardwareCapabilities::default();
    assert!(!caps.performance_modes);
    assert!(!caps.gpu_switching);
    assert!(!caps.fan_control);
    assert!(!caps.rgb_keyboard);
    assert!(caps.model_name.is_none());
}

#[test]
fn test_gpu_mode_display() {
    assert_eq!(GpuMode::Integrated.to_string(), "Integrated");
    assert_eq!(GpuMode::Hybrid.to_string(), "Hybrid");
    assert_eq!(GpuMode::Dedicated.to_string(), "Dedicated");
    assert_eq!(GpuMode::Compute.to_string(), "Compute");
}

#[test]
fn test_rgb_effect_display() {
    assert_eq!(RgbEffect::Static.to_string(), "Static");
    assert_eq!(RgbEffect::Breathing.to_string(), "Breathing");
    assert_eq!(RgbEffect::Rainbow.to_string(), "Rainbow");
    assert_eq!(RgbEffect::Off.to_string(), "Off");
}

#[cfg(test)]
mod profile_tests {
    use super::*;

    #[test]
    fn test_gaming_profile_characteristics() {
        let profile = Profile {
            name: "Gaming".to_string(),
            performance_mode: PerformanceMode::Turbo,
            gpu_mode: GpuMode::Dedicated,
            fan_mode: FanMode::Auto,
            fan_curve: None,
            rgb_settings: RgbSettings {
                effect: RgbEffect::Rainbow,
                color: RgbColor::new(255, 0, 0),
                color_secondary: None,
                brightness: 100,
                speed: 75,
            },
            battery_settings: BatterySettings { charge_limit: 100 },
        };
        
        assert_eq!(profile.performance_mode, PerformanceMode::Turbo);
        assert_eq!(profile.gpu_mode, GpuMode::Dedicated);
        assert_eq!(profile.battery_settings.charge_limit, 100);
    }

    #[test]
    fn test_silent_profile_characteristics() {
        let profile = Profile {
            name: "Silent".to_string(),
            performance_mode: PerformanceMode::Silent,
            gpu_mode: GpuMode::Integrated,
            fan_mode: FanMode::Auto,
            fan_curve: None,
            rgb_settings: RgbSettings {
                effect: RgbEffect::Off,
                color: RgbColor::default(),
                color_secondary: None,
                brightness: 0,
                speed: 0,
            },
            battery_settings: BatterySettings { charge_limit: 60 },
        };
        
        assert_eq!(profile.performance_mode, PerformanceMode::Silent);
        assert_eq!(profile.gpu_mode, GpuMode::Integrated);
        assert_eq!(profile.battery_settings.charge_limit, 60);
        assert_eq!(profile.rgb_settings.effect, RgbEffect::Off);
    }
}
