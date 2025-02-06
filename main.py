import importlib
import os
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from polars_styler.styler import Styler

EXAMPLES_DIR = Path(__file__).parent / "polars_styler" / "examples"


@dataclass
class Example:
    title: str
    code: str
    table: Styler


def main() -> None:
    html = render_table([load_example(i) for i in range(2)])
    Path("output.html").write_text(html)


def load_example(i: int) -> Example:
    path = EXAMPLES_DIR / f"t_{i:03d}.py"
    module = importlib.import_module(f"polars_styler.examples.t_{i:03d}")
    return Example(
        title=f"Table {i:03d}",
        code=path.read_text(),
        table=module.styler.to_html(),
    )


def render_table(examples):
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("template.html")
    return template.render(examples=examples)


if __name__ == "__main__":
    main()
