uv run ruff format && \
  uv run ruff check --fix && \
  uv run pytest && \
  uv run python -m doctest polars_styler/**/*.py