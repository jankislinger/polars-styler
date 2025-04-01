import sys
from typing import Callable, Dict, Literal

import polars as pl

from polars_styler.expression import (
    cast_into_string,
    format_all_classes,
    format_all_styles,
    make_table_cells,
    make_table_row,
    reduce_with_columns,
)
from polars_styler.table_attributes import TableAttributes

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class Styler:
    def __init__(self, data: pl.DataFrame, /) -> None:
        """Initialize the HTML Table Builder with a data frame.

        Args:
            data (pl.DataFrame): Polars data frame to convert to an HTML table.

        Returns:
            Styler: A new instance of the Styler class.

        Examples:
            >>> from polars_styler.styler import Styler
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> html = Styler(df).to_html()
            >>> assert html.startswith("<table>")
            >>> assert html.endswith("</table>")
        """
        self._df: pl.LazyFrame = apply_defaults(data)
        self._columns: list[str] = data.columns
        self._null_string: str = "null"
        self._table_attributes = TableAttributes(data.columns)
        self._format_exprs: list[pl.Expr] = []

    def set_table_class(self, class_names: str | list[str]) -> Self:
        """Store table-wide CSS class.

        Args:
            class_names (str | list[str]): CSS class name(s) to apply to the table.

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> styler = Styler(df).set_table_class("ui celled table")
            >>> assert '<table class="ui celled table">' in styler.to_html()
        """
        self._table_attributes.add_table_classes(class_names)
        return self

    def set_thead_class(self, class_names: str | list[str]) -> Self:
        """Store table-wide CSS class.

        Args:
            class_names (str | list[str]): CSS class name(s) to apply to the table header.

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> styler = Styler(df).set_thead_class("uppercase")
            >>> assert '<thead class="uppercase">' in styler.to_html()
        """
        self._table_attributes.add_thead_classes(class_names)
        return self

    def highlight_decrease(self, column: str, color: str) -> Self:
        """Apply background color to cells where value decreases from previous row.

        Args:
            column: Name of the column to format
            color: Color to highlight the decreasing value with

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 3, 2], "B": [4, 6, 5]})
            >>> styler = Styler(df).highlight_decrease("A", "#FFB3BA")
            >>> assert '<td style="background-color: #FFB3BA">2</td>' in styler.to_html()
        """
        expr = pl.col(column)
        condition = expr.shift(1).ge(expr) & expr.shift(1).is_not_null()
        return self.set_cell_style(column, condition, {"background-color": color})

    def highlight_max(self, column: str, color: str = "#FFB3BA") -> Self:
        """Highlight the maximum value in a column with a specified background color.

        Args:
            column: Name of the column to format
            color: Color to highlight the maximum value with (default: yellow)

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 5, 3, 2], "B": [10, 20, 50, 40]})
            >>> styler = Styler(df).highlight_max("A", "#ffcccb")
            >>> assert '<td style="background-color: #ffcccb">5</td>' in styler.to_html()
        """
        condition = pl.col(column) == pl.col(column).max()
        return self.set_cell_style(column, condition, {"background-color": color})

    def set_column_style(self, column: str, styles: Dict[str, str]) -> Self:
        """Assign an inline style to all cells in a column.

        Args:
            column: Name of the column to format
            styles: Dictionary of CSS properties and values

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> styler = Styler(df).set_column_style("A", {"color": "red"})
            >>> assert '<td style="color: red">1</td>' in styler.to_html()
        """
        exprs = [pl.repeat(value, pl.len()).alias(key) for key, value in styles.items()]
        self._apply_cell_styles(column, *exprs)
        return self

    def set_row_class(
        self,
        class_names: str | list[str],
        *,
        predicate: pl.Expr | None = None,
    ) -> Self:
        """Apply a CSS class to each table row tag.

        Args:
            class_names: CSS class name(s) to apply to the cell
            predicate: Condition to apply the class (default: None)

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> styler = Styler(df).set_row_class("border")
            >>> assert '<tr class="border">' in styler.to_html()
        """
        if isinstance(class_names, str):
            class_names = class_names.split(" ")
        class_expr = pl.lit(class_names)
        if predicate is not None:
            class_expr = pl.when(predicate).then(class_expr).otherwise(pl.lit([]))
        self._apply_cell_classes("tag::tr", class_expr)
        return self

    def set_cell_class(
        self,
        column: str,
        class_names: str | list[str],
        *,
        predicate: pl.Expr | None = None,
    ) -> Self:
        """Apply a CSS class to cells based on a condition.

        Args:
            column: Name of the column to format
            class_names: CSS class name(s) to apply to the cell
            predicate: Condition to apply the class (default: None)

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> styler = Styler(df).set_cell_class("A", "highlight", predicate=pl.col("A") > 2)
            >>> assert '<td class="highlight">3</td>' in styler.to_html()
        """
        if isinstance(class_names, str):
            class_names = class_names.split(" ")
        class_expr = pl.lit(class_names)
        if predicate is not None:
            class_expr = pl.when(predicate).then(class_expr).otherwise(pl.lit([]))
        self._apply_cell_classes(column, class_expr)
        return self

    def set_cell_style(self, column: str, condition: pl.Expr, styles: Dict[str, str]) -> Self:
        """Apply an inline style to cells based on a condition.

        Args:
            column: Name of the column to format
            condition: Condition to apply the style
            styles: Dictionary of CSS properties and values

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> styler = Styler(df).set_cell_style("A", pl.col("A") > 2, {"color": "red"})
            >>> assert '<td style="color: red">3</td>' in styler.to_html()
        """
        column_name = style_column_name(column, "style")
        self._df = self._df.with_columns(
            pl.when(condition).then(pl.lit(styles)).otherwise(pl.lit({})).alias(column_name)
        )
        return self

    def apply_cell_styles(self, column: str, *exprs: pl.Expr) -> Self:
        """Apply multiple inline styles to cells in a column.

        Args:
            column: Name of the column to format
            *exprs: List of expressions to apply to the column cells

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> styler = Styler(df).apply_cell_styles("A", pl.col("B").alias("font-size"))
            >>> assert '<td style="font-size: 4">1</td>' in styler.to_html()
        """
        self._apply_cell_styles(column, *exprs)
        return self

    def apply_cell_classes(self, column: str, expr: pl.Expr) -> Self:
        """Apply multiple CSS classes to cells in a column.

        Args:
            column: Name of the column to format
            expr: Expression that evaluates to a list of CSS classes

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> styler = Styler(df).apply_cell_classes("A", pl.lit("highlight"))
            >>> assert '<td class="highlight">1</td>' in styler.to_html()
        """
        self._apply_cell_classes(column, expr.str.split(" "))
        return self

    def relabel_index(self, labels: list[str] | dict[str, str] | Callable) -> Self:
        """Set custom labels for the index column.

        Args:
            labels: List of custom labels or a callable function to generate them

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> styler = Styler(df).relabel_index(["Column A", "Column B"])
            >>> assert '<th>Column A</th>' in styler.to_html()
        """
        if callable(labels):
            labels = {col: labels(col) for col in self._columns}
        elif isinstance(labels, list):
            assert len(labels) == len(self._columns)
            labels = dict(zip(self._columns, labels, strict=False))
        self._table_attributes.set_column_labels(labels)
        return self

    def set_null_class(self, column: str, class_name: str) -> Self:
        """Apply a CSS class to cells with null values in a column.

        Args:
            column: Name of the column to format
            class_name: CSS class name to apply to null cells

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, None, 3], "B": [4, 5, 6]})
            >>> styler = Styler(df).set_null_class("A", "missing")
            >>> assert '<td class="missing">null</td>' in styler.to_html()
        """
        return self.set_cell_class(column, class_name, predicate=pl.col(column).is_null())

    def format_bar(
        self,
        columns: str | list[str],
        color: str,
        *,
        min_val: float | str = 0.0,
        max_val: float | str = "max",
        width: int | str = 95,
        height: int | str = 45,
        align_right: bool = False,
        position: Literal["center", "left", "right"] = "center",
    ) -> Self:
        """
        Apply a bar chart effect to a numeric column using linear-gradient backgrounds.

        Args:
            columns: Names of the columns to format
            color: Color for the filled portion of the bar
            min_val: Minimum value for scaling or aggregation function (defaults to 0)
            max_val: Maximum value for scaling or aggregation function (defaults to column max)
            width: Width of the bar chart background (int signifies percent, default: 95)
            height: Height of the bar chart background (int signifies percent, default: 45)
            align_right: Align the bar chart to the right side of the cell (default: False)
            position: Horizontal alignment of the bar chart (default: "center")

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 4], "B": [4, 5, 6]})
            >>> styler = Styler(df).format_bar("A", "#123455", height=20, width="100px")
            >>> expected = 'linear-gradient(to right, #123455 50.0%, transparent 50.0%)'
            >>> assert expected in styler.to_html()
            >>> assert 'background-size: 100px 20%' in styler.to_html()
            >>> styler = Styler(df).format_bar(["A", "B"], "#FFFFFF", max_val=10)
            >>> expected = 'linear-gradient(to right, #FFFFFF 60.0%, transparent 60.0%)'
            >>> assert expected in styler.to_html()
        """
        if isinstance(columns, str):
            columns = [columns]

        if isinstance(width, int):
            width = f"{width}%"
        if isinstance(height, int):
            height = f"{height}%"

        bg_properties = {
            "background-position": pl.lit(position),
            "background-repeat": pl.lit("no-repeat"),
            "background-size": pl.lit(f"{width} {height}"),
        }

        for column in columns:
            fraction = relative_value(pl.col(column), min_val, max_val)
            bg_image = bar_chart_style(fraction, color, align_right=align_right).alias(
                "background-image"
            )
            self._apply_cell_styles(column, bg_image, **bg_properties)
        return self

    def set_precision(self, column: str, decimals: int) -> Self:
        """Set the number of decimal places to display in a numeric column.

        Args:
            column: Name of the column to format
            decimals: Number of decimal places to display

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1.2345, 2.3456, 3.4567]})
            >>> styler = Styler(df).set_precision("A", 2)
            >>> assert '<td>1.23</td>' in styler.to_html()
        """
        expr = pl.col(column).round(decimals)
        self._format_exprs.append(expr)
        return self

    def format(self, columns: str | list[str], fmt: str) -> Self:
        """Apply a custom format string to a column.

        Args:
            columns: Names of the columns to format
            fmt: Format string to apply

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1234, 1222333], "B": [1/3, 1/7], "C": [1.2345, 2.3456]})
            >>> styler = Styler(df).format("A", "{:,d}")
            >>> assert '<td>1,222,333</td>' in styler.to_html()
            >>> styler = Styler(df).format(["B", "C"], "{:.2f}")
            >>> assert '<td>0.33</td>' in styler.to_html()
            >>> assert '<td>1.23</td>' in styler.to_html()
        """
        expr = pl.col(columns).map_elements(fmt.format, return_dtype=pl.String)
        self._format_exprs.append(expr)
        return self

    def create_hyperlink(
        self, column: str, url: str | pl.Expr, *, url_format: str | None = None
    ) -> Self:
        """Create a hyperlink from a column value.

        Args:
            column: Name of the column to format
            url: Polars expression or column name that contains (a part of) the URL
            url_format: Format string to apply to the URL (default: None)

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": ["foo", "bar", "baz"], "B": ["com", "org", "gov"]})
            >>> styler = Styler(df).create_hyperlink("A", "B", url_format="https://example.{}")
            >>> assert '<a href="https://example.com">foo</a>' in styler.to_html()
        """
        if url_format is not None:
            url = pl.format(url_format, url)
        elif isinstance(url, str):
            url = pl.col(url)
        expr = pl.format('<a href="{}">{}</a>', url, pl.col(column)).alias(column)
        self._format_exprs.append(expr)
        return self

    def set_null(self, value: str) -> Self:
        """Set the string to display for null values.

        Args:
            value: String to display for null values

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, None, 3]})
            >>> styler = Styler(df).set_null("N/A")
            >>> assert '<td>N/A</td>' in styler.to_html()
        """
        self._null_string = value
        return self

    def skip_columns(self, columns: str | list[str]) -> Self:
        """Skip a column from the output table.

        Args:
            columns: Names of the columns to skip

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> styler = Styler(df).skip_columns("A")
            >>> assert '<th>A</th>' not in styler.to_html()
            >>> assert '<th>B</th>' in styler.to_html()
            >>> styler = Styler(df).skip_columns(["A", "B"])
            >>> assert '<th>' not in styler.to_html()
            >>> assert '<td>' not in styler.to_html()
        """
        if isinstance(columns, str):
            columns = [columns]
        for column in columns:
            self._columns.remove(column)
        return self

    def to_html(self, *, sep: str = "\n") -> str:
        """Convert the lazy frame to an HTML table.

        Args:
            sep: Separator to join the HTML elements with (default: newline)

        Returns:
            str: HTML string representing the table

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> html = Styler(df).to_html()
            >>> assert html.startswith("<table>")
            >>> assert html.endswith("</table>")
        """
        table = (
            self._df.pipe(reduce_with_columns, self._format_exprs)
            .with_columns(
                cast_into_string(self._columns, self._null_string),
                *format_all_classes(["tag::tr"] + self._columns),
                *format_all_styles(["tag::tr"] + self._columns),
            )
            .select(make_table_row(), *make_table_cells(self._columns))
            .collect()
        )

        html_table = [self._table_attributes.tag_table()]
        html_table.extend(self._table_attributes.tags_head(self._columns))

        html_table.append("<tbody>")
        for row in table.iter_rows():
            html_table.extend(row)
            html_table.append("</tr>")
        html_table.append("</tbody>")

        html_table.append("</table>")
        return sep.join(html_table)

    def _repr_html_(self) -> str:
        return self.to_html(sep="")

    def print_html(self) -> Self:
        """Print the HTML table to the console.

        Returns:
            Self: The current instance for method chaining.
        """
        print(self.to_html(sep="\n"))
        return self

    def _apply_cell_styles(self, column: str, *exprs: pl.Expr, **named_exprs: pl.Expr) -> None:
        column_style = style_column_name(column, "style")
        style_struct = pl.col(column_style).struct.with_fields(*exprs, **named_exprs)
        self._df.with_columns(style_struct).collect()
        self._df = self._df.with_columns(style_struct)

    def _apply_cell_classes(self, column: str, expr: pl.Expr) -> None:
        column_classes = style_column_name(column, "class")
        class_list = pl.col(column_classes).list.set_union(expr)
        self._df = self._df.with_columns(class_list)
        self._df.collect()


def relative_value(value: pl.Expr, min_val: float | str, max_val: float | str) -> pl.Expr:
    """Generate a Polars expression that computes the relative value of a column.

    Args:
        value: Polars expression representing the value.
        min_val: Minimum value or aggregation function for scaling.
        max_val: Maximum value or aggregation function for scaling.

    Returns:
        pl.Expr: An expression that evaluates to the relative value.

    Examples:
        >>> df = pl.DataFrame({"x": [1, 3, 4]})
        >>> df.with_columns(rel=relative_value(pl.col("x"), 0, 5))
        shape: (3, 2)
        ┌─────┬─────┐
        │ x   ┆ rel │
        │ --- ┆ --- │
        │ i64 ┆ f64 │
        ╞═════╪═════╡
        │ 1   ┆ 0.2 │
        │ 3   ┆ 0.6 │
        │ 4   ┆ 0.8 │
        └─────┴─────┘
        >>> df.with_columns(rel=relative_value(pl.col("x"), "min", "max"))
        shape: (3, 2)
        ┌─────┬──────────┐
        │ x   ┆ rel      │
        │ --- ┆ ---      │
        │ i64 ┆ f64      │
        ╞═════╪══════════╡
        │ 1   ┆ 0.0      │
        │ 3   ┆ 0.666667 │
        │ 4   ┆ 1.0      │
        └─────┴──────────┘
        >>> df.with_columns(rel=relative_value(pl.col("x"), 0, "sum"))
        shape: (3, 2)
        ┌─────┬───────┐
        │ x   ┆ rel   │
        │ --- ┆ ---   │
        │ i64 ┆ f64   │
        ╞═════╪═══════╡
        │ 1   ┆ 0.125 │
        │ 3   ┆ 0.375 │
        │ 4   ┆ 0.5   │
        └─────┴───────┘
    """
    min_val_ft = getattr(value, min_val)() if isinstance(min_val, str) else min_val
    max_val_ft = getattr(value, max_val)() if isinstance(max_val, str) else max_val
    return (value - min_val_ft) / (max_val_ft - min_val_ft)


def bar_chart_style(fraction: pl.Expr, color: str, *, align_right: bool = False) -> pl.Expr:
    """
    Generate a Polars expression that computes the background style for a bar chart inside a cell.

    Args:
        fraction (pl.Expr): Polars expression representing the value.
        color (str): The color for the filled portion of the bar.
        align_right (bool): Align the bar chart to the right side of the cell (default: False).

    Returns:
        pl.Expr: An expression that evaluates to a CSS background string.

    Examples:
        >>> df = pl.DataFrame({"x": [0.1, -0.1, 0.5, 1.3]})
        >>> with pl.Config(fmt_str_lengths=70):
        ...     df.with_columns(style=bar_chart_style(pl.col("x"), "#123455"))
        shape: (4, 2)
        ┌──────┬───────────────────────────────────────────────────────────────┐
        │ x    ┆ style                                                         │
        │ ---  ┆ ---                                                           │
        │ f64  ┆ str                                                           │
        ╞══════╪═══════════════════════════════════════════════════════════════╡
        │ 0.1  ┆ linear-gradient(to right, #123455 10.0%, transparent 10.0%)   │
        │ -0.1 ┆ linear-gradient(to right, #123455 0.0%, transparent 0.0%)     │
        │ 0.5  ┆ linear-gradient(to right, #123455 50.0%, transparent 50.0%)   │
        │ 1.3  ┆ linear-gradient(to right, #123455 100.0%, transparent 100.0%) │
        └──────┴───────────────────────────────────────────────────────────────┘
    """
    side = "to left" if align_right else "to right"
    percentage = fraction.clip(0, 1).mul(100).round(1).cast(pl.Utf8)
    f_string = f"linear-gradient({side}, {color} {{}}%, transparent {{}}%)"
    return pl.format(f_string, percentage, percentage)


def apply_defaults(data: pl.DataFrame, /) -> pl.LazyFrame:
    """
    Add default style and class columns to the DataFrame.

    Args:
        data (pl.DataFrame): The input Polars DataFrame.

    Returns:
        pl.LazyFrame: A lazy frame with additional style and class columns.

    Examples:
        >>> df = pl.DataFrame({"A": [1, 2, 3]})
        >>> apply_defaults(df).collect()
        shape: (3, 5)
        ┌─────┬────────────────┬───────────┬────────────────┬───────────┐
        │ A   ┆ tag::tr::style ┆ A::style  ┆ tag::tr::class ┆ A::class  │
        │ --- ┆ ---            ┆ ---       ┆ ---            ┆ ---       │
        │ i64 ┆ struct[0]      ┆ struct[0] ┆ list[str]      ┆ list[str] │
        ╞═════╪════════════════╪═══════════╪════════════════╪═══════════╡
        │ 1   ┆ {}             ┆ {}        ┆ []             ┆ []        │
        │ 2   ┆ {}             ┆ {}        ┆ []             ┆ []        │
        │ 3   ┆ {}             ┆ {}        ┆ []             ┆ []        │
        └─────┴────────────────┴───────────┴────────────────┴───────────┘
    """
    columns = ["tag::tr"] + data.columns
    exprs_styles = [pl.lit({}).alias(f"{col}::style") for col in columns]
    exprs_classes = [pl.lit([], dtype=pl.List(pl.String)).alias(f"{col}::class") for col in columns]
    return data.lazy().with_columns(*exprs_styles, *exprs_classes)


def style_column_name(column: str, suffix: Literal["style", "class"]) -> str:
    """Generate the name of an internal styling column."""
    return f"{column}::{suffix}"
