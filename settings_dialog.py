from __future__ import annotations

from typing import Dict, List

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from data_loader import get_excel_headers, infer_column_mapping
from models import AppConfig, AssetFile


COLUMN_FIELDS = [
    ("name", "Navn"),
    ("radio", "Sambandsnummer"),
    ("team", "Team"),
    ("area", "Område"),
    ("planned_on", "Planlagt Påtropp"),
    ("planned_off", "Planlagt Avtropp"),
    ("actual_on", "Skannet Påtropp"),
    ("actual_off", "Avtropp"),
]


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Innstillinger")
        self.resize(880, 640)
        self.setObjectName("settingsDialog")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        header = QHBoxLayout()
        title_label = QLabel("Innstillinger")
        title_label.setObjectName("dialogTitle")
        header.addWidget(title_label)
        header.addStretch()
        root.addLayout(header)

        card = QWidget()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)

        tabs = QTabWidget()
        tabs.addTab(self._build_sources_tab(), "Datakilder")
        tabs.addTab(self._build_columns_tab(), "Kolonner")
        tabs.addTab(self._build_media_tab(), "Bilder/Dokumenter")
        tabs.addTab(self._build_branding_tab(), "Branding")
        tabs.addTab(self._build_account_tab(), "Konto / API")
        card_layout.addWidget(tabs)
        root.addWidget(card, 1)

        footer = QHBoxLayout()
        save_btn = QPushButton("Lagre")
        save_btn.setObjectName("primaryButton")
        cancel_btn = QPushButton("Avbryt")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        footer.addStretch()
        footer.addWidget(cancel_btn)
        footer.addWidget(save_btn)
        root.addLayout(footer)

    def _build_sources_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QLabel("Datakilder for Påtropp / Avtropp")
        header.setObjectName("dialogSectionLabel")
        layout.addWidget(header)

        card = QFrame()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        form = QFormLayout()

        self.patropp_url = QLineEdit(self.config.patropp_url)
        self.avtropp_url = QLineEdit(self.config.avtropp_url)
        self.patropp_sheet = QSpinBox()
        self.avtropp_sheet = QSpinBox()
        self.patropp_sheet.setRange(0, 99)
        self.avtropp_sheet.setRange(0, 99)
        self.patropp_sheet.setValue(self.config.patropp_sheet)
        self.avtropp_sheet.setValue(self.config.avtropp_sheet)

        self.patropp_url.setPlaceholderText("SharePoint-delingslenke eller lokal filsti")
        self.avtropp_url.setPlaceholderText("SharePoint-delingslenke eller lokal filsti")

        patropp_row = QHBoxLayout()
        patropp_row.addWidget(self.patropp_url, 1)
        patropp_btn = QPushButton("Bla gjennom")
        patropp_btn.clicked.connect(self._browse_patropp_file)
        patropp_row.addWidget(patropp_btn)

        avtropp_row = QHBoxLayout()
        avtropp_row.addWidget(self.avtropp_url, 1)
        avtropp_btn = QPushButton("Bla gjennom")
        avtropp_btn.clicked.connect(self._browse_avtropp_file)
        avtropp_row.addWidget(avtropp_btn)

        form.addRow("Påtropp URL/fil", patropp_row)
        form.addRow("Påtropp ark-indeks", self.patropp_sheet)
        form.addRow("Avtropp URL/fil", avtropp_row)
        form.addRow("Avtropp ark-indeks", self.avtropp_sheet)
        card_layout.addLayout(form)
        layout.addWidget(card)
        layout.addStretch()
        return tab

    def _browse_patropp_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Velg Påtropp-fil",
            "",
            "Datafiler (*.xlsx *.csv);;Alle filer (*.*)",
        )
        if path:
            self.patropp_url.setText(path)

    def _browse_avtropp_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Velg Avtropp-fil",
            "",
            "Datafiler (*.xlsx *.csv);;Alle filer (*.*)",
        )
        if path:
            self.avtropp_url.setText(path)

    def _build_columns_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QLabel("Kolonnemapping fra Excel-filene")
        header.setObjectName("dialogSectionLabel")
        layout.addWidget(header)

        card = QFrame()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        form = QFormLayout()

        # Forsøk å hente kolonnenavn fra en av datakildene (påtropp eller avtropp)
        headers: List[str] = []
        probe_source = self.config.patropp_url or self.config.avtropp_url
        probe_sheet = self.config.patropp_sheet if self.config.patropp_url else self.config.avtropp_sheet
        if probe_source:
            try:
                headers = get_excel_headers(probe_source, probe_sheet)
            except Exception:
                headers = []

        self.column_inputs: Dict[str, QComboBox] = {}
        for key, label in COLUMN_FIELDS:
            combo = QComboBox()
            combo.setEditable(False)
            combo.addItem("— Ikke brukt —", "")
            for h in headers:
                combo.addItem(h, h)
            current_value = self.config.columns.get(key, "")
            if current_value:
                idx = combo.findData(current_value)
                if idx < 0:
                    combo.addItem(current_value, current_value)
                    idx = combo.count() - 1
                combo.setCurrentIndex(idx)
            self.column_inputs[key] = combo
            form.addRow(label, combo)
        card_layout.addLayout(form)

        auto_row = QHBoxLayout()
        auto_patropp = QPushButton("Auto-map fra Påtropp")
        auto_avtropp = QPushButton("Auto-map fra Avtropp")
        auto_patropp.clicked.connect(self.auto_map_from_patropp)
        auto_avtropp.clicked.connect(self.auto_map_from_avtropp)
        auto_row.addWidget(auto_patropp)
        auto_row.addWidget(auto_avtropp)
        auto_row.addStretch()
        card_layout.addLayout(auto_row)

        layout.addWidget(card)
        layout.addStretch()
        return tab

    def _build_branding_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QLabel("Logoer og dashboard-tittel")
        header.setObjectName("dialogSectionLabel")
        layout.addWidget(header)

        card = QFrame()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        form = QFormLayout()

        self.logo_primary_input = QLineEdit(self.config.branding.get("logo_primary", ""))
        self.logo_secondary_input = QLineEdit(self.config.branding.get("logo_secondary", ""))
        self.logo_primary_input.setPlaceholderText("Filsti til primær logo")
        self.logo_secondary_input.setPlaceholderText("Filsti til sekundær logo")

        primary_row = QHBoxLayout()
        primary_row.addWidget(self.logo_primary_input, 1)
        primary_btn = QPushButton("Velg fil")
        primary_btn.clicked.connect(self._pick_logo_primary)
        primary_row.addWidget(primary_btn)

        secondary_row = QHBoxLayout()
        secondary_row.addWidget(self.logo_secondary_input, 1)
        secondary_btn = QPushButton("Velg fil")
        secondary_btn.clicked.connect(self._pick_logo_secondary)
        secondary_row.addWidget(secondary_btn)

        form.addRow("Primær logo", primary_row)
        form.addRow("Sekundær logo", secondary_row)

        self.layout_title_input = QLineEdit(self.config.layout.get("title", "OPD Dashboard"))
        form.addRow("Dashboard-tittel", self.layout_title_input)

        card_layout.addLayout(form)
        layout.addWidget(card)
        layout.addStretch()
        return tab

    def _build_account_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        header = QLabel("API-adresse for OPS Monitor (innlogging og brukere)")
        header.setObjectName("dialogSectionLabel")
        layout.addWidget(header)
        card = QFrame()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)
        card_layout.addWidget(QLabel("Base URL (f.eks. http://127.0.0.1:8000)"))
        self.api_base_url_input = QLineEdit(self.config.api_base_url)
        self.api_base_url_input.setPlaceholderText("http://127.0.0.1:8000")
        self.api_base_url_input.setObjectName("dialogInput")
        card_layout.addWidget(self.api_base_url_input)
        layout.addWidget(card)
        layout.addStretch()
        return tab

    def _build_media_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QLabel("Bilder og dokumenter til mediapanelet")
        header.setObjectName("dialogSectionLabel")
        layout.addWidget(header)

        card = QFrame()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        desc = QLabel("Disse filene blir tilgjengelige i modulen «Visning av bilder / dokumenter».")
        desc.setObjectName("welcomeSubtitle")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        self.media_list = QListWidget()
        self.media_list.setObjectName("mediaList")
        card_layout.addWidget(self.media_list, 1)

        for a in (self.config.assets or []):
            item = QListWidgetItem(a.title)
            item.setToolTip(a.path)
            self.media_list.addItem(item)

        buttons = QHBoxLayout()
        add_btn = QPushButton("Legg til filer")
        rm_btn = QPushButton("Fjern valgt")
        add_btn.clicked.connect(self._add_media_files)
        rm_btn.clicked.connect(self._remove_media_file)
        buttons.addWidget(add_btn)
        buttons.addWidget(rm_btn)
        buttons.addStretch()
        card_layout.addLayout(buttons)

        layout.addWidget(card)
        return tab

    def _add_media_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Velg bilder/dokumenter",
            "",
            "Filer (*.png *.jpg *.jpeg *.webp *.gif *.pdf *.txt *.md *.csv *.json *.log);;Alle filer (*.*)",
        )
        if not paths:
            return
        for p in paths:
            item = QListWidgetItem(p.split("/")[-1])
            item.setToolTip(p)
            self.media_list.addItem(item)

    def _remove_media_file(self) -> None:
        row = self.media_list.currentRow()
        if row >= 0:
            self.media_list.takeItem(row)

    def _pick_logo_primary(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Velg primær logo", "", "Bilder (*.png *.jpg *.jpeg *.svg)")
        if path:
            self.logo_primary_input.setText(path)

    def _pick_logo_secondary(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Velg sekundær logo", "", "Bilder (*.png *.jpg *.jpeg *.svg)")
        if path:
            self.logo_secondary_input.setText(path)

    def apply_to_config(self) -> None:
        self.config.patropp_url = self.patropp_url.text().strip()
        self.config.avtropp_url = self.avtropp_url.text().strip()
        self.config.patropp_sheet = self.patropp_sheet.value()
        self.config.avtropp_sheet = self.avtropp_sheet.value()
        # Lagre valgt kolonne-header per felt (tom streng betyr "ikke brukt")
        self.config.columns = {
            key: (widget.currentData() or "").strip()
            for key, widget in self.column_inputs.items()
        }
        assets = []
        for i in range(self.media_list.count()):
            item = self.media_list.item(i)
            if item and item.toolTip():
                assets.append(AssetFile(title=item.text(), path=item.toolTip(), kind="file"))
        self.config.assets = assets
        self.config.branding["logo_primary"] = self.logo_primary_input.text().strip()
        self.config.branding["logo_secondary"] = self.logo_secondary_input.text().strip()
        self.config.layout["title"] = self.layout_title_input.text().strip()
        if hasattr(self, "api_base_url_input"):
            self.config.api_base_url = self.api_base_url_input.text().strip() or "http://127.0.0.1:8000"

    def auto_map_from_patropp(self) -> None:
        self._auto_map(self.patropp_url.text().strip(), self.patropp_sheet.value())

    def auto_map_from_avtropp(self) -> None:
        self._auto_map(self.avtropp_url.text().strip(), self.avtropp_sheet.value())

    def _auto_map(self, source: str, sheet_index: int) -> None:
        if not source:
            QMessageBox.warning(self, "Innstillinger", "Legg inn URL/fil først.")
            return
        try:
            headers = get_excel_headers(source, sheet_index)
            current = {k: (v.currentData() or "").strip() for k, v in self.column_inputs.items()}
            mapped = infer_column_mapping(headers, current)
            for key, combo in self.column_inputs.items():
                target = mapped.get(key, "")
                if not target:
                    combo.setCurrentIndex(0)
                    continue
                idx = combo.findData(target)
                if idx < 0:
                    combo.addItem(target, target)
                    idx = combo.count() - 1
                combo.setCurrentIndex(idx)
            QMessageBox.information(self, "Innstillinger", "Kolonnemapping oppdatert.")
        except Exception as exc:
            QMessageBox.critical(self, "Innstillinger", f"Kunne ikke hente kolonner:\n{exc}")
