//! D-Bus client for communicating with the daemon

use asus_armoury_common::{
    HardwareCapabilities, RgbSettings, SystemStatus,
};
use log::{error, info};
use zbus::{proxy, Connection, Result};

/// D-Bus proxy for the Armoury daemon
#[proxy(
    interface = "org.asuslinux.Armoury",
    default_service = "org.asuslinux.Armoury",
    default_path = "/org/asuslinux/Armoury"
)]
trait Armoury {
    fn version(&self) -> Result<String>;
    fn get_capabilities(&self) -> Result<String>;
    fn get_system_status(&self) -> Result<String>;
    
    fn get_performance_mode(&self) -> Result<String>;
    fn set_performance_mode(&self, mode: &str) -> Result<bool>;
    
    fn get_gpu_mode(&self) -> Result<String>;
    fn set_gpu_mode(&self, mode: &str) -> Result<bool>;
    
    fn get_fan_speeds(&self) -> Result<String>;
    fn set_fan_curve(&self, curve_json: &str) -> Result<bool>;
    fn reset_fan_auto(&self) -> Result<bool>;
    
    fn get_temperatures(&self) -> Result<String>;
    
    fn get_rgb_settings(&self) -> Result<String>;
    fn set_rgb_settings(&self, settings_json: &str) -> Result<bool>;
    
    fn get_battery_limit(&self) -> Result<u8>;
    fn set_battery_limit(&self, limit: u8) -> Result<bool>;
    
    fn list_profiles(&self) -> Result<String>;
    fn get_current_profile(&self) -> Result<String>;
    fn get_profile(&self, name: &str) -> Result<String>;
    fn apply_profile(&self, name: &str) -> Result<bool>;
    fn save_profile(&self, profile_json: &str) -> Result<bool>;
    fn delete_profile(&self, name: &str) -> Result<bool>;
}

/// Client wrapper for easier interaction with the daemon
pub struct DaemonClient {
    connection: Option<Connection>,
}

impl DaemonClient {
    /// Create a new daemon client
    pub async fn new() -> Self {
        match Connection::system().await {
            Ok(conn) => {
                match ArmouryProxy::new(&conn).await {
                    Ok(_) => {
                        info!("Connected to daemon");
                        Self {
                            connection: Some(conn),
                        }
                    }
                    Err(e) => {
                        error!("Failed to create proxy: {}", e);
                        Self { connection: None }
                    }
                }
            }
            Err(e) => {
                error!("Failed to connect to D-Bus: {}", e);
                Self { connection: None }
            }
        }
    }

    async fn proxy(&self) -> Option<ArmouryProxy<'_>> {
        let conn = self.connection.as_ref()?;
        ArmouryProxy::new(conn).await.ok()
    }

    /// Check if connected to daemon
    pub fn is_connected(&self) -> bool {
        self.connection.is_some()
    }

    /// Get daemon version
    pub async fn version(&self) -> Option<String> {
        let proxy = self.proxy().await?;
        proxy.version().await.ok()
    }

    /// Get hardware capabilities
    pub async fn get_capabilities(&self) -> Option<HardwareCapabilities> {
        let proxy = self.proxy().await?;
        let json = proxy.get_capabilities().await.ok()?;
        serde_json::from_str(&json).ok()
    }

    /// Get system status
    pub async fn get_system_status(&self) -> Option<SystemStatus> {
        let proxy = self.proxy().await?;
        let json = proxy.get_system_status().await.ok()?;
        serde_json::from_str(&json).ok()
    }

    /// Get current performance mode
    pub async fn get_performance_mode(&self) -> Option<String> {
        let proxy = self.proxy().await?;
        proxy.get_performance_mode().await.ok()
    }

    /// Set performance mode
    pub async fn set_performance_mode(&self, mode: &str) -> bool {
        if let Some(proxy) = self.proxy().await {
            proxy.set_performance_mode(mode).await.unwrap_or(false)
        } else {
            false
        }
    }

    /// Get current GPU mode
    pub async fn get_gpu_mode(&self) -> Option<String> {
        let proxy = self.proxy().await?;
        proxy.get_gpu_mode().await.ok()
    }

    /// Set GPU mode
    pub async fn set_gpu_mode(&self, mode: &str) -> bool {
        if let Some(proxy) = self.proxy().await {
            proxy.set_gpu_mode(mode).await.unwrap_or(false)
        } else {
            false
        }
    }

    /// Get fan speeds
    pub async fn get_fan_speeds(&self) -> Option<(u32, u32)> {
        let proxy = self.proxy().await?;
        let json = proxy.get_fan_speeds().await.ok()?;
        let v: serde_json::Value = serde_json::from_str(&json).ok()?;
        let cpu = v["cpu"].as_u64()? as u32;
        let gpu = v["gpu"].as_u64()? as u32;
        Some((cpu, gpu))
    }

    /// Get temperatures
    pub async fn get_temperatures(&self) -> Option<(f32, f32)> {
        let proxy = self.proxy().await?;
        let json = proxy.get_temperatures().await.ok()?;
        let v: serde_json::Value = serde_json::from_str(&json).ok()?;
        let cpu = v["cpu"].as_f64()? as f32;
        let gpu = v["gpu"].as_f64()? as f32;
        Some((cpu, gpu))
    }

    /// Get RGB settings
    pub async fn get_rgb_settings(&self) -> Option<RgbSettings> {
        let proxy = self.proxy().await?;
        let json = proxy.get_rgb_settings().await.ok()?;
        serde_json::from_str(&json).ok()
    }

    /// Set RGB settings
    pub async fn set_rgb_settings(&self, settings: &RgbSettings) -> bool {
        if let Some(proxy) = self.proxy().await {
            if let Ok(json) = serde_json::to_string(settings) {
                return proxy.set_rgb_settings(&json).await.unwrap_or(false);
            }
        }
        false
    }

    /// Get battery limit
    pub async fn get_battery_limit(&self) -> Option<u8> {
        let proxy = self.proxy().await?;
        proxy.get_battery_limit().await.ok()
    }

    /// Set battery limit
    pub async fn set_battery_limit(&self, limit: u8) -> bool {
        if let Some(proxy) = self.proxy().await {
            proxy.set_battery_limit(limit).await.unwrap_or(false)
        } else {
            false
        }
    }

    /// List profiles
    pub async fn list_profiles(&self) -> Vec<String> {
        if let Some(proxy) = self.proxy().await {
            if let Ok(json) = proxy.list_profiles().await {
                if let Ok(profiles) = serde_json::from_str::<Vec<String>>(&json) {
                    return profiles;
                }
            }
        }
        Vec::new()
    }

    /// Get current profile name
    pub async fn get_current_profile(&self) -> Option<String> {
        let proxy = self.proxy().await?;
        proxy.get_current_profile().await.ok()
    }

    /// Apply profile by name
    pub async fn apply_profile(&self, name: &str) -> bool {
        if let Some(proxy) = self.proxy().await {
            proxy.apply_profile(name).await.unwrap_or(false)
        } else {
            false
        }
    }
}

impl Default for DaemonClient {
    fn default() -> Self {
        Self { connection: None }
    }
}
