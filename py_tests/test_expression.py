import unittest

import polars as pl
import polars.testing

from polars_styler.expression import (
    format_classes_attr,
    format_all_classes,
    format_styles_attr,
    format_all_styles,
    reduce_with_columns,
)


def test_format_classes_attr():
    df_in = pl.DataFrame({"x::class": [None, [], ["foo"], ["foo bar"]]})
    df_out = df_in.select(format_classes_attr("x"))
    expected = pl.DataFrame({"x::class": ["", "", ' class="foo"', ' class="foo bar"']})
    pl.testing.assert_frame_equal(df_out, expected)


def test_format_classes_attr_multi():
    df_in = pl.DataFrame({"x::class": [None, ["foo"]], "y::class": [[], ["foo bar"]]})
    df_out = df_in.select(*format_all_classes(["x", "y"]))
    expected = pl.DataFrame(
        {
            "x::class": ["", ' class="foo"'],
            "y::class": ["", ' class="foo bar"'],
        }
    )
    pl.testing.assert_frame_equal(df_out, expected)


def test_format_styles_attr():
    x_styles = pl.Series(
        "x::style",
        [None, {}, {"foo": 1}, {"foo": 2, "bar": "baz"}],
        pl.Struct({"foo": pl.Int32, "bar": pl.String}),
    )
    df_in = x_styles.to_frame()
    df_out = df_in.select(format_styles_attr("x"))
    expected = pl.DataFrame(
        {"x::style": ["", "", ' style="foo: 1"', ' style="foo: 2; bar: baz"']}
    )
    pl.testing.assert_frame_equal(df_out, expected)


def test_format_styles_attr_multi():
    struct = pl.Struct({"foo": pl.Int32, "bar": pl.String})
    df_in = pl.DataFrame(
        [
            pl.Series("x::style", [None, {"foo": 1}], struct),
            pl.Series("y::style", [{}, {"foo": 2, "bar": "baz"}], struct),
        ]
    )
    df_out = df_in.select(*format_all_styles(["x", "y"]))
    expected = pl.DataFrame(
        {
            "x::style": ["", ' style="foo: 1"'],
            "y::style": ["", ' style="foo: 2; bar: baz"'],
        }
    )
    pl.testing.assert_frame_equal(df_out, expected)


def test_reduce():
    df = pl.LazyFrame(
        {
            "x_a": [1, 2, 3],
            "x_b": [4, 5, 6],
            "y_a": [7, 8, 9],
            "y_b": [10, 11, 12],
        }
    )
    exprs = [
        pl.selectors.starts_with("x").add(10),
        pl.selectors.ends_with("a").add(100),
    ]
    expected = pl.DataFrame(
        {
            "x_a": [111, 112, 113],
            "x_b": [14, 15, 16],
            "y_a": [107, 108, 109],
            "y_b": [10, 11, 12],
        }
    )

    result = reduce_with_columns(df, exprs).collect()
    pl.testing.assert_frame_equal(result, expected)


if __name__ == "__main__":
    unittest.main()
