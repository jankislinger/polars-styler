import math
import unittest
import polars as pl

from polars_styler.styler import Styler


class TestRendering(unittest.TestCase):
    def test_patching_dataframe(self):
        html = style(self.df).render()
        self.assertIsInstance(html, str)

    def test_rendering(self):
        html = style(self.df).set_precision(2).render()
        self.assertIn("3.14", html)
        self.assertNotIn("3.141", html)

    def test_background_gradient(self):
        html = style(self.df).background_gradient(subset=["b"]).render()
        self.assertIn("background-color", html)

    @property
    def df(self):
        return pl.DataFrame({
            'a': [1, 2, 3],
            'b': [math.pi, 1 / 5, math.sqrt(2)],
        })


def style(df: pl.DataFrame) -> Styler:
    # use this to patch pl.DataFrame.style
    from polars_styler.polars_styler import pydf_to_pystyler

    py_styler = pydf_to_pystyler(df)
    return Styler(py_styler)


if __name__ == '__main__':
    unittest.main()
