//! D-Bus server for exposing hardware control to GUI and other applications

use asus_armoury_common::{
    dbus_interface::{DBUS_NAME, DBUS_PATH},
    FanCurve, FanCurvePoint, GpuMode, PerformanceMode, RgbEffect, RgbSettings, SystemStatus,
};
use log::{error, info};
use std::sync::Arc;
use tokio::sync::RwLock;
use zbus::{interface, Connection, ConnectionBuilder};

use crate::AppState;

/// Main D-Bus interface for ASUS Armoury
pub struct ArmouryInterface {
    state: Arc<RwLock<AppState>>,
}

impl ArmouryInterface {
    pub fn new(state: Arc<RwLock<AppState>>) -> Self {
        Self { state }
    }
}

#[interface(name = "org.asuslinux.Armoury")]
impl ArmouryInterface {
    /// Get the daemon version
    async fn version(&self) -> String {
        env!("CARGO_PKG_VERSION").to_string()
    }

    /// Get hardware capabilities as JSON
    async fn get_capabilities(&self) -> String {
        let state = self.state.read().await;
        serde_json::to_string(&state.hardware.capabilities).unwrap_or_default()
    }

    /// Get system status as JSON
    async fn get_system_status(&self) -> String {
        let state = self.state.read().await;
        let status = state.hardware.get_system_status();
        serde_json::to_string(&status).unwrap_or_default()
    }

    // ==================== Performance Mode ====================

    /// Get current performance mode
    async fn get_performance_mode(&self) -> String {
        let state = self.state.read().await;
        state.hardware.get_performance_mode().to_string()
    }

    /// Set performance mode
    async fn set_performance_mode(&self, mode: &str) -> bool {
        let mut state = self.state.write().await;
        let mode = match mode.to_lowercase().as_str() {
            "silent" => PerformanceMode::Silent,
            "balanced" => PerformanceMode::Balanced,
            "turbo" | "performance" => PerformanceMode::Turbo,
            "manual" => PerformanceMode::Manual,
            _ => return false,
        };
        
        match state.hardware.set_performance_mode(mode) {
            Ok(()) => true,
            Err(e) => {
                error!("Failed to set performance mode: {}", e);
                false
            }
        }
    }

    // ==================== GPU Mode ====================

    /// Get current GPU mode
    async fn get_gpu_mode(&self) -> String {
        let state = self.state.read().await;
        state.hardware.get_gpu_mode().to_string()
    }

    /// Set GPU mode
    async fn set_gpu_mode(&self, mode: &str) -> bool {
        let mut state = self.state.write().await;
        let mode = match mode.to_lowercase().as_str() {
            "integrated" => GpuMode::Integrated,
            "dedicated" => GpuMode::Dedicated,
            "hybrid" => GpuMode::Hybrid,
            "compute" => GpuMode::Compute,
            _ => return false,
        };
        
        match state.hardware.set_gpu_mode(mode) {
            Ok(()) => true,
            Err(e) => {
                error!("Failed to set GPU mode: {}", e);
                false
            }
        }
    }

    // ==================== Fan Control ====================

    /// Get fan speeds as JSON { "cpu": rpm, "gpu": rpm }
    async fn get_fan_speeds(&self) -> String {
        let state = self.state.read().await;
        let (cpu, gpu) = state.hardware.get_fan_speeds();
        serde_json::json!({ "cpu": cpu, "gpu": gpu }).to_string()
    }

    /// Set fan curve from JSON
    async fn set_fan_curve(&self, curve_json: &str) -> bool {
        let mut state = self.state.write().await;
        
        let curve: FanCurve = match serde_json::from_str(curve_json) {
            Ok(c) => c,
            Err(e) => {
                error!("Invalid fan curve JSON: {}", e);
                return false;
            }
        };
        
        match state.hardware.set_fan_curve(&curve) {
            Ok(()) => true,
            Err(e) => {
                error!("Failed to set fan curve: {}", e);
                false
            }
        }
    }

    /// Reset fan control to automatic
    async fn reset_fan_auto(&self) -> bool {
        let mut state = self.state.write().await;
        match state.hardware.reset_fan_auto() {
            Ok(()) => true,
            Err(e) => {
                error!("Failed to reset fan control: {}", e);
                false
            }
        }
    }

    // ==================== Temperature ====================

    /// Get temperatures as JSON { "cpu": temp, "gpu": temp }
    async fn get_temperatures(&self) -> String {
        let state = self.state.read().await;
        let (cpu, gpu) = state.hardware.get_temperatures();
        serde_json::json!({ "cpu": cpu, "gpu": gpu }).to_string()
    }

    // ==================== RGB Keyboard ====================

    /// Get RGB settings as JSON
    async fn get_rgb_settings(&self) -> String {
        let state = self.state.read().await;
        let settings = state.hardware.get_rgb_settings();
        serde_json::to_string(&settings).unwrap_or_default()
    }

    /// Set RGB settings from JSON
    async fn set_rgb_settings(&self, settings_json: &str) -> bool {
        let mut state = self.state.write().await;
        
        let settings: RgbSettings = match serde_json::from_str(settings_json) {
            Ok(s) => s,
            Err(e) => {
                error!("Invalid RGB settings JSON: {}", e);
                return false;
            }
        };
        
        match state.hardware.set_rgb_settings(&settings) {
            Ok(()) => true,
            Err(e) => {
                error!("Failed to set RGB settings: {}", e);
                false
            }
        }
    }

    // ==================== Battery ====================

    /// Get battery charge limit
    async fn get_battery_limit(&self) -> u8 {
        let state = self.state.read().await;
        state.hardware.get_battery_limit()
    }

    /// Set battery charge limit
    async fn set_battery_limit(&self, limit: u8) -> bool {
        let mut state = self.state.write().await;
        match state.hardware.set_battery_limit(limit) {
            Ok(()) => true,
            Err(e) => {
                error!("Failed to set battery limit: {}", e);
                false
            }
        }
    }

    // ==================== Profiles ====================

    /// List available profiles
    async fn list_profiles(&self) -> String {
        let state = self.state.read().await;
        let profiles: Vec<String> = state.profiles.list_profiles()
            .iter()
            .map(|p| p.name.clone())
            .collect();
        serde_json::to_string(&profiles).unwrap_or_default()
    }

    /// Get current profile name
    async fn get_current_profile(&self) -> String {
        let state = self.state.read().await;
        state.profiles.current_profile_name().to_string()
    }

    /// Get profile by name as JSON
    async fn get_profile(&self, name: &str) -> String {
        let state = self.state.read().await;
        match state.profiles.get_profile(name) {
            Some(profile) => serde_json::to_string(profile).unwrap_or_default(),
            None => String::new(),
        }
    }

    /// Apply profile by name
    async fn apply_profile(&self, name: &str) -> bool {
        let mut state = self.state.write().await;
        
        let profile = match state.profiles.get_profile(name) {
            Some(p) => p.clone(),
            None => {
                error!("Profile not found: {}", name);
                return false;
            }
        };

        // Apply all settings from the profile
        let mut success = true;

        if let Err(e) = state.hardware.set_performance_mode(profile.performance_mode) {
            error!("Failed to set performance mode: {}", e);
            success = false;
        }

        if let Err(e) = state.hardware.set_rgb_settings(&profile.rgb_settings) {
            error!("Failed to set RGB settings: {}", e);
            // Don't fail completely if RGB fails
        }

        if let Err(e) = state.hardware.set_battery_limit(profile.battery_settings.charge_limit) {
            error!("Failed to set battery limit: {}", e);
            // Don't fail completely if battery limit fails
        }

        if let Some(ref curve) = profile.fan_curve {
            if let Err(e) = state.hardware.set_fan_curve(curve) {
                error!("Failed to set fan curve: {}", e);
            }
        }

        if success {
            state.profiles.set_current_profile(name);
        }

        success
    }

    /// Save profile from JSON
    async fn save_profile(&self, profile_json: &str) -> bool {
        let mut state = self.state.write().await;
        
        let profile = match serde_json::from_str(profile_json) {
            Ok(p) => p,
            Err(e) => {
                error!("Invalid profile JSON: {}", e);
                return false;
            }
        };
        
        match state.profiles.save_profile(profile) {
            Ok(()) => true,
            Err(e) => {
                error!("Failed to save profile: {}", e);
                false
            }
        }
    }

    /// Delete profile by name
    async fn delete_profile(&self, name: &str) -> bool {
        let mut state = self.state.write().await;
        match state.profiles.delete_profile(name) {
            Ok(()) => true,
            Err(e) => {
                error!("Failed to delete profile: {}", e);
                false
            }
        }
    }
}

/// Run the D-Bus server
pub async fn run_server(state: Arc<RwLock<AppState>>) -> anyhow::Result<()> {
    let interface = ArmouryInterface::new(state);
    
    let connection = ConnectionBuilder::system()?
        .name(DBUS_NAME)?
        .serve_at(DBUS_PATH, interface)?
        .build()
        .await?;

    info!("D-Bus server running at {} ({})", DBUS_NAME, DBUS_PATH);

    // Keep the server running
    loop {
        tokio::time::sleep(tokio::time::Duration::from_secs(3600)).await;
    }
}
