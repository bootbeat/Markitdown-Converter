"""PySide6 front end for the existing MarkItDown converter core."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar,
    QPushButton, QSplitter, QVBoxLayout, QWidget,
)
from PySide6.QtCore import QUrl

from .core import ConversionResult, DEFAULT_PYTHON, convert_many


class FileList(QListWidget):
    files_dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        self.dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()


class ConversionWorker(QThread):
    file_result = Signal(object)
    completed = Signal(int)

    def __init__(self, files: list[Path], output: Path, clean: bool, images: bool) -> None:
        super().__init__()
        self.files, self.output = files, output
        self.clean, self.images = clean, images

    def run(self) -> None:
        results = convert_many(self.files, self.output, DEFAULT_PYTHON,
                               on_result=self.file_result.emit,
                               cleanup=self.clean, manage_images=self.images)
        self.completed.emit(len(results))


class ConverterWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Universal MarkItDown Converter")
        self.resize(900, 720)
        self.setMinimumSize(700, 520)
        self.files: list[Path] = []
        self.output_dir = Path.home() / "Documents" / "MarkItDown output"
        self.worker: ConversionWorker | None = None
        self._build()

    def _build(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 16, 18, 16)
        title = QLabel("Universal MarkItDown Converter")
        title.setStyleSheet("font-size: 22px; font-weight: 700")
        layout.addWidget(title)
        layout.addWidget(QLabel(f"MarkItDown 0.1.8 · Python: {DEFAULT_PYTHON}"))

        row = QHBoxLayout()
        self.add_button = QPushButton("Add Files")
        self.remove_button = QPushButton("Remove Selected")
        self.clear_button = QPushButton("Clear")
        for button in (self.add_button, self.remove_button, self.clear_button):
            row.addWidget(button)
        row.addStretch(1)
        layout.addLayout(row)
        self.file_list = FileList()
        self.file_list.setToolTip("Drop files here or use Add Files")
        layout.addWidget(self.file_list, 3)
        self.add_button.clicked.connect(self.add_files)
        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button.clicked.connect(self.clear_files)
        self.file_list.files_dropped.connect(self.add_paths)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Output folder:"))
        self.output_label = QLabel(str(self.output_dir))
        self.output_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        output_row.addWidget(self.output_label, 1)
        self.browse_button = QPushButton("Choose…")
        output_row.addWidget(self.browse_button)
        self.open_button = QPushButton("Open Output Folder")
        output_row.addWidget(self.open_button)
        self.browse_button.clicked.connect(self.choose_output)
        self.open_button.clicked.connect(self.open_output)
        layout.addLayout(output_row)

        options = QHBoxLayout()
        self.raw_option = QCheckBox("Raw Markdown")
        self.clean_option = QCheckBox("Clean Markdown")
        self.images_option = QCheckBox("Extract Images")
        self.validate_option = QCheckBox("Validate Output")
        self.raw_option.setChecked(True)
        self.validate_option.setChecked(True)
        for check in (self.raw_option, self.clean_option, self.images_option, self.validate_option):
            options.addWidget(check)
        options.addStretch(1)
        self.raw_option.toggled.connect(lambda enabled: self.clean_option.setChecked(False) if enabled else None)
        self.clean_option.toggled.connect(lambda enabled: self.raw_option.setChecked(False) if enabled else None)
        layout.addLayout(options)

        action_row = QHBoxLayout()
        self.convert_button = QPushButton("Convert All")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.status = QLabel("Ready")
        action_row.addWidget(self.convert_button)
        action_row.addWidget(self.progress, 1)
        action_row.addWidget(self.status)
        layout.addLayout(action_row)
        self.convert_button.clicked.connect(self.convert)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Conversion log")
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Select a file to view its conversion details or errors.")
        splitter.addWidget(self.log)
        splitter.addWidget(self.details)
        splitter.setSizes([220, 100])
        layout.addWidget(splitter, 2)
        self.file_list.currentItemChanged.connect(self.show_details)
        self.validate_option.toggled.connect(self.refresh_details)
        self.setCentralWidget(root)

    def add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Select files to convert", "", "All files (*)")
        self.add_paths([Path(path) for path in paths])

    def add_paths(self, paths: list[Path]) -> None:
        for path in paths:
            path = Path(path).expanduser()
            if path.is_file() and path not in self.files:
                self.files.append(path)
                item = QListWidgetItem(f"{path}    ·    Queued")
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.file_list.addItem(item)
        self.status.setText(f"{len(self.files)} file(s) queued")

    def remove_selected(self) -> None:
        for item in self.file_list.selectedItems():
            self.files.remove(item.data(Qt.ItemDataRole.UserRole))
            self.file_list.takeItem(self.file_list.row(item))

    def clear_files(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        self.files.clear()
        self.file_list.clear()
        self.details.clear()
        self.status.setText("Ready")

    def choose_output(self) -> None:
        value = QFileDialog.getExistingDirectory(self, "Choose Markdown output folder", str(self.output_dir))
        if value:
            self.output_dir = Path(value)
            self.output_label.setText(value)

    def convert(self) -> None:
        if not self.files:
            QMessageBox.warning(self, "No files", "Add one or more files first.")
            return
        files = list(self.files)
        self.progress.setRange(0, len(files))
        self.progress.setValue(0)
        self.log.appendPlainText(f"Starting {len(files)} conversion(s) to {self.output_dir}")
        self._set_busy(True)
        self.worker = ConversionWorker(files, self.output_dir, self.clean_option.isChecked(),
                                       self.images_option.isChecked())
        self.worker.file_result.connect(self.on_result)
        self.worker.completed.connect(self.on_completed)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _set_busy(self, busy: bool) -> None:
        for widget in (self.add_button, self.remove_button, self.clear_button,
                       self.browse_button, self.convert_button):
            widget.setEnabled(not busy)

    def on_result(self, result: ConversionResult) -> None:
        index = next((i for i, path in enumerate(self.files) if path == result.source), None)
        label = "SUCCESS" if result.success else "FAILED"
        if index is not None:
            item = self.file_list.item(index)
            item.setText(f"{result.source}    ·    {label}")
            item.setData(Qt.ItemDataRole.UserRole + 1, result.message)
            item.setData(Qt.ItemDataRole.UserRole + 2, str(result.output or ""))
            item.setForeground(Qt.GlobalColor.darkGreen if result.success else Qt.GlobalColor.red)
        self.log.appendPlainText(f"[{label}] {result.source} — {result.output or ''}\n    {self._visible_message(result.message)}")
        self.progress.setValue(self.progress.value() + 1)
        self.status.setText(f"Processed {self.progress.value()} of {self.progress.maximum()} file(s)")
        if index is not None and self.file_list.currentRow() == index:
            self.show_details(self.file_list.item(index), None)

    def show_details(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            self.details.clear()
            return
        message = self._visible_message(current.data(Qt.ItemDataRole.UserRole + 1) or "Queued for conversion.")
        output = current.data(Qt.ItemDataRole.UserRole + 2) or "Not created yet"
        self.details.setPlainText(f"Source: {current.data(Qt.ItemDataRole.UserRole)}\nOutput: {output}\n\n{message}")

    def _visible_message(self, message: str) -> str:
        # The existing core performs its validation on every conversion; this
        # option controls whether its validation notes are surfaced in the UI.
        if not self.validate_option.isChecked() and " Validation: " in message:
            return message.split(" Validation: ", 1)[0]
        return message

    def refresh_details(self, _checked: bool) -> None:
        self.show_details(self.file_list.currentItem(), None)

    def on_completed(self, count: int) -> None:
        self._set_busy(False)
        self.status.setText(f"Finished: {count} file(s) processed")
    def _worker_finished(self) -> None:
        worker = self.sender()
        if worker is self.worker:
            self.worker = None
        worker.deleteLater()

    def open_output(self) -> None:
        if not self.output_dir.is_dir():
            QMessageBox.information(self, "Output folder", "The output folder does not exist yet.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output_dir)))


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = ConverterWindow()
    window.show()
    sys.exit(app.exec())
