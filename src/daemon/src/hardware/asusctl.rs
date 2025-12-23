//! Integration with asusctl for enhanced functionality
//!
//! This module provides integration with the asusctl tool when available,
//! offering additional features and better hardware support.
//!
//! Note: These functions are currently not used by the default hardware controller
//! but are available for future integration when asusctl is configured as the
//! preferred backend.

#![allow(dead_code)]

use asus_armoury_common::{ArmouryResult, ArmouryError, PerformanceMode, RgbSettings, RgbEffect};
use std::process::Command;

/// Check if asusctl is available on the system
pub fn is_available() -> bool {
    Command::new("asusctl")
        .arg("--version")
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

/// Set performance profile using asusctl
pub fn set_profile(mode: PerformanceMode) -> ArmouryResult<()> {
    let profile = match mode {
        PerformanceMode::Silent => "Quiet",
        PerformanceMode::Balanced => "Balanced",
        PerformanceMode::Turbo => "Performance",
        PerformanceMode::Manual => "Balanced",
    };

    let output = Command::new("asusctl")
        .args(["profile", "-P", profile])
        .output()
        .map_err(|e| ArmouryError::HardwareError(format!("Failed to run asusctl: {}", e)))?;

    if output.status.success() {
        Ok(())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(ArmouryError::HardwareError(format!("asusctl failed: {}", stderr)))
    }
}

/// Get current performance profile using asusctl
pub fn get_profile() -> Option<PerformanceMode> {
    let output = Command::new("asusctl")
        .args(["profile", "-p"])
        .output()
        .ok()?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let profile = stdout.trim().to_lowercase();
        
        match profile.as_str() {
            s if s.contains("quiet") => Some(PerformanceMode::Silent),
            s if s.contains("balanced") => Some(PerformanceMode::Balanced),
            s if s.contains("performance") => Some(PerformanceMode::Turbo),
            _ => None,
        }
    } else {
        None
    }
}

/// Set keyboard LED mode using asusctl
pub fn set_led_mode(settings: &RgbSettings) -> ArmouryResult<()> {
    let mode = match settings.effect {
        RgbEffect::Static => "static",
        RgbEffect::Breathing => "breathe",
        RgbEffect::Rainbow => "rainbow",
        RgbEffect::Wave => "comet",
        RgbEffect::Spectrum => "rainbow",
        RgbEffect::Reactive => "pulse",
        RgbEffect::Off => "off",
    };

    let mut args = vec!["led-mode", "-s", mode];
    
    // Add color if applicable
    let color_hex = settings.color.to_hex();
    if matches!(settings.effect, RgbEffect::Static | RgbEffect::Breathing | RgbEffect::Reactive) {
        args.extend(["-c", &color_hex]);
    }

    let output = Command::new("asusctl")
        .args(&args)
        .output()
        .map_err(|e| ArmouryError::HardwareError(format!("Failed to run asusctl: {}", e)))?;

    if output.status.success() {
        Ok(())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(ArmouryError::HardwareError(format!("asusctl led-mode failed: {}", stderr)))
    }
}

/// Set keyboard brightness using asusctl
pub fn set_kbd_brightness(brightness: u8) -> ArmouryResult<()> {
    // asusctl uses brightness levels 0-3
    let level = (brightness as u32 * 3 / 100).min(3);
    
    let output = Command::new("asusctl")
        .args(["led-mode", "-b", &level.to_string()])
        .output()
        .map_err(|e| ArmouryError::HardwareError(format!("Failed to run asusctl: {}", e)))?;

    if output.status.success() {
        Ok(())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(ArmouryError::HardwareError(format!("asusctl brightness failed: {}", stderr)))
    }
}

/// Set charge limit using asusctl
pub fn set_charge_limit(limit: u8) -> ArmouryResult<()> {
    let output = Command::new("asusctl")
        .args(["bios", "-c", &limit.to_string()])
        .output()
        .map_err(|e| ArmouryError::HardwareError(format!("Failed to run asusctl: {}", e)))?;

    if output.status.success() {
        Ok(())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(ArmouryError::HardwareError(format!("asusctl charge limit failed: {}", stderr)))
    }
}
