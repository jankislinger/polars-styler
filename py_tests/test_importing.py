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


def style(df_self):
    # use this to patch pl.DataFrame.style
    from polars_styler import pydf_to_pystyler

    styler = pydf_to_pystyler(df_self)
    return styler


if __name__ == '__main__':
    unittest.main()
