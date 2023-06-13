use crate::renderer::Renderer;

use polars::prelude::*;
use std::collections::HashMap;

pub trait StylerExt {
    fn style(&self) -> Styler;
}

impl StylerExt for DataFrame {
    fn style(&self) -> Styler {
        Styler::new(self)
    }
}

#[derive(Clone)]
pub struct Styler {
    df: DataFrame,
    params: StylerParams,
    applied_styles: Vec<Vec<HashMap<String, String>>>, // (col, row) => (attribute => value)
}

#[derive(Default, Clone)]
pub struct StylerParams {
    precision: Option<u32>,
}

impl Styler {
    pub fn new(df: &DataFrame) -> Styler {
        Styler {
            df: df.clone(),
            params: StylerParams::default(),
            applied_styles: vec![vec![HashMap::new(); df.height()]; df.width()],
        }
    }

    pub fn apply(
        mut self,
        column: &str,
        f: impl Fn(&Series) -> Vec<HashMap<String, String>>,
    ) -> Self {
        let (col, series) = self
            .icolumn(column)
            .expect(&format!("Unknown column {}", &column));
        let new_styles = f(series);
        self.applied_styles[col]
            .iter_mut()
            .zip(new_styles)
            .for_each(|(a, b)| a.extend(b));
        self
    }

    pub fn set_precision(mut self, precision: u32) -> Self {
        if self.params.precision.is_some() {
            panic!("precision can only be set once");
        }
        self.params.precision = Some(precision);
        self
    }

    pub fn render(self) -> String {
        let data = self
            .df
            .iter()
            .map(|row| format_row(row, &self.params))
            .collect();

        let mut cell_styles: HashMap<(usize, usize), HashMap<String, String>> = HashMap::new();
        for (i, vec) in self.applied_styles.iter().enumerate() {
            for (j, map) in vec.iter().enumerate() {
                if map.is_empty() {
                    continue;
                }
                cell_styles.insert((i, j), map.clone());
            }
        }

        let renderer = Renderer {
            column_names: self.column_names(),
            cell_values: data,
            cell_styles,
            hash: "asdf123".to_string(),
        };

        renderer.render()
    }

    fn column_names(&self) -> Vec<String> {
        self.df
            .get_column_names()
            .iter()
            .map(|v| v.to_string())
            .collect::<Vec<_>>()
    }

    fn icolumn(&self, column: &str) -> Option<(usize, &Series)> {
        let col = self
            .df
            .get_column_names()
            .iter()
            .position(|v| v == &column)?;
        Some((col, self.df.column(column).unwrap()))
    }
}

fn format_row(s: &Series, params: &StylerParams) -> Vec<String> {
    s.iter().map(|v| format_value(&v, params)).collect()
}

fn format_value(v: &AnyValue, params: &StylerParams) -> String {
    match v {
        AnyValue::Float64(f) => {
            let Some(precision) = &params.precision else {
                return f.to_string();
            };
            format!("{:.1$}", f, *precision as usize)
        }
        AnyValue::Float32(f) => {
            let Some(precision) = &params.precision else {
                return f.to_string();
            };
            format!("{:.1$}", f, *precision as usize)
        }
        AnyValue::Utf8(s) => s.to_string(),
        _ => v.to_string(),
    }
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn test_styler() {
        let df = DataFrame::new(vec![
            Series::new("a", &[1, 222, 3]),
            Series::new("b", &["fooo", "b", "c"]),
        ])
        .unwrap();

        let styler = df.style();
        let html = styler.render();
        println!("{}", html);
        assert!(html.contains("<style>"));
        assert!(html.contains("<div>"));
        assert!(html.contains("</div>"));
        assert!(html.find("fooo").unwrap() < html.find("222").unwrap());
    }

    #[test]
    fn test_precision() {
        let x = 1.123456789;
        let df = DataFrame::new(vec![Series::new("a", &[x, 2.123456789, 3.123456789])]).unwrap();

        let styler = df.style().set_precision(2);
        let html = styler.render();
        println!("{}", html);
        assert!(html.contains(format!("{:.2}", x).as_str()));
        assert!(!html.contains(format!("{:.3}", x).as_str()));
    }

    #[test]
    fn test_apply() {
        let df = DataFrame::new(vec![
            Series::new("a", &[1, 222, 3]),
            Series::new("b", &["fooo", "b", "c"]),
        ])
        .unwrap();

        let styler = df.style().apply("a", |s| {
            s.iter()
                .map(|v| {
                    if v == AnyValue::Int32(222) {
                        vec![("background-color".to_string(), "red".to_string())]
                    } else {
                        vec![]
                    }
                })
                .map(|v| v.into_iter().collect::<HashMap<_, _>>())
                .collect::<Vec<_>>()
        });
        assert!(styler
            .applied_styles
            .iter()
            .any(|v| { v.iter().any(|hm| !hm.is_empty()) }));
    }
}
