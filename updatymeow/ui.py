from datetime import datetime
import os
from typing import Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from updatymeow.ecosystems import scan_all_ecosystems
from updatymeow.models import Category, InstalledItem, Status, UpdateRecord
from updatymeow.runner import execute_command
from updatymeow.store import Store

STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: #cdd6f4;
}
QListWidget {
    background-color: #181825;
    border: none;
    border-right: 1px solid #313244;
    padding: 8px;
    outline: none;
}
QListWidget::item {
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 3px;
    color: #a6adc8;
    font-weight: 500;
}
QListWidget::item:selected {
    background-color: #313244;
    color: #cdd6f4;
    font-weight: bold;
}
QListWidget::item:hover:!selected {
    background-color: #24253a;
    color: #cdd6f4;
}
QTableWidget {
    background-color: #1e1e2e;
    border: none;
    gridline-color: #313244;
    selection-background-color: #313244;
    selection-color: #cdd6f4;
}
QHeaderView::section {
    background-color: #181825;
    color: #a6adc8;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #313244;
    font-weight: 600;
}
QLineEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 12px;
    color: #cdd6f4;
}
QLineEdit:focus {
    border: 1px solid #89b4fa;
}
QPushButton {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    color: #cdd6f4;
}
QPushButton:hover {
    background-color: #45475a;
}
QPushButton#primaryBtn {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
}
QPushButton#primaryBtn:hover {
    background-color: #b4befe;
}
QTextEdit {
    background-color: #11111b;
    border: 1px solid #313244;
    border-radius: 6px;
    font-family: monospace;
    font-size: 12px;
    color: #a6e3a1;
}
"""


class ScanWorker(QThread):
    finished = pyqtSignal(list)

    def run(self):
        items = scan_all_ecosystems()
        self.finished.emit(items)


class UpdateWorker(QThread):
    line_output = pyqtSignal(str)
    item_finished = pyqtSignal(str, bool, str)
    all_done = pyqtSignal()

    def __init__(self, items_to_update: list[InstalledItem]):
        super().__init__()
        self.items = items_to_update

    def run(self):
        for item in self.items:
            if not item.update_command:
                continue
            self.line_output.emit(f"==> Updating {item.name} ({item.id})...")
            self.line_output.emit(f"$ {item.update_command}")
            code, out = execute_command(item.update_command, on_output=self.line_output.emit)
            success = code == 0
            self.item_finished.emit(item.id, success, out)
        self.all_done.emit()


class MainWindow(QMainWindow):
    def __init__(self, store: Optional[Store] = None):
        super().__init__()
        self.store = store or Store()
        self.items: list[InstalledItem] = []
        self.scan_worker: Optional[ScanWorker] = None
        self.update_worker: Optional[UpdateWorker] = None
        self.current_category_filter = "All"
        self.current_status_filter = "All"

        self.setWindowTitle("UpdatyMeow - Linux Software Updates")
        self.resize(1100, 680)
        self.setStyleSheet(STYLESHEET)

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar_items = [
            ("📦 All Updates", "All"),
            ("🖥️ System", Category.SYSTEM.value),
            ("🚀 Apps", Category.APPS.value),
            ("⚡ Runtimes", Category.RUNTIMES.value),
            ("📦 Packages", Category.PACKAGES.value),
            ("⭐ Favorites", "Favorites"),
            ("🕒 History", "History"),
        ]
        for label, _ in self.sidebar_items:
            item = QListWidgetItem(label)
            self.sidebar.addItem(item)
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self._on_sidebar_changed)
        main_layout.addWidget(self.sidebar)

        # 2. Main Area Splitter (Table + Inspector)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Central panel
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(16, 16, 16, 16)
        center_layout.setSpacing(12)

        # Top Bar: Search & Actions
        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search packages or ecosystems...")
        self.search_input.textChanged.connect(self._apply_filters)
        top_bar.addWidget(self.search_input)

        self.filter_updates_btn = QPushButton("Updates Only")
        self.filter_updates_btn.setCheckable(True)
        self.filter_updates_btn.toggled.connect(self._toggle_updates_only)
        top_bar.addWidget(self.filter_updates_btn)

        self.refresh_btn = QPushButton("🔄 Check for Updates")
        self.refresh_btn.clicked.connect(self.start_scan)
        top_bar.addWidget(self.refresh_btn)

        self.update_all_btn = QPushButton("⚡ Update All")
        self.update_all_btn.setObjectName("primaryBtn")
        self.update_all_btn.clicked.connect(self.update_all)
        top_bar.addWidget(self.update_all_btn)

        center_layout.addLayout(top_bar)

        # Status / Summary bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
        center_layout.addWidget(self.status_label)

        # Table of items
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["⭐", "Name", "Ecosystem", "Installed", "Latest", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_table_selection)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        center_layout.addWidget(self.table)

        # History table widget (hidden by default, shown when History selected in sidebar)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Timestamp", "Package", "From", "To", "Result"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setVisible(False)
        center_layout.addWidget(self.history_table)

        splitter.addWidget(center_widget)

        # 3. Right Inspector Pane
        self.inspector = QWidget()
        self.inspector.setFixedWidth(320)
        inspector_layout = QVBoxLayout(self.inspector)
        inspector_layout.setContentsMargins(16, 16, 16, 16)
        inspector_layout.setSpacing(10)

        inspector_title = QLabel("Item Inspector")
        inspector_title.setFont(QFont("", 14, QFont.Bold))
        inspector_layout.addWidget(inspector_title)

        self.detail_name = QLabel("No item selected")
        self.detail_name.setFont(QFont("", 13, QFont.Bold))
        inspector_layout.addWidget(self.detail_name)

        self.detail_eco = QLabel("")
        self.detail_eco.setStyleSheet("color: #a6adc8;")
        inspector_layout.addWidget(self.detail_eco)

        self.detail_version = QLabel("")
        inspector_layout.addWidget(self.detail_version)

        self.detail_desc = QLabel("")
        self.detail_desc.setWordWrap(True)
        self.detail_desc.setStyleSheet("color: #bac2de;")
        inspector_layout.addWidget(self.detail_desc)

        cmd_label = QLabel("Update Command:")
        cmd_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        inspector_layout.addWidget(cmd_label)

        self.cmd_box = QTextEdit()
        self.cmd_box.setReadOnly(True)
        self.cmd_box.setMaximumHeight(70)
        inspector_layout.addWidget(self.cmd_box)

        btn_row = QHBoxLayout()
        self.copy_cmd_btn = QPushButton("📋 Copy")
        self.copy_cmd_btn.clicked.connect(self._copy_command)
        btn_row.addWidget(self.copy_cmd_btn)

        self.pin_btn = QPushButton("📌 Pin")
        self.pin_btn.clicked.connect(self._toggle_pin_selected)
        btn_row.addWidget(self.pin_btn)
        inspector_layout.addLayout(btn_row)

        self.update_single_btn = QPushButton("⚡ Update Package")
        self.update_single_btn.setObjectName("primaryBtn")
        self.update_single_btn.clicked.connect(self.update_selected)
        inspector_layout.addWidget(self.update_single_btn)

        inspector_layout.addStretch()
        splitter.addWidget(self.inspector)

    def set_items(self, items: list[InstalledItem]):
        self.items = items
        self.store.apply_preferences(self.items)
        self._populate_table()
        outdated_count = sum(1 for i in self.items if i.status == Status.OUTDATED)
        self.update_all_btn.setText(f"⚡ Update All ({outdated_count})")
        self.status_label.setText(f"Loaded {len(self.items)} items ({outdated_count} updates available)")

    def _populate_table(self):
        self.table.setRowCount(0)
        for row_idx, item in enumerate(self.items):
            self.table.insertRow(row_idx)

            # Star
            star_item = QTableWidgetItem("⭐" if item.is_favorite else "☆")
            star_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 0, star_item)

            # Name
            name_item = QTableWidgetItem(item.name)
            name_item.setData(Qt.UserRole, item.id)
            self.table.setItem(row_idx, 1, name_item)

            # Ecosystem
            eco_item = QTableWidgetItem(item.ecosystem.upper())
            eco_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 2, eco_item)

            # Installed
            self.table.setItem(row_idx, 3, QTableWidgetItem(item.installed_version or "-"))

            # Latest
            latest_item = QTableWidgetItem(item.latest_version or "-")
            self.table.setItem(row_idx, 4, latest_item)

            # Status Chip
            status_item = QTableWidgetItem(item.status.value)
            if item.status == Status.OUTDATED:
                status_item.setForeground(QColor("#fab387" if not item.is_major else "#f38ba8"))
                if item.is_major:
                    status_item.setText("Major update")
            elif item.status == Status.UP_TO_DATE:
                status_item.setForeground(QColor("#a6e3a1"))
            elif item.status == Status.PINNED:
                status_item.setForeground(QColor("#6c7086"))
            self.table.setItem(row_idx, 5, status_item)

        self._apply_filters()

    def _on_sidebar_changed(self, row: int):
        _, key = self.sidebar_items[row]
        if key == "History":
            self.table.setVisible(False)
            self.history_table.setVisible(True)
            self._populate_history()
            return

        self.table.setVisible(True)
        self.history_table.setVisible(False)
        self.current_category_filter = key
        self._apply_filters()

    def _populate_history(self):
        history = self.store.get_history()
        self.history_table.setRowCount(0)
        for idx, rec in enumerate(history):
            self.history_table.insertRow(idx)
            self.history_table.setItem(idx, 0, QTableWidgetItem(rec.timestamp))
            self.history_table.setItem(idx, 1, QTableWidgetItem(rec.item_name))
            self.history_table.setItem(idx, 2, QTableWidgetItem(rec.from_version))
            self.history_table.setItem(idx, 3, QTableWidgetItem(rec.to_version))
            res_item = QTableWidgetItem("✓ Success" if rec.success else "✗ Failed")
            res_item.setForeground(QColor("#a6e3a1" if rec.success else "#f38ba8"))
            self.history_table.setItem(idx, 4, res_item)

    def _toggle_updates_only(self, checked: bool):
        self.current_status_filter = "Updates" if checked else "All"
        self._apply_filters()

    def _apply_filters(self):
        query = self.search_input.text().lower().strip()
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            eco_item = self.table.item(row, 2)
            if not name_item or not eco_item:
                continue
            item_id = name_item.data(Qt.UserRole)
            item = next((i for i in self.items if i.id == item_id), None)
            if not item:
                continue

            matches_search = (not query) or (query in item.name.lower()) or (query in item.ecosystem.lower())

            matches_cat = True
            if self.current_category_filter == "Favorites":
                matches_cat = item.is_favorite
            elif self.current_category_filter != "All":
                matches_cat = (item.category.value == self.current_category_filter)

            matches_status = True
            if self.current_status_filter == "Updates":
                matches_status = (item.status == Status.OUTDATED)

            visible = matches_search and matches_cat and matches_status
            self.table.setRowHidden(row, not visible)

    def _on_table_selection(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        name_item = self.table.item(row, 1)
        if not name_item:
            return
        item_id = name_item.data(Qt.UserRole)
        item = next((i for i in self.items if i.id == item_id), None)
        if not item:
            return

        self.detail_name.setText(item.name)
        self.detail_eco.setText(f"{item.category.value} • {item.ecosystem}")
        self.detail_version.setText(f"Installed: {item.installed_version}  ➔  Latest: {item.latest_version or 'N/A'}")
        self.detail_desc.setText(item.description or "No description provided.")
        self.cmd_box.setPlainText(item.update_command or "# No update command defined")
        self.pin_btn.setText("📌 Unpin" if item.is_pinned else "📌 Pin")
        self.update_single_btn.setEnabled(bool(item.update_command and item.status == Status.OUTDATED))

    def _on_cell_double_clicked(self, row: int, col: int):
        if col == 0:  # Star clicked
            name_item = self.table.item(row, 1)
            if not name_item:
                return
            item_id = name_item.data(Qt.UserRole)
            item = next((i for i in self.items if i.id == item_id), None)
            if not item:
                return
            if item.is_favorite:
                self.store.unfavorite(item.id)
                item.is_favorite = False
                self.table.item(row, 0).setText("☆")
            else:
                self.store.favorite(item.id)
                item.is_favorite = True
                self.table.item(row, 0).setText("⭐")

    def _copy_command(self):
        cmd = self.cmd_box.toPlainText()
        if cmd:
            QApplication.clipboard().setText(cmd)
            self.status_label.setText("Command copied to clipboard!")

    def _toggle_pin_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        name_item = self.table.item(row, 1)
        if not name_item:
            return
        item_id = name_item.data(Qt.UserRole)
        item = next((i for i in self.items if i.id == item_id), None)
        if not item:
            return

        if item.is_pinned:
            self.store.unpin(item.id)
            item.is_pinned = False
            item.__post_init__()
        else:
            self.store.pin(item.id)
            item.is_pinned = True
            item.status = Status.PINNED

        self.set_items(self.items)

    def start_scan(self):
        self.refresh_btn.setEnabled(False)
        self.status_label.setText("Scanning system for updates...")
        self.scan_worker = ScanWorker()
        self.scan_worker.finished.connect(self._on_scan_finished)
        self.scan_worker.start()

    def _on_scan_finished(self, items: list[InstalledItem]):
        self.refresh_btn.setEnabled(True)
        self.set_items(items)

    def update_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        item_id = self.table.item(selected_rows[0].row(), 1).data(Qt.UserRole)
        item = next((i for i in self.items if i.id == item_id), None)
        if item:
            self._run_updates([item])

    def update_all(self):
        outdated = [i for i in self.items if i.status == Status.OUTDATED and i.update_command]
        if not outdated:
            QMessageBox.information(self, "No Updates", "All packages are already up to date!")
            return
        confirm = QMessageBox.question(
            self,
            "Confirm Update",
            f"Are you sure you want to update {len(outdated)} packages?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self._run_updates(outdated)

    def _run_updates(self, items_to_update: list[InstalledItem]):
        dlg = QDialog(self)
        dlg.setWindowTitle("Executing Updates")
        dlg.resize(600, 400)
        dlg.setStyleSheet(STYLESHEET)
        dlg_layout = QVBoxLayout(dlg)

        info_lbl = QLabel(f"Updating {len(items_to_update)} package(s)...")
        dlg_layout.addWidget(info_lbl)

        log_box = QTextEdit()
        log_box.setReadOnly(True)
        dlg_layout.addWidget(log_box)

        progress = QProgressBar()
        progress.setRange(0, len(items_to_update))
        progress.setValue(0)
        dlg_layout.addWidget(progress)

        close_btn = QPushButton("Close")
        close_btn.setEnabled(False)
        close_btn.clicked.connect(dlg.accept)
        dlg_layout.addWidget(close_btn)

        worker = UpdateWorker(items_to_update)
        worker.line_output.connect(log_box.append)

        def on_item_fin(item_id, success, out):
            progress.setValue(progress.value() + 1)
            item = next((i for i in self.items if i.id == item_id), None)
            if item:
                rec = UpdateRecord(
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    item_id=item.id,
                    item_name=item.name,
                    from_version=item.installed_version,
                    to_version=item.latest_version or "latest",
                    success=success,
                    output=out,
                )
                self.store.add_history(rec)

        def on_all_done():
            close_btn.setEnabled(True)
            info_lbl.setText("Updates finished!")
            self.start_scan()

        worker.item_finished.connect(on_item_fin)
        worker.all_done.connect(on_all_done)
        worker.start()
        dlg.exec_()
