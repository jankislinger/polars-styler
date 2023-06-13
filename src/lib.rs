use crate::styler::Styler;
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
