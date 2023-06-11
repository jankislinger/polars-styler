# Styler for Polars Data Frames

A soon-to-be crate and python package for styling Polars Data Frames.
It is based on the [Styler](https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html) from Pandas.

## Why does this exist?

1. I think that the Styler in Pandas is powerful tool for data analysis and visualization.
2. Polars is a great Rust library that might be the next step after Pandas.
3. There is nothing like this for Polars yet. (Or at least I didn't search hard enough.)
4. I wanted to learn Rust and this is a good project to do so.

## Should you use it?

No, not yet. It is not ready for production use.

With Pandas 2.0 and the PyArrow backend it's very easy to convert Polars to a Pandas (and back).
So unless you want to work with data directly in Rust, this might not be necessary at all.

```
import polars as pl

df = pl.DataFrame({'a': [1, 2, 3], 'b': [4.56, 5.4321, 6.66]})
df.to_pandas().style
```

This project may be interesting for you only if:
- you want to work with data directly in Rust,
- you want to create blazingly fast dashboard (e.g. with [Yew](https://yew.rs/) or [Rocket](https://rocket.rs/)), or
- you already use Polars in Python and install Pandas only for the Styler.

## Design

The Styler is written using a Builder pattern.
One class, `Styler`, is used to collect all the styles and parameters.
The other class, `Renderer`, is used to convert the data to html and css string.
Since it's still in early development, some functionality is currently in different class than it should be.


## Example

```rust
use polars::prelude::*;
use crate::styler::StylerExt;

mod renderer;
mod styler;

fn main() {
    let df = df! (
        "a" => &[1, 2, 3],
        "b" => &[4.56, 5.4321, 6.66]
    ).unwrap();

    let styled = df
        .style()
        // .set_caption("This is a caption")
        // .set_table_styles(&[("font-size", "1.2em")])
        .set_precision(2)
        // .set_table_attributes(&[("class", "table table-striped")])
        // .set_cell_styles(&[("background-color", "lightblue")])
        // .set_column_styles(&[("background-color", "lightgreen")])
        // .set_caption_styles(&[("font-size", "1.5em")])
        // .set_caption_attributes(&[("class", "caption")])
        // .set_index_styles(&[("background-color", "lightgrey")])
        // .set_index_attributes(&[("class", "index")])
        // .set_td_classes(&[("class", "td")])
        // .set_th_classes(&[("class", "th")])
        // .set_tr_classes(&[("class", "tr")])
        // .set_na_rep("N/A")
        .render()
        // .unwrap()
        ;

    println!("{}", styled);
}
```

Commented out lines are not yet implemented.