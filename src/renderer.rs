use std::collections::HashMap;

struct Renderer {
    column_names: Vec<String>,
    cell_values: Vec<Vec<String>>, // (col, row)
    cell_styles: HashMap<(usize, usize), String>,
    hash: String,
}

impl Renderer {
    pub fn render(&self) -> String {
        format!("{}\n{}", self.styles(), self.table())
    }

    fn styles(&self) -> String {
        let mut styles = vec![];
        for ((col, row), style) in &self.cell_styles {
            let cell_id = format!("T_{}_row{}_col{}", &self.hash, row, col);
            styles.push(format!("#{} {{ \n  {}\n}}", cell_id, style));
        }
        format!("<style>\n{}\n</style>", styles.join("\n"))
    }

    fn table(&self) -> String {
        let table_head = self.table_head();
        let table_body = self.table_body();
        format!(
            r#"<table class="dataframe">
              {table_head}
              {table_body}
            </table>"#
        )
    }

    fn table_head(&self) -> String {
        let table_head = self
            .column_names
            .iter()
            .map(|v| format!("      <th>{}</th>", v))
            .collect::<Vec<_>>()
            .join("\n");
        format!("<thead>\n{}\n</thead>", table_head)
    }

    fn table_body(&self) -> String {
        let ncol = self.cell_values.len();
        if ncol == 0 {
            panic!("No data to render");
        }
        let nrow = self.cell_values[0].len();

        let table_body = (0..nrow)
            .into_iter()
            .map(|i| {
                let row_html = (0..ncol)
                    .into_iter()
                    .map(|j| {
                        let cell_id = format!("T_{}_row{}_col{}", &self.hash, i, j);
                        let inner = &self.cell_values[j][i];
                        format!("      <td id={}>{}</td>", cell_id, inner)
                    })
                    .collect::<Vec<_>>()
                    .join("\n");
                format!("    <tr>\n{}\n  </tr>", row_html)
            })
            .collect::<Vec<_>>()
            .join("\n");

        format!("<tbody>\n{}\n</tbody>", table_body)
    }
}

#[cfg(test)]
mod test {
    use super::*;
    use polars::prelude::ArrowDataType::Struct;

    #[test]
    fn test_init() {
        let column_names = vec!["col1".to_string(), "col2".to_string()];
        let cell_values = vec![
            vec!["a".to_string(), "b".to_string()],
            vec!["c".to_string(), "d".to_string()],
        ];
        let mut cell_styles = HashMap::new();
        cell_styles.insert((0, 0), "color: red".to_string());
        let hash = "asdf".to_string();
        let renderer = Renderer {
            column_names,
            cell_values,
            cell_styles,
            hash,
        };
        println!("{}", renderer.render());
    }
}
