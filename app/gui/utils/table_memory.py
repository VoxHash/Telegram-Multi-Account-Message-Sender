"""Helpers to reduce QWidget memory use when reloading tables."""

from PyQt5.QtWidgets import QTableWidget


def prepare_table_reload(table: QTableWidget) -> None:
    """Release existing row widgets/items before loading a new page of data."""
    table.setRowCount(0)
    table.clearContents()
