from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "Operasjonssentral V2"
CONFIG_FILE = "ops_v2_layout.json"
ACCENT = "#13e3c1"
BG = "#090d12"
PANEL = "#11161d"
PANEL_2 = "#151b23"
PANEL_3 = "#0d1319"
TEXT = "#e9f1f7"
MUTED = "#8793a1"
RED = "#ff4d5e"
AMBER = "#ffb547"
GREEN = "#2ad18b"
BLUE = "#3ea6ff"


@dataclass
class AssetFile:
    title: str
    path: str
    kind: str = "file"


@dataclass
class AppConfig:
    patropp_url: str = ""
    avtropp_url: str = ""
    assets: Optional[List[AssetFile]] = None
    fullscreen: bool = False

    def to_json(self) -> dict:
        return {
            "patropp_url": self.patropp_url,
            "avtropp_url": self.avtropp_url,
            "assets": [asdict(a) for a in (self.assets or [])],
            "fullscreen": self.fullscreen,
        }

    @classmethod
    def from_json(cls, data: dict) -> "AppConfig":
        assets = [AssetFile(**a) for a in data.get("assets", [])]
        return cls(
            patropp_url=data.get("patropp_url", ""),
            avtropp_url=data.get("avtropp_url", ""),
            assets=assets,
            fullscreen=data.get("fullscreen", False),
        )


def load_config() -> AppConfig:
    path = Path(CONFIG_FILE)
    if not path.exists():
        return AppConfig(assets=[])
    try:
        return AppConfig.from_json(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return AppConfig(assets=[])


def save_config(config: AppConfig) -> None:
    Path(CONFIG_FILE).write_text(
        json.dumps(config.to_json(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def make_icon(char: str, color: str = ACCENT, size: int = 22) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor(color))
    font = QFont("Arial", max(10, size - 6))
    painter.setFont(font)
    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, char)
    painter.end()
    return QIcon(pix)


class SectionTitle(QWidget):
    def __init__(self, title: str, subtitle: str = "") -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("sectionSubtitle")
            layout.addWidget(sub)


class StatCard(QFrame):
    def __init__(self, icon: str, title: str, value: str, subtitle: str, color: str) -> None:
        super().__init__()
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        top = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setObjectName("statIcon")
        icon_label.setStyleSheet(f"color: {color};")
        top.addWidget(icon_label)
        top.addStretch()
        layout.addLayout(top)

        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        layout.addWidget(title_label)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        layout.addWidget(self.value_label)

        sub = QLabel(subtitle)
        sub.setObjectName("statSubtitle")
        layout.addWidget(sub)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class ToolbarButton(QPushButton):
    def __init__(self, text: str, icon_char: str) -> None:
        super().__init__(text)
        self.setIcon(make_icon(icon_char))
        self.setIconSize(QSize(18, 18))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("toolbarButton")


class SidebarNavButton(QPushButton):
    def __init__(self, text: str, icon_char: str) -> None:
        super().__init__(text)
        self.setIcon(make_icon(icon_char))
        self.setIconSize(QSize(18, 18))
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("navButton")
        self.setMinimumHeight(46)


class MonitorTile(QFrame):
    clicked = Signal()

    def __init__(self, title: str, subtitle: str, status: str = "LIVE") -> None:
        super().__init__()
        self.setObjectName("monitorTile")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(210)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        top = QHBoxLayout()
        badge = QLabel(status)
        badge.setObjectName("badge")
        top.addWidget(badge)
        top.addStretch()
        ts = QLabel(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        ts.setObjectName("tileTimestamp")
        top.addWidget(ts)
        layout.addLayout(top)

        view = QFrame()
        view.setObjectName("monitorViewport")
        view_layout = QVBoxLayout(view)
        view_layout.setContentsMargins(0, 0, 0, 0)
        view_layout.addStretch()
        center = QLabel("Videovegg / dokumentflate")
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.setObjectName("monitorPlaceholder")
        view_layout.addWidget(center)
        view_layout.addStretch()
        layout.addWidget(view, 1)

        bottom = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("monitorTitle")
        bottom.addWidget(title_label)
        bottom.addStretch()
        sub = QLabel(subtitle)
        sub.setObjectName("monitorSubtitle")
        bottom.addWidget(sub)
        layout.addLayout(bottom)

    def mousePressEvent(self, event):  # noqa: N802
        self.clicked.emit()
        super().mousePressEvent(event)


class DataTable(QTableWidget):
    def __init__(self, headers: List[str]) -> None:
        super().__init__(0, len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setMinimumSectionSize(40)
        self.horizontalHeader().setDefaultSectionSize(120)
        self.setObjectName("dataTable")

    def load_rows(self, rows: List[List[str]], alarm_rows: Optional[List[int]] = None, blink: bool = False) -> None:
        self.setRowCount(len(rows))
        alarm_rows = alarm_rows or []
        for row_idx, row in enumerate(rows):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                if row_idx in alarm_rows:
                    item.setForeground(QColor("#ffe9ec"))
                    item.setBackground(QColor("#7a1626" if blink else "#451019"))
                else:
                    item.setForeground(QColor(TEXT))
                    item.setBackground(QColor(PANEL_2))
                self.setItem(row_idx, col_idx, item)
        self.resizeRowsToContents()


class AssetsPanel(QFrame):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(SectionTitle("Eventfiler", "Sambandsdiagram, gridkart, planverk og operative dokumenter"))
        header.addStretch()
        add_btn = ToolbarButton("Legg til filer", "+")
        add_btn.clicked.connect(self.add_files)
        header.addWidget(add_btn)
        layout.addLayout(header)

        body = QSplitter(Qt.Orientation.Horizontal)
        body.setChildrenCollapsible(False)
        body.setHandleWidth(1)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("assetList")
        self.list_widget.currentRowChanged.connect(self.show_asset)
        body.addWidget(self.list_widget)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setObjectName("assetPreview")
        body.addWidget(self.preview)
        body.setSizes([240, 700])
        layout.addWidget(body, 1)

        self.refresh_list()

    def add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Velg eventfiler",
            "",
            "Alle filer (*.*)",
        )
        if not paths:
            return
        self.config.assets = self.config.assets or []
        for path in paths:
            self.config.assets.append(AssetFile(title=Path(path).name, path=path))
        save_config(self.config)
        self.refresh_list()

    def refresh_list(self) -> None:
        self.list_widget.clear()
        for asset in self.config.assets or []:
            item = QListWidgetItem(make_icon("▣"), asset.title)
            item.setToolTip(asset.path)
            self.list_widget.addItem(item)
        if self.list_widget.count() and self.list_widget.currentRow() < 0:
            self.list_widget.setCurrentRow(0)

    def show_asset(self, index: int) -> None:
        assets = self.config.assets or []
        if index < 0 or index >= len(assets):
            self.preview.clear()
            return
        asset = assets[index]
        suffix = Path(asset.path).suffix.lower()
        try:
            if suffix in {".txt", ".md", ".csv", ".json", ".log"}:
                content = Path(asset.path).read_text(encoding="utf-8", errors="replace")
                self.preview.setPlainText(content[:80000])
            else:
                self.preview.setPlainText(
                    f"Fil: {asset.path}\n\n"
                    "Denne v2-visningen viser tekstinnhold direkte.\n"
                    "Neste steg er innebygd PDF- og bildefremviser i samme layout."
                )
        except Exception as exc:
            self.preview.setPlainText(f"Kunne ikke åpne filen.\n\n{exc}")


class OperationsCenterWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.blink = False
        self.setWindowTitle(APP_NAME)
        self.resize(1680, 980)
        self.setMinimumSize(1360, 820)

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_blink)
        self.blink_timer.start(700)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.mock_refresh)
        self.refresh_timer.start(5000)

        self.build_ui()
        self.apply_styles()
        self.mock_refresh()

        if self.config.fullscreen:
            self.showFullScreen()

    def build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        shell = QHBoxLayout(central)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.sidebar = self.build_sidebar()
        shell.addWidget(self.sidebar)

        self.main = QWidget()
        shell.addWidget(self.main, 1)
        main_layout = QVBoxLayout(self.main)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(14)

        main_layout.addLayout(self.build_topbar())
        main_layout.addLayout(self.build_stat_row())

        self.stack = QStackedWidget()
        self.dashboard_page = self.build_dashboard_page()
        self.assets_page = self.build_assets_page()
        self.settings_page = self.build_settings_page()
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.assets_page)
        self.stack.addWidget(self.settings_page)
        main_layout.addWidget(self.stack, 1)

    def build_sidebar(self) -> QWidget:
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(300)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(14)

        top = QHBoxLayout()
        logo = QLabel("⟵")
        logo.setObjectName("brandArrow")
        top.addWidget(logo)
        brand = QLabel("B-NODE // OPS")
        brand.setObjectName("brandTitle")
        top.addWidget(brand)
        top.addStretch()
        tune = QLabel("⚙")
        tune.setObjectName("brandTune")
        top.addWidget(tune)
        layout.addLayout(top)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Søk navn, samband, team eller område")
        self.search.setObjectName("searchInput")
        layout.addWidget(self.search)

        self.nav_dashboard = SidebarNavButton("Operasjonssentral", "◫")
        self.nav_assets = SidebarNavButton("Eventfiler", "▣")
        self.nav_settings = SidebarNavButton("Innstillinger", "⚙")
        self.nav_dashboard.setChecked(True)

        self.nav_dashboard.clicked.connect(lambda: self.switch_page(0))
        self.nav_assets.clicked.connect(lambda: self.switch_page(1))
        self.nav_settings.clicked.connect(lambda: self.switch_page(2))

        layout.addWidget(self.nav_dashboard)
        layout.addWidget(self.nav_assets)
        layout.addWidget(self.nav_settings)

        ops_title = QLabel("OPERATIVE SONER")
        ops_title.setObjectName("sideGroupTitle")
        layout.addWidget(ops_title)

        for text in [
            "Samband / sentral",
            "Grid og områdekart",
            "Innsjekk / utsjekk",
            "Forsinkede vakter",
            "Logg og hendelser",
        ]:
            btn = QPushButton(text)
            btn.setObjectName("sideItem")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)

        layout.addStretch()

        footer = QLabel("Mørk operasjonssentral-layout uten lyse borders.\nV2 PySide6 prototype.")
        footer.setObjectName("sideFooter")
        layout.addWidget(footer)
        return side

    def build_topbar(self):
        layout = QHBoxLayout()
        left = SectionTitle("Video wall / operasjonssentral", "Moderne layout inspirert av overvåkningssystemer og hendelsesrom")
        layout.addWidget(left)
        layout.addStretch()

        for text, icon in [
            ("Oppdater nå", "↻"),
            ("Layout", "◫"),
            ("Fullskjerm", "⛶"),
        ]:
            btn = ToolbarButton(text, icon)
            if text == "Oppdater nå":
                btn.clicked.connect(self.mock_refresh)
            elif text == "Fullskjerm":
                btn.clicked.connect(self.toggle_fullscreen)
            layout.addWidget(btn)
        return layout

    def build_stat_row(self):
        layout = QHBoxLayout()
        layout.setSpacing(12)
        self.card_on = StatCard("◉", "PÅ JOBB", "0", "Skannet inn og aktiv nå", GREEN)
        self.card_soon = StatCard("◷", "KOMMER SNART", "0", "Starter innen 30–60 min", BLUE)
        self.card_late = StatCard("⚠", "FORSINKET", "0", "Mangler skann / krever oppfølging", RED)
        self.card_off = StatCard("↘", "AVTROPP", "0", "Troppet av siste 10 min", AMBER)
        for card in [self.card_on, self.card_soon, self.card_late, self.card_off]:
            layout.addWidget(card, 1)
        return layout

    def build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        video_panel = QFrame()
        video_panel.setObjectName("panel")
        vp_layout = QVBoxLayout(video_panel)
        vp_layout.setContentsMargins(16, 16, 16, 16)
        vp_layout.setSpacing(12)
        vp_layout.addWidget(SectionTitle("Videovegg og operative flater", "Kamera, oversiktsflater, dokumentruter og situasjonsbilder"))

        grid = QGridLayout()
        grid.setSpacing(12)
        self.tiles = [
            MonitorTile("Sektor A", "Inngang nord"),
            MonitorTile("Sektor B", "Backstage"),
            MonitorTile("Gridkart", "Operativ oversikt", "DOC"),
            MonitorTile("Sambandsdiagram", "Kanalstruktur", "DOC"),
        ]
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for tile, (r, c) in zip(self.tiles, positions):
            grid.addWidget(tile, r, c)
        vp_layout.addLayout(grid)
        left_layout.addWidget(video_panel, 2)

        late_panel = QFrame()
        late_panel.setObjectName("panel")
        lp_layout = QVBoxLayout(late_panel)
        lp_layout.setContentsMargins(16, 16, 16, 16)
        lp_layout.setSpacing(10)
        lp_layout.addWidget(SectionTitle("Forsinket / mangler skann", "Rød alarmvisning med blink og prioritert oppfølging"))
        self.late_table = DataTable(["Alarm", "Navn", "Samband", "Team", "Område", "Planlagt", "Forsinket"])
        lp_layout.addWidget(self.late_table)
        left_layout.addWidget(late_panel, 1)

        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        roster_panel = QFrame()
        roster_panel.setObjectName("panel")
        rp_layout = QVBoxLayout(roster_panel)
        rp_layout.setContentsMargins(16, 16, 16, 16)
        rp_layout.setSpacing(10)
        rp_layout.addWidget(SectionTitle("Statusoversikt", "På jobb nå og hvem som kommer snart"))
        self.status_table = DataTable(["Status", "Navn", "Samband", "Team", "Område", "Tid"])
        rp_layout.addWidget(self.status_table)
        right_layout.addWidget(roster_panel, 1)

        recent_panel = QFrame()
        recent_panel.setObjectName("panel")
        rc_layout = QVBoxLayout(recent_panel)
        rc_layout.setContentsMargins(16, 16, 16, 16)
        rc_layout.setSpacing(10)
        rc_layout.addWidget(SectionTitle("Troppet av siste 10 min", "Nylig avsluttet vakt / skannet ut"))
        self.off_table = DataTable(["Navn", "Samband", "Team", "Område", "Avtropp"])
        rc_layout.addWidget(self.off_table)
        right_layout.addWidget(recent_panel, 1)

        log_panel = QFrame()
        log_panel.setObjectName("panel")
        lg_layout = QVBoxLayout(log_panel)
        lg_layout.setContentsMargins(16, 16, 16, 16)
        lg_layout.setSpacing(10)
        lg_layout.addWidget(SectionTitle("Hendelseslogg", "Varsler, systemhendelser og operatørnotater"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setObjectName("logView")
        lg_layout.addWidget(self.log)
        right_layout.addWidget(log_panel, 1)

        splitter.addWidget(right)
        splitter.setSizes([980, 580])
        layout.addWidget(splitter)
        return page

    def build_assets_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.assets_panel = AssetsPanel(self.config)
        layout.addWidget(self.assets_panel)
        return page

    def build_settings_page(self) -> QWidget:
        page = QFrame()
        page.setObjectName("panel")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.addWidget(SectionTitle("Innstillinger", "Datakilder, URL-er og systemvalg for operasjonssentralen"))

        self.patropp_input = QLineEdit(self.config.patropp_url)
        self.patropp_input.setPlaceholderText("URL til påtropp-fil")
        self.patropp_input.setObjectName("searchInput")
        layout.addWidget(QLabel("Påtropp-URL"))
        layout.addWidget(self.patropp_input)

        self.avtropp_input = QLineEdit(self.config.avtropp_url)
        self.avtropp_input.setPlaceholderText("URL til avtropp-fil")
        self.avtropp_input.setObjectName("searchInput")
        layout.addWidget(QLabel("Avtropp-URL"))
        layout.addWidget(self.avtropp_input)

        buttons = QHBoxLayout()
        save_btn = ToolbarButton("Lagre innstillinger", "✓")
        save_btn.clicked.connect(self.save_settings)
        buttons.addWidget(save_btn)
        test_btn = ToolbarButton("Test oppsett", "↻")
        test_btn.clicked.connect(self.test_settings)
        buttons.addWidget(test_btn)
        buttons.addStretch()
        layout.addLayout(buttons)
        layout.addStretch()
        return page

    def apply_styles(self) -> None:
        self.setStyleSheet(
            f"""
            * {{
                color: {TEXT};
                font-family: Inter, Segoe UI, Arial, sans-serif;
                font-size: 13px;
                outline: none;
                border: none;
            }}
            QMainWindow, QWidget {{
                background: {BG};
            }}
            #sidebar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #171b22, stop:1 #11161c);
                border-right: 1px solid #1a212a;
            }}
            #brandArrow {{
                color: {ACCENT};
                font-size: 26px;
                font-weight: 700;
            }}
            #brandTitle {{
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
            #brandTune {{
                color: {ACCENT};
                font-size: 18px;
            }}
            #searchInput {{
                background: #1a2028;
                border-radius: 12px;
                padding: 14px 14px;
                color: {TEXT};
                selection-background-color: #21414e;
            }}
            #navButton, #sideItem {{
                background: #131920;
                color: {TEXT};
                text-align: left;
                padding: 12px 14px;
                border-radius: 12px;
            }}
            #navButton:checked {{
                background: #18242a;
                color: {ACCENT};
            }}
            #navButton:hover, #sideItem:hover, #toolbarButton:hover {{
                background: #1a222c;
            }}
            #toolbarButton {{
                background: #171d25;
                border-radius: 12px;
                padding: 12px 14px;
                color: {TEXT};
            }}
            #sideGroupTitle {{
                color: {MUTED};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.8px;
                margin-top: 6px;
            }}
            #sideFooter {{
                color: {MUTED};
                font-size: 12px;
                line-height: 1.4;
            }}
            #sectionTitle {{
                font-size: 24px;
                font-weight: 700;
            }}
            #sectionSubtitle {{
                color: {MUTED};
                font-size: 13px;
            }}
            #statCard, #panel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PANEL}, stop:1 {PANEL_2});
                border-radius: 18px;
            }}
            #statIcon {{
                font-size: 22px;
                font-weight: 700;
            }}
            #statTitle {{
                color: {MUTED};
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
            #statValue {{
                font-size: 36px;
                font-weight: 800;
            }}
            #statSubtitle {{
                color: {MUTED};
                font-size: 12px;
            }}
            #monitorTile {{
                background: #0f141b;
                border-radius: 16px;
            }}
            #monitorViewport {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:1.0, stop:0 #16222b, stop:1 #0b1016);
                border-radius: 14px;
            }}
            #monitorPlaceholder {{
                color: #667281;
                font-size: 16px;
                font-weight: 600;
            }}
            #monitorTitle {{
                font-size: 14px;
                font-weight: 700;
            }}
            #monitorSubtitle {{
                color: {MUTED};
                font-size: 12px;
            }}
            #badge {{
                background: rgba(19, 227, 193, 0.14);
                color: {ACCENT};
                border-radius: 10px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 700;
            }}
            #tileTimestamp {{
                color: {MUTED};
                font-size: 11px;
            }}
            #assetList, #assetPreview, #logView, #dataTable {{
                background: {PANEL_3};
                border-radius: 14px;
            }}
            QListWidget::item {{
                background: #111821;
                margin: 4px;
                padding: 12px;
                border-radius: 12px;
            }}
            QListWidget::item:selected {{
                background: #17242c;
                color: {ACCENT};
            }}
            QHeaderView::section {{
                background: #17202a;
                color: {MUTED};
                padding: 10px;
                border: none;
                font-size: 11px;
                font-weight: 700;
            }}
            QTableWidget {{
                gridline-color: transparent;
                padding: 6px;
            }}
            QTableCornerButton::section {{
                background: #17202a;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 6px 0 6px 0;
            }}
            QScrollBar::handle:vertical {{
                background: #25303d;
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
                height: 0px;
            }}
            """
        )

    def switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.nav_dashboard.setChecked(index == 0)
        self.nav_assets.setChecked(index == 1)
        self.nav_settings.setChecked(index == 2)

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            self.config.fullscreen = False
        else:
            self.showFullScreen()
            self.config.fullscreen = True
        save_config(self.config)

    def save_settings(self) -> None:
        self.config.patropp_url = self.patropp_input.text().strip()
        self.config.avtropp_url = self.avtropp_input.text().strip()
        save_config(self.config)
        QMessageBox.information(self, APP_NAME, "Innstillinger lagret.")

    def test_settings(self) -> None:
        QMessageBox.information(
            self,
            APP_NAME,
            "Neste steg i v2 er å koble til Excel-lesing, SharePoint/OneDrive-støtte og sanntidsfiltrering direkte i denne PySide6-layouten.",
        )

    def toggle_blink(self) -> None:
        self.blink = not self.blink
        self.load_demo_tables()

    def append_log(self, text: str) -> None:
        stamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        self.log.append(f"[{stamp}] {text}")

    def mock_refresh(self) -> None:
        self.card_on.set_value("18")
        self.card_soon.set_value("7")
        self.card_late.set_value("3")
        self.card_off.set_value("5")
        self.load_demo_tables()
        self.append_log("Sanntidsvisning oppdatert. Demo-data lastet i PySide6-layout.")

    def load_demo_tables(self) -> None:
        self.status_table.load_rows([
            ["PÅ", "Mats Hansen", "21", "Sikkerhet", "Nord", "10:12"],
            ["PÅ", "Lina Solberg", "14", "Samband", "Sentral", "10:09"],
            ["SNART", "Eirik Nilsen", "33", "Vertsservice", "Vest", "10:45"],
            ["SNART", "Sara Berg", "18", "Medisinsk", "Scene", "10:52"],
        ])

        self.late_table.load_rows(
            [
                ["🚨", "Andreas Vik", "11", "Sikkerhet", "Backstage", "10:05", "18 min"],
                ["🚨", "Julie Moe", "27", "Samband", "Nordport", "10:10", "13 min"],
                ["🚨", "Robin Dahl", "42", "Vakt", "Camp", "10:12", "11 min"],
            ],
            alarm_rows=[0, 1, 2],
            blink=self.blink,
        )

        self.off_table.load_rows([
            ["Kaja Lien", "08", "Medisinsk", "Sør", "10:16"],
            ["Ola Haug", "29", "Logistikk", "Lager", "10:14"],
            ["Nina Klev", "07", "Vertsservice", "Inngang øst", "10:11"],
        ])


def main() -> None:
    from main_window import APP_NAME as NEW_APP_NAME
    from main_window import OperationsCenterWindow as NewOperationsCenterWindow

    app = QApplication(sys.argv)
    app.setApplicationName(NEW_APP_NAME)
    window = NewOperationsCenterWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
