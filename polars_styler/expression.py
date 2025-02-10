from typing import TypeVar

import polars as pl

T = TypeVar("T")


def make_table_cells(columns: list[str]) -> list[pl.Expr]:
    return [make_table_cell(col) for col in columns]


def make_table_cell(column: str) -> pl.Expr:
    classes = pl.col(f"{column}__classes")
    style = pl.col(f"{column}__styles")
    return pl.format("<td{}{}>{}</td>", classes, style, pl.col(column)).alias(column)


def format_all_classes(column_names: list[str]) -> list[pl.Expr]:
    return [format_classes_attr(col) for col in column_names]


def format_classes_attr(column: str) -> pl.Expr:
    class_column = f"{column}__classes"
    expr = pl.col(class_column)
    expr = pl.when(expr.list.len() > 0).then(expr).otherwise(None).list.join(" ")
    return pl.format(' class="{}"', expr).fill_null("").alias(class_column)


def format_all_styles(column_names: list[str]) -> list[pl.Expr]:
    return [format_styles_attr(col) for col in column_names]


def format_styles_attr(column: str) -> pl.Expr:
    styles_column = f"{column}__styles"
    styles = pl.col(styles_column).map_elements(
        _styles_struct_to_str, return_dtype=pl.String
    )
    return pl.format(' style="{}"', styles).fill_null("").alias(styles_column)


def _styles_struct_to_str(mapping: dict, /) -> str | None:
    mapping = {k: v for k, v in mapping.items() if k != "_" and v is not None}
    if not mapping:
        return None
    return "; ".join(f"{k}: {v}" for k, v in mapping.items())


def cast_into_string(columns: list[str], null_value: str) -> pl.Expr:
    return pl.selectors.by_name(columns).cast(pl.String).fill_null(null_value)


def if_else(predicate: pl.Expr, true: T, false: T, null: T | None = None) -> pl.Expr:
    return (
        pl.when(predicate.is_null())
        .then(pl.lit(null))
        .when(predicate)
        .then(pl.lit(true))
        .otherwise(pl.lit(false))
    )
