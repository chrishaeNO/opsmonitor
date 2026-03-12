from __future__ import annotations

import base64
from typing import Dict, List

from PySide6.QtCore import Qt, QPoint
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


def _decode_key_url(key: str) -> str | None:
    """Extract embedded server URL from an API key, or None if invalid."""
    parts = key.strip().split("_", 2)
    if len(parts) != 3 or parts[0] != "opsm":
        return None
    try:
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        url = base64.urlsafe_b64decode(padded).decode()
        return url.rstrip("/") if url.startswith("http") else None
    except Exception:
        return None


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
        # Frameless, avrundet dialog med custom chrome
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self._drag_pos: QPoint | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        header = QHBoxLayout()
        title_label = QLabel("Innstillinger")
        title_label.setObjectName("dialogTitle")
        header.addWidget(title_label)
        header.addStretch()
        # Tillat dra i header for å flytte dialogen
        self.header_widget = QLabel()  # bare et anker for event-filter
        self.header_widget.setVisible(False)
        root.addWidget(self.header_widget)
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

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _update_key_status(self, key: str) -> None:
        key = key.strip()
        if not key:
            self._key_status.setText("")
            return
        url = _decode_key_url(key)
        if url:
            self._key_status.setText(
                f"<span style='color:#34d399;'>&#10003; Server: <b>{url}</b></span>"
            )
        else:
            self._key_status.setText(
                "<span style='color:#f87171;'>&#10005; Ugyldig nøkkelformat "
                "(forventet <code>opsm_…</code>)</span>"
            )

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
        layout.setSpacing(12)

        # ── API-nøkkel (primary) ──────────────────────────────────────────
        key_header = QLabel("API-nøkkel (anbefalt)")
        key_header.setObjectName("dialogSectionLabel")
        layout.addWidget(key_header)

        key_card = QFrame()
        key_card.setObjectName("dialogCard")
        key_layout = QVBoxLayout(key_card)
        key_layout.setContentsMargins(14, 12, 14, 12)
        key_layout.setSpacing(8)

        key_desc = QLabel(
            "Lim inn API-nøkkelen fra admin-portalen (<i>/admin</i> → API-nøkler).\n"
            "Nøkkelen kobler desktop-appen til riktig organisasjon og server automatisk."
        )
        key_desc.setObjectName("welcomeSubtitle")
        key_desc.setWordWrap(True)
        key_layout.addWidget(key_desc)

        key_input_row = QHBoxLayout()
        self.api_key_input = QLineEdit(self.config.api_key)
        self.api_key_input.setPlaceholderText("opsm_…  (lim inn fra admin-portalen → API-nøkler)")
        self.api_key_input.setObjectName("dialogInput")
        self.api_key_input.setMinimumHeight(36)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_input_row.addWidget(self.api_key_input, 1)

        toggle_btn = QPushButton("Vis")
        toggle_btn.setFixedWidth(52)
        toggle_btn.setCheckable(True)
        toggle_btn.toggled.connect(
            lambda checked: self.api_key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        toggle_btn.toggled.connect(lambda checked: toggle_btn.setText("Skjul" if checked else "Vis"))
        key_input_row.addWidget(toggle_btn)
        key_layout.addLayout(key_input_row)

        # Live feedback: show decoded server URL when a valid key is pasted
        self._key_status = QLabel()
        self._key_status.setObjectName("welcomeSubtitle")
        self._key_status.setWordWrap(True)
        key_layout.addWidget(self._key_status)
        self._update_key_status(self.config.api_key)
        self.api_key_input.textChanged.connect(self._update_key_status)

        key_hint = QLabel(
            "Nøkkelen inneholder server-URL og kobler appen direkte — ingen manuell URL-konfigurasjon nødvendig.<br>"
            "Opprett nøkler på: "
            "<a href='https://opsmonitor-alpha.vercel.app/admin' style='color:#60a5fa;'>opsmonitor-alpha.vercel.app/admin</a>"
        )
        key_hint.setObjectName("welcomeSubtitle")
        key_hint.setOpenExternalLinks(True)
        key_hint.setWordWrap(True)
        key_layout.addWidget(key_hint)

        layout.addWidget(key_card)

        # ── Base URL (avansert / fallback) ────────────────────────────────
        url_header = QLabel("Server-URL (avansert)")
        url_header.setObjectName("dialogSectionLabel")
        layout.addWidget(url_header)

        url_card = QFrame()
        url_card.setObjectName("dialogCard")
        url_layout = QVBoxLayout(url_card)
        url_layout.setContentsMargins(14, 12, 14, 12)
        url_layout.setSpacing(8)

        url_desc = QLabel(
            "Brukes bare hvis du kjører en egendriftet OPS Monitor-backend.\n"
            "La feltet stå tomt for å bruke standardserveren."
        )
        url_desc.setObjectName("welcomeSubtitle")
        url_desc.setWordWrap(True)
        url_layout.addWidget(url_desc)

        self.api_base_url_input = QLineEdit(self.config.api_base_url)
        self.api_base_url_input.setPlaceholderText("https://opsmonitor-alpha.vercel.app")
        self.api_base_url_input.setObjectName("dialogInput")
        self.api_base_url_input.setMinimumHeight(36)
        url_layout.addWidget(self.api_base_url_input)

        layout.addWidget(url_card)
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
        if hasattr(self, "api_key_input"):
            self.config.api_key = self.api_key_input.text().strip()
        if hasattr(self, "api_base_url_input"):
            self.config.api_base_url = self.api_base_url_input.text().strip() or "https://opsmonitor-alpha.vercel.app"

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
