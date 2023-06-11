use polars::prelude::*;

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
}

#[derive(Default)]
pub struct StylerParams {
    precision: Option<u32>,
}

impl Styler<'_> {
    pub fn new(df: &DataFrame) -> Styler {
        let params = StylerParams::default();
        Styler { df, params }
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
        let table_body = self
            .df
            .iter()
            .map(move |v| render_series(v, self.params.precision))
            .collect::<Vec<_>>()
            .join("");
        let table = format!(
            "<table>
              <thead>{}</thead>
              <tbody>{}</tbody>
            </table>",
            table_head, table_body
        );
        format!("<div>{}{}</div>", style(), table)
    }
}

fn render_series(s: &Series, precision: Option<u32>) -> String {
    let cells = s
        .iter()
        .map(|v| {
            let Some(precision) = precision else {
                return v.to_string();
            };
            match v {
                AnyValue::Float64(f) => format!("{:.1$}", f, precision as usize),
                AnyValue::Float32(f) => format!("{:.1$}", f, precision as usize),
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
        .dataframe > thead > tr > th,
        .dataframe > tbody > tr > td {
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
            Series::new("a", &[1, 2, 3]),
            Series::new("b", &["a", "b", "c"]),
        ])
        .unwrap();

        let styler = df.styler();
        let html = styler.render();
        println!("{}", html);
        assert!(html.contains("<style>"));
        assert!(html.contains("<div>"));
        assert!(html.contains("</div>"));
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
}
