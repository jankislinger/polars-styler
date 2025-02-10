import unittest

import polars as pl

from polars_styler.styler import Styler


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.data = pl.DataFrame(
            {
                "x": [1, 2, 5, 10],
                "y": [1, 2, 5, 10],
                "single_line": ["aaaa", "adfasd", "dfsdfasdf", "a"],
                "text": ["some long text " * 40] * 4,
            },
        )

    def test_default(self):
        html = Styler(self.data).to_html()
        self.assertIsInstance(html, str)

    def test_simple(self):
        table = (
            Styler(self.data)
            .set_table_class("ui celled table")
            .set_column_style("x", {"text-align": "center", "color": "blue"})
            .set_cell_class("text", "single line")
            .format_bar("y", "#123455")
        )
        html = table.to_html()
        self.assertIsInstance(html, str)
        self.assertNotIn('class=""', html)

    def test_overwrite(self):
        html = (
            Styler(self.data)
            .set_column_style("x", {"background-color": "black"})
            .set_column_style("x", {})
            .to_html()
        )
        self.assertIn("background-color: black", html)

    def test_highlight_max(self):
        """Test highlighting maximum values in columns."""
        df = pl.DataFrame({"A": [1, 5, 3, 2], "B": [10, 20, 50, 40]})

        html = (
            Styler(df)
            .highlight_max("A", "#ffcccb")
            .highlight_max("B", "#90EE90")
            .to_html()
        )

        self.assertIn("background-color: #ffcccb", html)
        self.assertIn("background-color: #90EE90", html)

    def test_precision(self):
        df = pl.DataFrame({"x": [1 / 2, 1 / 3]})
        html = Styler(df).set_precision("x", 3).to_html()
        self.assertIn("0.5", html)
        self.assertIn("0.333", html)
        self.assertNotIn("0.50", html)
        self.assertNotIn("0.3333", html)


if __name__ == "__main__":
    unittest.main()
