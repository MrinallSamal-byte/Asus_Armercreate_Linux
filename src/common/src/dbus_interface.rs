//! D-Bus interface constants for communication between daemon and GUI

/// D-Bus service name
pub const DBUS_NAME: &str = "org.asuslinux.Armoury";

/// D-Bus object path for the main interface
pub const DBUS_PATH: &str = "/org/asuslinux/Armoury";

/// D-Bus interface name
pub const DBUS_INTERFACE: &str = "org.asuslinux.Armoury";

/// D-Bus interface for performance control
pub const DBUS_INTERFACE_PERFORMANCE: &str = "org.asuslinux.Armoury.Performance";

/// D-Bus interface for fan control
pub const DBUS_INTERFACE_FAN: &str = "org.asuslinux.Armoury.Fan";

/// D-Bus interface for RGB control
pub const DBUS_INTERFACE_RGB: &str = "org.asuslinux.Armoury.RGB";

/// D-Bus interface for battery settings
pub const DBUS_INTERFACE_BATTERY: &str = "org.asuslinux.Armoury.Battery";

/// D-Bus interface for system monitoring
pub const DBUS_INTERFACE_MONITOR: &str = "org.asuslinux.Armoury.Monitor";

/// D-Bus interface for profile management
pub const DBUS_INTERFACE_PROFILES: &str = "org.asuslinux.Armoury.Profiles";
