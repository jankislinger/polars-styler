import importlib
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
    html = render_examples([load_example(i) for i in range(3)])
    output_file = Path("output.html")
    output_file.write_text(html)
    print(f"Open in browser: file://{output_file.absolute()}")


def load_example(i: int) -> Example:
    code = EXAMPLES_DIR.joinpath(f"t_{i:03d}.py").read_text()
    module = importlib.import_module(f"polars_styler.examples.t_{i:03d}")
    return Example(title=f"Table {i:03d}", code=code, table=module.styler.to_html())


def render_examples(examples):
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("template.html")
    return template.render(examples=examples)


if __name__ == "__main__":
    main()
