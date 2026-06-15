//! D-Bus interface constants for communication between daemon and GUI
//!
//! The daemon currently exposes **one** D-Bus interface (`DBUS_INTERFACE`) that
//! aggregates all functionality (performance, fans, RGB, battery, profiles).
//! The sub-interface constants below (`DBUS_INTERFACE_*`) are reserved names
//! for a future refactor that splits the interface into per-feature objects.
//! They are **not** registered on the bus today — use `DBUS_INTERFACE` for all
//! proxy calls.

/// Well-known D-Bus service name for the ASUS Armoury daemon.
pub const DBUS_NAME: &str = "org.asuslinux.Armoury";

/// D-Bus object path at which the main interface is registered.
pub const DBUS_PATH: &str = "/org/asuslinux/Armoury";

/// Primary D-Bus interface name.  All current methods live here.
pub const DBUS_INTERFACE: &str = "org.asuslinux.Armoury";

// ---------------------------------------------------------------------------
// Reserved sub-interface names (NOT currently registered on the bus)
// ---------------------------------------------------------------------------

/// Reserved interface name for a future dedicated performance-control object.
pub const DBUS_INTERFACE_PERFORMANCE: &str = "org.asuslinux.Armoury.Performance";

/// Reserved interface name for a future dedicated fan-control object.
pub const DBUS_INTERFACE_FAN: &str = "org.asuslinux.Armoury.Fan";

/// Reserved interface name for a future dedicated RGB-control object.
pub const DBUS_INTERFACE_RGB: &str = "org.asuslinux.Armoury.RGB";

/// Reserved interface name for a future dedicated battery-settings object.
pub const DBUS_INTERFACE_BATTERY: &str = "org.asuslinux.Armoury.Battery";

/// Reserved interface name for a future dedicated system-monitoring object.
pub const DBUS_INTERFACE_MONITOR: &str = "org.asuslinux.Armoury.Monitor";

/// Reserved interface name for a future dedicated profile-management object.
pub const DBUS_INTERFACE_PROFILES: &str = "org.asuslinux.Armoury.Profiles";
