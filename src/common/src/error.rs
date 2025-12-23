//! Error types for ASUS Armoury Crate Linux

use thiserror::Error;

/// Main error type for the application
#[derive(Error, Debug)]
pub enum ArmouryError {
    #[error("Hardware not supported: {0}")]
    UnsupportedHardware(String),

    #[error("Feature not available: {0}")]
    FeatureNotAvailable(String),

    #[error("Permission denied: {0}")]
    PermissionDenied(String),

    #[error("D-Bus error: {0}")]
    DbusError(String),

    #[error("Configuration error: {0}")]
    ConfigError(String),

    #[error("I/O error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Invalid value: {0}")]
    InvalidValue(String),

    #[error("Hardware communication error: {0}")]
    HardwareError(String),

    #[error("Service not running")]
    ServiceNotRunning,
}

/// Result type alias using ArmouryError
pub type ArmouryResult<T> = Result<T, ArmouryError>;
