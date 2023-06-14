import math
import unittest
import polars as pl


class MyTestCase(unittest.TestCase):
    def test_something(self):
        import polars_styler  # noqa: F401

    def test_importing_pystyler(self):
        from polars_styler import PyStyler  # noqa: F401

    def test_pydf_to_pystyler(self):
        from polars_styler import pydf_to_pystyler

        df = pl.DataFrame({
            'a': [1, 2, 3],
            'b': [4, 5, 6],
        })
        styler = pydf_to_pystyler(df)
        print(styler.render())
        self.assertIsInstance(styler.render(), str)

    def test_patching_dataframe(self):
        pl.DataFrame.style = style
        df = pl.DataFrame({
            'a': [1, 2, 3],
            'b': [4, 5, 6],
        })
        html = df.style().render()
        print(html)
        self.assertIsInstance(html, str)

    def test_rendering(self):
        pl.DataFrame.style = style
        df = pl.DataFrame({
            'a': [1, 2, 3],
            'b': [math.pi, 1/5, math.sqrt(2)],
        })
        html = df.style().set_precision(2).render()
        print(html)
        self.assertIn("3.14", html)
        self.assertNotIn("3.141", html)


class Styler:

    def __init__(self, py_styler):
        self.py_styler = py_styler

    def set_precision(self, precision):
        self.py_styler.set_precision(precision)
        return self

    def _repr_html_(self):
        return self.py_styler.render()

    def render(self):
        return self.py_styler.render()


def style(df_self):
    # use this to patch pl.DataFrame.style
    from polars_styler import pydf_to_pystyler

    py_styler = pydf_to_pystyler(df_self)
    return Styler(py_styler)


if __name__ == '__main__':
    unittest.main()
