import polars as pl

from polars_styler.expression import if_else
from polars_styler.styler import Styler

df = pl.DataFrame(
    {
        "x": [1, 3, None, 15, 3],
        "y": [1 / 2, 1 / 3, 1 / 7, 2 / 5, 2 / 3],
    }
)
styler = (
    Styler(df)
    .set_table_class("ui celled table")
    .apply_cell_classes("x", if_else(pl.col("x") > 10, "positive", "error", "disabled"))
    .set_precision("y", 3)
)
