import unittest

import polars as pl

from polars_styler.styler import Styler


class MyTestCase(unittest.TestCase):
    def test_something(self):
        data = pl.DataFrame(
            {
                "x": [1, 2, 5, 10],
                "y": [1, 2, 5, 10],
                "single_line": ["aaaa", "adfasd", "dfsdfasdf", "a"],
                "text": ["some long text " * 40] * 4,
            },
        )
        table = (
            Styler(data)
            .set_table_class("ui celled table")
            .set_column_style("x", {"text-align": "center", "color": "blue"})
            .set_column_class("text", "single line")
            .apply_gradient(
                "x", min_val=0, max_val=15, color_start="#ffffff", color_end="#ff0000"
            )
            .format_bar("y", "#123455")
        )
        self.assertIsInstance(table.to_html(), str)


if __name__ == "__main__":
    unittest.main()
