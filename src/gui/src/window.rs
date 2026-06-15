//! Main application window

use gtk4::{glib, prelude::*, Application, Box, Label, Orientation};
use libadwaita as adw;
use adw::prelude::*;
use log::warn;
use std::sync::Arc;
use tokio::sync::Mutex;

use crate::dbus_client::DaemonClient;

/// Status labels that are updated by the periodic polling task.
struct StatusLabels {
    cpu_temp: Label,
    gpu_temp: Label,
    cpu_fan: Label,
    gpu_fan: Label,
    battery: Label,
    performance: Label,
}

/// Main application window
pub struct MainWindow {
    window: adw::ApplicationWindow,
    client: Arc<Mutex<DaemonClient>>,
}

impl MainWindow {
    pub fn new(app: &Application) -> Self {
        // Initialize D-Bus client
        let client = Arc::new(Mutex::new(DaemonClient::default()));

        // Create the main window
        let window = adw::ApplicationWindow::builder()
            .application(app)
            .title("ASUS Armoury Crate")
            .default_width(900)
            .default_height(700)
            .build();

        // Create header bar
        let header = adw::HeaderBar::new();

        // Add profile selector to header
        let profile_dropdown = gtk4::DropDown::from_strings(&[
            "Gaming", "Work", "Silent", "Balanced"
        ]);
        profile_dropdown.set_tooltip_text(Some("Select Profile"));
        header.pack_start(&profile_dropdown);

        // Create main content with sidebar navigation
        let split_view = adw::NavigationSplitView::new();

        // Create sidebar
        let sidebar_content = Self::create_sidebar();
        let sidebar_page = adw::NavigationPage::builder()
            .title("Menu")
            .child(&sidebar_content)
            .build();
        split_view.set_sidebar(Some(&sidebar_page));

        // Create main content (returns widget + label refs for live updates)
        let (content_widget, status_labels) = Self::create_content();
        let content_page = adw::NavigationPage::builder()
            .title("Dashboard")
            .child(&content_widget)
            .build();
        split_view.set_content(Some(&content_page));

        // Main layout with header
        let main_box = Box::new(Orientation::Vertical, 0);
        main_box.append(&header);
        main_box.append(&split_view);

        window.set_content(Some(&main_box));

        let window_obj = Self {
            window: window.clone(),
            client: client.clone(),
        };

        // Connect to daemon asynchronously
        let client_clone = client.clone();
        glib::MainContext::default().spawn_local(async move {
            let mut client_guard = client_clone.lock().await;
            *client_guard = DaemonClient::new().await;

            if !client_guard.is_connected() {
                warn!("Could not connect to daemon. Some features may not work.");
            }
        });

        // Start periodic status updates, passing live label references
        Self::start_status_updates(client, status_labels);

        window_obj
    }

    fn create_sidebar() -> gtk4::Widget {
        let list_box = gtk4::ListBox::new();
        list_box.set_selection_mode(gtk4::SelectionMode::Single);
        list_box.add_css_class("navigation-sidebar");

        // Navigation items
        let items = [
            ("view-dashboard-symbolic", "Dashboard"),
            ("speedometer-symbolic", "Performance"),
            ("weather-windy-symbolic", "Fans"),
            ("keyboard-symbolic", "RGB Lighting"),
            ("battery-symbolic", "Battery"),
            ("preferences-system-symbolic", "Settings"),
        ];

        for (icon, label) in items {
            let row = Self::create_nav_row(icon, label);
            list_box.append(&row);
        }

        // Select first row by default
        if let Some(first_row) = list_box.row_at_index(0) {
            list_box.select_row(Some(&first_row));
        }

        list_box.upcast()
    }

    fn create_nav_row(icon_name: &str, label_text: &str) -> gtk4::ListBoxRow {
        let row = gtk4::ListBoxRow::new();

        let hbox = Box::new(Orientation::Horizontal, 12);
        hbox.set_margin_top(8);
        hbox.set_margin_bottom(8);
        hbox.set_margin_start(12);
        hbox.set_margin_end(12);

        let icon = gtk4::Image::from_icon_name(icon_name);
        let label = Label::new(Some(label_text));

        hbox.append(&icon);
        hbox.append(&label);

        row.set_child(Some(&hbox));
        row
    }

    /// Build the main content area and return both the widget and live label
    /// references so the polling task can update them without requiring a
    /// global lookup.
    fn create_content() -> (gtk4::Widget, StatusLabels) {
        let scroll = gtk4::ScrolledWindow::new();
        scroll.set_policy(gtk4::PolicyType::Never, gtk4::PolicyType::Automatic);

        let content_box = Box::new(Orientation::Vertical, 24);
        content_box.set_margin_top(24);
        content_box.set_margin_bottom(24);
        content_box.set_margin_start(24);
        content_box.set_margin_end(24);

        // Dashboard title
        let title = Label::new(Some("Dashboard"));
        title.add_css_class("title-1");
        title.set_halign(gtk4::Align::Start);
        content_box.append(&title);

        // System status cards
        let (status_widget, status_labels) = Self::create_status_section();
        content_box.append(&status_widget);

        // Quick actions
        content_box.append(&Self::create_quick_actions());

        scroll.set_child(Some(&content_box));
        (scroll.upcast(), status_labels)
    }

    /// Build the status card grid and return it together with mutable `Label`
    /// handles so the polling task can push live data into them.
    fn create_status_section() -> (gtk4::Widget, StatusLabels) {
        let flow_box = gtk4::FlowBox::new();
        flow_box.set_selection_mode(gtk4::SelectionMode::None);
        flow_box.set_homogeneous(true);
        flow_box.set_max_children_per_line(4);
        flow_box.set_min_children_per_line(2);
        flow_box.set_row_spacing(12);
        flow_box.set_column_spacing(12);

        let (cpu_temp_widget, cpu_temp_label) =
            Self::create_status_card("CPU Temperature", "—", "temperature-symbolic");
        flow_box.append(&cpu_temp_widget);

        let (gpu_temp_widget, gpu_temp_label) =
            Self::create_status_card("GPU Temperature", "—", "temperature-symbolic");
        flow_box.append(&gpu_temp_widget);

        let (cpu_fan_widget, cpu_fan_label) =
            Self::create_status_card("CPU Fan", "—", "weather-windy-symbolic");
        flow_box.append(&cpu_fan_widget);

        let (gpu_fan_widget, gpu_fan_label) =
            Self::create_status_card("GPU Fan", "—", "weather-windy-symbolic");
        flow_box.append(&gpu_fan_widget);

        let (battery_widget, battery_label) =
            Self::create_status_card("Battery", "—", "battery-symbolic");
        flow_box.append(&battery_widget);

        let (perf_widget, perf_label) =
            Self::create_status_card("Performance", "—", "speedometer-symbolic");
        flow_box.append(&perf_widget);

        let labels = StatusLabels {
            cpu_temp: cpu_temp_label,
            gpu_temp: gpu_temp_label,
            cpu_fan: cpu_fan_label,
            gpu_fan: gpu_fan_label,
            battery: battery_label,
            performance: perf_label,
        };

        (flow_box.upcast(), labels)
    }

    /// Create a single status card.  Returns the card widget and a handle to
    /// the value `Label` so callers can update the displayed value.
    fn create_status_card(title: &str, initial_value: &str, icon: &str) -> (gtk4::Widget, Label) {
        let card = Box::new(Orientation::Vertical, 8);
        card.add_css_class("card");
        card.set_margin_top(12);
        card.set_margin_bottom(12);
        card.set_margin_start(12);
        card.set_margin_end(12);

        let icon_widget = gtk4::Image::from_icon_name(icon);
        icon_widget.set_pixel_size(32);
        icon_widget.add_css_class("dim-label");

        let title_label = Label::new(Some(title));
        title_label.add_css_class("caption");
        title_label.add_css_class("dim-label");

        let value_label = Label::new(Some(initial_value));
        value_label.add_css_class("title-2");

        card.append(&icon_widget);
        card.append(&title_label);
        card.append(&value_label);

        (card.upcast(), value_label)
    }

    fn create_quick_actions() -> gtk4::Widget {
        let group = adw::PreferencesGroup::new();
        group.set_title("Quick Actions");

        // Performance mode row
        let perf_row = adw::ComboRow::new();
        perf_row.set_title("Performance Mode");
        perf_row.set_subtitle("CPU and system performance profile");
        perf_row.set_model(Some(&gtk4::StringList::new(&[
            "Silent", "Balanced", "Turbo", "Manual"
        ])));
        perf_row.set_selected(1); // Balanced
        group.add(&perf_row);

        // GPU mode row
        let gpu_row = adw::ComboRow::new();
        gpu_row.set_title("GPU Mode");
        gpu_row.set_subtitle("Graphics switching mode (session restart may be required)");
        gpu_row.set_model(Some(&gtk4::StringList::new(&[
            "Integrated", "Hybrid", "Dedicated"
        ])));
        gpu_row.set_selected(1); // Hybrid
        group.add(&gpu_row);

        // Battery limit row
        let battery_row = adw::ComboRow::new();
        battery_row.set_title("Battery Charge Limit");
        battery_row.set_subtitle("Maximum battery charge percentage");
        battery_row.set_model(Some(&gtk4::StringList::new(&[
            "60%", "80%", "100%"
        ])));
        battery_row.set_selected(2); // 100%
        group.add(&battery_row);

        // RGB toggle
        let rgb_row = adw::SwitchRow::new();
        rgb_row.set_title("RGB Lighting");
        rgb_row.set_subtitle("Keyboard backlight");
        rgb_row.set_active(true);
        group.add(&rgb_row);

        group.upcast()
    }

    /// Schedule a 2-second polling timer that fetches live hardware data from
    /// the daemon and pushes it into the status card labels.
    fn start_status_updates(client: Arc<Mutex<DaemonClient>>, labels: StatusLabels) {
        // Wrap labels in Arc so they can be shared with the closure.
        let labels = Arc::new(labels);

        glib::timeout_add_seconds_local(2, move || {
            let client = client.clone();
            let labels = labels.clone();

            glib::MainContext::default().spawn_local(async move {
                let client_guard = client.lock().await;
                if !client_guard.is_connected() {
                    return;
                }

                // Fetch temperatures and fan speeds in parallel (sequentially
                // here because the proxy is borrowed, but each call is cheap).
                if let Some(status) = client_guard.get_system_status().await {
                    labels.cpu_temp.set_text(&format!("{:.0}°C", status.cpu_temp));
                    labels.gpu_temp.set_text(&format!("{:.0}°C", status.gpu_temp));
                    labels.cpu_fan.set_text(&format!("{} RPM", status.cpu_fan_rpm));
                    labels.gpu_fan.set_text(&format!("{} RPM", status.gpu_fan_rpm));
                    labels.battery.set_text(&format!("{}%", status.battery_percent));
                }

                if let Some(mode) = client_guard.get_performance_mode().await {
                    labels.performance.set_text(&mode);
                }
            });

            glib::ControlFlow::Continue
        });
    }

    pub fn present(&self) {
        self.window.present();
    }
}
