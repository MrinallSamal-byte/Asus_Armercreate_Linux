"""
Main window for ASUS Armoury Crate Linux.
"""

from typing import Optional, Dict, Any

try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw, Gio, GLib, Gdk
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from ...backend.utils.logger import get_logger
from ...backend.utils.config import Config
from ...backend.services.dbus_service import DBusClient
from ...backend.hardware.detector import HardwareDetector
from ...backend.hardware.cpu_control import CPUController, CPUMode
from ...backend.hardware.fan_control import FanController
from ...backend.hardware.rgb_control import RGBController, RGBMode, RGBColor
from ...backend.hardware.battery_control import BatteryController
from ...backend.hardware.thermal_monitor import ThermalMonitor
from ...backend.services.profile_manager import ProfileManager


class MainWindow(Adw.ApplicationWindow if GTK_AVAILABLE else object):
    """
    Main application window.
    
    Contains the dashboard and all control panels.
    """
    
    def __init__(
        self,
        application,
        config: Config,
        dbus_client: Optional[DBusClient] = None,
        detector: Optional[HardwareDetector] = None,
        cpu_controller: Optional[CPUController] = None,
        fan_controller: Optional[FanController] = None,
        rgb_controller: Optional[RGBController] = None,
        battery_controller: Optional[BatteryController] = None,
        thermal_monitor: Optional[ThermalMonitor] = None,
        profile_manager: Optional[ProfileManager] = None
    ):
        """Initialize main window."""
        if not GTK_AVAILABLE:
            return
        
        super().__init__(application=application)
        
        self.logger = get_logger()
        self._config = config
        self._dbus = dbus_client
        self._detector = detector
        self._cpu = cpu_controller
        self._fan = fan_controller
        self._rgb = rgb_controller
        self._battery = battery_controller
        self._thermal = thermal_monitor
        self._profile_manager = profile_manager
        
        # Window properties
        self.set_title("ASUS Armoury Crate")
        self.set_default_size(1000, 700)
        
        # Build UI
        self._build_ui()
        
        # Start update timer
        self._update_interval = 1000  # milliseconds
        GLib.timeout_add(self._update_interval, self._update_stats)
        
        # Initial update
        self._update_stats()
    
    def _build_ui(self) -> None:
        """Build the user interface."""
        # Main layout with navigation
        self._split_view = Adw.NavigationSplitView()
        self._split_view.set_max_sidebar_width(220)
        self._split_view.set_min_sidebar_width(180)
        
        # Sidebar
        sidebar = self._build_sidebar()
        self._split_view.set_sidebar(sidebar)
        
        # Content
        self._content_stack = Gtk.Stack()
        self._content_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Add pages
        self._content_stack.add_titled(self._build_dashboard_page(), "dashboard", "Dashboard")
        self._content_stack.add_titled(self._build_performance_page(), "performance", "Performance")
        self._content_stack.add_titled(self._build_fan_page(), "fans", "Fans")
        self._content_stack.add_titled(self._build_rgb_page(), "rgb", "RGB")
        self._content_stack.add_titled(self._build_battery_page(), "battery", "Battery")
        self._content_stack.add_titled(self._build_profiles_page(), "profiles", "Profiles")
        
        content_page = Adw.NavigationPage(child=self._content_stack, title="Dashboard")
        self._split_view.set_content(content_page)
        
        # Set as window content
        self.set_content(self._split_view)
    
    def _build_sidebar(self) -> Adw.NavigationPage:
        """Build the sidebar navigation."""
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        sidebar_box.append(header)
        
        # Navigation list
        nav_list = Gtk.ListBox()
        nav_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        nav_list.add_css_class("navigation-sidebar")
        
        # Navigation items
        nav_items = [
            ("dashboard", "Dashboard", "computer-symbolic"),
            ("performance", "Performance", "speedometer-symbolic"),
            ("fans", "Fans", "weather-windy-symbolic"),
            ("rgb", "RGB Keyboard", "preferences-color-symbolic"),
            ("battery", "Battery", "battery-symbolic"),
            ("profiles", "Profiles", "view-list-symbolic"),
        ]
        
        for page_id, label, icon in nav_items:
            row = Adw.ActionRow()
            row.set_title(label)
            row.set_icon_name(icon)
            row.page_id = page_id
            nav_list.append(row)
        
        nav_list.connect("row-selected", self._on_nav_selected)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_child(nav_list)
        
        sidebar_box.append(scroll)
        
        # Select first item
        first_row = nav_list.get_row_at_index(0)
        if first_row:
            nav_list.select_row(first_row)
        
        return Adw.NavigationPage(child=sidebar_box, title="Navigation")
    
    def _on_nav_selected(self, listbox: Gtk.ListBox, row: Adw.ActionRow) -> None:
        """Handle navigation selection."""
        if row and hasattr(row, 'page_id'):
            self._content_stack.set_visible_child_name(row.page_id)
    
    def _build_dashboard_page(self) -> Gtk.Widget:
        """Build the dashboard page."""
        page = Adw.ToolbarView()
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Dashboard", subtitle="System Overview"))
        page.add_top_bar(header)
        
        # Content
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)
        
        # System Info Card
        system_group = Adw.PreferencesGroup(title="System Information")
        
        self._model_row = Adw.ActionRow(title="Model", subtitle="Detecting...")
        system_group.add(self._model_row)
        
        self._cpu_model_row = Adw.ActionRow(title="CPU", subtitle="Detecting...")
        system_group.add(self._cpu_model_row)
        
        content.append(system_group)
        
        # Stats Cards
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        stats_box.set_homogeneous(True)
        
        # CPU Temperature Card
        cpu_card = self._create_stat_card("CPU Temperature", "-- °C", "thermometer-symbolic")
        self._cpu_temp_label = cpu_card.get_data("value_label")
        stats_box.append(cpu_card)
        
        # GPU Temperature Card
        gpu_card = self._create_stat_card("GPU Temperature", "-- °C", "video-display-symbolic")
        self._gpu_temp_label = gpu_card.get_data("value_label")
        stats_box.append(gpu_card)
        
        # Fan Speed Card
        fan_card = self._create_stat_card("Fan Speed", "-- RPM", "weather-windy-symbolic")
        self._fan_speed_label = fan_card.get_data("value_label")
        stats_box.append(fan_card)
        
        content.append(stats_box)
        
        # Performance Mode Card
        perf_group = Adw.PreferencesGroup(title="Quick Controls")
        
        self._perf_mode_row = Adw.ComboRow(title="Performance Mode")
        self._perf_mode_row.set_subtitle("Current CPU performance profile")
        
        modes = Gtk.StringList()
        for mode in ["Silent", "Balanced", "Turbo"]:
            modes.append(mode)
        self._perf_mode_row.set_model(modes)
        self._perf_mode_row.connect("notify::selected", self._on_perf_mode_changed)
        perf_group.add(self._perf_mode_row)
        
        # Battery Charge Limit
        self._battery_row = Adw.SpinRow.new_with_range(20, 100, 10)
        self._battery_row.set_title("Battery Charge Limit")
        self._battery_row.set_subtitle("Maximum battery charge level")
        self._battery_row.connect("notify::value", self._on_battery_limit_changed)
        perf_group.add(self._battery_row)
        
        content.append(perf_group)
        
        scroll.set_child(content)
        page.set_content(scroll)
        
        return page
    
    def _create_stat_card(self, title: str, value: str, icon: str) -> Gtk.Frame:
        """Create a statistics card widget."""
        frame = Gtk.Frame()
        frame.add_css_class("card")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)
        
        icon_widget = Gtk.Image.new_from_icon_name(icon)
        icon_widget.set_pixel_size(32)
        icon_widget.add_css_class("dim-label")
        box.append(icon_widget)
        
        title_label = Gtk.Label(label=title)
        title_label.add_css_class("dim-label")
        box.append(title_label)
        
        value_label = Gtk.Label(label=value)
        value_label.add_css_class("title-1")
        box.append(value_label)
        
        frame.set_child(box)
        frame.set_data("value_label", value_label)
        
        return frame
    
    def _build_performance_page(self) -> Gtk.Widget:
        """Build the performance control page."""
        page = Adw.ToolbarView()
        
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Performance", subtitle="CPU & GPU Control"))
        page.add_top_bar(header)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)
        
        # CPU Mode
        cpu_group = Adw.PreferencesGroup(title="CPU Performance")
        
        mode_row = Adw.ComboRow(title="Performance Mode")
        modes = Gtk.StringList()
        for mode in ["Silent", "Balanced", "Turbo"]:
            modes.append(mode)
        mode_row.set_model(modes)
        mode_row.set_selected(1)  # Balanced
        cpu_group.add(mode_row)
        
        content.append(cpu_group)
        
        # CPU Info
        info_group = Adw.PreferencesGroup(title="CPU Information")
        
        self._cpu_freq_row = Adw.ActionRow(title="Current Frequency", subtitle="-- MHz")
        info_group.add(self._cpu_freq_row)
        
        self._cpu_governor_row = Adw.ActionRow(title="Governor", subtitle="--")
        info_group.add(self._cpu_governor_row)
        
        content.append(info_group)
        
        scroll.set_child(content)
        page.set_content(scroll)
        
        return page
    
    def _build_fan_page(self) -> Gtk.Widget:
        """Build the fan control page."""
        page = Adw.ToolbarView()
        
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Fans", subtitle="Fan Speed Control"))
        page.add_top_bar(header)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)
        
        # Fan Mode
        mode_group = Adw.PreferencesGroup(title="Fan Mode")
        
        auto_row = Adw.SwitchRow(title="Automatic Control")
        auto_row.set_subtitle("Let the system control fan speeds")
        auto_row.set_active(True)
        mode_group.add(auto_row)
        
        content.append(mode_group)
        
        # Fan Status
        status_group = Adw.PreferencesGroup(title="Fan Status")
        
        self._fan1_row = Adw.ActionRow(title="CPU Fan", subtitle="-- RPM")
        status_group.add(self._fan1_row)
        
        self._fan2_row = Adw.ActionRow(title="GPU Fan", subtitle="-- RPM")
        status_group.add(self._fan2_row)
        
        content.append(status_group)
        
        # Manual Control
        manual_group = Adw.PreferencesGroup(title="Manual Control")
        manual_group.set_description("Available when automatic control is disabled")
        
        fan_speed_row = Adw.SpinRow.new_with_range(0, 100, 5)
        fan_speed_row.set_title("Fan Speed")
        fan_speed_row.set_subtitle("Speed percentage for all fans")
        fan_speed_row.set_value(50)
        manual_group.add(fan_speed_row)
        
        content.append(manual_group)
        
        scroll.set_child(content)
        page.set_content(scroll)
        
        return page
    
    def _build_rgb_page(self) -> Gtk.Widget:
        """Build the RGB keyboard control page."""
        page = Adw.ToolbarView()
        
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="RGB Keyboard", subtitle="Lighting Control"))
        page.add_top_bar(header)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)
        
        # RGB Mode
        mode_group = Adw.PreferencesGroup(title="Lighting Mode")
        
        mode_row = Adw.ComboRow(title="Mode")
        modes = Gtk.StringList()
        for mode in ["Off", "Static", "Breathing", "Color Cycle", "Rainbow", "Strobe"]:
            modes.append(mode)
        mode_row.set_model(modes)
        mode_row.set_selected(1)  # Static
        mode_group.add(mode_row)
        
        # Brightness
        brightness_row = Adw.SpinRow.new_with_range(0, 100, 10)
        brightness_row.set_title("Brightness")
        brightness_row.set_value(100)
        mode_group.add(brightness_row)
        
        # Speed
        speed_row = Adw.SpinRow.new_with_range(0, 100, 10)
        speed_row.set_title("Animation Speed")
        speed_row.set_value(50)
        mode_group.add(speed_row)
        
        content.append(mode_group)
        
        # Color Selection
        color_group = Adw.PreferencesGroup(title="Color")
        
        # Color button
        color_row = Adw.ActionRow(title="Select Color")
        color_row.set_subtitle("#FF0000")
        
        color_button = Gtk.ColorButton()
        color_button.set_valign(Gtk.Align.CENTER)
        color_button.set_rgba(Gdk.RGBA(red=1.0, green=0.0, blue=0.0, alpha=1.0))
        color_row.add_suffix(color_button)
        color_row.set_activatable_widget(color_button)
        
        color_group.add(color_row)
        
        content.append(color_group)
        
        # Presets
        preset_group = Adw.PreferencesGroup(title="Color Presets")
        
        preset_box = Gtk.FlowBox()
        preset_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        preset_box.set_max_children_per_line(6)
        preset_box.set_homogeneous(True)
        
        presets = [
            ("#FF0000", "Red"),
            ("#00FF00", "Green"),
            ("#0000FF", "Blue"),
            ("#FFFF00", "Yellow"),
            ("#FF00FF", "Magenta"),
            ("#00FFFF", "Cyan"),
            ("#FF8000", "Orange"),
            ("#8000FF", "Purple"),
            ("#FFFFFF", "White"),
        ]
        
        for color, name in presets:
            btn = Gtk.Button()
            btn.set_size_request(50, 50)
            btn.set_tooltip_text(name)
            
            # Set button color using CSS
            css = f"button {{ background: {color}; min-width: 50px; min-height: 50px; }}"
            provider = Gtk.CssProvider()
            provider.load_from_data(css.encode())
            btn.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            
            preset_box.append(btn)
        
        preset_group.add(preset_box)
        content.append(preset_group)
        
        scroll.set_child(content)
        page.set_content(scroll)
        
        return page
    
    def _build_battery_page(self) -> Gtk.Widget:
        """Build the battery control page."""
        page = Adw.ToolbarView()
        
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Battery", subtitle="Power Management"))
        page.add_top_bar(header)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)
        
        # Battery Status
        status_group = Adw.PreferencesGroup(title="Battery Status")
        
        self._battery_status_row = Adw.ActionRow(title="Status", subtitle="Unknown")
        status_group.add(self._battery_status_row)
        
        self._battery_level_row = Adw.ActionRow(title="Charge Level", subtitle="--%")
        status_group.add(self._battery_level_row)
        
        self._battery_health_row = Adw.ActionRow(title="Health", subtitle="--%")
        status_group.add(self._battery_health_row)
        
        content.append(status_group)
        
        # Charge Limit
        limit_group = Adw.PreferencesGroup(title="Charge Limit")
        limit_group.set_description("Limit maximum charge to extend battery lifespan")
        
        limit_row = Adw.SpinRow.new_with_range(20, 100, 10)
        limit_row.set_title("Maximum Charge")
        limit_row.set_subtitle("Recommended: 80% for daily use, 60% if always plugged in")
        limit_row.set_value(80)
        limit_group.add(limit_row)
        
        # Preset buttons
        preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        preset_box.set_halign(Gtk.Align.CENTER)
        preset_box.set_margin_top(8)
        
        for limit, label in [(60, "Max Lifespan"), (80, "Balanced"), (100, "Full Charge")]:
            btn = Gtk.Button(label=f"{label} ({limit}%)")
            btn.connect("clicked", lambda b, l=limit: limit_row.set_value(l))
            preset_box.append(btn)
        
        limit_group.add(preset_box)
        content.append(limit_group)
        
        scroll.set_child(content)
        page.set_content(scroll)
        
        return page
    
    def _build_profiles_page(self) -> Gtk.Widget:
        """Build the profiles management page."""
        page = Adw.ToolbarView()
        
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Profiles", subtitle="Saved Configurations"))
        
        # Add profile button
        add_btn = Gtk.Button.new_from_icon_name("list-add-symbolic")
        add_btn.set_tooltip_text("Create new profile")
        header.pack_end(add_btn)
        
        page.add_top_bar(header)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)
        
        # Profiles List
        profiles_group = Adw.PreferencesGroup(title="Available Profiles")
        
        # Built-in profiles
        profiles = [
            ("Silent", "Low performance, quiet operation", "weather-few-clouds-symbolic"),
            ("Balanced", "Optimal balance of performance and power", "weather-overcast-symbolic"),
            ("Turbo", "Maximum performance", "weather-storm-symbolic"),
            ("Gaming", "Optimized for gaming workloads", "input-gaming-symbolic"),
        ]
        
        for name, desc, icon in profiles:
            row = Adw.ActionRow(title=name, subtitle=desc)
            row.set_icon_name(icon)
            
            apply_btn = Gtk.Button(label="Apply")
            apply_btn.add_css_class("suggested-action")
            apply_btn.set_valign(Gtk.Align.CENTER)
            apply_btn.connect("clicked", lambda b, n=name: self._apply_profile(n))
            row.add_suffix(apply_btn)
            
            profiles_group.add(row)
        
        content.append(profiles_group)
        
        scroll.set_child(content)
        page.set_content(scroll)
        
        return page
    
    def _update_stats(self) -> bool:
        """Update dashboard statistics."""
        try:
            # Update temperatures
            if self._thermal:
                cpu_temp = self._thermal.get_cpu_package_temp()
                if cpu_temp is not None:
                    self._cpu_temp_label.set_text(f"{cpu_temp:.1f} °C")
                
                gpu_temp = self._thermal.get_gpu_temperature()
                if gpu_temp is not None:
                    self._gpu_temp_label.set_text(f"{gpu_temp:.1f} °C")
            elif self._dbus:
                temps = self._dbus.get_temperatures()
                if 'CPU Package' in temps:
                    self._cpu_temp_label.set_text(f"{temps['CPU Package']:.1f} °C")
                if 'GPU' in temps:
                    self._gpu_temp_label.set_text(f"{temps['GPU']:.1f} °C")
            
            # Update fan speed
            if self._fan:
                fan_info = self._fan.get_fan_info(1)
                if fan_info:
                    self._fan_speed_label.set_text(f"{fan_info.current_rpm} RPM")
                    self._fan1_row.set_subtitle(f"{fan_info.current_rpm} RPM")
                
                fan_info2 = self._fan.get_fan_info(2)
                if fan_info2:
                    self._fan2_row.set_subtitle(f"{fan_info2.current_rpm} RPM")
            
            # Update battery
            if self._battery:
                battery_info = self._battery.get_battery_info()
                if battery_info.get('present'):
                    self._battery_status_row.set_subtitle(battery_info.get('status', 'Unknown'))
                    if battery_info.get('capacity'):
                        self._battery_level_row.set_subtitle(f"{battery_info['capacity']}%")
                    if battery_info.get('health'):
                        self._battery_health_row.set_subtitle(f"{battery_info['health']:.1f}%")
            
            # Update system info
            if self._detector:
                caps = self._detector.capabilities
                self._model_row.set_subtitle(caps.model_name or "Unknown")
                self._cpu_model_row.set_subtitle(caps.cpu_model or "Unknown")
            
            # Update CPU info
            if self._cpu:
                freq_info = self._cpu.get_cpu_frequency_info()
                if freq_info.get('current_freq_mhz'):
                    self._cpu_freq_row.set_subtitle(f"{freq_info['current_freq_mhz']:.0f} MHz")
                if freq_info.get('governor'):
                    self._cpu_governor_row.set_subtitle(freq_info['governor'])
                
        except Exception as e:
            self.logger.error(f"Error updating stats: {e}")
        
        return True  # Continue timer
    
    def _on_perf_mode_changed(self, row: Adw.ComboRow, param) -> None:
        """Handle performance mode change."""
        selected = row.get_selected()
        modes = [CPUMode.SILENT, CPUMode.BALANCED, CPUMode.TURBO]
        
        if 0 <= selected < len(modes):
            mode = modes[selected]
            if self._cpu:
                self._cpu.set_mode(mode)
            elif self._dbus:
                self._dbus.set_cpu_mode(mode.value)
    
    def _on_battery_limit_changed(self, row: Adw.SpinRow, param) -> None:
        """Handle battery charge limit change."""
        limit = int(row.get_value())
        
        if self._battery:
            self._battery.set_charge_limit(limit)
        elif self._dbus:
            self._dbus.call("SetBatteryChargeLimit", limit)
    
    def _apply_profile(self, name: str) -> None:
        """Apply a performance profile."""
        self.logger.info(f"Applying profile: {name}")
        
        if self._profile_manager:
            self._profile_manager.apply_profile(name)
        elif self._dbus:
            self._dbus.call("ApplyProfile", name)
        
        # Show notification
        toast = Adw.Toast(title=f"Profile '{name}' applied")
        toast.set_timeout(2)
        
        # Find toast overlay and show toast
        # For now just log
        self.logger.info(f"Profile {name} applied")
