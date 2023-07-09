use itertools::Itertools;
use polars::export::num::Pow;
use regex::Regex;
use std::cmp::Ordering;
use std::fmt::Error;

#[derive(PartialEq, Debug, Clone)]
pub struct Color {
    r: u8,
    g: u8,
    b: u8,
}

impl Color {
    pub fn new(r: u8, g: u8, b: u8) -> Self {
        Color { r, g, b }
    }

    pub fn from_hex(hex: &str) -> Result<Self, Error> {
        if hex.len() != 7 {
            return Err(Error);
        }
        let r = u8::from_str_radix(&hex[1..3], 16).map_err(|_| Error)?;
        let g = u8::from_str_radix(&hex[3..5], 16).map_err(|_| Error)?;
        let b = u8::from_str_radix(&hex[5..7], 16).map_err(|_| Error)?;
        Ok(Color::new(r, g, b))
    }

    pub fn from_rgb(rgb: &str) -> Result<Self, Error> {
        let re = Regex::new(r"rgb\((\d+), (\d+), (\d+)\)$").unwrap();

        let captures = re.captures(rgb).ok_or(Error)?;
        let mut groups = captures.iter().skip(1).map(|m| {
            let m = m.ok_or(Error)?;
            m.as_str().parse::<u8>().map_err(|_| Error)
        });

        let r = groups.next().ok_or(Error)??;
        let g = groups.next().ok_or(Error)??;
        let b = groups.next().ok_or(Error)??;
        Ok(Color::new(r, g, b))
    }

    fn to_csv(&self) -> String {
        format!("{}, {}, {}", self.r, self.g, self.b)
    }

    pub fn to_hex(&self) -> String {
        format!("#{:02x}{:02x}{:02x}", self.r, self.g, self.b)
    }

    pub fn to_rgb(&self) -> String {
        format!("rgb({})", self.to_csv())
    }

    pub fn to_rgba(&self, a: f64) -> String {
        // TODO: create struct for color with opacity
        format!("rgba({}, {})", self.to_csv(), a)
    }

    pub fn relative_luminance(&self) -> f64 {
        0.2126 * normalize_channel(self.r)
            + 0.7152 * normalize_channel(self.g)
            + 0.0722 * normalize_channel(self.b)
    }
}

impl TryFrom<&str> for Color {
    type Error = Error;

    fn try_from(s: &str) -> Result<Self, Error> {
        if let Ok(hex) = Color::from_hex(s) {
            return Ok(hex);
        }
        if let Ok(rgb) = Color::from_rgb(s) {
            return Ok(rgb);
        }
        match s {
            "red" => Ok(Color::new(255, 0, 0)),
            "green" => Ok(Color::new(0, 255, 0)),
            "blue" => Ok(Color::new(0, 0, 255)),
            "yellow" => Ok(Color::new(255, 255, 0)),
            "cyan" => Ok(Color::new(0, 255, 255)),
            "magenta" => Ok(Color::new(255, 0, 255)),
            "black" => Ok(Color::new(0, 0, 0)),
            "white" => Ok(Color::new(255, 255, 255)),
            _ => Err(Error),
        }
    }
}

#[derive(PartialEq, Debug)]
pub struct Gradient {
    start: Color,
    end: Color,
}

impl Gradient {
    pub fn new(start: Color, end: Color) -> Self {
        Gradient { start, end }
    }

    pub fn interpolate(&self, a: f64) -> Result<Color, Error> {
        if !(0.0..=1.0).contains(&a) {
            return Err(Error);
        }
        let r = interpolate(self.start.r, self.end.r, a);
        let g = interpolate(self.start.g, self.end.g, a);
        let b = interpolate(self.start.b, self.end.b, a);
        Ok(Color::new(r, g, b))
    }
}

#[derive(Clone, Debug)]
pub struct ColorBreakPoint {
    value: f64,
    color: Color,
}

impl PartialEq<Self> for ColorBreakPoint {
    fn eq(&self, other: &Self) -> bool {
        self.value.eq(&other.value)
    }
}

impl PartialOrd for ColorBreakPoint {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        self.value.partial_cmp(&other.value)
    }
}

#[derive(Clone, Debug)]
pub struct ColorMap {
    v: Vec<ColorBreakPoint>,
}

impl ColorMap {
    pub fn new(v: Vec<ColorBreakPoint>) -> Self {
        // TODO: check that v is sorted
        ColorMap { v }
    }

    pub fn red_scale() -> Self {
        ColorMap::from_palette(vec![Color::new(255, 255, 255), Color::new(255, 0, 0)])
    }

    pub fn from_palette(colors: Vec<Color>) -> Self {
        let n = colors.len();
        let v = colors
            .iter()
            .enumerate()
            .map(|(i, c)| ColorBreakPoint {
                value: i as f64 / (n - 1) as f64,
                color: c.clone(),
            })
            .collect();
        ColorMap::new(v)
    }

    pub fn get(&self, value: f64) -> Result<Color, Error> {
        if value < self.v[0].value {
            // TODO: maybe throw an error?
            return Ok(self.v[0].color.clone());
        }
        for (left, right) in self.v.iter().tuples() {
            if value == left.value {
                return Ok(left.color.clone());
            }
            if value < right.value {
                let a = (value - left.value) / (right.value - left.value);
                let gradient = Gradient::new(left.color.clone(), right.color.clone());
                return gradient.interpolate(a);
            }
        }
        let n = self.v.len();
        Ok(self.v[n - 1].color.clone())
    }
}

fn interpolate(x: u8, y: u8, a: f64) -> u8 {
    (x as f64 * (1.0 - a) + y as f64 * a).round() as u8
}

fn normalize_channel(x: u8) -> f64 {
    let x = x as f64 / 255.0;
    if x <= 0.04045 {
        return x / 12.92;
    }
    ((x + 0.055) / 1.055).pow(2.4)
}

#[cfg(test)]
mod test {
    use super::*;
    use polars::export::num::abs;

    #[test]
    fn test_color_csv() {
        let c = Color::new(110, 50, 0);
        assert_eq!(c.to_csv(), "110, 50, 0");
    }

    #[test]
    fn test_color_hex() {
        let c = Color::new(110, 50, 0);
        assert_eq!(c.to_hex(), "#6e3200");
    }

    #[test]
    fn test_color_luminance() {
        let c = Color::new(110, 50, 0);
        assert!(abs(c.relative_luminance() - 0.055962009) < 0.0001);
    }

    #[test]
    fn test_color_luminance_black() {
        let c = Color::new(0, 0, 0);
        assert_eq!(c.relative_luminance(), 0.0);
    }

    #[test]
    fn test_color_luminance_white() {
        let c = Color::new(255, 255, 255);
        assert_eq!(c.relative_luminance(), 1.0);
    }

    #[test]
    fn test_interpolate_u8() {
        assert_eq!(interpolate(0, 10, 0.0), 0);
        assert_eq!(interpolate(0, 10, 0.5), 5);
        assert_eq!(interpolate(0, 10, 1.0), 10);
    }

    #[test]
    fn test_from_hex() {
        assert_eq!(Color::from_hex("#6e3200"), Ok(Color::new(110, 50, 0)));
    }

    #[test]
    fn test_from_rgb() {
        assert_eq!(
            Color::from_rgb("rgb(110, 50, 0)"),
            Ok(Color::new(110, 50, 0))
        );
    }

    #[test]
    fn test_from_rgb_fail() {
        assert!(Color::from_rgb("110, 50, 0").is_err());
        assert!(Color::from_rgb("(110, 50, 0)").is_err());
        assert!(Color::from_rgb("rgb(110, 110, 50, 0)").is_err());
        assert!(Color::from_rgb("#6e3200").is_err());
    }

    #[test]
    fn test_interpolate_color() {
        let gradient = Gradient::new(Color::new(0, 0, 0), Color::new(10, 10, 10));
        let color = gradient.interpolate(0.5).unwrap();
        let expected = Color::new(5, 5, 5);
        assert_eq!(color, expected);
    }

    #[test]
    fn test_interpolate_color_start() {
        let start = Color::new(0, 0, 0);
        let end = Color::new(100, 255, 0);
        let gradient = Gradient::new(start.clone(), end.clone());

        assert_eq!(gradient.interpolate(0.0), Ok(start));
        assert_eq!(gradient.interpolate(1.0), Ok(end));
    }
}
