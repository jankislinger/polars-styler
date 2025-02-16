__run_tests() {
  uv run $1 $2 pytest && \
  uv run $1 $2 python -m doctest polars_styler/**/*.py && \
  echo $1 $2
}

uv run ruff format && \
  uv run ruff check --fix && \
  __run_tests && \
  __run_tests --with='polars~=1.10.0' && \
  __run_tests --upgrade &&
  uv run main.py
