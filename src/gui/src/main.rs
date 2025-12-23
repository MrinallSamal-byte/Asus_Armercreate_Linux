//! ASUS Armoury Crate Linux GUI
//!
//! Modern GTK4/libadwaita application for controlling ASUS laptop hardware.

use gtk4::{glib, prelude::*, Application};
use libadwaita as adw;
use log::info;

mod window;
mod dbus_client;
mod widgets;

use window::MainWindow;

const APP_ID: &str = "org.asuslinux.ArmouryGui";

fn main() -> glib::ExitCode {
    // Initialize logging
    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info")
    ).init();

    info!("ASUS Armoury Crate Linux GUI starting...");

    // Initialize GTK and libadwaita
    adw::init().expect("Failed to initialize libadwaita");

    // Create application
    let app = Application::builder()
        .application_id(APP_ID)
        .build();

    app.connect_activate(build_ui);

    // Run application
    app.run()
}

fn build_ui(app: &Application) {
    // Create main window
    let window = MainWindow::new(app);
    window.present();
}
