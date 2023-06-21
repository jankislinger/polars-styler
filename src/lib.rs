use crate::styler::{Color, Styler};
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use pyo3_polars::PyDataFrame;

mod renderer;
mod styler;

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

    fn set_precision(&mut self, precision: u32) {
        self.s = self.clone().s.set_precision(precision);
    }

    fn background_gradient(&mut self, column: &str) {
        let red = Color::new(255, 0, 0);
        self.s = self.clone().s.background_gradient(column, &red);
    }

    fn render(&self) -> PyResult<String> {
        let s = self.s.clone();
        Ok(s.render())
    }
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
