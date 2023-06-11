use polars::frame::row::Row;
use polars::prelude::*;
use std::collections::HashMap;

pub trait StylerExt {
    fn styler(&self) -> Styler;
}

impl StylerExt for DataFrame {
    fn styler(&self) -> Styler {
        Styler::new(self)
    }
}

pub struct Styler<'a> {
    df: &'a DataFrame,
    params: StylerParams,
    applied_styles: Vec<Vec<HashMap<String, String>>>, // (col, row) => (attribute => value)
}

#[derive(Default)]
pub struct StylerParams {
    precision: Option<u32>,
}

impl Styler<'_> {
    pub fn new(df: &DataFrame) -> Styler {
        Styler {
            df,
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

    pub fn precision(mut self, precision: u32) -> Self {
        if self.params.precision.is_some() {
            panic!("precision can only be set once");
        }
        self.params.precision = Some(precision);
        self
    }

    pub fn render(&self) -> String {
        let table_head = self
            .df
            .get_column_names()
            .iter()
            .map(|v| format!("<th>{}</th>", v))
            .collect::<Vec<_>>()
            .join("");

        let nrows = self.df.height();
        let mut table_body = "".to_string();
        for i in 0..nrows {
            let row = self.df.get_row(i).unwrap();
            let row_html = render_row(&row, &self.params.precision);
            table_body.push_str(&row_html);
        }
        let table = format!(
            r#"<table class="dataframe">
              <thead>{}</thead>
              <tbody>{}</tbody>
            </table>"#,
            table_head, table_body
        );
        format!("<div>{}{}</div>", style(), table)
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

fn render_row(row: &Row, precision: &Option<u32>) -> String {
    let cells = row
        .0
        .iter()
        .map(|v| {
            let Some(precision) = precision else {
                return v.to_string();
            };
            match v {
                AnyValue::Float64(f) => format!("{:.1$}", f, *precision as usize),
                AnyValue::Float32(f) => format!("{:.1$}", f, *precision as usize),
                _ => v.to_string(),
            }
        })
        .map(|v| format!("<td>{}</td>", v))
        .collect::<Vec<_>>()
        .join("");
    format!("<tr>{}</tr>", cells)
}

fn style() -> &'static str {
    "<style>
        .dataframe {
          border-collapse: collapse;
        }
        .dataframe > thead > tr > th, .dataframe > tbody > tr > td {
          border: 1px solid black;
          text-align: right;
        }
    </style>"
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

        let styler = df.styler();
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

        let styler = df.styler().precision(2);
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

        let styler = df.styler().apply("a", |s| {
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
