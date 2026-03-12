from __future__ import annotations

import base64
from typing import Dict, List

from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from data_loader import get_excel_headers, infer_column_mapping
from models import AppConfig, AssetFile


# ── Design system ─────────────────────────────────────────────────────────────
_STYLE = """
QDialog#sd_root {
    background: #0d1526;
    border: 1px solid rgba(148,163,184,0.14);
    border-radius: 12px;
}

/* Header */
QWidget#sd_header {
    background: #0d1526;
    border-radius: 12px 12px 0 0;
}
QLabel#sd_title {
    color: #f1f5f9;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: -0.1px;
}
QPushButton#sd_close {
    background: transparent;
    border: none;
    color: #475569;
    border-radius: 6px;
    font-size: 15px;
    padding: 0;
}
QPushButton#sd_close:hover { background: rgba(239,68,68,0.12); color: #ef4444; }

/* Dividers */
QFrame#sd_hdiv { background: rgba(148,163,184,0.09); border: none; }
QFrame#sd_vdiv { background: rgba(148,163,184,0.09); border: none; }

/* Sidebar */
QWidget#sd_sidebar { background: #080f1d; }
QPushButton#sd_nav {
    background: transparent;
    border: none;
    border-left: 2px solid transparent;
    color: #526070;
    text-align: left;
    padding: 7px 14px 7px 16px;
    font-size: 13px;
    font-weight: 500;
    border-radius: 0px;
}
QPushButton#sd_nav:hover {
    background: rgba(148,163,184,0.05);
    color: #94a3b8;
}
QPushButton#sd_nav:checked {
    background: rgba(59,130,246,0.09);
    color: #60a5fa;
    border-left-color: #3b82f6;
    font-weight: 600;
}

/* Scroll area */
QScrollArea#sd_scroll { background: #0d1526; border: none; }
QScrollArea#sd_scroll > QWidget { background: #0d1526; }
QScrollBar:vertical {
    background: transparent;
    width: 5px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(148,163,184,0.18);
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* Typography */
QLabel#sd_sec_title  { color: #f1f5f9; font-size: 15px; font-weight: 600; }
QLabel#sd_sec_desc   { color: #4e6072; font-size: 12px; }
QLabel#sd_field_lbl  { color: #94a3b8; font-size: 12px; font-weight: 500; }
QLabel#sd_field_hint { color: #374557; font-size: 11px; }

/* Inputs */
QLineEdit, QSpinBox, QComboBox {
    background: #131f33;
    border: 1px solid rgba(148,163,184,0.13);
    border-radius: 7px;
    color: #e2e8f0;
    padding: 0 10px;
    font-size: 13px;
    min-height: 36px;
    selection-background-color: #3b82f6;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #3b82f6;
    background: #16253d;
}
QLineEdit:disabled, QSpinBox:disabled { color: #374557; background: #0f1a2b; }
QComboBox::drop-down { border: none; width: 26px; }
QComboBox QAbstractItemView {
    background: #1e293b;
    border: 1px solid rgba(148,163,184,0.14);
    color: #e2e8f0;
    selection-background-color: #3b82f6;
    selection-color: white;
    outline: none;
    padding: 4px;
}
QSpinBox::up-button, QSpinBox::down-button { width: 18px; background: transparent; border: none; }

/* Card groups */
QWidget#sd_card {
    background: #111e31;
    border: 1px solid rgba(148,163,184,0.1);
    border-radius: 8px;
}

/* Buttons */
QPushButton#sd_ghost {
    background: transparent;
    border: 1px solid rgba(148,163,184,0.16);
    border-radius: 6px;
    color: #64748b;
    padding: 0 14px;
    min-height: 34px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton#sd_ghost:hover { background: rgba(148,163,184,0.07); color: #94a3b8; }
QPushButton#sd_ghost:pressed { background: rgba(148,163,184,0.12); }

QPushButton#sd_outline {
    background: transparent;
    border: 1px solid rgba(148,163,184,0.18);
    border-radius: 6px;
    color: #94a3b8;
    padding: 0 12px;
    min-height: 34px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton#sd_outline:hover { background: rgba(148,163,184,0.07); color: #e2e8f0; }

QPushButton#sd_primary {
    background: #2563eb;
    border: none;
    border-radius: 7px;
    color: white;
    padding: 0 22px;
    min-height: 36px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#sd_primary:hover { background: #1d4ed8; }
QPushButton#sd_primary:pressed { background: #1e40af; }

QPushButton#sd_danger {
    background: transparent;
    border: 1px solid rgba(239,68,68,0.2);
    border-radius: 6px;
    color: #f87171;
    padding: 0 12px;
    min-height: 34px;
    font-size: 12px;
}
QPushButton#sd_danger:hover { background: rgba(239,68,68,0.08); }

/* Media list */
QListWidget#sd_list {
    background: #131f33;
    border: 1px solid rgba(148,163,184,0.12);
    border-radius: 8px;
    color: #cbd5e1;
    font-size: 13px;
    outline: none;
    padding: 4px;
}
QListWidget#sd_list::item { padding: 5px 8px; border-radius: 5px; }
QListWidget#sd_list::item:selected { background: rgba(59,130,246,0.18); color: #93c5fd; }
QListWidget#sd_list::item:hover:!selected { background: rgba(148,163,184,0.05); }

/* Footer */
QWidget#sd_footer { background: #0d1526; border-radius: 0 0 12px 12px; }
"""


# ── Helpers ──────────────────────────────────────────────────────────────────
def _decode_key_url(key: str) -> str | None:
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
    ("name",        "Navn"),
    ("radio",       "Sambandsnummer"),
    ("team",        "Team"),
    ("area",        "Område"),
    ("planned_on",  "Planlagt Påtropp"),
    ("planned_off", "Planlagt Avtropp"),
    ("actual_on",   "Skannet Påtropp"),
    ("actual_off",  "Avtropp"),
]

_NAV_ITEMS = [
    ("Datakilder",    "datakilder"),
    ("Kolonner",      "kolonner"),
    ("Media",         "media"),
    ("Branding",      "branding"),
    ("Konto / API",   "konto"),
]


# ── Main dialog ───────────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Innstillinger")
        self.resize(900, 600)
        self.setObjectName("sd_root")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setStyleSheet(_STYLE)
        self._drag_pos: QPoint | None = None
        self._nav_btns: list[QPushButton] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(_hdiv())
        root.addWidget(self._build_body(), 1)
        root.addWidget(_hdiv())
        root.addWidget(self._build_footer())

        self._switch(0)

    # ── Drag support ─────────────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        super().mouseReleaseEvent(e)

    # ── Chrome ───────────────────────────────────────────────────────────────
    def _build_header(self) -> QWidget:
        w = QWidget()
        w.setObjectName("sd_header")
        w.setFixedHeight(52)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(22, 0, 14, 0)

        title = QLabel("Innstillinger")
        title.setObjectName("sd_title")

        close = QPushButton("✕")
        close.setObjectName("sd_close")
        close.setFixedSize(30, 30)
        close.clicked.connect(self.reject)

        lay.addWidget(title)
        lay.addStretch()
        lay.addWidget(close)
        return w

    def _build_body(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._build_sidebar())
        lay.addWidget(_vdiv())

        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_sources())
        self._stack.addWidget(self._page_columns())
        self._stack.addWidget(self._page_media())
        self._stack.addWidget(self._page_branding())
        self._stack.addWidget(self._page_account())
        lay.addWidget(self._stack, 1)
        return w

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sd_sidebar")
        sidebar.setFixedWidth(196)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 16, 0, 16)
        lay.setSpacing(1)

        for i, (label, _) in enumerate(_NAV_ITEMS):
            btn = QPushButton(label)
            btn.setObjectName("sd_nav")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=i: self._switch(idx))
            btn.setFixedHeight(36)
            lay.addWidget(btn)
            self._nav_btns.append(btn)

        lay.addStretch()
        return sidebar

    def _build_footer(self) -> QWidget:
        w = QWidget()
        w.setObjectName("sd_footer")
        w.setFixedHeight(60)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(22, 0, 22, 0)
        lay.setSpacing(10)

        cancel = QPushButton("Avbryt")
        cancel.setObjectName("sd_ghost")
        cancel.clicked.connect(self.reject)

        save = QPushButton("Lagre innstillinger")
        save.setObjectName("sd_primary")
        save.clicked.connect(self.accept)

        lay.addStretch()
        lay.addWidget(cancel)
        lay.addWidget(save)
        return w

    def _switch(self, idx: int) -> None:
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == idx)

    # ── Page builder helpers ──────────────────────────────────────────────────
    @staticmethod
    def _scroll_page(inner: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName("sd_scroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        return scroll

    @staticmethod
    def _sec_header(title: str, desc: str = "") -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 16)
        lay.setSpacing(3)
        t = QLabel(title)
        t.setObjectName("sd_sec_title")
        lay.addWidget(t)
        if desc:
            d = QLabel(desc)
            d.setObjectName("sd_sec_desc")
            d.setWordWrap(True)
            lay.addWidget(d)
        sep = _hdiv()
        sep.setContentsMargins(0, 8, 0, 0)
        lay.addWidget(sep)
        return w

    @staticmethod
    def _field(label: str, widget: QWidget, hint: str = "") -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        lbl = QLabel(label)
        lbl.setObjectName("sd_field_lbl")
        lay.addWidget(lbl)
        lay.addWidget(widget)
        if hint:
            h = QLabel(hint)
            h.setObjectName("sd_field_hint")
            h.setWordWrap(True)
            lay.addWidget(h)
        return w

    @staticmethod
    def _card(*fields: QWidget) -> QWidget:
        card = QWidget()
        card.setObjectName("sd_card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(14)
        for f in fields:
            lay.addWidget(f)
        return card

    @staticmethod
    def _inline(widget: QWidget, btn: QPushButton) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(widget, 1)
        row.addWidget(btn)
        w = QWidget()
        w.setLayout(row)
        return w

    # ── Pages ─────────────────────────────────────────────────────────────────
    def _page_sources(self) -> QScrollArea:
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)
        lay.addWidget(self._sec_header(
            "Datakilder",
            "Koble til Excel-filer eller SharePoint for Påtropp og Avtropp.",
        ))

        # Påtropp
        self.patropp_url = QLineEdit(self.config.patropp_url)
        self.patropp_url.setPlaceholderText("SharePoint-lenke eller lokal filsti")
        pa_btn = QPushButton("Bla gjennom")
        pa_btn.setObjectName("sd_outline")
        pa_btn.setFixedHeight(36)
        pa_btn.clicked.connect(self._browse_patropp_file)

        self.patropp_sheet = QSpinBox()
        self.patropp_sheet.setRange(0, 99)
        self.patropp_sheet.setValue(self.config.patropp_sheet)
        self.patropp_sheet.setFixedWidth(90)

        lay.addWidget(self._card(
            self._field("Påtropp – URL / filsti",  self._inline(self.patropp_url, pa_btn)),
            self._field("Påtropp – ark-indeks",     self.patropp_sheet,
                        "0 = første ark i filen"),
        ))

        # Avtropp
        self.avtropp_url = QLineEdit(self.config.avtropp_url)
        self.avtropp_url.setPlaceholderText("SharePoint-lenke eller lokal filsti")
        av_btn = QPushButton("Bla gjennom")
        av_btn.setObjectName("sd_outline")
        av_btn.setFixedHeight(36)
        av_btn.clicked.connect(self._browse_avtropp_file)

        self.avtropp_sheet = QSpinBox()
        self.avtropp_sheet.setRange(0, 99)
        self.avtropp_sheet.setValue(self.config.avtropp_sheet)
        self.avtropp_sheet.setFixedWidth(90)

        lay.addWidget(self._card(
            self._field("Avtropp – URL / filsti",   self._inline(self.avtropp_url, av_btn)),
            self._field("Avtropp – ark-indeks",     self.avtropp_sheet,
                        "0 = første ark i filen"),
        ))

        lay.addStretch()
        return self._scroll_page(inner)

    def _page_columns(self) -> QScrollArea:
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)
        lay.addWidget(self._sec_header(
            "Kolonnemapping",
            "Koble Excel-kolonner til feltene i OPS Monitor.",
        ))

        headers: List[str] = []
        probe = self.config.patropp_url or self.config.avtropp_url
        sheet = self.config.patropp_sheet if self.config.patropp_url else self.config.avtropp_sheet
        if probe:
            try:
                headers = get_excel_headers(probe, sheet)
            except Exception:
                pass

        self.column_inputs: Dict[str, QComboBox] = {}
        col_fields: list[QWidget] = []
        for key, label in COLUMN_FIELDS:
            combo = QComboBox()
            combo.setEditable(False)
            combo.addItem("— Ikke brukt —", "")
            for h in headers:
                combo.addItem(h, h)
            val = self.config.columns.get(key, "")
            if val:
                idx = combo.findData(val)
                if idx < 0:
                    combo.addItem(val, val)
                    idx = combo.count() - 1
                combo.setCurrentIndex(idx)
            self.column_inputs[key] = combo
            col_fields.append(self._field(label, combo))

        lay.addWidget(self._card(*col_fields))

        # Auto-map buttons
        btn_row = QHBoxLayout()
        auto_pa = QPushButton("Auto-map fra Påtropp")
        auto_av = QPushButton("Auto-map fra Avtropp")
        auto_pa.setObjectName("sd_ghost")
        auto_av.setObjectName("sd_ghost")
        auto_pa.clicked.connect(self.auto_map_from_patropp)
        auto_av.clicked.connect(self.auto_map_from_avtropp)
        btn_row.addWidget(auto_pa)
        btn_row.addWidget(auto_av)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        lay.addStretch()
        return self._scroll_page(inner)

    def _page_media(self) -> QScrollArea:
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)
        lay.addWidget(self._sec_header(
            "Media",
            "Bilder og dokumenter tilgjengelige i modulen «Visning av bilder / dokumenter».",
        ))

        self.media_list = QListWidget()
        self.media_list.setObjectName("sd_list")
        self.media_list.setMinimumHeight(220)
        for a in (self.config.assets or []):
            item = QListWidgetItem(a.title)
            item.setToolTip(a.path)
            self.media_list.addItem(item)

        lay.addWidget(self.media_list, 1)

        btns = QHBoxLayout()
        add_btn = QPushButton("+ Legg til filer")
        rm_btn  = QPushButton("Fjern valgt")
        add_btn.setObjectName("sd_outline")
        rm_btn.setObjectName("sd_danger")
        add_btn.clicked.connect(self._add_media_files)
        rm_btn.clicked.connect(self._remove_media_file)
        btns.addWidget(add_btn)
        btns.addWidget(rm_btn)
        btns.addStretch()
        lay.addLayout(btns)

        lay.addStretch()
        return self._scroll_page(inner)

    def _page_branding(self) -> QScrollArea:
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)
        lay.addWidget(self._sec_header(
            "Branding",
            "Logoer og dashboard-tittel.",
        ))

        self.logo_primary_input = QLineEdit(self.config.branding.get("logo_primary", ""))
        self.logo_primary_input.setPlaceholderText("Filsti til primær logo")
        p_btn = QPushButton("Velg fil")
        p_btn.setObjectName("sd_outline")
        p_btn.setFixedHeight(36)
        p_btn.clicked.connect(self._pick_logo_primary)

        self.logo_secondary_input = QLineEdit(self.config.branding.get("logo_secondary", ""))
        self.logo_secondary_input.setPlaceholderText("Filsti til sekundær logo")
        s_btn = QPushButton("Velg fil")
        s_btn.setObjectName("sd_outline")
        s_btn.setFixedHeight(36)
        s_btn.clicked.connect(self._pick_logo_secondary)

        self.layout_title_input = QLineEdit(self.config.layout.get("title", "OPD Dashboard"))
        self.layout_title_input.setPlaceholderText("OPD Dashboard")

        lay.addWidget(self._card(
            self._field("Primær logo",     self._inline(self.logo_primary_input, p_btn)),
            self._field("Sekundær logo",   self._inline(self.logo_secondary_input, s_btn)),
            self._field("Dashboard-tittel", self.layout_title_input),
        ))
        lay.addStretch()
        return self._scroll_page(inner)

    def _page_account(self) -> QScrollArea:
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)
        lay.addWidget(self._sec_header(
            "Konto / API",
            "Koble desktop-appen til organisasjonskontoen din med en API-nøkkel.",
        ))

        self.api_key_input = QLineEdit(self.config.api_key)
        self.api_key_input.setPlaceholderText("opsm_…  (hentes fra admin-portalen → API-nøkler)")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

        toggle = QPushButton("Vis")
        toggle.setObjectName("sd_outline")
        toggle.setFixedWidth(56)
        toggle.setFixedHeight(36)
        toggle.setCheckable(True)
        toggle.toggled.connect(
            lambda on: self.api_key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        toggle.toggled.connect(lambda on: toggle.setText("Skjul" if on else "Vis"))

        # Live server-URL feedback
        self._key_status = QLabel()
        self._key_status.setObjectName("sd_field_hint")
        self._key_status.setWordWrap(True)
        self._update_key_status(self.config.api_key)
        self.api_key_input.textChanged.connect(self._update_key_status)

        key_row = self._inline(self.api_key_input, toggle)

        hint = QLabel(
            "Nøkkelen er selvforsynt – den inneholder server-URL og organisasjonstilknytning. "
            "Opprett nøkler på: "
            "<a href='https://opsmonitor-alpha.vercel.app/admin'"
            " style='color:#60a5fa;text-decoration:none;'>"
            "opsmonitor-alpha.vercel.app/admin</a>"
        )
        hint.setObjectName("sd_field_hint")
        hint.setOpenExternalLinks(True)
        hint.setWordWrap(True)

        api_card = QWidget()
        api_card.setObjectName("sd_card")
        api_lay = QVBoxLayout(api_card)
        api_lay.setContentsMargins(16, 14, 16, 14)
        api_lay.setSpacing(10)
        api_lay.addWidget(self._field("API-nøkkel", key_row))
        api_lay.addWidget(self._key_status)
        api_lay.addWidget(hint)

        lay.addWidget(api_card)
        lay.addStretch()
        return self._scroll_page(inner)

    # ── Slot: key status ──────────────────────────────────────────────────────
    def _update_key_status(self, key: str) -> None:
        key = key.strip()
        if not key:
            self._key_status.setText("")
            return
        url = _decode_key_url(key)
        if url:
            self._key_status.setText(
                f"<span style='color:#34d399;'>&#10003;&nbsp;Server: <b>{url}</b></span>"
            )
        else:
            self._key_status.setText(
                "<span style='color:#f87171;'>&#10005;&nbsp;Ugyldig nøkkelformat "
                "(forventet <code>opsm_…</code>)</span>"
            )

    # ── File pickers ──────────────────────────────────────────────────────────
    def _browse_patropp_file(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Velg Påtropp-fil", "",
                                           "Datafiler (*.xlsx *.csv);;Alle (*.*)")
        if p:
            self.patropp_url.setText(p)

    def _browse_avtropp_file(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Velg Avtropp-fil", "",
                                           "Datafiler (*.xlsx *.csv);;Alle (*.*)")
        if p:
            self.avtropp_url.setText(p)

    def _add_media_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Velg bilder/dokumenter", "",
            "Filer (*.png *.jpg *.jpeg *.webp *.gif *.pdf *.txt *.md *.csv *.json *.log);;Alle (*.*)",
        )
        for p in paths:
            item = QListWidgetItem(p.split("/")[-1])
            item.setToolTip(p)
            self.media_list.addItem(item)

    def _remove_media_file(self) -> None:
        row = self.media_list.currentRow()
        if row >= 0:
            self.media_list.takeItem(row)

    def _pick_logo_primary(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Velg primær logo", "",
                                           "Bilder (*.png *.jpg *.jpeg *.svg)")
        if p:
            self.logo_primary_input.setText(p)

    def _pick_logo_secondary(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Velg sekundær logo", "",
                                           "Bilder (*.png *.jpg *.jpeg *.svg)")
        if p:
            self.logo_secondary_input.setText(p)

    # ── Column auto-map ───────────────────────────────────────────────────────
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

    # ── Save ──────────────────────────────────────────────────────────────────
    def apply_to_config(self) -> None:
        self.config.patropp_url   = self.patropp_url.text().strip()
        self.config.avtropp_url   = self.avtropp_url.text().strip()
        self.config.patropp_sheet = self.patropp_sheet.value()
        self.config.avtropp_sheet = self.avtropp_sheet.value()
        self.config.columns = {
            k: (w.currentData() or "").strip()
            for k, w in self.column_inputs.items()
        }
        assets = []
        for i in range(self.media_list.count()):
            item = self.media_list.item(i)
            if item and item.toolTip():
                assets.append(AssetFile(title=item.text(), path=item.toolTip(), kind="file"))
        self.config.assets = assets
        self.config.branding["logo_primary"]   = self.logo_primary_input.text().strip()
        self.config.branding["logo_secondary"] = self.logo_secondary_input.text().strip()
        self.config.layout["title"]            = self.layout_title_input.text().strip()
        if hasattr(self, "api_key_input"):
            self.config.api_key = self.api_key_input.text().strip()


# ── Divider factories ─────────────────────────────────────────────────────────
def _hdiv() -> QFrame:
    f = QFrame()
    f.setObjectName("sd_hdiv")
    f.setFixedHeight(1)
    return f


def _vdiv() -> QFrame:
    f = QFrame()
    f.setObjectName("sd_vdiv")
    f.setFixedWidth(1)
    return f
