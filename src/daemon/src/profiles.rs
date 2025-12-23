//! Profile management for storing and loading user profiles

use asus_armoury_common::{ArmouryResult, ArmouryError, Profile, PerformanceMode, GpuMode, FanMode};
use log::{info, warn};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

use crate::config::DaemonConfig;

/// Profile manager handling loading, saving, and applying profiles
pub struct ProfileManager {
    /// Directory where profiles are stored
    profiles_dir: PathBuf,
    /// Loaded profiles
    profiles: HashMap<String, Profile>,
    /// Currently active profile name
    current_profile: String,
}

impl Default for ProfileManager {
    fn default() -> Self {
        let mut manager = Self {
            profiles_dir: PathBuf::from("/tmp/asus-armoury/profiles"),
            profiles: HashMap::new(),
            current_profile: "Balanced".to_string(),
        };
        manager.create_default_profiles();
        manager
    }
}

impl ProfileManager {
    /// Create a new profile manager
    pub fn new(config: &DaemonConfig) -> ArmouryResult<Self> {
        let profiles_dir = config.profiles_dir.clone();
        
        // Ensure profiles directory exists
        if !profiles_dir.exists() {
            fs::create_dir_all(&profiles_dir)?;
        }

        let mut manager = Self {
            profiles_dir,
            profiles: HashMap::new(),
            current_profile: config.default_profile.clone(),
        };

        // Load existing profiles
        manager.load_profiles()?;

        // Create default profiles if none exist
        if manager.profiles.is_empty() {
            manager.create_default_profiles();
            manager.save_all_profiles()?;
        }

        Ok(manager)
    }

    /// Create default profiles
    fn create_default_profiles(&mut self) {
        // Gaming profile
        let gaming = Profile {
            name: "Gaming".to_string(),
            performance_mode: PerformanceMode::Turbo,
            gpu_mode: GpuMode::Dedicated,
            fan_mode: FanMode::Auto,
            fan_curve: None,
            rgb_settings: asus_armoury_common::RgbSettings {
                effect: asus_armoury_common::RgbEffect::Rainbow,
                color: asus_armoury_common::RgbColor::new(255, 0, 0),
                color_secondary: None,
                brightness: 100,
                speed: 75,
            },
            battery_settings: asus_armoury_common::BatterySettings { charge_limit: 100 },
        };

        // Work profile
        let work = Profile {
            name: "Work".to_string(),
            performance_mode: PerformanceMode::Balanced,
            gpu_mode: GpuMode::Integrated,
            fan_mode: FanMode::Auto,
            fan_curve: None,
            rgb_settings: asus_armoury_common::RgbSettings {
                effect: asus_armoury_common::RgbEffect::Static,
                color: asus_armoury_common::RgbColor::new(255, 255, 255),
                color_secondary: None,
                brightness: 50,
                speed: 50,
            },
            battery_settings: asus_armoury_common::BatterySettings { charge_limit: 80 },
        };

        // Silent profile
        let silent = Profile {
            name: "Silent".to_string(),
            performance_mode: PerformanceMode::Silent,
            gpu_mode: GpuMode::Integrated,
            fan_mode: FanMode::Auto,
            fan_curve: None,
            rgb_settings: asus_armoury_common::RgbSettings {
                effect: asus_armoury_common::RgbEffect::Off,
                color: asus_armoury_common::RgbColor::default(),
                color_secondary: None,
                brightness: 0,
                speed: 0,
            },
            battery_settings: asus_armoury_common::BatterySettings { charge_limit: 60 },
        };

        // Balanced profile
        let balanced = Profile {
            name: "Balanced".to_string(),
            performance_mode: PerformanceMode::Balanced,
            gpu_mode: GpuMode::Hybrid,
            fan_mode: FanMode::Auto,
            fan_curve: None,
            rgb_settings: asus_armoury_common::RgbSettings::default(),
            battery_settings: asus_armoury_common::BatterySettings { charge_limit: 100 },
        };

        self.profiles.insert("Gaming".to_string(), gaming);
        self.profiles.insert("Work".to_string(), work);
        self.profiles.insert("Silent".to_string(), silent);
        self.profiles.insert("Balanced".to_string(), balanced);
    }

    /// Load profiles from disk
    fn load_profiles(&mut self) -> ArmouryResult<()> {
        if !self.profiles_dir.exists() {
            return Ok(());
        }

        let entries = fs::read_dir(&self.profiles_dir)?;
        
        for entry in entries.flatten() {
            let path = entry.path();
            if path.extension().map(|e| e == "json").unwrap_or(false) {
                if let Ok(content) = fs::read_to_string(&path) {
                    if let Ok(profile) = serde_json::from_str::<Profile>(&content) {
                        info!("Loaded profile: {}", profile.name);
                        self.profiles.insert(profile.name.clone(), profile);
                    }
                }
            }
        }

        Ok(())
    }

    /// Save all profiles to disk
    fn save_all_profiles(&self) -> ArmouryResult<()> {
        for profile in self.profiles.values() {
            self.save_profile_to_disk(profile)?;
        }
        Ok(())
    }

    /// Save a single profile to disk
    fn save_profile_to_disk(&self, profile: &Profile) -> ArmouryResult<()> {
        let path = self.profiles_dir.join(format!("{}.json", profile.name));
        let content = serde_json::to_string_pretty(profile)
            .map_err(|e| ArmouryError::ConfigError(format!("Failed to serialize profile: {}", e)))?;
        fs::write(&path, content)?;
        Ok(())
    }

    /// List all available profiles
    pub fn list_profiles(&self) -> Vec<&Profile> {
        self.profiles.values().collect()
    }

    /// Get a profile by name
    pub fn get_profile(&self, name: &str) -> Option<&Profile> {
        self.profiles.get(name)
    }

    /// Get current profile name
    pub fn current_profile_name(&self) -> &str {
        &self.current_profile
    }

    /// Set current profile
    pub fn set_current_profile(&mut self, name: &str) {
        if self.profiles.contains_key(name) {
            self.current_profile = name.to_string();
        }
    }

    /// Save or update a profile
    pub fn save_profile(&mut self, profile: Profile) -> ArmouryResult<()> {
        let name = profile.name.clone();
        self.save_profile_to_disk(&profile)?;
        self.profiles.insert(name, profile);
        Ok(())
    }

    /// Delete a profile
    pub fn delete_profile(&mut self, name: &str) -> ArmouryResult<()> {
        // Don't delete default profiles
        let default_profiles = ["Gaming", "Work", "Silent", "Balanced"];
        if default_profiles.contains(&name) {
            return Err(ArmouryError::InvalidValue(
                "Cannot delete default profiles".to_string()
            ));
        }

        if self.profiles.remove(name).is_some() {
            let path = self.profiles_dir.join(format!("{}.json", name));
            if path.exists() {
                fs::remove_file(&path)?;
            }
            info!("Deleted profile: {}", name);
            Ok(())
        } else {
            Err(ArmouryError::InvalidValue(
                format!("Profile not found: {}", name)
            ))
        }
    }
}
