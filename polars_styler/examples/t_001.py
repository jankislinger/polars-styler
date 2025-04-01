import polars as pl

from polars_styler.const import COLOR_BLUE, COLOR_RED
from polars_styler.styler import Styler

df = pl.DataFrame(
    {
        "x": [1, 3, 2, 5, 3],
        "y": [0.4, 0.25, 0.65, 0.15, 0.95],
    }
)
styler = (
    Styler(df)
    .set_table_class("ui celled table selectable")
    .highlight_decrease("x", COLOR_RED)
    .format_bar("y", COLOR_BLUE, max_val=1, align_right=True)
    .relabel_index(lambda x: f"Column '{x}'")
)
