use build_html::{Html, Table, TableRow};
use build_html::{HtmlContainer, TableCell, TableCellType};
use std::collections::HashMap;

struct Renderer {
    column_names: Vec<String>,
    cell_values: Vec<Vec<String>>, // (col, row)
    cell_styles: HashMap<(usize, usize), HashMap<String, String>>,
    hash: String,
}

impl Renderer {
    pub fn render(&self) -> String {
        format!("{}\n{}", self.styles(), self.table().to_html_string())
    }

    fn styles(&self) -> String {
        let foo_styles = self
            .cell_styles
            .iter()
            .map(|((row, col), styles)| {
                format!(
                    "#{} {{{}}}",
                    cell_id(&self.hash, row, col),
                    css_styles(styles)
                )
            })
            .collect::<Vec<_>>()
            .join("\n  ");
        format!("<style>\n  {}\n</style>", foo_styles)
    }

    fn table(&self) -> Table {
        if self.cell_values.is_empty() {
            // It may be possible to set `nrow = 0` and have the table rendered
            panic!("No data to render; there are no columns in the DataFrame.");
        }
        let nrow = self.cell_values[0].len();

        (0..nrow)
            .map(|i| self.row(i))
            .fold(Table::new(), |table, row| table.with_custom_body_row(row))
            .with_header_row(&self.column_names)
            .with_attributes([("class", "dataframe")])
    }

    fn row(&self, row: usize) -> TableRow {
        let ncol = self.cell_values.len();
        (0..ncol)
            .map(|j| self.cell(row, j))
            .fold(TableRow::new(), |row, cell| row.with_cell(cell))
    }

    fn cell(&self, row: usize, col: usize) -> TableCell {
        let cell_id = format!("T_{}_row{}_col{}", &self.hash, row, col);
        let inner = &self.cell_values[col][row];
        TableCell::new(TableCellType::Data)
            .with_attributes([("id".to_string(), cell_id)])
            .with_raw(inner)
    }
}

fn cell_id(hash: &str, row: &usize, col: &usize) -> String {
    format!("T_{}_row{}_col{}", hash, row, col)
}

fn css_styles(styles: &HashMap<String, String>) -> String {
    styles
        .iter()
        .map(|(attr, val)| format!("{}: {}", attr, val))
        .collect::<Vec<_>>()
        .join("; ")
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn test_init() {
        let column_names = vec!["col1".to_string(), "col2".to_string()];
        let cell_values = vec![
            vec!["a".to_string(), "b".to_string()],
            vec!["c".to_string(), "d".to_string()],
        ];
        let mut cell_styles = HashMap::new();
        cell_styles.insert(
            (0, 0),
            HashMap::from([
                ("color".to_string(), "red".to_string()),
                ("background-color".to_string(), "yellow".to_string()),
            ]),
        );
        let hash = "asdf".to_string();
        let renderer = Renderer {
            column_names,
            cell_values,
            cell_styles,
            hash,
        };
        println!("{}", renderer.render());
    }

    #[test]
    fn test_css_styles_generation() {
        let styles = HashMap::from([
            ("color".to_string(), "red".to_string()),
            ("background-color".to_string(), "yellow".to_string()),
        ]);
        let styles_string = css_styles(&styles);
        assert!(styles_string.contains("color: red"));
        assert!(styles_string.contains("background-color: yellow"));
    }
}
