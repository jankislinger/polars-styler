import sys
from typing import Dict, Literal, Optional, Callable

import polars as pl

from polars_styler.expression import (
    cast_into_string,
    format_all_classes,
    format_all_styles,
    make_table_cells,
)
from polars_styler.table_attributes import TableAttributes

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class Styler:
    def __init__(self, df: pl.DataFrame):
        """Initialize the HTML Table Builder with a data frame.

        Args:
            df (pl.DataFrame): Polars data frame to convert to an HTML table.

        Returns:
            Styler: A new instance of the Styler class.

        Examples:
            >>> import polars as pl
            >>> from polars_styler.styler import Styler
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> html = Styler(df).to_html()
            >>> assert html.startswith("<table>")
            >>> assert html.endswith("</table>")
        """
        self._df: pl.LazyFrame = apply_defaults(df)
        self._columns: list[str] = df.columns
        self._null_string: str = "null"
        self._table_attributes = TableAttributes(df.columns)
        self._format_exprs: dict[str, pl.Expr] = {}

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

    def set_cell_style(
        self, column: str, condition: pl.Expr, styles: Dict[str, str]
    ) -> Self:
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
        column_name = style_column_name(column, "styles")
        self._df = self._df.with_columns(
            pl.when(condition)
            .then(pl.lit(styles))
            .otherwise(pl.lit({}))
            .alias(column_name)
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
            labels = [labels(col) for col in self._columns]
        elif isinstance(labels, dict):
            labels = [labels.get(col, col) for col in self._columns]
        self._table_attributes.set_column_labels(labels)
        return self

    def set_null_class(self, column: str, class_name: str):
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
        return self.set_cell_class(
            column, class_name, predicate=pl.col(column).is_null()
        )

    def paged(self, page_num: int, rows_per_page: int) -> Self:
        self._table_attributes.set_page_settings(rows_per_page, page_num)
        return self

    def format_bar(
        self,
        column: str,
        color: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ):
        """
        Apply a bar chart effect to a numeric column using linear-gradient backgrounds.

        Args:
            column: Name of the column to format
            color: Color for the filled portion of the bar
            min_val: Minimum value for scaling (defaults to column min)
            max_val: Maximum value for scaling (defaults to column max)

        Returns:
            Self: The current instance for method chaining.

        Examples:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> styler = Styler(df).format_bar("A", "#123455")
            >>> assert 'linear-gradient(90deg, #123455 50.0%, transparent 50.0%)' in styler.to_html()
        """
        background = bar_chart_style(pl.col(column), color, min_val, max_val)
        self._apply_cell_styles(
            column,
            background.alias("background"),
            pl.lit("100% 40%").alias("background-size"),
        )
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
        expr = self._get_format_expr(column).round(decimals)
        self._format_exprs[column] = expr
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
        df = (
            self._df.with_columns(**self._format_exprs)
            .with_columns(
                cast_into_string(self._columns, self._null_string),
                *format_all_classes(self._columns),
                *format_all_styles(self._columns),
            )
            .select(*make_table_cells(self._columns))
            .pipe(self._apply_pages)
            .collect()
        )

        html_table = [self._table_attributes.tag_table()]
        html_table.extend(self._table_attributes.tags_head())

        # Body
        html_table.append("<tbody>")
        for row in df.iter_rows():
            html_table.append("<tr>")
            html_table.extend(row)
            html_table.append("</tr>")
        html_table.append("</tbody>")

        html_table.append("</table>")
        return sep.join(html_table)

    def _get_format_expr(self, column: str) -> pl.Expr:
        return self._format_exprs.get(column, pl.col(column))

    def _apply_cell_styles(self, column: str, *exprs: pl.Expr) -> None:
        column_style = style_column_name(column, "styles")
        style_struct = pl.col(column_style).struct.with_fields(exprs)
        self._df.with_columns(style_struct).collect()
        self._df = self._df.with_columns(style_struct)

    def _apply_cell_classes(self, column: str, expr: pl.Expr) -> None:
        column_classes = style_column_name(column, "classes")
        class_list = pl.col(column_classes).list.set_union(expr)
        self._df = self._df.with_columns(class_list)
        self._df.collect()

    def _apply_pages(self, df: pl.LazyFrame) -> pl.LazyFrame:
        if self._table_attributes.page_settings is None:
            return df
        page_num, rows_per_page = self._table_attributes.page_settings
        offset = page_num * rows_per_page
        length = rows_per_page
        return df.slice(offset, length)


def relative_value(
    value: pl.Expr, min_val: float | None = None, max_val: float | None = None
) -> pl.Expr:
    min_val = value.min() if min_val is None else pl.lit(min_val)
    max_val = value.max() if max_val is None else pl.lit(max_val)
    return (value - min_val) / (max_val - min_val)


def bar_chart_style(
    value: pl.Expr,
    color: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> pl.Expr:
    """
    Generate a Polars expression that computes the background style for a bar chart inside a cell.

    Args:
        value (pl.Expr): Polars expression representing the value.
        color (str): The color for the filled portion of the bar.
        min_val (Optional[float]): Minimum value for scaling (defaults to column min).
        max_val (Optional[float]): Maximum value for scaling (defaults to column max).

    Returns:
        pl.Expr: An expression that evaluates to a CSS background string.
    """
    percentage = relative_value(value, min_val, max_val).mul(100).round(1).cast(pl.Utf8)
    return pl.format(
        "linear-gradient(90deg, {} {}%, transparent {}%) no-repeat center;",
        pl.lit(color),
        percentage,
        percentage,
    )


def apply_defaults(df: pl.DataFrame, /) -> pl.LazyFrame:
    """
    Add default style and class columns to the DataFrame.

    Args:
        df (pl.DataFrame): The input Polars DataFrame.

    Returns:
        pl.LazyFrame: A lazy frame with additional style and class columns.

    Examples:
        >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        >>> lazy_df = apply_defaults(df)
        >>> assert "A__styles" in lazy_df.collect_schema().names()
        >>> assert "B__classes" in lazy_df.collect_schema().names()
    """
    exprs_styles = [pl.lit({}).alias(f"{col}__styles") for col in df.columns]
    exprs_classes = [
        pl.lit([], dtype=pl.List(pl.String)).alias(f"{col}__classes")
        for col in df.columns
    ]
    return df.lazy().with_columns(*exprs_styles, *exprs_classes)


def style_column_name(column: str, suffix: Literal["styles", "classes"]) -> str:
    """Generate the name of an internal styling column."""
    return f"{column}__{suffix}"
