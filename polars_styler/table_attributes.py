import html
from typing import Iterable


class TableAttributes:
    """Class to store table-wide attributes that don't affect individual cells."""

    def __init__(self, column_names: list[str]) -> None:
        self._table_classes: list[str] = []
        self._thead_classes: list[str] = []
        self._column_labels: dict[str, str] = {k: k for k in column_names}
        self.page_settings: tuple[int, int] | None = None

    def add_table_classes(self, class_names: str | list[str]) -> None:
        """Set the CSS class for the table element."""
        if isinstance(class_names, str):
            class_names = class_names.split(" ")
        self._table_classes.extend(class_names)

    def add_thead_classes(self, class_names: str | list[str]) -> None:
        """Set the CSS class for the table element."""
        if isinstance(class_names, str):
            class_names = class_names.split(" ")
        self._thead_classes.extend(class_names)

    def set_column_labels(self, labels: dict[str, str]) -> None:
        """Set custom labels for table columns."""
        self._column_labels.update(labels)

    def tag_table(self) -> str:
        return _tag("table", self._table_classes)

    def tags_head(self, columns: list[str]) -> Iterable[str]:
        yield from [
            _tag("thead", self._thead_classes),
            "<tr>",
        ]
        for col in columns:
            label = self._column_labels[col]
            yield f"<th>{html.escape(label)}</th>"
        yield from ["</tr>", "</thead>"]

def _tag(tag: str, classes: list[str] | None) -> str:
    if not classes:
        return f"<{tag}>"
    return f'<{tag} class="{" ".join(classes)}">'
