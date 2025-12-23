//! Main application window

use gtk4::{glib, prelude::*, Application, Box, Label, Orientation};
use libadwaita as adw;
use adw::prelude::*;
use std::sync::Arc;
use tokio::sync::Mutex;

use crate::dbus_client::DaemonClient;
use crate::widgets;

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

        // Create navigation view with pages
        let nav_view = adw::NavigationView::new();
        
        // Create main content with sidebar navigation
        let split_view = adw::NavigationSplitView::new();
        
        // Create sidebar
        let sidebar_content = Self::create_sidebar();
        let sidebar_page = adw::NavigationPage::builder()
            .title("Menu")
            .child(&sidebar_content)
            .build();
        split_view.set_sidebar(Some(&sidebar_page));
        
        // Create main content
        let content = Self::create_content();
        let content_page = adw::NavigationPage::builder()
            .title("Dashboard")
            .child(&content)
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
                eprintln!("Warning: Could not connect to daemon. Some features may not work.");
            }
        });
        
        // Start periodic status updates
        Self::start_status_updates(client, window.clone());

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

    fn create_content() -> gtk4::Widget {
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
        content_box.append(&Self::create_status_section());

        // Quick actions
        content_box.append(&Self::create_quick_actions());

        scroll.set_child(Some(&content_box));
        scroll.upcast()
    }

    fn create_status_section() -> gtk4::Widget {
        let flow_box = gtk4::FlowBox::new();
        flow_box.set_selection_mode(gtk4::SelectionMode::None);
        flow_box.set_homogeneous(true);
        flow_box.set_max_children_per_line(4);
        flow_box.set_min_children_per_line(2);
        flow_box.set_row_spacing(12);
        flow_box.set_column_spacing(12);

        // CPU Temperature card
        flow_box.append(&Self::create_status_card(
            "CPU Temperature",
            "45°C",
            "temperature-symbolic",
        ));

        // GPU Temperature card
        flow_box.append(&Self::create_status_card(
            "GPU Temperature",
            "42°C",
            "temperature-symbolic",
        ));

        // CPU Fan card
        flow_box.append(&Self::create_status_card(
            "CPU Fan",
            "2100 RPM",
            "weather-windy-symbolic",
        ));

        // GPU Fan card
        flow_box.append(&Self::create_status_card(
            "GPU Fan",
            "1800 RPM",
            "weather-windy-symbolic",
        ));

        // Battery card
        flow_box.append(&Self::create_status_card(
            "Battery",
            "85%",
            "battery-good-symbolic",
        ));

        // Performance mode card
        flow_box.append(&Self::create_status_card(
            "Performance",
            "Balanced",
            "speedometer-symbolic",
        ));

        flow_box.upcast()
    }

    fn create_status_card(title: &str, value: &str, icon: &str) -> gtk4::Widget {
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

        let value_label = Label::new(Some(value));
        value_label.add_css_class("title-2");

        card.append(&icon_widget);
        card.append(&title_label);
        card.append(&value_label);

        card.upcast()
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
        gpu_row.set_subtitle("Graphics switching mode");
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
    
    fn start_status_updates(client: Arc<Mutex<DaemonClient>>, _window: adw::ApplicationWindow) {
        // Schedule periodic updates every 2 seconds
        glib::timeout_add_seconds_local(2, move || {
            let client = client.clone();
            glib::MainContext::default().spawn_local(async move {
                let client_guard = client.lock().await;
                if client_guard.is_connected() {
                    // Fetch status from daemon
                    if let Some(_status) = client_guard.get_system_status().await {
                        // TODO: Update UI widgets with new status
                        // This would require storing references to the UI widgets
                    }
                }
            });
            glib::ControlFlow::Continue
        });
    }

    pub fn present(&self) {
        self.window.present();
    }
}
