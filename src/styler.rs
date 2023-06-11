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
}

impl Styler<'_> {
    pub fn new(df: &DataFrame) -> Styler {
        Styler { df }
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
            .map(render_series)
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

fn render_series(s: &Series) -> String {
    let cells = s
        .iter()
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
}
