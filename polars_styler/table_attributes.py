import html
from typing import Iterable


class TableAttributes:
    """Class to store table-wide attributes that don't affect individual cells."""

    def __init__(self, column_names: list[str]):
        self._table_classes: list[str] = []
        self._column_labels: dict[str, str] = {k: k for k in column_names}
        self.page_settings: tuple[int, int] | None = None

    def add_table_classes(self, class_names: str | list[str]) -> None:
        """Set the CSS class for the table element."""
        if isinstance(class_names, str):
            class_names = class_names.split(" ")
        self._table_classes.extend(class_names)

    def set_column_labels(self, labels: dict[str, str]) -> None:
        """Set custom labels for table columns."""
        self._column_labels.update(labels)

    def set_page_settings(self, page_size: int, page_number: int) -> None:
        """Set pagination settings."""
        self.page_settings = (page_size, page_number)

    def tag_table(self) -> str:
        if not self._table_classes:
            return "<table>"
        classes = " ".join(self._table_classes)
        return f'<table class="{classes}">'

    def tags_head(self, columns: list[str]) -> Iterable[str]:
        yield from ["<thead>", "<tr>"]
        for col in columns:
            label = self._column_labels[col]
            yield f"<th>{html.escape(label)}</th>"
        yield from ["</tr>", "</thead>"]
