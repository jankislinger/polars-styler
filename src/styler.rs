use crate::renderer::Renderer;

use crate::colors::Color;
use polars::prelude::*;
use polars_lazy::prelude::*;
use rand::Rng;
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
    labels: HashMap<String, String>,
}

#[derive(Default, Clone)]
pub struct StylerParams {
    precision: Option<u32>,
    table_classes: Option<Vec<String>>,
}

impl Styler {
    pub fn new(df: &DataFrame) -> Styler {
        Styler {
            df: df.clone(),
            params: StylerParams::default(),
            applied_styles: vec![vec![HashMap::new(); df.height()]; df.width()],
            labels: HashMap::new(),
        }
    }

    pub fn apply(
        mut self,
        column: &str,
        f: impl Fn(&Series) -> Vec<HashMap<String, String>>,
    ) -> Self {
        let (col, series) = self
            .icolumn(column)
            .unwrap_or_else(|| panic!("Unknown column {}", &column));
        let new_styles = f(series);
        self.applied_styles[col]
            .iter_mut()
            .zip(new_styles)
            .for_each(|(a, b)| a.extend(b));
        self
    }

    pub fn set_table_classes(mut self, classes: Vec<String>) -> Self {
        if self.params.table_classes.is_some() {
            panic!("table_classes can only be set once");
        }
        self.params.table_classes = Some(classes);
        self
    }

    pub fn add_table_classes(mut self, classes: Vec<String>) -> Self {
        let Some(mut table_classes) = self.params.table_classes else {
            return self.set_table_classes(classes);
        };
        table_classes.extend(classes);
        self.params.table_classes = Some(table_classes);
        self
    }

    pub fn set_labels(mut self, labels: Vec<String>) -> Self {
        self.df
            .get_column_names()
            .iter()
            .zip(labels)
            .for_each(|(&col, lab)| {
                self.labels.insert(col.to_string(), lab);
            });
        self
    }

    pub fn relabel_column(mut self, column: &str, label: &str) -> Self {
        self.labels.insert(column.to_string(), label.to_string());
        self
    }

    pub fn relabel(mut self, mapping: &HashMap<String, String>) -> Self {
        mapping.iter().for_each(|(k, v)| {
            self.labels.insert(k.to_owned(), v.to_owned());
        });
        self
    }

    pub fn set_precision(mut self, precision: u32) -> Self {
        if self.params.precision.is_some() {
            panic!("precision can only be set once");
        }
        self.params.precision = Some(precision);
        self
    }

    pub fn background_gradient(
        self,
        column: &str,
        color: &Color,
        vmin: &Option<f64>,
        vmax: &Option<f64>,
    ) -> Self {
        self.apply(column, |s| {
            normalize_series(s, vmin, vmax)
                .iter()
                .map(|v| {
                    let AnyValue::Float64(v) = v else {
                        panic!("values should have been casted to float64")
                    };
                    HashMap::from([("background-color".to_string(), color.to_rgba(v))])
                })
                .collect()
        })
    }

    pub fn background_gradient_expr(self, e: Expr, color: &Color) -> Self {
        let s = evaluate_expr(e, &self.df);
        self.background_gradient_series(&s, color)
    }

    fn background_gradient_series(mut self, s: &Series, color: &Color) -> Self {
        let c = self.get_col_idx(s.name()).unwrap();
        normalize_series(s, &None, &None)
            .iter()
            .map(|v| {
                let AnyValue::Float64(v) = v else {
                    panic!("values should have been casted to float64")
                };
                color.to_rgba(v)
            })
            .enumerate()
            .for_each(|(i, v)| {
                self.applied_styles[c][i].insert("background-color".to_string(), v);
            });
        self
    }

    pub fn render(self) -> String {
        let data = self
            .df
            .iter()
            .map(|row| format_row(row, &self.params))
            .collect();

        let mut cell_styles: HashMap<(usize, usize), HashMap<String, String>> = HashMap::new();
        for (c, vec) in self.applied_styles.iter().enumerate() {
            for (r, map) in vec.iter().enumerate() {
                if map.is_empty() {
                    continue;
                }
                cell_styles.insert((r, c), map.clone());
            }
        }

        let column_labels = self
            .column_names()
            .iter()
            .map(|col| {
                let col = col.to_owned();
                self.labels.get(&col).unwrap_or(&col).to_owned()
            })
            .collect::<Vec<String>>();

        let renderer = Renderer {
            column_labels,
            cell_values: data,
            cell_styles,
            hash: random_hash(),
            classes: self.params.table_classes.unwrap_or_default(),
        };

        renderer.render()
    }

    pub fn column_names(&self) -> Vec<String> {
        self.df
            .get_column_names()
            .iter()
            .map(|v| v.to_string())
            .collect::<Vec<_>>()
    }

    fn icolumn(&self, column: &str) -> Option<(usize, &Series)> {
        let col = self.get_col_idx(column)?;
        Some((col, self.df.column(column).unwrap()))
    }

    fn get_col_idx(&self, column: &str) -> Option<usize> {
        self.df.get_column_names().iter().position(|v| v == &column)
    }
}

fn evaluate_expr(e: Expr, df: &DataFrame) -> Series {
    // LazyF
    df.clone()
        .lazy()
        .select(vec![e])
        .collect()
        .unwrap()
        .get_columns()
        .iter()
        .next()
        .unwrap()
        .clone()
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

fn random_hash() -> String {
    let mut rng = rand::thread_rng();
    let max_val: u32 = 16_u32.pow(6);
    format!("{:x}", rng.gen_range(0..max_val))
}

fn normalize_series(s: &Series, vmin: &Option<f64>, vmax: &Option<f64>) -> Series {
    let mut s = s.cast(&DataType::Float64).unwrap();
    if let Some(vmin) = vmin {
        s = s.clip_min(AnyValue::Float64(*vmin)).unwrap();
    }
    if let Some(vmax) = vmax {
        s = s.clip_max(AnyValue::Float64(*vmax)).unwrap();
    }

    let min: f32 = s.min::<f32>().unwrap();
    s = s - min;

    let range: f32 = s.max::<f32>().unwrap();
    s = s / range;

    s.cast(&DataType::Float64).unwrap()
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
    fn test_set_labels_all() {
        let df = DataFrame::new(vec![Series::new("a", &[0])]).unwrap();
        let styler = df.style().set_labels(vec!["Foo".to_string()]);
        let html = styler.render();
        assert!(html.contains("Foo"));
    }

    #[test]
    fn test_set_labels_map() {
        let df = DataFrame::new(vec![Series::new("a", &[0])]).unwrap();
        let mapping = HashMap::from([("a".to_string(), "Foo".to_string())]);
        let styler = df.style().relabel(&mapping);
        let html = styler.render();
        assert!(html.contains("Foo"));
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

    #[test]
    fn test_background_gradient() {
        let df = DataFrame::new(vec![
            Series::new("a", &[1, 222, 3]),
            Series::new("b", &["fooo", "b", "c"]),
        ])
        .unwrap();

        let styler = df
            .style()
            .background_gradient_expr(col("a").log(2.0), &Color::new(0, 0, 0));
        assert!(styler
            .applied_styles
            .iter()
            .any(|v| { v.iter().any(|hm| !hm.is_empty()) }));
    }

    #[test]
    fn test_normalize_series_float() {
        let s = Series::new("a", &[-1.0, 2.0, 3.0]);
        let s = normalize_series(&s, &None, &None);
        assert_eq!(s, Series::new("a", &[0.0, 0.75, 1.0]));
    }

    #[test]
    fn test_normalize_series_int() {
        let s = Series::new("a", &[-1, 2, 3]);
        let s = normalize_series(&s, &None, &None);
        assert_eq!(s, Series::new("a", &[0.0, 0.75, 1.0]));
    }
}
