from typing import Any

import polars as pl


def if_else(predicate: pl.Expr, true: Any, false: Any) -> pl.Expr:
    return (
        pl.when(predicate.is_null())
        .then(pl.lit(None))
        .when(predicate)
        .then(pl.lit(true))
        .otherwise(pl.lit(false))
    )
