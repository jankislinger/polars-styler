import html
import sys
from typing import Any, Dict, Literal, Optional

import polars as pl

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class Styler:
    def __init__(self, df: pl.DataFrame | pl.LazyFrame):
        """Initialize the HTML Table Builder with a data frame."""
        self._df: pl.LazyFrame = df.lazy()
        self._columns: list[str] = df.columns
        self._table_class: str | None = None
        self._column_labels: list[str] | None = None
        self._null_string: str = "null"
        self._attr_columns: set[str] = set()
        self._page_settings: tuple[int, int] | None = None

    def set_table_class(self, class_names: str | list[str]) -> Self:
        """Store table-wide CSS class (stored as metadata)."""
        if isinstance(class_names, list):
            class_names = " ".join(class_names)
        self._table_class = class_names
        return self

    def set_column_class(self, column: str, class_names: str | list[str]) -> Self:
        """Assign a CSS class to all cells in a column."""
        if isinstance(class_names, str):
            class_names = class_names.split(" ")
        self._apply_cell_classes(column, pl.lit(class_names))
        return self

    def set_column_style(self, column: str, styles: Dict[str, str]) -> Self:
        """Assign an inline style to all cells in a column."""
        column_name = style_column_name(column, "styles")
        self._df = self._df.with_columns(pl.lit(styles).alias(column_name))
        return self

    def set_cell_class(self, column: str, condition: pl.Expr, class_name: str) -> Self:
        """Apply a CSS class to cells based on a condition."""
        class_expr = pl.when(condition).then(pl.lit([class_name])).otherwise(pl.lit([]))
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

    def relabel_index(self, labels: list[str] | dict[str, str]) -> Self:
        assert len(labels) == len(self._columns)
        if isinstance(labels, dict):
            labels = [labels[col] for col in self._columns]
        self._column_labels = labels
        return self

    def set_null_class(self, column: str, class_name: str):
        return self.set_cell_class(column, pl.col(column).is_null(), class_name)

    def paged(self, page_num: int, rows_per_page: int) -> Self:
        self._page_settings = page_num, rows_per_page
        return self

    def _apply_cell_styles(self, column: str, *exprs: pl.Expr) -> None:
        column_style = style_column_name(column, "styles")
        if column_style in self._attr_columns:
            style_struct = pl.col(column_style).struct.with_fields(exprs)
        else:
            self._attr_columns.add(column_style)
            style_struct = pl.struct(*exprs).alias(column_style)
        self._df = self._df.with_columns(style_struct)

    def _apply_cell_classes(self, column: str, expr: pl.Expr) -> None:
        column_classes = style_column_name(column, "classes")
        if column_classes in self._attr_columns:
            class_list = pl.col(column_classes).list.set_union(expr)
        else:
            self._attr_columns.add(column_classes)
            class_list = expr.fill_null(pl.lit([])).alias(column_classes)
        self._df = self._df.with_columns(class_list)

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

    def set_null(self, value: str) -> Self:
        self._null_string = value
        return self

    def to_html(self) -> str:
        """Convert the lazy frame to an HTML table."""

        df = (
            self._df.with_columns(
                pl.selectors.by_name(self._columns)
                .cast(pl.String)
                .fill_null(self._null_string),
                pl.selectors.ends_with("__classes").list.join(" "),
                pl.selectors.ends_with("__styles").map_elements(styles_struct_to_str),
            )
            .pipe(self._apply_pages)
            .collect()
        )

        table_class_attr = f' class="{self._table_class}"' if self._table_class else ""
        html_table = [f"<table{table_class_attr}>"]

        # Headers
        html_table.extend(["<thead>", "<tr>"])
        for col in self._column_labels or self._columns:
            html_table.append(f"<th>{html.escape(col)}</th>")
        html_table.extend(["</tr>", "</thead>"])

        # Body
        html_table.append("<tbody>")
        for row in df.iter_rows(named=True):
            html_table.append("<tr>")
            for col in self._columns:
                cell_value = row[col]
                class_column = style_column_name(col, "classes")
                style_column = style_column_name(col, "styles")

                class_attr = (
                    f' class="{row[class_column]}"' if class_column in row else ""
                )
                style_attr = (
                    f' style="{row[style_column]}"' if style_column in row else ""
                )

                html_table.append(
                    f"<td{class_attr}{style_attr}>{html.escape(str(cell_value))}</td>"
                )
            html_table.append("</tr>")
        html_table.append("</tbody>")

        html_table.append("</table>")
        return "\n".join(html_table)

    def _apply_pages(self, df: pl.LazyFrame) -> pl.LazyFrame:
        if self._page_settings is None:
            return df
        page_num, rows_per_page = self._page_settings
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


def styles_struct_to_str(x: dict, /) -> str:
    return "; ".join(f"{k}: {v}" for k, v in x.items())


def style_column_name(column: str, suffix: Literal["styles", "classes"]) -> str:
    """Generate the name of an internal styling column."""
    return f"__{column}__{suffix}"


def if_else(predicate: pl.Expr, true: Any, false: Any) -> pl.Expr:
    return (
        pl.when(predicate.is_null())
        .then(pl.lit(None))
        .when(predicate)
        .then(pl.lit(true))
        .otherwise(pl.lit(false))
    )
