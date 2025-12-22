"""
Main GTK4 application for ASUS Armoury Crate Linux.
"""

import sys
from typing import Optional

# Try to import GTK4 and libadwaita
try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw, Gio, GLib
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False
    # Provide stub classes for type hints
    class Gtk:
        class Application:
            pass
    class Adw:
        class Application:
            pass

from ...backend.utils.logger import get_logger
from ...backend.utils.config import Config
from ...backend.services.dbus_service import DBusClient
from ...backend.hardware.detector import HardwareDetector
from ...backend.hardware.cpu_control import CPUController
from ...backend.hardware.fan_control import FanController
from ...backend.hardware.rgb_control import RGBController
from ...backend.hardware.battery_control import BatteryController
from ...backend.hardware.thermal_monitor import ThermalMonitor
from ...backend.services.profile_manager import ProfileManager


APP_ID = "org.asus.armoury.app"


class AsusArmouryApp:
    """
    Main GTK4/libadwaita application.
    
    This is the entry point for the graphical user interface.
    """
    
    def __init__(self):
        """Initialize the application."""
        self.logger = get_logger()
        
        if not GTK_AVAILABLE:
            self.logger.error("GTK4 or libadwaita not available")
            self._app = None
            return
        
        # Initialize config
        self._config = Config()
        
        # Try to connect to D-Bus daemon first
        self._dbus_client = DBusClient(use_session_bus=True)
        
        # If D-Bus not available, use direct hardware access
        if not self._dbus_client.is_connected:
            self.logger.info("D-Bus service not available, using direct hardware access")
            self._detector = HardwareDetector()
            self._cpu = CPUController()
            self._fan = FanController()
            self._rgb = RGBController()
            self._battery = BatteryController()
            self._thermal = ThermalMonitor()
            self._profile_manager = ProfileManager(
                config=self._config,
                cpu_controller=self._cpu,
                fan_controller=self._fan,
                rgb_controller=self._rgb,
                battery_controller=self._battery
            )
        else:
            self.logger.info("Connected to D-Bus service")
            self._detector = None
            self._cpu = None
            self._fan = None
            self._rgb = None
            self._battery = None
            self._thermal = None
            self._profile_manager = None
        
        # Create GTK application
        self._app = Adw.Application(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        
        self._app.connect('activate', self._on_activate)
        self._app.connect('startup', self._on_startup)
        
        self._window: Optional['MainWindow'] = None
    
    def _on_startup(self, app: Adw.Application) -> None:
        """Handle application startup."""
        self.logger.info("Application starting...")
        
        # Set up actions
        self._setup_actions(app)
        
        # Apply dark mode if configured
        if self._config.get('dark_mode', True):
            style_manager = Adw.StyleManager.get_default()
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    
    def _on_activate(self, app: Adw.Application) -> None:
        """Handle application activation."""
        if not self._window:
            from .main_window import MainWindow
            
            self._window = MainWindow(
                application=app,
                config=self._config,
                dbus_client=self._dbus_client if self._dbus_client.is_connected else None,
                detector=self._detector,
                cpu_controller=self._cpu,
                fan_controller=self._fan,
                rgb_controller=self._rgb,
                battery_controller=self._battery,
                thermal_monitor=self._thermal,
                profile_manager=self._profile_manager
            )
        
        self._window.present()
    
    def _setup_actions(self, app: Adw.Application) -> None:
        """Set up application actions."""
        # Quit action
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: app.quit())
        app.add_action(quit_action)
        app.set_accels_for_action("app.quit", ["<Control>q"])
        
        # About action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        app.add_action(about_action)
        
        # Preferences action
        prefs_action = Gio.SimpleAction.new("preferences", None)
        prefs_action.connect("activate", self._on_preferences)
        app.add_action(prefs_action)
        app.set_accels_for_action("app.preferences", ["<Control>comma"])
    
    def _on_about(self, action: Gio.SimpleAction, param) -> None:
        """Show about dialog."""
        about = Adw.AboutWindow(
            transient_for=self._window,
            application_name="ASUS Armoury Crate",
            application_icon="org.asus.armoury",
            version="1.0.0",
            developer_name="ASUS Armoury Crate Linux Contributors",
            website="https://github.com/asus-armoury-linux",
            issue_url="https://github.com/asus-armoury-linux/issues",
            license_type=Gtk.License.GPL_3_0,
            developers=["ASUS Armoury Crate Linux Contributors"],
            copyright="© 2024 ASUS Armoury Crate Linux Contributors"
        )
        about.present()
    
    def _on_preferences(self, action: Gio.SimpleAction, param) -> None:
        """Show preferences dialog."""
        # TODO: Implement preferences dialog
        pass
    
    def run(self, argv: list = None) -> int:
        """
        Run the application.
        
        Args:
            argv: Command line arguments
            
        Returns:
            Exit code
        """
        if not GTK_AVAILABLE:
            print("Error: GTK4 or libadwaita not available")
            print("Please install: python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1")
            return 1
        
        if argv is None:
            argv = sys.argv
        
        return self._app.run(argv)


def main():
    """Main entry point for the GUI application."""
    app = AsusArmouryApp()
    return app.run()


if __name__ == '__main__':
    sys.exit(main())
