from typing import TypeVar

import polars as pl


T = TypeVar("T")


def if_else(predicate: pl.Expr, true: T, false: T, null: T | None = None) -> pl.Expr:
    return (
        pl.when(predicate.is_null())
        .then(pl.lit(null))
        .when(predicate)
        .then(pl.lit(true))
        .otherwise(pl.lit(false))
    )
