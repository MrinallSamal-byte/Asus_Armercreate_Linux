//! Fan curve editor widget

use gtk4::{glib, prelude::*, DrawingArea};
use asus_armoury_common::{FanCurve, FanCurvePoint};

/// Widget for editing fan curves
pub struct FanCurveWidget {
    drawing_area: DrawingArea,
    curve: FanCurve,
}

impl FanCurveWidget {
    pub fn new() -> Self {
        let drawing_area = DrawingArea::new();
        drawing_area.set_content_width(400);
        drawing_area.set_content_height(300);

        let curve = FanCurve::default();

        let widget = Self {
            drawing_area,
            curve,
        };

        widget.setup_drawing();
        widget
    }

    fn setup_drawing(&self) {
        let curve = self.curve.clone();
        
        self.drawing_area.set_draw_func(move |_area, cr, width, height| {
            let width = width as f64;
            let height = height as f64;
            let padding = 40.0;
            let graph_width = width - 2.0 * padding;
            let graph_height = height - 2.0 * padding;

            // Background
            cr.set_source_rgb(0.15, 0.15, 0.15);
            let _ = cr.paint();

            // Grid
            cr.set_source_rgb(0.3, 0.3, 0.3);
            cr.set_line_width(0.5);

            // Vertical grid lines (temperature)
            for i in 0..=10 {
                let x = padding + (i as f64 / 10.0) * graph_width;
                cr.move_to(x, padding);
                cr.line_to(x, height - padding);
            }

            // Horizontal grid lines (fan %)
            for i in 0..=10 {
                let y = padding + (i as f64 / 10.0) * graph_height;
                cr.move_to(padding, y);
                cr.line_to(width - padding, y);
            }
            let _ = cr.stroke();

            // Draw curve
            cr.set_source_rgb(0.2, 0.6, 1.0);
            cr.set_line_width(2.0);

            let points = &curve.points;
            if !points.is_empty() {
                let first = &points[0];
                let x = padding + (first.temperature as f64 / 100.0) * graph_width;
                let y = height - padding - (first.fan_percent as f64 / 100.0) * graph_height;
                cr.move_to(x, y);

                for point in points.iter().skip(1) {
                    let x = padding + (point.temperature as f64 / 100.0) * graph_width;
                    let y = height - padding - (point.fan_percent as f64 / 100.0) * graph_height;
                    cr.line_to(x, y);
                }
                let _ = cr.stroke();

                // Draw points
                cr.set_source_rgb(1.0, 1.0, 1.0);
                for point in points {
                    let x = padding + (point.temperature as f64 / 100.0) * graph_width;
                    let y = height - padding - (point.fan_percent as f64 / 100.0) * graph_height;
                    cr.arc(x, y, 5.0, 0.0, 2.0 * std::f64::consts::PI);
                    let _ = cr.fill();
                }
            }

            // Labels
            cr.set_source_rgb(0.7, 0.7, 0.7);
            cr.select_font_face("Sans", gtk4::cairo::FontSlant::Normal, gtk4::cairo::FontWeight::Normal);
            cr.set_font_size(10.0);

            // X-axis labels (temperature)
            for i in 0..=5 {
                let temp = i * 20;
                let x = padding + (temp as f64 / 100.0) * graph_width;
                let text = format!("{}°C", temp);
                let extents = cr.text_extents(&text).unwrap();
                cr.move_to(x - extents.width() / 2.0, height - padding + 15.0);
                let _ = cr.show_text(&text);
            }

            // Y-axis labels (fan %)
            for i in 0..=5 {
                let percent = i * 20;
                let y = height - padding - (percent as f64 / 100.0) * graph_height;
                let text = format!("{}%", percent);
                let extents = cr.text_extents(&text).unwrap();
                cr.move_to(padding - extents.width() - 5.0, y + extents.height() / 2.0);
                let _ = cr.show_text(&text);
            }
        });
    }

    pub fn get_widget(&self) -> &DrawingArea {
        &self.drawing_area
    }

    pub fn set_curve(&mut self, curve: FanCurve) {
        self.curve = curve;
        self.drawing_area.queue_draw();
    }

    pub fn get_curve(&self) -> &FanCurve {
        &self.curve
    }
}

impl Default for FanCurveWidget {
    fn default() -> Self {
        Self::new()
    }
}
