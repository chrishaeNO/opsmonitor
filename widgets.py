from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QMimeData, Qt, QSize, Signal, QPoint, QObject, QThread, QTimer
from PySide6.QtGui import QColor, QDrag, QFont, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QStyle,
    QSizePolicy,
)

from pathlib import Path


ACCENT = "#2dd4bf"
TEXT = "#e7eef8"
MUTED = "#8b98ab"
PANEL_ALT = "#161f2a"


def make_icon(char: str, color: str = ACCENT, size: int = 20) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor(color))
    painter.setFont(QFont("Arial", max(10, size - 7)))
    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, char)
    painter.end()
    return QIcon(pix)


def themed_icon(key: str, fallback_char: str | None = None) -> QIcon:
    """Returner Remix-ikon hvis tilgjengelig, ellers OS-icon, ellers tekstikon.

    For Remix-icons: legg f.eks. `assets/icons/remix/add.svg`,
    `assets/icons/remix/delete.svg` osv. i prosjektet.
    """
    # 1) Forsøk Remix-icon fra assets-mappa og tint det i appens accent-farge
    base = Path("assets/icons/remix")
    for ext in (".svg", ".png", ".ico"):
        candidate = base / f"{key}{ext}"
        if candidate.exists():
            pix = QPixmap(str(candidate))
            if not pix.isNull():
                tinted = QPixmap(pix.size())
                tinted.fill(Qt.GlobalColor.transparent)
                painter = QPainter(tinted)
                painter.drawPixmap(0, 0, pix)
                painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                painter.setBrush(QColor(ACCENT))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(tinted.rect())
                painter.end()
                return QIcon(tinted)

    # 2) Forsøk OS/themede ikoner
    style = QApplication.instance().style() if QApplication.instance() else None
    if style is not None:
        mapping: dict[str, QStyle.StandardPixmap] = {
            "add": QStyle.StandardPixmap.SP_DialogYesButton,
            "delete": QStyle.StandardPixmap.SP_TrashIcon,
            "settings": QStyle.StandardPixmap.SP_FileDialogDetailedView,
            "grid": QStyle.StandardPixmap.SP_DirIcon,
            "log": QStyle.StandardPixmap.SP_FileDialogInfoView,
            "folder": QStyle.StandardPixmap.SP_DirOpenIcon,
            "file": QStyle.StandardPixmap.SP_FileIcon,
        }
        if key in mapping:
            return style.standardIcon(mapping[key])

    # 3) Fallback til enkel tekst-ikon
    return make_icon(fallback_char or key)


class SectionTitle(QWidget):
    def __init__(self, title: str, subtitle: str = "") -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("sectionTitle")
        self._layout.addWidget(self._title_label)

        self._subtitle_label: Optional[QLabel] = None
        if subtitle:
            self._subtitle_label = QLabel(subtitle)
            self._subtitle_label.setObjectName("sectionSubtitle")
            self._layout.addWidget(self._subtitle_label)

    def set_title(self, title: str, subtitle: str = "") -> None:
        self._title_label.setText(title)
        if subtitle:
            if not self._subtitle_label:
                self._subtitle_label = QLabel(subtitle)
                self._subtitle_label.setObjectName("sectionSubtitle")
                self._layout.addWidget(self._subtitle_label)
            else:
                self._subtitle_label.setText(subtitle)
            self._subtitle_label.show()
        elif self._subtitle_label:
            self._subtitle_label.hide()


class ToolbarButton(QPushButton):
    def __init__(self, text: str, icon_key: str) -> None:
        super().__init__(text)
        # Bruk ekte OS/themede ikoner der vi har nøkler, ellers tekstikon
        self.setIcon(themed_icon(icon_key, fallback_char=icon_key))
        self.setIconSize(QSize(20, 20))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("toolbarButton")


class StatCard(QFrame):
    def __init__(self, icon: str, title: str, value: str, subtitle: str, color: str) -> None:
        super().__init__()
        self.setObjectName("statCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(4)

        top = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 700;")
        top.addWidget(icon_label)
        top.addStretch()
        layout.addLayout(top)

        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        layout.addWidget(title_label)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        layout.addWidget(self.value_label)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("statSubtitle")
        layout.addWidget(subtitle_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class DataTable(QTableWidget):
    def __init__(self, headers: List[str]) -> None:
        super().__init__(0, len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultSectionSize(120)
        self.setObjectName("dataTable")

    def load_rows(self, rows: List[List[str]], late_rows: Optional[List[int]] = None) -> None:
        self.setRowCount(len(rows))
        late_rows = late_rows or []

        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                if row_index in late_rows:
                    item.setForeground(QColor("#ffe9ed"))
                    item.setBackground(QColor("#5d1e29"))
                else:
                    item.setForeground(QColor(TEXT))
                    item.setBackground(QColor(PANEL_ALT))
                self.setItem(row_index, col_index, item)

        self.resizeRowsToContents()


class PanelCard(QFrame):
    removeRequested = Signal(str)

    def __init__(self, panel_id: str, title: str, subtitle: str, body: QWidget, tone: str = "") -> None:
        super().__init__()
        self.panel_id = panel_id
        self.setObjectName("panel")
        if tone:
            self.setProperty("tone", tone)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(6)

        self.header = SectionTitle(title, subtitle)
        header_row.addWidget(self.header, 1)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("panelClose")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.clicked.connect(lambda: self.removeRequested.emit(self.panel_id))
        self.close_btn.setVisible(False)
        header_row.addWidget(self.close_btn, 0, Qt.AlignmentFlag.AlignTop)

        self._drag_start_pos = None

        layout.addLayout(header_row)
        layout.addWidget(body, 1)

    def set_header_title(self, title: str, subtitle: str = "") -> None:
        self.header.set_title(title, subtitle)

    def set_edit_mode(self, enabled: bool) -> None:
        self.close_btn.setVisible(enabled)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        # Dra paneler mellom drop-zones KUN i edit mode
        if event.buttons() != Qt.MouseButton.LeftButton or self._drag_start_pos is None:
            return
        # Finn LayoutCanvas-forelder for å sjekke edit_mode
        parent = self.parent()
        slot = None
        while parent is not None and not isinstance(parent, LayoutCanvas) and not isinstance(parent, PanelDropSlot):
            parent = parent.parent()
        if isinstance(parent, PanelDropSlot):
            slot = parent
            canvas = parent.parent()
        else:
            canvas = parent
        if not isinstance(canvas, LayoutCanvas) or not canvas.edit_mode or slot is None:
            return
        if (event.position().toPoint() - self._drag_start_pos).manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.panel_id)
        mime.setData(b"application/x-ops-source-slot", str(slot.index).encode("utf-8"))
        drag.setMimeData(mime)

        pix = self.grab()
        if not pix.isNull():
            drag.setPixmap(pix)
            drag.setHotSpot(event.position().toPoint())
        drag.exec(Qt.DropAction.MoveAction)


class DashboardBuilder(QListWidget):
    orderChanged = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboardBuilder")
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Snap)
        self.setSpacing(10)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def add_panel(self, panel_id: str, widget: QWidget, size: QSize) -> None:
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, panel_id)
        item.setSizeHint(size)
        self.addItem(item)
        self.setItemWidget(item, widget)

    def get_panel_order(self) -> List[str]:
        order: List[str] = []
        for index in range(self.count()):
            item = self.item(index)
            order.append(item.data(Qt.ItemDataRole.UserRole))
        return order

    def dropEvent(self, event) -> None:  # noqa: N802
        super().dropEvent(event)
        self.orderChanged.emit(self.get_panel_order())


class TemplateRow(QFrame):
    clicked = Signal(str)

    def __init__(self, template_id: str, label: str, icon: str, selected: bool = False) -> None:
        super().__init__()
        self.template_id = template_id
        self.setObjectName("templateRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        icon_label = QLabel(icon)
        icon_label.setObjectName("templateIcon")
        layout.addWidget(icon_label)

        text = QLabel(label)
        text.setObjectName("templateLabel")
        layout.addWidget(text, 1)

        self.check = QLabel("✓" if selected else "")
        self.check.setObjectName("templateCheck")
        layout.addWidget(self.check)

    def set_selected(self, selected: bool) -> None:
        self.check.setText("✓" if selected else "")
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit(self.template_id)
        super().mousePressEvent(event)


class _LoginWorker(QObject):
    """Runs the blocking login API call in a background thread."""
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, config, email: str, password: str) -> None:
        super().__init__()
        self._config = config
        self._email = email
        self._password = password

    def run(self) -> None:
        from api_client import login, APIError, NotAuthenticatedError
        import requests as _requests
        try:
            user = login(self._config, self._email, self._password)
            self.finished.emit(user)
        except NotAuthenticatedError:
            self.failed.emit("Ugyldig e-post eller passord")
        except APIError as exc:
            self.failed.emit((exc.detail or "Innlogging feilet")[:120])
        except _requests.RequestException:
            self.failed.emit("Kunne ikke koble til – sjekk nett/API")
        except Exception:
            self.failed.emit("Innlogging feilet uventet – prøv igjen")


class LoginScreen(QWidget):
    """Innloggingsskjerm – kun e-post og passord (ingen registrering i klienten)."""
    loginSuccess = Signal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("welcomeScreen")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addStretch()

        row = QHBoxLayout()
        row.addStretch()

        card = QFrame()
        card.setObjectName("welcomeCard")
        card.setFixedWidth(420)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(14)

        title = QLabel("OPS Monitor")
        title.setObjectName("welcomeTitle")
        layout.addWidget(title)

        sub = QLabel("Logg inn for å fortsette")
        sub.setObjectName("welcomeSubtitle")
        layout.addWidget(sub)

        layout.addSpacing(6)

        layout.addWidget(QLabel("E-post"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("din@epost.no")
        self.email_input.setObjectName("dialogInput")
        self.email_input.returnPressed.connect(self._do_login)
        layout.addWidget(self.email_input)

        layout.addWidget(QLabel("Passord"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setObjectName("dialogInput")
        self.password_input.returnPressed.connect(self._do_login)
        layout.addWidget(self.password_input)

        self.error_label = QLabel("")
        self.error_label.setObjectName("welcomeSubtitle")
        self.error_label.setStyleSheet("color: #f97373; min-height: 18px;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        self.login_button = QPushButton("Logg inn")
        self.login_button.setObjectName("welcomeOpenButton")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.clicked.connect(self._do_login)
        layout.addWidget(self.login_button)

        # Loading indicator – hidden until login is in progress
        self._loader_label = QLabel("")
        self._loader_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loader_label.setObjectName("welcomeSubtitle")
        self._loader_label.setStyleSheet("color: #94a3b8; font-size: 12px; min-height: 20px;")
        self._loader_label.hide()
        layout.addWidget(self._loader_label)

        row.addWidget(card)
        row.addStretch()
        root.addLayout(row)
        root.addStretch()

        # Animated dots timer
        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(420)
        self._dot_timer.timeout.connect(self._tick_loader)
        self._dot_count = 0

        self._busy = False
        self._active_thread: QThread | None = None
        self._active_worker: _LoginWorker | None = None

    def _set_loading(self, loading: bool) -> None:
        self.email_input.setEnabled(not loading)
        self.password_input.setEnabled(not loading)
        self.login_button.setEnabled(not loading)
        self.login_button.setText("Logger inn…" if loading else "Logg inn")
        if loading:
            self._dot_count = 0
            self._loader_label.setText("Kobler til server")
            self._loader_label.show()
            self._dot_timer.start()
        else:
            self._dot_timer.stop()
            self._loader_label.hide()

    def _tick_loader(self) -> None:
        self._dot_count = (self._dot_count + 1) % 4
        self._loader_label.setText("Kobler til server" + ("·" * self._dot_count))

    def _do_login(self) -> None:
        self.error_label.setText("")
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if not email or not password:
            self.error_label.setText("Fyll inn e-post og passord")
            return

        config = self.window().config if hasattr(self.window(), "config") else None
        if not config:
            self.error_label.setText("Konfigurasjon mangler")
            return

        if self._busy:
            return

        self._busy = True
        self._set_loading(True)

        # Create thread without parent so thread.deleteLater() fully cleans it up
        thread = QThread()
        worker = _LoginWorker(config, email, password)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_worker_success)
        worker.failed.connect(self._on_worker_error)
        # Orderly shutdown: worker signals → thread quits → both cleaned up
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        # Keep refs alive until thread finishes to prevent premature GC
        self._active_thread = thread
        self._active_worker = worker
        thread.start()

    def _on_worker_success(self, user: dict) -> None:
        # Called on main thread via cross-thread queued connection – safe to touch UI
        self._busy = False
        self._set_loading(False)
        # Emit via AutoConnection (direct) so parent receives it synchronously.
        # Parent schedules setCentralWidget via QTimer to stay out of this stack frame.
        self.loginSuccess.emit(user)

    def _on_worker_error(self, msg: str) -> None:
        self._busy = False
        self._set_loading(False)
        self.error_label.setText(msg)

    def _open_register(self) -> None:
        self.error_label.setText("Registrering gjøres via admin-portalen, ikke i klienten.")


class RegisterDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registrer bedrift")
        self.setObjectName("settingsDialog")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self._drag_pos: QPoint | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.addWidget(QLabel("Bedriftsnavn"))
        self.org_input = QLineEdit()
        self.org_input.setObjectName("dialogInput")
        root.addWidget(self.org_input)
        root.addWidget(QLabel("E-post (admin)"))
        self.email_input = QLineEdit()
        self.email_input.setObjectName("dialogInput")
        root.addWidget(self.email_input)
        root.addWidget(QLabel("Passord"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("dialogInput")
        root.addWidget(self.password_input)
        row = QHBoxLayout()
        row.addStretch()
        ok = QPushButton("Registrer")
        ok.setObjectName("primaryButton")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Avbryt")
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        row.addWidget(ok)
        root.addLayout(row)

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

    def org_name(self) -> str:
        return self.org_input.text().strip()

    def email(self) -> str:
        return self.email_input.text().strip()

    def password(self) -> str:
        return self.password_input.text()


class UsersDialog(QDialog):
    """Admin-dialog: list brukere, legg til, fjern."""

    _ROLE_BADGE = {
        "admin": ("Admin", "#f59e0b", "#1c1400"),
        "user":  ("Bruker", "#3b82f6", "#001433"),
    }

    def __init__(self, config, current_user: dict, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.current_user = current_user
        self._users: list[dict] = []
        self.setWindowTitle("Brukere i organisasjonen")
        self.setObjectName("settingsDialog")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setMinimumWidth(680)
        self.setMinimumHeight(480)
        self.resize(720, 540)
        self._drag_pos: QPoint | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toppbar ──────────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("dialogHeader")
        header.setStyleSheet(
            "#dialogHeader { background: #0f172a; border-bottom: 1px solid #1e293b; }"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 14, 14, 14)
        hl.setSpacing(10)

        title_lbl = QLabel("Brukere")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9;")
        org = current_user.get("organization_name", "")
        sub_lbl = QLabel(org)
        sub_lbl.setStyleSheet("font-size: 12px; color: #64748b;")
        hl.addWidget(title_lbl)
        hl.addWidget(sub_lbl)
        hl.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #64748b; border: none;"
            "  border-radius: 6px; font-size: 14px; }"
            "QPushButton:hover { background: #1e293b; color: #f1f5f9; }"
        )
        close_btn.clicked.connect(self.accept)
        hl.addWidget(close_btn)
        root.addWidget(header)

        # ── Body ─────────────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background: #0f172a;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20, 18, 20, 18)
        bl.setSpacing(14)

        # Brukertabell
        self.table = QTableWidget(0, 3)
        self.table.setObjectName("usersTable")
        self.table.setHorizontalHeaderLabels(["E-post", "Rolle", ""])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 72)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setStyleSheet(
            "QTableWidget { background: #0b1120; border: 1px solid #1e293b;"
            "  border-radius: 8px; font-size: 13px; color: #e2e8f0; outline: none; }"
            "QTableWidget::item { padding: 8px 10px; border-bottom: 1px solid #1e293b; }"
            "QTableWidget::item:selected { background: #1e3a5f; color: #fff; }"
            "QHeaderView::section { background: #0f172a; color: #64748b; font-size: 11px;"
            "  font-weight: 600; padding: 6px 10px; border: none;"
            "  border-bottom: 1px solid #1e293b; text-transform: uppercase; }"
        )
        bl.addWidget(self.table, 1)

        # Status/feil-linje
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 12px; color: #f87171; min-height: 16px;")
        bl.addWidget(self.status_label)

        # Knapper
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.add_btn = QPushButton("+ Legg til bruker")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet(
            "QPushButton { background: #1d4ed8; color: #fff; border: none;"
            "  border-radius: 7px; padding: 8px 18px; font-size: 13px; font-weight: 600; }"
            "QPushButton:hover { background: #2563eb; }"
            "QPushButton:disabled { background: #1e293b; color: #475569; }"
        )
        self.add_btn.clicked.connect(self._add_user)

        self.refresh_btn = QPushButton("↻  Oppdater")
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet(
            "QPushButton { background: #1e293b; color: #94a3b8; border: none;"
            "  border-radius: 7px; padding: 8px 14px; font-size: 13px; }"
            "QPushButton:hover { background: #263248; color: #e2e8f0; }"
        )
        self.refresh_btn.clicked.connect(self._load_users)

        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addStretch()
        bl.addLayout(btn_row)

        root.addWidget(body, 1)
        self._load_users()

    # ── drag support ──────────────────────────────────────────────────────────
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

    # ── helpers ───────────────────────────────────────────────────────────────
    def _load_users(self) -> None:
        self.status_label.setText("")
        self.table.setRowCount(0)
        try:
            from api_client import list_users
            self._users = list_users(self.config)
        except Exception as exc:
            self.status_label.setText(f"Kunne ikke hente brukere: {exc}"[:120])
            return

        for u in self._users:
            row = self.table.rowCount()
            self.table.insertRow(row)

            email_item = QTableWidgetItem(u.get("email", ""))
            email_item.setData(Qt.ItemDataRole.UserRole, u.get("id"))
            self.table.setItem(row, 0, email_item)

            role = u.get("role", "user")
            label_txt, bg, fg = self._ROLE_BADGE.get(role, (role, "#334155", "#e2e8f0"))
            badge = QLabel(f" {label_txt} ")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                f"background:{bg}; color:{fg}; border-radius:4px;"
                "font-size:11px; font-weight:600; padding:2px 6px;"
            )
            cell = QWidget()
            cl = QHBoxLayout(cell)
            cl.setContentsMargins(6, 4, 6, 4)
            cl.addWidget(badge)
            cl.addStretch()
            self.table.setCellWidget(row, 1, cell)

            if u.get("id") != self.current_user.get("id"):
                del_btn = QPushButton("Fjern")
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.setStyleSheet(
                    "QPushButton { background: transparent; color: #ef4444; border: none;"
                    "  font-size: 12px; padding: 4px 8px; border-radius: 5px; }"
                    "QPushButton:hover { background: #1f1010; color: #f87171; }"
                )
                del_btn.clicked.connect(lambda _, uid=u.get("id"), em=u.get("email", ""): self._remove_user(uid, em))
                cell2 = QWidget()
                cl2 = QHBoxLayout(cell2)
                cl2.setContentsMargins(4, 2, 4, 2)
                cl2.addWidget(del_btn)
                self.table.setCellWidget(row, 2, cell2)

            self.table.setRowHeight(row, 44)

    def _add_user(self) -> None:
        dlg = _AddUserDialog(self)
        if not dlg.exec():
            return
        email, password, role = dlg.values()
        if not email or not password:
            self.status_label.setText("E-post og passord er påkrevd.")
            return
        self.add_btn.setEnabled(False)
        self.add_btn.setText("Oppretter…")
        try:
            from api_client import create_user
            create_user(self.config, email, password, role)
            self._load_users()
            self.status_label.setStyleSheet("font-size:12px; color:#4ade80; min-height:16px;")
            self.status_label.setText(f"Bruker {email} ble opprettet.")
        except Exception as exc:
            self.status_label.setStyleSheet("font-size:12px; color:#f87171; min-height:16px;")
            self.status_label.setText(str(exc)[:160])
        finally:
            self.add_btn.setEnabled(True)
            self.add_btn.setText("+ Legg til bruker")

    def _remove_user(self, uid, email: str) -> None:
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Fjern bruker",
            f"Vil du fjerne brukeren\n{email}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            from api_client import delete_user
            delete_user(self.config, int(uid))
            self._load_users()
            self.status_label.setStyleSheet("font-size:12px; color:#4ade80; min-height:16px;")
            self.status_label.setText(f"Bruker ble fjernet.")
        except Exception as exc:
            self.status_label.setStyleSheet("font-size:12px; color:#f87171; min-height:16px;")
            self.status_label.setText(str(exc)[:160])


class _AddUserDialog(QDialog):
    """Popup for å opprette en ny bruker – moderne, bredde-riktig."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Legg til bruker")
        self.setObjectName("settingsDialog")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setMinimumWidth(440)
        self.resize(460, 0)
        self._drag_pos: QPoint | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("background:#0f172a; border-bottom:1px solid #1e293b;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 14, 14, 14)
        title = QLabel("Legg til bruker")
        title.setStyleSheet("font-size:14px; font-weight:600; color:#f1f5f9;")
        hl.addWidget(title)
        hl.addStretch()
        x_btn = QPushButton("✕")
        x_btn.setFixedSize(26, 26)
        x_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        x_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#64748b;border:none;border-radius:5px;font-size:13px;}"
            "QPushButton:hover{background:#1e293b;color:#f1f5f9;}"
        )
        x_btn.clicked.connect(self.reject)
        hl.addWidget(x_btn)
        root.addWidget(header)

        # Body
        body = QWidget()
        body.setStyleSheet("background:#0f172a;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 20, 24, 24)
        bl.setSpacing(12)

        def field(label: str, placeholder: str, echo=QLineEdit.EchoMode.Normal) -> QLineEdit:
            lbl = QLabel(label)
            lbl.setStyleSheet("color:#94a3b8; font-size:12px; font-weight:500;")
            bl.addWidget(lbl)
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setEchoMode(echo)
            inp.setObjectName("dialogInput")
            inp.setMinimumHeight(36)
            bl.addWidget(inp)
            return inp

        self.email_in = field("E-post", "bruker@bedrift.no")
        self.pw_in = field("Passord (minst 8 tegn)", "••••••••", QLineEdit.EchoMode.Password)

        role_lbl = QLabel("Rolle")
        role_lbl.setStyleSheet("color:#94a3b8; font-size:12px; font-weight:500;")
        bl.addWidget(role_lbl)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])
        self.role_combo.setObjectName("dialogInput")
        self.role_combo.setMinimumHeight(36)
        bl.addWidget(self.role_combo)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color:#f87171; font-size:12px; min-height:16px;")
        self.error_label.setWordWrap(True)
        bl.addWidget(self.error_label)

        bl.addSpacing(4)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("Avbryt")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(
            "QPushButton{background:#1e293b;color:#94a3b8;border:none;"
            "border-radius:7px;padding:9px 18px;font-size:13px;}"
            "QPushButton:hover{background:#263248;color:#e2e8f0;}"
        )
        cancel_btn.clicked.connect(self.reject)

        self.ok_btn = QPushButton("Opprett bruker")
        self.ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ok_btn.setStyleSheet(
            "QPushButton{background:#1d4ed8;color:#fff;border:none;"
            "border-radius:7px;padding:9px 18px;font-size:13px;font-weight:600;}"
            "QPushButton:hover{background:#2563eb;}"
            "QPushButton:disabled{background:#1e293b;color:#475569;}"
        )
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._validate_and_accept)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.ok_btn)
        bl.addLayout(btn_row)

        root.addWidget(body)

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

    def _validate_and_accept(self) -> None:
        email = self.email_in.text().strip()
        pw = self.pw_in.text()
        if not email:
            self.error_label.setText("E-post er påkrevd.")
            return
        if "@" not in email:
            self.error_label.setText("Ugyldig e-postadresse.")
            return
        if len(pw) < 8:
            self.error_label.setText("Passord må ha minst 8 tegn.")
            return
        self.accept()

    def values(self) -> tuple[str, str, str]:
        return (
            self.email_in.text().strip(),
            self.pw_in.text(),
            self.role_combo.currentText(),
        )


class CreateLayoutDialog(QDialog):
    def __init__(self, title: str, template: str, rows: int, cols: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create layout")
        self.resize(520, 640)
        self.setObjectName("createLayoutDialog")

        self._selected_template = template if template else "2x2"
        self._rows = rows or 2
        self._cols = cols or 2

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header = QHBoxLayout()
        title_label = QLabel("Oppsett for dashboard")
        title_label.setObjectName("dialogTitle")
        header.addWidget(title_label)
        header.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("dialogClose")
        close_btn.clicked.connect(self.reject)
        header.addWidget(close_btn)
        root.addLayout(header)

        title_card = QFrame()
        title_card.setObjectName("dialogCard")
        tl = QVBoxLayout(title_card)
        tl.setContentsMargins(14, 12, 14, 12)
        tl.setSpacing(6)
        tl.addWidget(QLabel("Navn på dashboard"))
        self.title_input = QLineEdit(title or "Nytt dashboard")
        self.title_input.setObjectName("dialogInput")
        tl.addWidget(self.title_input)
        root.addWidget(title_card)

        grid_label = QLabel("VELG GRID")
        grid_label.setObjectName("dialogSectionLabel")
        root.addWidget(grid_label)

        grid_card = QFrame()
        grid_card.setObjectName("dialogCard")
        gl = QVBoxLayout(grid_card)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.setSpacing(0)

        self._template_rows: Dict[str, TemplateRow] = {}
        options = [
            ("1x1", "1×1 – fokusvisning", "□"),
            ("2x2", "2×2 – fire like ruter", "▦"),
            ("2x2+1", "2×2 + 1 – fire + én rad", "▤"),
            ("3x3", "3×3 – ni ruter", "▩"),
            ("4x4", "4×4 – seksten ruter", "▩"),
            ("5x5", "5×5 – tjuefem ruter", "▩"),
            ("custom", "Egendefinert grid", "?"),
        ]
        for tid, label, icon in options:
            row = TemplateRow(tid, label, icon, selected=(tid == self._selected_template))
            row.clicked.connect(self._select_template)
            self._template_rows[tid] = row
            gl.addWidget(row)
        root.addWidget(grid_card)

        self.custom_card = QFrame()
        self.custom_card.setObjectName("dialogCard")
        cl = QFormLayout(self.custom_card)
        cl.setContentsMargins(14, 12, 14, 12)
        cl.setSpacing(10)
        self.rows_spin = QSpinBox()
        self.cols_spin = QSpinBox()
        self.rows_spin.setRange(1, 5)
        self.cols_spin.setRange(1, 5)
        self.rows_spin.setValue(self._rows)
        self.cols_spin.setValue(self._cols)
        cl.addRow("Rows", self.rows_spin)
        cl.addRow("Cols", self.cols_spin)
        root.addWidget(self.custom_card)

        root.addStretch()

        create_btn = QPushButton("Create")
        create_btn.setObjectName("primaryButton")
        create_btn.clicked.connect(self.accept)
        root.addWidget(create_btn)

        self._apply_template_state()

    def _select_template(self, template_id: str) -> None:
        self._selected_template = template_id
        self._apply_template_state()

    def _apply_template_state(self) -> None:
        presets = {
            "1x1": (1, 1),
            "2x2": (2, 2),
            "2x2+1": (2, 3),   # to rader, tre kolonner – spesialhåndteres i LayoutCanvas
            "3top+1": (2, 3),  # tre bokser øverst, én full bredde under
            "3x3": (3, 3),
            "4x4": (4, 4),
            "5x5": (5, 5),
        }
        for tid, row in self._template_rows.items():
            row.set_selected(tid == self._selected_template)
        custom = self._selected_template == "custom"
        self.custom_card.setVisible(custom)
        if not custom and self._selected_template in presets:
            r, c = presets[self._selected_template]
            self.rows_spin.setValue(r)
            self.cols_spin.setValue(c)

    def values(self) -> Tuple[str, int, int]:
        return (self._selected_template, int(self.rows_spin.value()), int(self.cols_spin.value()))

    def title_value(self) -> str:
        return self.title_input.text().strip()


class LayoutWelcomeScreen(QWidget):
    """Velkomstskjerm som vises inne i hovedvinduet, før dashboard lastes."""

    layoutSelected = Signal(str)
    createLayoutRequested = Signal()

    def __init__(self, layouts: List[dict], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("welcomeScreen")

        # Ytre layout – sentrer velkomstkortet både horisontalt og vertikalt
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addStretch()

        center_row = QHBoxLayout()
        center_row.addStretch()

        card = QFrame()
        card.setObjectName("welcomeCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(20)

        header_row = QHBoxLayout()

        # App-logo: rendrer SVG i høy oppløsning så det blir skarpt på HiDPI/Retina
        logo_label = QLabel()
        logo_label.setObjectName("welcomeLogo")
        logo_label.setFixedSize(80, 80)
        logo_path = Path("assets/opsmonitor.svg")
        if logo_path.exists():
            renderer = QSvgRenderer(str(logo_path))
            if renderer.isValid():
                # SVG rendres i 2x oppløsning – skarpt på Retina/HiDPI
                size = 160
                px = QPixmap(size, size)
                px.fill(Qt.GlobalColor.transparent)
                painter = QPainter(px)
                renderer.render(painter)
                painter.end()
                px.setDevicePixelRatio(2)
                logo_label.setPixmap(px)
        header_row.addWidget(logo_label)

        title_block = QVBoxLayout()
        title = QLabel("OPS Monitor")
        title.setObjectName("welcomeTitle")
        subtitle = QLabel("Velg et eksisterende dashboard eller opprett et nytt oppsett.")
        subtitle.setObjectName("welcomeSubtitle")
        subtitle.setWordWrap(True)
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        header_row.addLayout(title_block, 1)

        card_layout.addLayout(header_row)

        self.list = QListWidget()
        self.list.setObjectName("layoutList")
        self.list.itemDoubleClicked.connect(self._emit_current)
        card_layout.addWidget(self.list, 1)

        last_five = layouts[-5:] if layouts else []
        for entry in reversed(last_five):
            title = entry.get("title", "Uten navn")
            template = entry.get("template", "")
            rows = entry.get("rows", 0)
            cols = entry.get("cols", 0)
            desc = f"{title}  —  {template} ({rows}×{cols})"
            item = QListWidgetItem(desc)
            item.setData(Qt.ItemDataRole.UserRole, entry.get("id", ""))
            self.list.addItem(item)

        if self.list.count():
            self.list.setCurrentRow(0)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        create_btn = QPushButton("Opprett nytt layout")
        create_btn.setObjectName("secondaryButton")
        create_btn.clicked.connect(lambda: self.createLayoutRequested.emit())
        btn_row.addWidget(create_btn)
        open_btn = QPushButton("Åpne valgt dashboard")
        open_btn.setObjectName("welcomeOpenButton")
        open_btn.clicked.connect(self._emit_current)
        btn_row.addWidget(open_btn)
        card_layout.addLayout(btn_row)

        center_row.addWidget(card)
        center_row.addStretch()
        root.addLayout(center_row)
        root.addStretch()

    def _emit_current(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        layout_id = item.data(Qt.ItemDataRole.UserRole)
        if not layout_id:
            return
        self.layoutSelected.emit(layout_id)

class DraggablePanelCard(PanelCard):
    def __init__(self, panel_id: str, title: str, subtitle: str, body: QWidget) -> None:
        super().__init__(panel_id, title, subtitle, body)
        self._drag_start_pos = None

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if event.buttons() != Qt.MouseButton.LeftButton or self._drag_start_pos is None:
            return
        if (event.position().toPoint() - self._drag_start_pos).manhattanLength() < 10:
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.panel_id)
        drag.setMimeData(mime)

        pix = self.grab()
        if not pix.isNull():
            drag.setPixmap(pix)
            drag.setHotSpot(event.position().toPoint())
        drag.exec(Qt.DropAction.MoveAction)


class PanelDropSlot(QFrame):
    panelDropped = Signal(int, str, int)

    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index
        self.current_panel_id = ""
        self.setAcceptDrops(True)
        self.setObjectName("dropSlot")
        self._drag_start_pos = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.placeholder = QLabel("")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setObjectName("dropPlaceholder")
        self.layout.addWidget(self.placeholder)
        self._show_placeholder(True)
        self.setProperty("dragActive", False)

    def set_panel(self, panel_id: str, panel_widget: QWidget) -> None:
        self.clear(show_placeholder=False)
        self.current_panel_id = panel_id
        self.layout.addWidget(panel_widget)

    def clear(self, show_placeholder: bool = True) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        self.placeholder = QLabel("")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setObjectName("dropPlaceholder")
        self.layout.addWidget(self.placeholder)
        self.current_panel_id = ""
        self._show_placeholder(show_placeholder)
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def _show_placeholder(self, show: bool) -> None:
        if show:
            self.placeholder.setText("Slipp boks her")
            self.placeholder.setVisible(True)
        else:
            self.placeholder.setText("")
            self.placeholder.setVisible(False)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        # Drag-håndtering gjøres av PanelCard, ikke av sloten
        return

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        parent = self.parent()
        if not getattr(parent, "edit_mode", False):
            event.ignore()
            return
        if event.mimeData().hasText():
            self.setProperty("dragActive", True)
            if not self.current_panel_id:
                self._show_placeholder(True)
                self.placeholder.setText("Slipp for å plassere")
            self.style().unpolish(self)
            self.style().polish(self)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self.setProperty("dragActive", False)
        if not self.current_panel_id:
            self._show_placeholder(True)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802
        parent = self.parent()
        if not getattr(parent, "edit_mode", False):
            event.ignore()
            return
        panel_id = event.mimeData().text()
        source_slot = -1
        try:
            raw = event.mimeData().data(b"application/x-ops-source-slot")
            if raw:
                source_slot = int(bytes(raw).decode("utf-8"))
        except Exception:
            source_slot = -1
        self.panelDropped.emit(self.index, panel_id, source_slot)
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        event.acceptProposedAction()


class LayoutCanvas(QWidget):
    layoutChanged = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.edit_mode = False
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(10)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.rows = 2
        self.cols = 2
        self._prev_rows = 0
        self._prev_cols = 0
        self.slots: List[PanelDropSlot] = []
        self.panel_library: Dict[str, QWidget] = {}
        self.assignments: Dict[str, str] = {}

    def set_panel_library(self, panel_library: Dict[str, QWidget]) -> None:
        self.panel_library = panel_library
        # Koble remove-signaler fra panelene til layoutet
        for panel in self.panel_library.values():
            if hasattr(panel, "removeRequested"):
                try:
                    panel.removeRequested.disconnect(self.handle_remove_panel)  # type: ignore[arg-type]
                except Exception:
                    pass
                panel.removeRequested.connect(self.handle_remove_panel)  # type: ignore[arg-type]

    def set_edit_mode(self, edit: bool) -> None:
        self.edit_mode = edit
        for slot in self.slots:
            slot.setAcceptDrops(edit)
        for panel in self.panel_library.values():
            if hasattr(panel, "set_edit_mode"):
                panel.set_edit_mode(edit)  # type: ignore[arg-type]

    def configure_grid(self, rows: int, cols: int, template: str | None = None) -> None:
        # Null ut gamle stretch-verdier slik at vi ikke arver rare høyder
        for r in range(self._prev_rows):
            self.grid.setRowStretch(r, 0)
        for c in range(self._prev_cols):
            self.grid.setColumnStretch(c, 0)

        self.rows = max(1, rows)
        self.cols = max(1, cols)
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.slots = []

        # Spesial-case for 2x2+1: to rader med 2x2-grid til venstre og én høy rute til høyre
        if template == "2x2+1" and self.rows == 2 and self.cols == 3:
            total_slots = 5
            for i in range(total_slots):
                slot = PanelDropSlot(i)
                slot.panelDropped.connect(self.handle_drop)
                self.slots.append(slot)
            # indeks 0–3: 2x2-grid
            self.grid.addWidget(self.slots[0], 0, 0)
            self.grid.addWidget(self.slots[1], 0, 1)
            self.grid.addWidget(self.slots[2], 1, 0)
            self.grid.addWidget(self.slots[3], 1, 1)
            # indeks 4: høy rute som dekker begge rader
            self.grid.addWidget(self.slots[4], 0, 2, 2, 1)
        # Spesial-case for 3top+1: tre like bokser øverst og én som dekker hele bredden under
        elif template == "3top+1" and self.rows == 2 and self.cols == 3:
            total_slots = 4
            for i in range(total_slots):
                slot = PanelDropSlot(i)
                slot.panelDropped.connect(self.handle_drop)
                self.slots.append(slot)
            # indeks 0–2: tre bokser øverst
            self.grid.addWidget(self.slots[0], 0, 0)
            self.grid.addWidget(self.slots[1], 0, 1)
            self.grid.addWidget(self.slots[2], 0, 2)
            # indeks 3: én rute som dekker hele bredden under
            self.grid.addWidget(self.slots[3], 1, 0, 1, 3)
        else:
            for i in range(self.rows * self.cols):
                slot = PanelDropSlot(i)
                slot.panelDropped.connect(self.handle_drop)
                self.slots.append(slot)
                self.grid.addWidget(slot, i // self.cols, i % self.cols)

        # Sørg for konsistent grid: alle rader/kolonner får lik stretch,
        # slik at drop-zones beholder proporsjoner når innhold legges til.
        for r in range(self.rows):
            self.grid.setRowStretch(r, 1)
        for c in range(self.cols):
            self.grid.setColumnStretch(c, 1)

        self._prev_rows = self.rows
        self._prev_cols = self.cols
        # Viktig: vi resetter IKKE self.assignments her.
        # Det er vinduet (main_window) som eksplisitt kaller restore_assignments(...)
        # med slot_assignments for AKTIV layout-ID.

    def handle_drop(self, slot_index: int, panel_id: str, source_slot: int = -1) -> None:
        if panel_id not in self.panel_library:
            return
        target = self.slots[slot_index]
        target_existing = target.current_panel_id

        # Swap when dragging from another slot onto an occupied slot.
        if source_slot >= 0 and source_slot < len(self.slots) and source_slot != slot_index and target_existing:
            src = self.slots[source_slot]
            src_existing = src.current_panel_id
            target.set_panel(panel_id, self.panel_library[panel_id])
            if src_existing and target_existing:
                src.set_panel(target_existing, self.panel_library[target_existing])
            self._emit_assignments()
            return

        # Move: clear any existing instance of this panel id
        for slot in self.slots:
            if slot.current_panel_id == panel_id and slot is not target:
                slot.clear(show_placeholder=True)
        target.set_panel(panel_id, self.panel_library[panel_id])
        self._emit_assignments()

    def handle_remove_panel(self, panel_id: str) -> None:
        """Fjern en modul fra aktiv layout når X-klikkes i edit-mode."""
        if not self.edit_mode:
            return
        changed = False
        for idx, slot in enumerate(self.slots):
            if slot.current_panel_id == panel_id:
                slot.clear(show_placeholder=True)
                # Fjern fra assignments hvis den finnes der
                key = f"slot_{idx}"
                if key in self.assignments:
                    del self.assignments[key]
                changed = True
        if changed:
            self._emit_assignments()

    def restore_assignments(self, assignments: Dict[str, str], emit: bool = False) -> None:
        """Gjenopprett slot-assignments fra lagret layout.

        emit=False brukes når vi bare laster en layout (for eksempel ved
        oppstart eller når bruker bytter layout), slik at vi IKKE skriver
        tilbake til config samtidig. Når bruker faktisk endrer layout
        (drag/drop/X-knapp), går det via _emit_assignments().
        """
        self.assignments = dict(assignments or {})
        for slot in self.slots:
            slot.clear()
        for key, panel_id in self.assignments.items():
            if panel_id in self.panel_library and key.startswith("slot_"):
                idx = int(key.split("_")[1])
                if 0 <= idx < len(self.slots):
                    self.slots[idx].set_panel(panel_id, self.panel_library[panel_id])
        if emit:
            self._emit_assignments()

    def _emit_assignments(self) -> None:
        assignments: Dict[str, str] = {}
        for idx, slot in enumerate(self.slots):
            if slot.current_panel_id:
                assignments[f"slot_{idx}"] = slot.current_panel_id
        self.assignments = assignments
        self.layoutChanged.emit(assignments)


class MediaPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.list = QListWidget()
        self.list.setObjectName("mediaList")
        self.list.currentRowChanged.connect(self._show_current)
        layout.addWidget(self.list, 1)

        right = QFrame()
        right.setObjectName("mediaPreview")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(10, 10, 10, 10)
        rl.setSpacing(10)

        top = QHBoxLayout()
        add_btn = QPushButton("Legg til")
        add_btn.setObjectName("sideButton")
        add_btn.clicked.connect(self.add_files)
        remove_btn = QPushButton("Fjern")
        remove_btn.setObjectName("sideButton")
        remove_btn.clicked.connect(self.remove_current)
        top.addWidget(add_btn)
        top.addWidget(remove_btn)
        top.addStretch()
        rl.addLayout(top)

        self.preview_stack = QStackedWidget()
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setObjectName("logView")
        self.preview_image = QLabel("Velg en fil")
        self.preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image.setObjectName("mediaImage")
        self.preview_stack.addWidget(self.preview_image)
        self.preview_stack.addWidget(self.preview_text)
        rl.addWidget(self.preview_stack, 1)

        layout.addWidget(right, 3)

    def set_files(self, paths: List[str]) -> None:
        self.list.clear()
        for p in paths:
            self.list.addItem(QListWidgetItem(Path(p).name))
            self.list.item(self.list.count() - 1).setToolTip(p)
        if self.list.count() and self.list.currentRow() < 0:
            self.list.setCurrentRow(0)
        self._show_current(self.list.currentRow())

    def files(self) -> List[str]:
        out: List[str] = []
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item and item.toolTip():
                out.append(item.toolTip())
        return out

    def add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Velg bilder/dokumenter",
            "",
            "Filer (*.png *.jpg *.jpeg *.webp *.gif *.pdf *.txt *.md *.csv *.json *.log);;Alle filer (*.*)",
        )
        if not paths:
            return
        self.set_files(self.files() + paths)

    def remove_current(self) -> None:
        row = self.list.currentRow()
        if row < 0:
            return
        self.list.takeItem(row)
        self._show_current(self.list.currentRow())

    def _show_current(self, row: int) -> None:
        if row < 0 or row >= self.list.count():
            self.preview_image.setText("Velg en fil")
            self.preview_image.setPixmap(QPixmap())
            self.preview_stack.setCurrentWidget(self.preview_image)
            return
        item = self.list.item(row)
        path = Path(item.toolTip()) if item and item.toolTip() else None
        if not path or not path.exists():
            self.preview_text.setPlainText("Filen finnes ikke lenger.")
            self.preview_stack.setCurrentWidget(self.preview_text)
            return
        suffix = path.suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            pix = QPixmap(str(path))
            if pix.isNull():
                self.preview_text.setPlainText("Kunne ikke lese bildet.")
                self.preview_stack.setCurrentWidget(self.preview_text)
                return
            self.preview_image.setPixmap(pix.scaled(self.preview_image.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.preview_stack.setCurrentWidget(self.preview_image)
            return
        if suffix in {".txt", ".md", ".csv", ".json", ".log"}:
            try:
                self.preview_text.setPlainText(path.read_text(encoding="utf-8", errors="replace")[:80000])
            except Exception as exc:
                self.preview_text.setPlainText(f"Kunne ikke lese filen.\n\n{exc}")
            self.preview_stack.setCurrentWidget(self.preview_text)
            return
        if suffix == ".pdf":
            self.preview_text.setPlainText("PDF-visning er ikke aktivert i denne builden ennå.")
            self.preview_stack.setCurrentWidget(self.preview_text)
            return
        self.preview_text.setPlainText("Filtypen støttes ikke i forhåndsvisning.")
        self.preview_stack.setCurrentWidget(self.preview_text)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self.preview_stack.currentWidget() is self.preview_image and not self.preview_image.pixmap():
            return
        row = self.list.currentRow()
        if row < 0 or row >= self.list.count():
            return
        item = self.list.item(row)
        path = Path(item.toolTip()) if item and item.toolTip() else None
        if path and path.exists() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            pix = QPixmap(str(path))
            if not pix.isNull():
                self.preview_image.setPixmap(pix.scaled(self.preview_image.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
