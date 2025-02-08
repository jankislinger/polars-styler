import unittest

import polars as pl
import polars.testing

from polars_styler.expression import format_classes_attr, format_all_classes


def test_format_classes_attr():
    df_in = pl.DataFrame({"x__classes": [None, [], ["foo"], ["foo bar"]]})
    df_out = df_in.select(format_classes_attr("x"))
    expected = pl.DataFrame(
        {"x__classes": ["", "", ' class="foo"', ' class="foo bar"']}
    )
    pl.testing.assert_frame_equal(df_out, expected)


def test_format_classes_attr_multi():
    df_in = pl.DataFrame(
        {"x__classes": [None, ["foo"]], "y__classes": [[], ["foo bar"]]}
    )
    df_out = df_in.select(*format_all_classes(["x", "y"]))
    expected = pl.DataFrame(
        {
            "x__classes": ["", ' class="foo"'],
            "y__classes": ["", ' class="foo bar"'],
        }
    )
    pl.testing.assert_frame_equal(df_out, expected)


if __name__ == "__main__":
    unittest.main()
