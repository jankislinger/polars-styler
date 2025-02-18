uv run ruff format && \
  uv run ruff check --fix && \
  uv run pytest && \
  uv run --with='polars~=1.10.0' pytest && \
  uv run --upgrade pytest &&
  uv run main.py
