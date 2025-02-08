from typing import TypeVar

import polars as pl

T = TypeVar("T")


def format_all_classes(column_names: list[str]) -> list[pl.Expr]:
    return [format_classes_attr(col) for col in column_names]


def format_classes_attr(column: str) -> pl.Expr:
    class_column = f"{column}__classes"
    expr = pl.col(class_column)
    expr = pl.when(expr.list.len() > 0).then(expr).otherwise(None).list.join(" ")
    return pl.format(' class="{}"', expr).fill_null("").alias(class_column)


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
