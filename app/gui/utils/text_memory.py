"""Helpers to cap in-memory log viewer growth."""

from PyQt5.QtWidgets import QTextEdit

MAX_LOG_VIEW_LINES = 5000


def load_log_tail(content: str, max_lines: int = MAX_LOG_VIEW_LINES) -> str:
    """Return only the most recent lines for the live log viewer."""
    lines = content.splitlines()
    if len(lines) <= max_lines:
        return content
    return "\n".join(lines[-max_lines:])


def append_log_with_limit(
    text_edit: QTextEdit, new_content: str, max_lines: int = MAX_LOG_VIEW_LINES
) -> None:
    """Append log text and trim the widget to the newest ``max_lines`` lines."""
    if not new_content:
        return

    text_edit.append(new_content)
    lines = text_edit.toPlainText().splitlines()
    if len(lines) <= max_lines:
        return

    text_edit.setPlainText("\n".join(lines[-max_lines:]))
