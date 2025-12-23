//! ASUS Armoury Crate Linux Daemon
//!
//! Background service providing hardware control for ASUS laptops via D-Bus.

use anyhow::Result;
use log::{info, warn};
use std::sync::Arc;
use tokio::sync::RwLock;

mod config;
mod hardware;
mod dbus_server;
mod profiles;

use config::DaemonConfig;
use hardware::HardwareController;
use profiles::ProfileManager;

/// Application state shared between D-Bus handlers
pub struct AppState {
    pub hardware: HardwareController,
    pub profiles: ProfileManager,
    pub config: DaemonConfig,
}

impl AppState {
    pub fn new() -> Result<Self> {
        let config = DaemonConfig::load()?;
        let hardware = HardwareController::new()?;
        let profiles = ProfileManager::new(&config)?;

        Ok(Self {
            hardware,
            profiles,
            config,
        })
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info")
    ).init();

    info!("ASUS Armoury Crate Linux Daemon starting...");

    // Initialize application state
    let state = match AppState::new() {
        Ok(state) => Arc::new(RwLock::new(state)),
        Err(e) => {
            warn!("Failed to initialize hardware: {}", e);
            warn!("Running in limited mode - some features may not be available");
            Arc::new(RwLock::new(AppState {
                hardware: HardwareController::dummy(),
                profiles: ProfileManager::default(),
                config: DaemonConfig::default(),
            }))
        }
    };

    // Check hardware capabilities
    {
        let state_guard = state.read().await;
        let caps = &state_guard.hardware.capabilities;
        info!("Detected hardware capabilities:");
        info!("  Performance modes: {}", caps.performance_modes);
        info!("  GPU switching: {}", caps.gpu_switching);
        info!("  Fan control: {}", caps.fan_control);
        info!("  RGB keyboard: {}", caps.rgb_keyboard);
        info!("  Battery limit: {}", caps.battery_limit);
        if let Some(model) = &caps.model_name {
            info!("  Model: {}", model);
        }
    }

    // Start D-Bus server
    info!("Starting D-Bus server...");
    dbus_server::run_server(state).await?;

    Ok(())
}
