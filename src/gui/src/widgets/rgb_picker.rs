//! RGB color picker widget

use gtk4::{glib, prelude::*, Box, ColorButton, Label, Orientation, Scale};
use asus_armoury_common::{RgbColor, RgbEffect, RgbSettings};

/// Widget for selecting RGB colors and effects
pub struct RgbPicker {
    container: Box,
    color_button: ColorButton,
    brightness_scale: Scale,
    speed_scale: Scale,
}

impl RgbPicker {
    pub fn new() -> Self {
        let container = Box::new(Orientation::Vertical, 12);

        // Color picker
        let color_box = Box::new(Orientation::Horizontal, 8);
        let color_label = Label::new(Some("Color"));
        let color_button = ColorButton::new();
        color_button.set_rgba(&gtk4::gdk::RGBA::new(1.0, 0.0, 0.0, 1.0));
        color_box.append(&color_label);
        color_box.append(&color_button);
        container.append(&color_box);

        // Brightness slider
        let brightness_box = Box::new(Orientation::Horizontal, 8);
        let brightness_label = Label::new(Some("Brightness"));
        let brightness_scale = Scale::with_range(Orientation::Horizontal, 0.0, 100.0, 1.0);
        brightness_scale.set_value(100.0);
        brightness_scale.set_hexpand(true);
        brightness_box.append(&brightness_label);
        brightness_box.append(&brightness_scale);
        container.append(&brightness_box);

        // Speed slider
        let speed_box = Box::new(Orientation::Horizontal, 8);
        let speed_label = Label::new(Some("Speed"));
        let speed_scale = Scale::with_range(Orientation::Horizontal, 0.0, 100.0, 1.0);
        speed_scale.set_value(50.0);
        speed_scale.set_hexpand(true);
        speed_box.append(&speed_label);
        speed_box.append(&speed_scale);
        container.append(&speed_box);

        Self {
            container,
            color_button,
            brightness_scale,
            speed_scale,
        }
    }

    pub fn get_widget(&self) -> &Box {
        &self.container
    }

    pub fn get_color(&self) -> RgbColor {
        let rgba = self.color_button.rgba();
        RgbColor {
            r: (rgba.red() * 255.0) as u8,
            g: (rgba.green() * 255.0) as u8,
            b: (rgba.blue() * 255.0) as u8,
        }
    }

    pub fn set_color(&self, color: &RgbColor) {
        let rgba = gtk4::gdk::RGBA::new(
            color.r as f32 / 255.0,
            color.g as f32 / 255.0,
            color.b as f32 / 255.0,
            1.0,
        );
        self.color_button.set_rgba(&rgba);
    }

    pub fn get_brightness(&self) -> u8 {
        self.brightness_scale.value() as u8
    }

    pub fn set_brightness(&self, brightness: u8) {
        self.brightness_scale.set_value(brightness as f64);
    }

    pub fn get_speed(&self) -> u8 {
        self.speed_scale.value() as u8
    }

    pub fn set_speed(&self, speed: u8) {
        self.speed_scale.set_value(speed as f64);
    }

    pub fn get_settings(&self, effect: RgbEffect) -> RgbSettings {
        RgbSettings {
            effect,
            color: self.get_color(),
            color_secondary: None,
            brightness: self.get_brightness(),
            speed: self.get_speed(),
        }
    }

    pub fn set_settings(&self, settings: &RgbSettings) {
        self.set_color(&settings.color);
        self.set_brightness(settings.brightness);
        self.set_speed(settings.speed);
    }
}

impl Default for RgbPicker {
    fn default() -> Self {
        Self::new()
    }
}
