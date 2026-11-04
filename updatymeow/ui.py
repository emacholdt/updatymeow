from datetime import datetime
import os
import subprocess
from typing import Optional

from PyQt5.QtCore import Qt, QThread, QTimer, QUrl, pyqtSignal
from PyQt5.QtGui import QColor, QDesktopServices, QFont, QIcon
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizeGrip,
    QSplitter,
    QStyle,
    QSystemTrayIcon,
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
QMainWindow, QDialog {
    background-color: #0d0f12;
    color: #e6e8ec;
}
QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: #e6e8ec;
}

/* Sidebar */
QListWidget {
    background-color: #12151b;
    border: none;
    border-right: 1px solid #1a1e27;
    padding: 12px 8px;
    outline: none;
}
QListWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
    margin-bottom: 3px;
    color: #8b929e;
    font-weight: 500;
}
QListWidget::item:selected {
    background-color: #1c222d;
    color: #ffffff;
    font-weight: 600;
}
QListWidget::item:hover:!selected {
    background-color: #161a22;
    color: #d1d5db;
}

/* Table */
QTableWidget {
    background-color: #0d0f12;
    border: none;
    gridline-color: transparent;
    selection-background-color: #171c26;
    selection-color: #ffffff;
    outline: none;
}
QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #151820;
}
QTableWidget::item:selected {
    background-color: #171c26;
}
QHeaderView::section {
    background-color: #0d0f12;
    color: #64748b;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid #1a1e27;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

/* Inputs */
QLineEdit {
    background-color: #12151b;
    border: 1px solid #1e232e;
    border-radius: 6px;
    padding: 7px 12px;
    color: #f1f3f7;
    selection-background-color: #2563eb;
}
QLineEdit:focus {
    border: 1px solid #3b82f6;
    background-color: #151922;
}

/* Buttons */
QPushButton {
    background-color: #141820;
    border: 1px solid #202633;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 500;
    color: #cbd5e1;
}
QPushButton:hover {
    background-color: #1b212c;
    border-color: #2b3345;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #12151b;
}
QPushButton:checked {
    background-color: #1e2430;
    border-color: #3b82f6;
    color: #60a5fa;
}
QPushButton#primaryBtn {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton#primaryBtn:hover {
    background-color: #1d4ed8;
}
QPushButton#primaryBtn:disabled {
    background-color: #171b24;
    color: #4b5563;
    border: 1px solid #1e232e;
}

#inspectorPane {
    background-color: #12151b;
    border-left: 1px solid #1a1e27;
}
#inspectorPane QPushButton {
    background-color: #161a22;
    border: 1px solid #222733;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 500;
    color: #cbd5e1;
}
#inspectorPane QPushButton:hover {
    background-color: #1c212c;
    border-color: #2b3345;
    color: #ffffff;
}
#inspectorPane QPushButton#primaryBtn {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
}
#inspectorPane QPushButton#primaryBtn:hover {
    background-color: #1d4ed8;
}
#inspectorPane QPushButton#primaryBtn:disabled {
    background-color: #171b24;
    color: #4b5563;
    border: 1px solid #1e232e;
}

#sidebarContainer {
    background-color: #12151b;
    border-right: 1px solid #1a1e27;
}

/* Text and Code Areas */
QTextEdit {
    background-color: #090a0d;
    border: 1px solid #181c25;
    border-radius: 6px;
    font-family: ui-monospace, "SF Mono", "Fira Code", monospace;
    font-size: 12px;
    color: #e2e8f0;
    padding: 8px;
}

/* Forms & Modals */
QGroupBox {
    border: 1px solid #1a1e27;
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 14px;
    font-weight: 600;
    color: #94a3b8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #cbd5e1;
}
QComboBox {
    background-color: #12151b;
    border: 1px solid #1e232e;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2e8f0;
}
QComboBox QAbstractItemView {
    background-color: #12151b;
    border: 1px solid #1e232e;
    selection-background-color: #1c222d;
    selection-color: #ffffff;
}
QCheckBox {
    spacing: 8px;
    color: #cbd5e1;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #2b3345;
    background-color: #12151b;
}
QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #3b82f6;
}
QProgressBar {
    background-color: #12151b;
    border: 1px solid #1e232e;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #10b981;
    border-radius: 3px;
}
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 7px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #1e232e;
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #2b3345;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
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

    def __init__(self, items_to_update: list[InstalledItem], sudo_password: Optional[str] = None):
        super().__init__()
        self.items = items_to_update
        self.sudo_password = sudo_password

    def run(self):
        for item in self.items:
            if not item.update_command:
                continue
            self.line_output.emit(f"==> Updating {item.name} ({item.id})...")
            self.line_output.emit(f"$ {item.update_command}")
            code, out = execute_command(
                item.update_command,
                on_output=self.line_output.emit,
                sudo_password=self.sudo_password,
            )
            success = code == 0
            self.item_finished.emit(item.id, success, out)
        self.all_done.emit()


class SettingsDialog(QDialog):
    def __init__(self, parent=None, store: Optional[Store] = None):
        super().__init__(parent)
        self.store = store or Store()
        self.setWindowTitle("Settings")
        self.resize(480, 420)
        self.setStyleSheet(STYLESHEET)
        layout = QVBoxLayout(self)

        settings = self.store.get_settings()

        # General
        gen_group = QGroupBox("General")
        gen_layout = QVBoxLayout(gen_group)
        self.autostart_chk = QCheckBox("Open at login")
        self.autostart_chk.setChecked(self.store.is_autostart_enabled())
        gen_layout.addWidget(self.autostart_chk)

        self.tray_chk = QCheckBox("Keep running in system tray on close")
        self.tray_chk.setChecked(settings.get("minimize_to_tray", True))
        gen_layout.addWidget(self.tray_chk)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Check automatically:"))
        self.interval_combo = QComboBox()
        self.intervals = [
            ("Every 6 hours", "6h"),
            ("Every 12 hours", "12h"),
            ("Daily", "24h"),
            ("Weekly", "weekly"),
            ("Never", "never"),
        ]
        for label, val in self.intervals:
            self.interval_combo.addItem(label, val)
        curr_int = settings.get("check_interval", "6h")
        for idx, (_, val) in enumerate(self.intervals):
            if val == curr_int:
                self.interval_combo.setCurrentIndex(idx)
        interval_layout.addWidget(self.interval_combo)
        gen_layout.addLayout(interval_layout)
        layout.addWidget(gen_group)

        # Notifications
        notif_group = QGroupBox("Notifications")
        notif_layout = QVBoxLayout(notif_group)
        self.notif_new_chk = QCheckBox("Notify when new updates are available")
        self.notif_new_chk.setChecked(settings.get("notify_new_updates", True))
        notif_layout.addWidget(self.notif_new_chk)

        self.notif_fin_chk = QCheckBox("Notify when updates finish in background")
        self.notif_fin_chk.setChecked(settings.get("notify_updates_finished", True))
        notif_layout.addWidget(self.notif_fin_chk)
        layout.addWidget(notif_group)

        # Configuration (tools.json)
        tools_group = QGroupBox("Configuration")
        tools_layout = QVBoxLayout(tools_group)
        tools_info = QLabel("Add custom CLI tools or GitHub release checks to tools.json without code changes.")
        tools_info.setWordWrap(True)
        tools_info.setStyleSheet("color: #8b929e; font-size: 11px;")
        tools_layout.addWidget(tools_info)
        open_tools_btn = QPushButton("Open Config Folder")
        open_tools_btn.clicked.connect(self._open_config_folder)
        tools_layout.addWidget(open_tools_btn)
        layout.addWidget(tools_group)

        # Action buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save)
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)

    def _open_config_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.store.config_dir)))

    def _save(self):
        self.store.set_autostart(self.autostart_chk.isChecked())
        settings = self.store.get_settings()
        settings["autostart"] = self.autostart_chk.isChecked()
        settings["minimize_to_tray"] = self.tray_chk.isChecked()
        settings["check_interval"] = self.interval_combo.currentData()
        settings["notify_new_updates"] = self.notif_new_chk.isChecked()
        settings["notify_updates_finished"] = self.notif_fin_chk.isChecked()
        self.store.save_settings(settings)
        self.accept()


class IntegratedTitleBar(QWidget):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.win = parent_window
        self.setFixedHeight(34)
        self.setStyleSheet("""
            IntegratedTitleBar {
                background-color: #0d0f12;
                border-bottom: 1px solid #1a1e27;
            }
            QLabel#titleText {
                color: #64748b;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
                padding-left: 14px;
            }
            QPushButton.windowControl {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: #8b929e;
                font-size: 11px;
                width: 26px;
                height: 20px;
                margin-right: 4px;
            }
            QPushButton.windowControl:hover {
                background-color: #1f242e;
                color: #ffffff;
            }
            QPushButton#closeControl:hover {
                background-color: #dc2626;
                color: #ffffff;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(4)

        self.title_lbl = QLabel("UPDATYMEOW")
        self.title_lbl.setObjectName("titleText")
        layout.addWidget(self.title_lbl)

        layout.addStretch()

        self.min_btn = QPushButton("—")
        self.min_btn.setProperty("class", "windowControl")
        self.min_btn.clicked.connect(self.win.showMinimized)
        layout.addWidget(self.min_btn)

        self.max_btn = QPushButton("□")
        self.max_btn.setProperty("class", "windowControl")
        self.max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.max_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setProperty("class", "windowControl")
        self.close_btn.setObjectName("closeControl")
        self.close_btn.clicked.connect(self.win.close)
        layout.addWidget(self.close_btn)

        self._drag_pos = None

    def _toggle_maximize(self):
        if self.win.isMaximized():
            self.win.showNormal()
            self.max_btn.setText("□")
        else:
            self.win.showMaximized()
            self.max_btn.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.win.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.win.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        self._toggle_maximize()


class MainWindow(QMainWindow):
    def __init__(self, store: Optional[Store] = None):
        super().__init__()
        self.store = store or Store()
        self.items: list[InstalledItem] = []
        self.scan_worker: Optional[ScanWorker] = None
        self.update_worker: Optional[UpdateWorker] = None
        self.current_category_filter = "All"
        self.current_status_filter = "All"
        self.last_sidebar_row = 0

        self.setWindowTitle("UpdatyMeow - Linux Software Updates")
        self.resize(1100, 680)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setStyleSheet(STYLESHEET)

        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.start_scan)

        self._init_ui()
        self._setup_tray()
        self._setup_timer()

    def _init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("mainWindowRoot")
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(1, 1, 1, 1)
        root_layout.setSpacing(0)

        # Integrated Modern Top Titlebar
        self.title_bar = IntegratedTitleBar(self)
        root_layout.addWidget(self.title_bar)

        # Body Row (Sidebar + Splitter)
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # 1. Left Sidebar Container with App Brand Header
        sidebar_container = QWidget()
        sidebar_container.setObjectName("sidebarContainer")
        sidebar_container.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        brand_widget = QWidget()
        brand_layout = QVBoxLayout(brand_widget)
        brand_layout.setContentsMargins(18, 16, 18, 12)
        brand_layout.setSpacing(2)

        brand_title = QLabel("UpdatyMeow")
        brand_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc; letter-spacing: -0.2px;")
        brand_sub = QLabel("Linux Software Updates")
        brand_sub.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 500;")
        brand_layout.addWidget(brand_title)
        brand_layout.addWidget(brand_sub)
        sidebar_layout.addWidget(brand_widget)

        self.sidebar = QListWidget()
        self.sidebar_items = [
            ("All Updates", "All"),
            ("System", Category.SYSTEM.value),
            ("Apps", Category.APPS.value),
            ("Runtimes", Category.RUNTIMES.value),
            ("Packages", Category.PACKAGES.value),
            ("Favorites", "Favorites"),
            ("History", "History"),
            ("Settings", "Settings"),
        ]
        for label, _ in self.sidebar_items:
            item = QListWidgetItem(label)
            self.sidebar.addItem(item)
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self._on_sidebar_changed)
        sidebar_layout.addWidget(self.sidebar)
        body_layout.addWidget(sidebar_container)

        # 2. Main Area Splitter (Table + Inspector)
        splitter = QSplitter(Qt.Horizontal)
        body_layout.addWidget(splitter)

        # Central panel
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(24, 20, 24, 20)
        center_layout.setSpacing(16)

        # Top Section: Two-tier View Header
        header_row = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)

        self.view_title = QLabel("All Updates")
        self.view_title.setStyleSheet("font-size: 20px; font-weight: 700; color: #f8fafc; letter-spacing: -0.3px;")
        self.status_label = QLabel("Scanning system for updates...")
        self.status_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 400;")
        header_text_layout.addWidget(self.view_title)
        header_text_layout.addWidget(self.status_label)
        header_row.addLayout(header_text_layout)

        header_row.addStretch()

        self.refresh_btn = QPushButton("Check for Updates")
        self.refresh_btn.clicked.connect(self.start_scan)
        header_row.addWidget(self.refresh_btn)

        self.update_all_btn = QPushButton("Update All")
        self.update_all_btn.setObjectName("primaryBtn")
        self.update_all_btn.clicked.connect(self.update_all)
        header_row.addWidget(self.update_all_btn)

        center_layout.addLayout(header_row)

        # Tier 2: Search & Filter Toolbar
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter packages...")
        self.search_input.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self.search_input)

        self.filter_updates_btn = QPushButton("Updates only")
        self.filter_updates_btn.setCheckable(True)
        self.filter_updates_btn.toggled.connect(self._toggle_updates_only)
        filter_row.addWidget(self.filter_updates_btn)

        center_layout.addLayout(filter_row)

        # Table of items
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["", "Package", "Ecosystem", "Installed", "Latest", "Status"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 32)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 90)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 110)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 110)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 140)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setShowGrid(False)
        self.table.itemSelectionChanged.connect(self._on_table_selection)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        center_layout.addWidget(self.table)

        # History table widget
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Timestamp", "Package", "From", "To", "Result"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.verticalHeader().setDefaultSectionSize(36)
        self.history_table.setShowGrid(False)
        self.history_table.setVisible(False)
        center_layout.addWidget(self.history_table)

        splitter.addWidget(center_widget)

        # 3. Right Inspector Pane
        self.inspector = QWidget()
        self.inspector.setObjectName("inspectorPane")
        self.inspector.setFixedWidth(310)
        inspector_layout = QVBoxLayout(self.inspector)
        inspector_layout.setContentsMargins(18, 20, 18, 20)
        inspector_layout.setSpacing(12)

        inspector_title = QLabel("Package Details")
        inspector_title.setStyleSheet("font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; color: #64748b;")
        inspector_layout.addWidget(inspector_title)

        self.detail_name = QLabel("No item selected")
        self.detail_name.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        inspector_layout.addWidget(self.detail_name)

        self.detail_eco = QLabel("")
        self.detail_eco.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; text-transform: uppercase;")
        inspector_layout.addWidget(self.detail_eco)

        # Version Comparison Card
        ver_card = QWidget()
        ver_card.setStyleSheet("background-color: #090a0d; border: 1px solid #1a1e27; border-radius: 6px;")
        ver_card_layout = QHBoxLayout(ver_card)
        ver_card_layout.setContentsMargins(10, 8, 10, 8)
        self.detail_version = QLabel("—  →  —")
        self.detail_version.setStyleSheet("color: #94a3b8; font-size: 12px; font-family: monospace; border: none; background: transparent;")
        ver_card_layout.addWidget(self.detail_version)
        inspector_layout.addWidget(ver_card)

        self.detail_desc = QLabel("")
        self.detail_desc.setWordWrap(True)
        self.detail_desc.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4;")
        inspector_layout.addWidget(self.detail_desc)

        cmd_label = QLabel("Update Command")
        cmd_label.setStyleSheet("font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; margin-top: 6px;")
        inspector_layout.addWidget(cmd_label)

        self.cmd_box = QTextEdit()
        self.cmd_box.setReadOnly(True)
        self.cmd_box.setMaximumHeight(65)
        inspector_layout.addWidget(self.cmd_box)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.copy_cmd_btn = QPushButton("Copy")
        self.copy_cmd_btn.clicked.connect(self._copy_command)
        btn_row.addWidget(self.copy_cmd_btn)

        self.pin_btn = QPushButton("Pin")
        self.pin_btn.clicked.connect(self._toggle_pin_selected)
        btn_row.addWidget(self.pin_btn)
        inspector_layout.addLayout(btn_row)

        self.update_single_btn = QPushButton("Update Package")
        self.update_single_btn.setObjectName("primaryBtn")
        self.update_single_btn.clicked.connect(self.update_selected)
        inspector_layout.addWidget(self.update_single_btn)

        inspector_layout.addStretch()
        splitter.addWidget(self.inspector)

        root_layout.addWidget(body_widget)

        # Bottom SizeGrip
        grip_layout = QHBoxLayout()
        grip_layout.setContentsMargins(0, 0, 2, 2)
        grip_layout.addStretch()
        grip = QSizeGrip(self)
        grip_layout.addWidget(grip)
        root_layout.addLayout(grip_layout)

    def set_items(self, items: list[InstalledItem]):
        self.items = items
        self.store.apply_preferences(self.items)
        self._populate_table()
        outdated_count = sum(1 for i in self.items if i.status == Status.OUTDATED)
        self.update_all_btn.setText(f"Update All ({outdated_count})" if outdated_count else "Update All")
        self.status_label.setText(f"{len(self.items)} items discovered ({outdated_count} updates available)")

    def _populate_table(self):
        self.table.setRowCount(0)
        for row_idx, item in enumerate(self.items):
            self.table.insertRow(row_idx)

            # Star
            star_item = QTableWidgetItem("★" if item.is_favorite else "☆")
            star_item.setTextAlignment(Qt.AlignCenter)
            star_item.setForeground(QColor("#eab308" if item.is_favorite else "#334155"))
            self.table.setItem(row_idx, 0, star_item)

            # Name
            name_item = QTableWidgetItem(item.name)
            name_item.setData(Qt.UserRole, item.id)
            name_item.setForeground(QColor("#f8fafc"))
            self.table.setItem(row_idx, 1, name_item)

            # Ecosystem
            eco_item = QTableWidgetItem(item.ecosystem.upper())
            eco_item.setTextAlignment(Qt.AlignCenter)
            eco_item.setForeground(QColor("#64748b"))
            self.table.setItem(row_idx, 2, eco_item)

            # Installed
            inst_item = QTableWidgetItem(item.installed_version or "—")
            inst_item.setForeground(QColor("#94a3b8"))
            self.table.setItem(row_idx, 3, inst_item)

            # Latest
            latest_item = QTableWidgetItem(item.latest_version or "—")
            latest_item.setForeground(QColor("#f8fafc" if item.status == Status.OUTDATED else "#64748b"))
            self.table.setItem(row_idx, 4, latest_item)

            # Status Chip
            status_item = QTableWidgetItem(item.status.value)
            if item.status == Status.OUTDATED:
                status_item.setForeground(QColor("#f59e0b" if not item.is_major else "#f43f5e"))
                if item.is_major:
                    status_item.setText("Major update")
            elif item.status == Status.UP_TO_DATE:
                status_item.setForeground(QColor("#10b981"))
            elif item.status == Status.PINNED:
                status_item.setForeground(QColor("#64748b"))
            self.table.setItem(row_idx, 5, status_item)

        self._apply_filters()

    def _on_sidebar_changed(self, row: int):
        label, key = self.sidebar_items[row]
        if key == "Settings":
            self.open_settings()
            self.sidebar.setCurrentRow(self.last_sidebar_row)
            return

        self.last_sidebar_row = row
        self.view_title.setText(label)
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
            res_item = QTableWidgetItem("Success" if rec.success else "Failed")
            res_item.setForeground(QColor("#10b981" if rec.success else "#f43f5e"))
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
        self.detail_eco.setText(f"{item.category.value.upper()} • {item.ecosystem.upper()}")
        self.detail_version.setText(f"{item.installed_version or 'unknown'}  →  {item.latest_version or 'latest'}")
        self.detail_desc.setText(item.description or "No description provided.")
        self.cmd_box.setPlainText(item.update_command or "# No update command defined")
        self.pin_btn.setText("Unpin" if item.is_pinned else "Pin")
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
                self.table.item(row, 0).setForeground(QColor("#334155"))
            else:
                self.store.favorite(item.id)
                item.is_favorite = True
                self.table.item(row, 0).setText("★")
                self.table.item(row, 0).setForeground(QColor("#eab308"))

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
        outdated_count = sum(1 for i in self.items if i.status == Status.OUTDATED)
        if hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            self.tray_icon.setToolTip(f"UpdatyMeow - {outdated_count} update(s) available")
            settings = self.store.get_settings()
            if settings.get("notify_new_updates", True) and outdated_count > 0:
                if not self.isActiveWindow():
                    self.tray_icon.showMessage(
                        "Updates Available",
                        f"{outdated_count} software update(s) are ready to install.",
                        QSystemTrayIcon.Information,
                        5000,
                    )

    def open_settings(self):
        dlg = SettingsDialog(self, self.store)
        if dlg.exec_() == QDialog.Accepted:
            self._setup_timer()

    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon.fromTheme("system-software-update")
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.SP_ArrowUp)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("UpdatyMeow - Software Updates")

        tray_menu = QMenu()
        open_action = tray_menu.addAction("Open UpdatyMeow")
        open_action.triggered.connect(self._show_and_activate)
        check_action = tray_menu.addAction("Check for Updates")
        check_action.triggered.connect(self.start_scan)
        settings_action = tray_menu.addAction("Settings...")
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self._show_and_activate()

    def _show_and_activate(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        settings = self.store.get_settings()
        if settings.get("minimize_to_tray", True) and hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
        else:
            event.accept()

    def _setup_timer(self):
        settings = self.store.get_settings()
        interval = settings.get("check_interval", "6h")
        intervals_ms = {
            "6h": 6 * 3600 * 1000,
            "12h": 12 * 3600 * 1000,
            "24h": 24 * 3600 * 1000,
            "weekly": 7 * 24 * 3600 * 1000,
        }
        if interval in intervals_ms:
            self.auto_timer.setInterval(intervals_ms[interval])
            self.auto_timer.start()
        else:
            self.auto_timer.stop()

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
        needs_sudo = any(
            item.ecosystem in ("apt", "snap") or "sudo" in item.update_command or "pkexec" in item.update_command
            for item in items_to_update
        )

        sudo_password = None
        if needs_sudo:
            try:
                res = subprocess.run(["sudo", "-n", "true"], capture_output=True)
                has_cached_sudo = (res.returncode == 0)
            except Exception:
                has_cached_sudo = False

            if not has_cached_sudo:
                pwd, ok = QInputDialog.getText(
                    self,
                    "Authentication Required",
                    "Administrative privileges required for updating system packages.\nEnter sudo password:",
                    QLineEdit.Password,
                )
                if not ok or not pwd:
                    self.status_label.setText("Update cancelled: Sudo password required.")
                    return
                sudo_password = pwd

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

        worker = UpdateWorker(items_to_update, sudo_password=sudo_password)
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
            settings = self.store.get_settings()
            if settings.get("notify_updates_finished", True) and hasattr(self, "tray_icon") and self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    "Updates Completed",
                    "Finished installing selected software updates.",
                    QSystemTrayIcon.Information,
                    4000,
                )
            self.start_scan()

        worker.item_finished.connect(on_item_fin)
        worker.all_done.connect(on_all_done)
        worker.start()
        dlg.exec_()

