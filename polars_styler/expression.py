from typing import TypeVar, overload

import polars as pl

T = TypeVar("T")


def make_table_cells(columns: list[str]) -> list[pl.Expr]:
    """Make table cells.

    Args:
        columns: The column names.

    Returns:

    Examples:
        >>> df = pl.DataFrame({
        ...     "x": [1, 2, 3],
        ...     "x__classes": ["", ' class=\"foo\"',  'class=\"foo bar\"'],
        ...     "x__styles": ["", ' style=\"foo: 2"', 'style="foo: 2; bar: baz"'],
        ...     "y": [4, 5, 6],
        ...     "y__classes": ["", ' class=\"foo\"',  'class=\"foo bar\"'],
        ...     "y__styles": ["", ' style=\"foo: 2"', 'style="foo: 2; bar: baz"'],
        ... })
        >>> df.select(make_table_cells(["x", "y"]))
        shape: (3, 2)
        ┌─────────────────────────────────┬─────────────────────────────────┐
        │ x                               ┆ y                               │
        │ ---                             ┆ ---                             │
        │ str                             ┆ str                             │
        ╞═════════════════════════════════╪═════════════════════════════════╡
        │ <td>1</td>                      ┆ <td>4</td>                      │
        │ <td class="foo" style="foo: 2"… ┆ <td class="foo" style="foo: 2"… │
        │ <tdclass="foo bar"style="foo: … ┆ <tdclass="foo bar"style="foo: … │
        └─────────────────────────────────┴─────────────────────────────────┘
    """
    return [make_table_cell(col) for col in columns]


def make_table_cell(column: str) -> pl.Expr:
    """Make a table cell.

    Args:
        column: The column name.

    Returns:
        The Polars expression.

    Examples:
        >>> df = pl.DataFrame({
        ...     "x": [1, 2, 3],
        ...     "x__classes": ["", ' class=\"foo\"',  'class=\"foo bar\"'],
        ...     "x__styles": ["", ' style=\"foo: 2"', 'style="foo: 2; bar: baz"'],
        ... })
        >>> with pl.Config(fmt_str_lengths=70):
        ...     df.select(make_table_cell("x"))
        shape: (3, 1)
        ┌───────────────────────────────────────────────────┐
        │ x                                                 │
        │ ---                                               │
        │ str                                               │
        ╞═══════════════════════════════════════════════════╡
        │ <td>1</td>                                        │
        │ <td class="foo" style="foo: 2">2</td>             │
        │ <tdclass="foo bar"style="foo: 2; bar: baz">3</td> │
        └───────────────────────────────────────────────────┘
    """
    classes = pl.col(f"{column}__classes")
    style = pl.col(f"{column}__styles")
    return pl.format("<td{}{}>{}</td>", classes, style, pl.col(column)).alias(column)


def format_all_classes(column_names: list[str]) -> list[pl.Expr]:
    """Format the classes attribute for all columns.

    Converts the classes attribute from a list of strings to a string with
    space-separated values.

    Args:
        column_names: The column names.

    Returns:
        A list of Polars expressions that format the classes attribute.

    Examples:
        >>> df = pl.DataFrame({
        ...     "x__classes": [None, ["foo"]],
        ...     "y__classes": [[],  ["bar foo"]],
        ... })
        >>> df.select(format_all_classes(["x", "y"]))
        shape: (2, 2)
        ┌──────────────┬──────────────────┐
        │ x__classes   ┆ y__classes       │
        │ ---          ┆ ---              │
        │ str          ┆ str              │
        ╞══════════════╪══════════════════╡
        │              ┆                  │
        │  class="foo" ┆  class="bar foo" │
        └──────────────┴──────────────────┘
    """
    return [format_classes_attr(col) for col in column_names]


def format_classes_attr(column: str) -> pl.Expr:
    """Format the classes attribute for a column.

    Args:
        column: The column name.

    Returns:
        A Polars expression that formats the classes attribute.

    Examples:
        >>> df = pl.DataFrame({"x__classes": [None, [], ["foo"], ["foo bar"]]})
        >>> df.select(format_classes_attr("x"))
        shape: (4, 1)
        ┌──────────────────┐
        │ x__classes       │
        │ ---              │
        │ str              │
        ╞══════════════════╡
        │                  │
        │                  │
        │  class="foo"     │
        │  class="foo bar" │
        └──────────────────┘
    """
    class_column = f"{column}__classes"
    expr = pl.col(class_column)
    expr = pl.when(expr.list.len() > 0).then(expr).otherwise(None).list.join(" ")
    return pl.format(' class="{}"', expr).fill_null("").alias(class_column)


def format_all_styles(column_names: list[str]) -> list[pl.Expr]:
    """Format the styles attribute for all columns.

    Args:
        column_names: The column names.

    Returns:
        A list of Polars expressions that format the styles attribute.

    Examples:
        >>> struct = pl.Struct({"foo": pl.Int32, "bar": pl.String})
        >>> df = pl.DataFrame([
        ...     pl.Series("x__styles", [None, {"foo": 1}], struct),
        ...     pl.Series("y__styles", [{}, {"foo": 2, "bar": "baz"}], struct),
        ... ])
        >>> df.select(*format_all_styles(["x", "y"]))
        shape: (2, 2)
        ┌─────────────────┬───────────────────────────┐
        │ x__styles       ┆ y__styles                 │
        │ ---             ┆ ---                       │
        │ str             ┆ str                       │
        ╞═════════════════╪═══════════════════════════╡
        │                 ┆                           │
        │  style="foo: 1" ┆  style="foo: 2; bar: baz" │
        └─────────────────┴───────────────────────────┘
    """
    return [format_styles_attr(col) for col in column_names]


def format_styles_attr(column: str) -> pl.Expr:
    """Format the styles attribute for a column.

    Args:
        column: The column name.

    Returns:
        A Polars expression that formats the styles attribute.

    Examples:
        >>> x_styles = pl.Series(
        ...     "x__styles",
        ...     [None, {}, {"foo": 1}, {"foo": 2, "bar": "baz"}],
        ...     pl.Struct({"foo": pl.Int32, "bar": pl.String}),
        ... )
        >>> df = x_styles.to_frame()
        >>> df.select(format_styles_attr("x"))
        shape: (4, 1)
        ┌───────────────────────────┐
        │ x__styles                 │
        │ ---                       │
        │ str                       │
        ╞═══════════════════════════╡
        │                           │
        │                           │
        │  style="foo: 1"           │
        │  style="foo: 2; bar: baz" │
        └───────────────────────────┘
    """
    styles_column = f"{column}__styles"
    styles = pl.col(styles_column).map_elements(
        _styles_struct_to_str, return_dtype=pl.String
    )
    return pl.format(' style="{}"', styles).fill_null("").alias(styles_column)


@overload
def reduce_with_columns(data: pl.LazyFrame, exprs: list[pl.Expr]) -> pl.LazyFrame:
    pass


@overload
def reduce_with_columns(data: pl.DataFrame, exprs: list[pl.Expr]) -> pl.DataFrame:
    pass


def reduce_with_columns(
    data: pl.LazyFrame | pl.DataFrame, exprs: list[pl.Expr]
) -> pl.LazyFrame | pl.DataFrame:
    """Sequentially apply method `with_columns` to a frame.

    Args:
        data: DataFrame or LazyFrame.
        exprs: A list of expressions to apply sequentially.

    Returns:
        A DataFrame or LazyFrame with applied expressions.

    Examples:
        >>> df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        >>> e1 = (pl.col("a") + pl.col("b")).alias("a_plus_b")
        >>> e2 = pl.format("{} + {} = {}", "a", "b", "a_plus_b").alias("formula")
        >>> reduce_with_columns(df, [e1, e2])
        shape: (3, 4)
        ┌─────┬─────┬──────────┬───────────┐
        │ a   ┆ b   ┆ a_plus_b ┆ formula   │
        │ --- ┆ --- ┆ ---      ┆ ---       │
        │ i64 ┆ i64 ┆ i64      ┆ str       │
        ╞═════╪═════╪══════════╪═══════════╡
        │ 1   ┆ 4   ┆ 5        ┆ 1 + 4 = 5 │
        │ 2   ┆ 5   ┆ 7        ┆ 2 + 5 = 7 │
        │ 3   ┆ 6   ┆ 9        ┆ 3 + 6 = 9 │
        └─────┴─────┴──────────┴───────────┘
    """
    if isinstance(data, pl.LazyFrame):
        return _reduce_lazy(data, exprs)
    return _reduce_lazy(data.lazy(), exprs).collect()


def _reduce_lazy(data: pl.LazyFrame, exprs: list[pl.Expr]) -> pl.LazyFrame:
    # same as functools.reduce(lambda d, e: d.with_columns(e), exprs, data)
    for expr in exprs:
        data = data.with_columns(expr)
    return data


def _styles_struct_to_str(mapping: dict, /) -> str | None:
    mapping = {k: v for k, v in mapping.items() if k != "_" and v is not None}
    if not mapping:
        return None
    return "; ".join(f"{k}: {v}" for k, v in mapping.items())


def cast_into_string(columns: list[str], null_value: str) -> pl.Expr:
    return pl.selectors.by_name(columns).cast(pl.String).fill_null(null_value)


def if_else(predicate: pl.Expr, true: T, false: T, null: T | None = None) -> pl.Expr:
    """Return the true value if the predicate is true, otherwise the false value.

    Args:
        predicate: The predicate.
        true: The true value.
        false: The false value.
        null: The null value.

    Returns:
        The Polars expression.

    Examples:
        >>> df = pl.DataFrame({"x": [1, 3, None, 15, 3]})
        >>> df.with_columns(if_else(pl.col("x") > 10, "high", "low", "missing"))
        shape: (5, 2)
        ┌──────┬─────────┐
        │ x    ┆ literal │
        │ ---  ┆ ---     │
        │ i64  ┆ str     │
        ╞══════╪═════════╡
        │ 1    ┆ low     │
        │ 3    ┆ low     │
        │ null ┆ missing │
        │ 15   ┆ high    │
        │ 3    ┆ low     │
        └──────┴─────────┘
    """
    return (
        pl.when(predicate.is_null())
        .then(pl.lit(null))
        .when(predicate)
        .then(pl.lit(true))
        .otherwise(pl.lit(false))
    )
