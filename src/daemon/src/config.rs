//! Daemon configuration management

use anyhow::Result;
use directories::ProjectDirs;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

/// Daemon configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DaemonConfig {
    /// Path to profiles directory
    pub profiles_dir: PathBuf,
    /// Default profile to load on startup
    pub default_profile: String,
    /// Enable debug logging
    pub debug: bool,
    /// Poll interval for system monitoring (milliseconds)
    pub poll_interval_ms: u64,
    /// Whether to integrate with asusctl if available
    pub use_asusctl: bool,
    /// Whether to integrate with supergfxctl for GPU switching
    pub use_supergfxctl: bool,
}

impl Default for DaemonConfig {
    fn default() -> Self {
        Self {
            profiles_dir: Self::default_profiles_dir(),
            default_profile: "Balanced".to_string(),
            debug: false,
            poll_interval_ms: 1000,
            use_asusctl: true,
            use_supergfxctl: true,
        }
    }
}

impl DaemonConfig {
    /// Load configuration from file or create default
    pub fn load() -> Result<Self> {
        let config_path = Self::config_file_path();
        
        if config_path.exists() {
            let content = fs::read_to_string(&config_path)?;
            let config: DaemonConfig = serde_json::from_str(&content)?;
            Ok(config)
        } else {
            let config = Self::default();
            config.save()?;
            Ok(config)
        }
    }

    /// Save configuration to file
    pub fn save(&self) -> Result<()> {
        let config_path = Self::config_file_path();
        
        // Ensure parent directory exists
        if let Some(parent) = config_path.parent() {
            fs::create_dir_all(parent)?;
        }

        let content = serde_json::to_string_pretty(self)?;
        fs::write(&config_path, content)?;
        Ok(())
    }

    /// Get the configuration file path
    pub fn config_file_path() -> PathBuf {
        if let Some(proj_dirs) = ProjectDirs::from("org", "asuslinux", "armoury") {
            proj_dirs.config_dir().join("daemon.json")
        } else {
            PathBuf::from("/etc/asus-armoury/daemon.json")
        }
    }

    /// Get the default profiles directory
    fn default_profiles_dir() -> PathBuf {
        if let Some(proj_dirs) = ProjectDirs::from("org", "asuslinux", "armoury") {
            proj_dirs.data_dir().join("profiles")
        } else {
            PathBuf::from("/var/lib/asus-armoury/profiles")
        }
    }
}
