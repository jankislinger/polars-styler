import html
import sys
from typing import Dict, Literal, Optional, Callable

import polars as pl

from polars_styler.expression import (
    cast_into_string,
    format_all_classes,
    format_all_styles,
)
from polars_styler.table_attributes import TableAttributes

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class Styler:
    def __init__(self, df: pl.DataFrame):
        """Initialize the HTML Table Builder with a data frame."""
        self._df: pl.LazyFrame = apply_defaults(df)
        self._columns: list[str] = df.columns
        self._null_string: str = "null"
        self._table_attributes = TableAttributes(df.columns)
        self._format_exprs: dict[str, pl.Expr] = {}

    def set_table_class(self, class_names: str | list[str]) -> Self:
        """Store table-wide CSS class."""
        self._table_attributes.add_table_classes(class_names)
        return self

    def highlight_decrease(self, column: str, color: str) -> Self:
        """Apply background color to cells where value decreases from previous row."""
        expr = pl.col(column)
        condition = expr.shift(1).ge(expr) & expr.shift(1).is_not_null()
        return self.set_cell_style(column, condition, {"background-color": color})

    def highlight_max(self, column: str, color: str = "#FFB3BA") -> Self:
        """Highlight the maximum value in a column with a specified background color.

        Args:
            column: Name of the column to format
            color: Color to highlight the maximum value with (default: yellow)

        Returns:
            Self for method chaining
        """
        condition = pl.col(column) == pl.col(column).max()
        return self.set_cell_style(column, condition, {"background-color": color})

    def set_column_style(self, column: str, styles: Dict[str, str]) -> Self:
        """Assign an inline style to all cells in a column."""
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
        """Apply a CSS class to cells based on a condition."""
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
        """Apply an inline style to cells based on a condition."""
        column_name = style_column_name(column, "styles")
        self._df = self._df.with_columns(
            pl.when(condition)
            .then(pl.lit(styles))
            .otherwise(pl.lit({}))
            .alias(column_name)
        )
        return self

    def apply_cell_styles(self, column: str, *exprs: pl.Expr) -> Self:
        self._apply_cell_styles(column, *exprs)
        return self

    def apply_cell_classes(self, column: str, expr: pl.Expr) -> Self:
        self._apply_cell_classes(column, expr.str.split(" "))
        return self

    def relabel_index(self, labels: list[str] | dict[str, str] | Callable) -> Self:
        if callable(labels):
            labels = [labels(col) for col in self._columns]
        elif isinstance(labels, dict):
            labels = [labels.get(col, col) for col in self._columns]
        self._table_attributes.set_column_labels(labels)
        return self

    def set_null_class(self, column: str, class_name: str):
        return self.set_cell_class(
            column, class_name, predicate=pl.col(column).is_null()
        )

    def paged(self, page_num: int, rows_per_page: int) -> Self:
        self._table_attributes.set_page_settings(rows_per_page, page_num)
        return self

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

    def apply_gradient(
        self,
        column: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        color_start: str = "#ffffff",
        color_end: str = "#ff0000",
    ):
        """Apply a background color gradient to numeric cells in a column."""
        min_val = (
            min_val
            if min_val is not None
            else self._df.select(pl.min(column)).collect().item()
        )
        max_val = (
            max_val
            if max_val is not None
            else self._df.select(pl.max(column)).collect().item()
        )
        range_val = (
            max_val - min_val if max_val != min_val else 1
        )  # Prevent div by zero

        gradient_expr = (pl.col(column) - min_val) / range_val
        background = pl.format(
            "linear-gradient(to right, {} {}%, {});",
            pl.lit(color_start),
            (gradient_expr * 100).cast(pl.Float64),
            pl.lit(color_end),
        )
        self._apply_cell_styles(column, background.alias("background"))
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
        """
        background = bar_chart_style(pl.col(column), color, min_val, max_val)
        self._apply_cell_styles(
            column,
            background.alias("background"),
            pl.lit("100% 40%").alias("background-size"),
        )
        return self

    def set_precision(self, column: str, decimals: int) -> Self:
        expr = self._get_format_expr(column).round(decimals)
        self._format_exprs[column] = expr
        return self

    def _get_format_expr(self, column: str) -> pl.Expr:
        return self._format_exprs.get(column, pl.col(column))

    def set_null(self, value: str) -> Self:
        self._null_string = value
        return self

    def to_html(self) -> str:
        """Convert the lazy frame to an HTML table."""
        df = (
            self._df.with_columns(**self._format_exprs)
            .with_columns(
                cast_into_string(self._columns, self._null_string),
                *format_all_classes(self._columns),
                *format_all_styles(self._columns),
            )
            .pipe(self._apply_pages)
            .collect()
        )

        html_table = [self._table_attributes.tag_table()]
        html_table.extend(self._table_attributes.tags_head())

        # Body
        html_table.append("<tbody>")
        for row in df.iter_rows(named=True):
            html_table.append("<tr>")
            for col in self._columns:
                cell_value = row[col]

                class_column = style_column_name(col, "classes")
                style_column = style_column_name(col, "styles")
                cell_tag = f"<td{row[class_column]}{row[style_column]}>"

                html_table.append(f"{cell_tag}{html.escape(str(cell_value))}</td>")
            html_table.append("</tr>")
        html_table.append("</tbody>")

        html_table.append("</table>")
        return "\n".join(html_table)

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
    exprs_styles = [pl.lit({}).alias(f"{col}__styles") for col in df.columns]
    exprs_classes = [
        pl.lit([], dtype=pl.List(pl.String)).alias(f"{col}__classes")
        for col in df.columns
    ]
    return df.lazy().with_columns(*exprs_styles, *exprs_classes)


def style_column_name(column: str, suffix: Literal["styles", "classes"]) -> str:
    """Generate the name of an internal styling column."""
    return f"{column}__{suffix}"
