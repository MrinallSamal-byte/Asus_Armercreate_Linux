//! Common data types for ASUS Armoury Crate Linux

use serde::{Deserialize, Serialize};

/// CPU Performance modes available on ASUS laptops
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum PerformanceMode {
    /// Silent mode - prioritizes low noise and temperatures
    Silent,
    /// Balanced mode - default mode balancing performance and thermals
    #[default]
    Balanced,
    /// Turbo/Performance mode - maximum performance
    Turbo,
    /// Manual mode - user-defined settings
    Manual,
}

impl std::fmt::Display for PerformanceMode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Silent => write!(f, "Silent"),
            Self::Balanced => write!(f, "Balanced"),
            Self::Turbo => write!(f, "Turbo"),
            Self::Manual => write!(f, "Manual"),
        }
    }
}

/// GPU operation modes
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum GpuMode {
    /// Use integrated graphics only
    Integrated,
    /// Use dedicated GPU only
    Dedicated,
    /// Hybrid mode - automatic switching
    #[default]
    Hybrid,
    /// Compute mode - GPU available but no display output
    Compute,
}

impl std::fmt::Display for GpuMode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Integrated => write!(f, "Integrated"),
            Self::Dedicated => write!(f, "Dedicated"),
            Self::Hybrid => write!(f, "Hybrid"),
            Self::Compute => write!(f, "Compute"),
        }
    }
}

/// Fan control mode
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum FanMode {
    /// Automatic fan control based on temperature
    #[default]
    Auto,
    /// Manual fan curve
    Manual,
}

/// A point in a fan curve (temperature -> fan percentage)
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct FanCurvePoint {
    /// Temperature in Celsius
    pub temperature: u8,
    /// Fan speed percentage (0-100)
    pub fan_percent: u8,
}

/// Fan curve definition with multiple temperature/speed points
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FanCurve {
    /// Name of the fan curve profile
    pub name: String,
    /// Points defining the fan curve
    pub points: Vec<FanCurvePoint>,
}

impl Default for FanCurve {
    fn default() -> Self {
        Self {
            name: "Default".to_string(),
            points: vec![
                FanCurvePoint { temperature: 30, fan_percent: 0 },
                FanCurvePoint { temperature: 40, fan_percent: 20 },
                FanCurvePoint { temperature: 50, fan_percent: 35 },
                FanCurvePoint { temperature: 60, fan_percent: 50 },
                FanCurvePoint { temperature: 70, fan_percent: 70 },
                FanCurvePoint { temperature: 80, fan_percent: 85 },
                FanCurvePoint { temperature: 90, fan_percent: 100 },
            ],
        }
    }
}

/// RGB lighting effects
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum RgbEffect {
    /// Static single color
    #[default]
    Static,
    /// Breathing/pulsing effect
    Breathing,
    /// Rainbow color cycling
    Rainbow,
    /// Color wave effect
    Wave,
    /// Spectrum cycling
    Spectrum,
    /// Reactive/keypress effect
    Reactive,
    /// Off
    Off,
}

impl std::fmt::Display for RgbEffect {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Static => write!(f, "Static"),
            Self::Breathing => write!(f, "Breathing"),
            Self::Rainbow => write!(f, "Rainbow"),
            Self::Wave => write!(f, "Wave"),
            Self::Spectrum => write!(f, "Spectrum"),
            Self::Reactive => write!(f, "Reactive"),
            Self::Off => write!(f, "Off"),
        }
    }
}

/// RGB color value
#[derive(Debug, Clone, Copy, Serialize, Deserialize, Default)]
pub struct RgbColor {
    pub r: u8,
    pub g: u8,
    pub b: u8,
}

impl RgbColor {
    pub fn new(r: u8, g: u8, b: u8) -> Self {
        Self { r, g, b }
    }

    pub fn from_hex(hex: &str) -> Option<Self> {
        let hex = hex.trim_start_matches('#');
        if hex.len() != 6 {
            return None;
        }
        let r = u8::from_str_radix(&hex[0..2], 16).ok()?;
        let g = u8::from_str_radix(&hex[2..4], 16).ok()?;
        let b = u8::from_str_radix(&hex[4..6], 16).ok()?;
        Some(Self { r, g, b })
    }

    pub fn to_hex(&self) -> String {
        format!("#{:02X}{:02X}{:02X}", self.r, self.g, self.b)
    }
}

/// RGB keyboard settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RgbSettings {
    /// Current effect
    pub effect: RgbEffect,
    /// Primary color
    pub color: RgbColor,
    /// Secondary color (for effects that use two colors)
    pub color_secondary: Option<RgbColor>,
    /// Brightness (0-100)
    pub brightness: u8,
    /// Effect speed (0-100)
    pub speed: u8,
}

impl Default for RgbSettings {
    fn default() -> Self {
        Self {
            effect: RgbEffect::Static,
            color: RgbColor::new(255, 0, 0),
            color_secondary: None,
            brightness: 100,
            speed: 50,
        }
    }
}

/// Battery charge limit settings
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct BatterySettings {
    /// Maximum charge limit percentage (60, 80, or 100)
    pub charge_limit: u8,
}

impl Default for BatterySettings {
    fn default() -> Self {
        Self {
            charge_limit: 100,
        }
    }
}

/// System status information
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SystemStatus {
    /// CPU temperature in Celsius
    pub cpu_temp: f32,
    /// GPU temperature in Celsius
    pub gpu_temp: f32,
    /// CPU usage percentage
    pub cpu_usage: f32,
    /// GPU usage percentage
    pub gpu_usage: f32,
    /// CPU fan speed (RPM)
    pub cpu_fan_rpm: u32,
    /// GPU fan speed (RPM)
    pub gpu_fan_rpm: u32,
    /// Battery percentage
    pub battery_percent: u8,
    /// Whether AC is connected
    pub ac_connected: bool,
    /// Current power draw in watts
    pub power_draw: f32,
}

/// User profile containing all settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Profile {
    /// Profile name
    pub name: String,
    /// Performance mode
    pub performance_mode: PerformanceMode,
    /// GPU mode
    pub gpu_mode: GpuMode,
    /// Fan settings
    pub fan_mode: FanMode,
    /// Custom fan curve (if fan_mode is Manual)
    pub fan_curve: Option<FanCurve>,
    /// RGB keyboard settings
    pub rgb_settings: RgbSettings,
    /// Battery settings
    pub battery_settings: BatterySettings,
}

impl Default for Profile {
    fn default() -> Self {
        Self {
            name: "Default".to_string(),
            performance_mode: PerformanceMode::Balanced,
            gpu_mode: GpuMode::Hybrid,
            fan_mode: FanMode::Auto,
            fan_curve: None,
            rgb_settings: RgbSettings::default(),
            battery_settings: BatterySettings::default(),
        }
    }
}

/// Supported ASUS laptop features
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct HardwareCapabilities {
    /// Whether performance mode switching is supported
    pub performance_modes: bool,
    /// Whether GPU mode switching is supported
    pub gpu_switching: bool,
    /// Whether fan control is supported
    pub fan_control: bool,
    /// Whether RGB keyboard control is supported
    pub rgb_keyboard: bool,
    /// Whether per-key RGB is supported
    pub per_key_rgb: bool,
    /// Whether battery charge limit is supported
    pub battery_limit: bool,
    /// Whether panel overdrive is supported
    pub panel_overdrive: bool,
    /// Whether Anime Matrix display is supported
    pub anime_matrix: bool,
    /// Model name if detected
    pub model_name: Option<String>,
}
