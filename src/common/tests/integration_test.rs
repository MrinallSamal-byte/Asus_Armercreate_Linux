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

    #[test]
    fn test_profile_with_fan_curve_serialization() {
        let profile = Profile {
            name: "Custom".to_string(),
            performance_mode: PerformanceMode::Manual,
            gpu_mode: GpuMode::Hybrid,
            fan_mode: FanMode::Manual,
            fan_curve: Some(FanCurve::default()),
            rgb_settings: RgbSettings::default(),
            battery_settings: BatterySettings { charge_limit: 80 },
        };

        let json = serde_json::to_string(&profile).unwrap();
        let deserialized: Profile = serde_json::from_str(&json).unwrap();

        assert!(deserialized.fan_curve.is_some());
        assert_eq!(deserialized.fan_mode, FanMode::Manual);
        assert_eq!(deserialized.battery_settings.charge_limit, 80);
    }
}

#[cfg(test)]
mod fan_curve_validation_tests {
    use super::*;

    #[test]
    fn test_valid_fan_curve() {
        let curve = FanCurve::default();
        assert!(curve.validate().is_ok());
    }

    #[test]
    fn test_empty_fan_curve_invalid() {
        let curve = FanCurve {
            name: "Empty".to_string(),
            points: vec![],
        };
        assert!(curve.validate().is_err());
    }

    #[test]
    fn test_out_of_order_temperatures_invalid() {
        let curve = FanCurve {
            name: "Bad".to_string(),
            points: vec![
                FanCurvePoint { temperature: 60, fan_percent: 50 },
                FanCurvePoint { temperature: 40, fan_percent: 30 }, // out of order
            ],
        };
        assert!(curve.validate().is_err());
    }

    #[test]
    fn test_duplicate_temperatures_invalid() {
        let curve = FanCurve {
            name: "Dup".to_string(),
            points: vec![
                FanCurvePoint { temperature: 50, fan_percent: 30 },
                FanCurvePoint { temperature: 50, fan_percent: 60 }, // duplicate
            ],
        };
        assert!(curve.validate().is_err());
    }

    #[test]
    fn test_fan_percent_over_100_invalid() {
        let curve = FanCurve {
            name: "OverSpeed".to_string(),
            points: vec![
                FanCurvePoint { temperature: 50, fan_percent: 101 },
            ],
        };
        assert!(curve.validate().is_err());
    }

    #[test]
    fn test_single_point_fan_curve_valid() {
        let curve = FanCurve {
            name: "Single".to_string(),
            points: vec![FanCurvePoint { temperature: 70, fan_percent: 80 }],
        };
        assert!(curve.validate().is_ok());
    }
}

#[cfg(test)]
mod rgb_settings_validation_tests {
    use super::*;

    #[test]
    fn test_valid_rgb_settings() {
        let settings = RgbSettings::default();
        assert!(settings.validate().is_ok());
    }

    #[test]
    fn test_brightness_over_100_invalid() {
        let settings = RgbSettings {
            brightness: 101,
            ..RgbSettings::default()
        };
        assert!(settings.validate().is_err());
    }

    #[test]
    fn test_speed_over_100_invalid() {
        let settings = RgbSettings {
            speed: 255,
            ..RgbSettings::default()
        };
        assert!(settings.validate().is_err());
    }

    #[test]
    fn test_boundary_values_valid() {
        let settings = RgbSettings {
            brightness: 100,
            speed: 100,
            ..RgbSettings::default()
        };
        assert!(settings.validate().is_ok());
    }
}

#[cfg(test)]
mod rgb_color_tests {
    use super::*;

    #[test]
    fn test_hex_round_trip() {
        let colors = [
            RgbColor::new(0, 0, 0),
            RgbColor::new(255, 255, 255),
            RgbColor::new(128, 64, 32),
        ];
        for c in &colors {
            let hex = c.to_hex();
            let parsed = RgbColor::from_hex(&hex).unwrap();
            assert_eq!(parsed.r, c.r);
            assert_eq!(parsed.g, c.g);
            assert_eq!(parsed.b, c.b);
        }
    }

    #[test]
    fn test_hex_invalid_inputs() {
        assert!(RgbColor::from_hex("").is_none());
        assert!(RgbColor::from_hex("#FFF").is_none()); // 3-char, not supported
        assert!(RgbColor::from_hex("ZZZZZZ").is_none());
        assert!(RgbColor::from_hex("#0000001").is_none()); // too long
    }

    #[test]
    fn test_rgb_color_serialization() {
        let color = RgbColor::new(10, 20, 30);
        let json = serde_json::to_string(&color).unwrap();
        let parsed: RgbColor = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.r, 10);
        assert_eq!(parsed.g, 20);
        assert_eq!(parsed.b, 30);
    }
}

#[cfg(test)]
mod system_status_tests {
    use super::*;

    #[test]
    fn test_system_status_serialization() {
        let status = SystemStatus {
            cpu_temp: 55.5,
            gpu_temp: 48.0,
            cpu_usage: 30.0,
            gpu_usage: 0.0,
            cpu_fan_rpm: 2500,
            gpu_fan_rpm: 0,
            battery_percent: 78,
            ac_connected: true,
            power_draw: 15.3,
        };

        let json = serde_json::to_string(&status).unwrap();
        let parsed: SystemStatus = serde_json::from_str(&json).unwrap();

        assert!((parsed.cpu_temp - 55.5).abs() < 0.01);
        assert_eq!(parsed.cpu_fan_rpm, 2500);
        assert!(parsed.ac_connected);
        assert_eq!(parsed.battery_percent, 78);
    }

    #[test]
    fn test_system_status_default_values() {
        let status = SystemStatus::default();
        assert_eq!(status.cpu_fan_rpm, 0);
        assert_eq!(status.gpu_fan_rpm, 0);
        assert!(!status.ac_connected);
        assert!((status.power_draw).abs() < 0.001);
    }
}
