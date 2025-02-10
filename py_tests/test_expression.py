import unittest

import polars as pl
import polars.testing

from polars_styler.expression import (
    format_classes_attr,
    format_all_classes,
    format_styles_attr,
    format_all_styles,
)


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


def test_format_styles_attr():
    x_styles = pl.Series(
        "x__styles",
        [None, {}, {"foo": 1}, {"foo": 2, "bar": "baz"}],
        pl.Struct({"foo": pl.Int32, "bar": pl.String}),
    )
    df_in = x_styles.to_frame()
    df_out = df_in.select(format_styles_attr("x"))
    expected = pl.DataFrame(
        {"x__styles": ["", "", ' style="foo: 1"', ' style="foo: 2; bar: baz"']}
    )
    pl.testing.assert_frame_equal(df_out, expected)


def test_format_styles_attr_multi():
    struct = pl.Struct({"foo": pl.Int32, "bar": pl.String})
    df_in = pl.DataFrame(
        [
            pl.Series("x__styles", [None, {"foo": 1}], struct),
            pl.Series("y__styles", [{}, {"foo": 2, "bar": "baz"}], struct),
        ]
    )
    df_out = df_in.select(*format_all_styles(["x", "y"]))
    expected = pl.DataFrame(
        {
            "x__styles": ["", ' style="foo: 1"'],
            "y__styles": ["", ' style="foo: 2; bar: baz"'],
        }
    )
    pl.testing.assert_frame_equal(df_out, expected)


if __name__ == "__main__":
    unittest.main()
