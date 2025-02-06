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

    def test_something(self):
        table = (
            Styler(self.data)
            .set_table_class("ui celled table")
            .set_column_style("x", {"text-align": "center", "color": "blue"})
            .set_cell_class("text", "single line")
            .apply_gradient(
                "x", min_val=0, max_val=15, color_start="#ffffff", color_end="#ff0000"
            )
            .format_bar("y", "#123455")
        )
        self.assertIsInstance(table.to_html(), str)

    def test_overwrite(self):
        html = (
            Styler(self.data)
            .set_column_style("x", {"background-color": "black"})
            .set_column_style("x", {})
            .to_html()
        )
        self.assertIn('background-color: "black"', html)

    def test_gpt(self):
        df = pl.DataFrame(
            {
                "data": [
                    {"a": 1},
                    {},
                    {},
                    {},
                    {"a": 1, "b": 2},
                    # {"a": 3, "b": 4},
                    # {"a": 5, "b": 6}
                ]
            }
        )

        # print(df.select(pl.col("data").struct.unnest()))

        print(df["data"].dtype)

        # Add a constant field to the struct
        df = (
            df.filter(pl.col("data").struct.field("a").is_null()).with_columns(
                pl.col("data").struct.with_fields(pl.lit(42).alias("c"))
            )
            # .select(pl.col("data").struct.unnest())
        )
        print(df)

    def test_highlight_max(self):
        """Test highlighting maximum values in columns."""
        df = pl.DataFrame({"A": [1, 5, 3, 2], "B": [10, 20, 50, 40]})

        html = (
            Styler(df)
            .highlight_max("A", "#ffcccb")
            .highlight_max("B", "#90EE90")
            .to_html()
        )

        self.assertIn('background-color: "#ffcccb"', html)
        self.assertIn('background-color: "#90EE90"', html)


if __name__ == "__main__":
    unittest.main()
