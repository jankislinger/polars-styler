use crate::colors::{Color, ColorMap};
use crate::styler::Styler;

use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use pyo3_polars::PyDataFrame;

pub mod colors;
pub mod renderer;
pub mod styler;

#[pyclass]
#[derive(Clone)]
struct PyStyler {
    s: Styler,
}

#[pymethods]
impl PyStyler {
    #[new]
    fn new(df: PyDataFrame) -> Self {
        PyStyler {
            s: Styler::new(&df.0),
        }
    }

    fn set_table_classes(&mut self, classes: Vec<String>) {
        self.s = self.clone().s.set_table_classes(classes);
    }

    fn add_table_classes(&mut self, classes: Vec<String>) {
        self.s = self.clone().s.add_table_classes(classes);
    }

    fn set_labels(&mut self, labels: Vec<String>) {
        self.s = self.clone().s.set_labels(labels);
    }

    fn relabel_column(&mut self, column: &str, label: &str) {
        self.s = self.clone().s.relabel_column(column, label);
    }

    // fn relabel(&mut self, mapping: &HashMap<String, String>) {
    //     // TODO: how to convert from PyDict to HashMap?
    //     self.s = self.clone().s.relabel(mapping);
    // }

    fn set_precision(&mut self, precision: u32) {
        self.s = self.clone().s.set_precision(precision);
    }

    fn background_gradient(
        &mut self,
        cmap: Option<PyColorMap>,
        subset: Option<Vec<String>>,
        vmin: Option<f64>,
        vmax: Option<f64>,
        text_color_threshold: Option<f32>,
    ) {
        let _cmap: ColorMap = match cmap {
            Some(cmap) => cmap.cmap,
            None => ColorMap::red_scale(),
        };
        let _text_color_threshold = text_color_threshold.unwrap_or(0.408);
        let red = Color::new(255, 0, 0);
        let subset = subset.unwrap_or_else(|| self.s.column_names());

        self.s = subset.iter().fold(self.clone().s, |s, column| {
            s.background_gradient(column, &red, &vmin, &vmax)
        });
    }

    fn render(&self) -> PyResult<String> {
        let s = self.s.clone();
        Ok(s.render())
    }
}

#[pyclass]
#[derive(Clone)]
struct PyColorMap {
    cmap: ColorMap,
}

#[pyfunction]
fn pydf_to_pystyler(df: PyDataFrame) -> PyResult<PyStyler> {
    let s = Styler::new(&df.0);
    Ok(PyStyler { s })
}

#[pymodule]
fn polars_styler(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyStyler>()?;
    m.add_function(wrap_pyfunction!(pydf_to_pystyler, m)?)?;
    Ok(())
}
