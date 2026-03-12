from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QMimeData, Qt, QSize, Signal
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


class LoginScreen(QWidget):
    """Innloggingsskjerm – e-post, passord, logg inn / registrer bedrift."""
    loginSuccess = Signal(dict)  # user info from /me

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
        card.setFixedWidth(400)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)
        title = QLabel("OPS Monitor")
        title.setObjectName("welcomeTitle")
        layout.addWidget(title)
        sub = QLabel("Logg inn for å fortsette")
        sub.setObjectName("welcomeSubtitle")
        layout.addWidget(sub)
        layout.addWidget(QLabel("E-post"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("din@epost.no")
        self.email_input.setObjectName("dialogInput")
        layout.addWidget(self.email_input)
        layout.addWidget(QLabel("Passord"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setObjectName("dialogInput")
        layout.addWidget(self.password_input)
        self.error_label = QLabel("")
        self.error_label.setObjectName("welcomeSubtitle")
        self.error_label.setStyleSheet("color: #f97373;")
        layout.addWidget(self.error_label)
        btn = QPushButton("Logg inn")
        btn.setObjectName("welcomeOpenButton")
        btn.clicked.connect(self._do_login)
        layout.addWidget(btn)
        reg_btn = QPushButton("Registrer ny bedrift")
        reg_btn.setObjectName("secondaryButton")
        reg_btn.clicked.connect(self._open_register)
        layout.addWidget(reg_btn)
        row.addWidget(card)
        row.addStretch()
        root.addLayout(row)
        root.addStretch()
        self._register_dialog = None

    def _do_login(self) -> None:
        self.error_label.setText("")
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if not email or not password:
            self.error_label.setText("Fyll inn e-post og passord")
            return
        try:
            from api_client import login, APIError, NotAuthenticatedError
            config = self.window().config if hasattr(self.window(), "config") else None
            if not config:
                self.error_label.setText("Konfigurasjon mangler")
                return
            user = login(config, email, password)
            self.loginSuccess.emit(user)
        except Exception as e:
            from api_client import NotAuthenticatedError, APIError
            if isinstance(e, NotAuthenticatedError):
                self.error_label.setText("Ugyldig e-post eller passord")
            elif isinstance(e, APIError):
                self.error_label.setText(e.detail[:80])
            else:
                self.error_label.setText("Kunne ikke koble til – sjekk at API kjører")

    def _open_register(self) -> None:
        from api_client import register, APIError, NotAuthenticatedError
        config = self.window().config if hasattr(self.window(), "config") else None
        if not config:
            return
        dlg = RegisterDialog(self)
        if dlg.exec():
            org_name = dlg.org_name()
            email = dlg.email()
            password = dlg.password()
            if not org_name or not email or not password:
                self.error_label.setText("Fyll inn alle felt")
                return
            try:
                user = register(config, org_name, email, password)
                self.loginSuccess.emit(user)
            except APIError as e:
                self.error_label.setText(e.detail[:80])
            except Exception:
                self.error_label.setText("Kunne ikke registrere – sjekk at API kjører")


class RegisterDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registrer bedrift")
        self.setObjectName("settingsDialog")
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

    def org_name(self) -> str:
        return self.org_input.text().strip()

    def email(self) -> str:
        return self.email_input.text().strip()

    def password(self) -> str:
        return self.password_input.text()


class UsersDialog(QDialog):
    """Admin-dialog: list brukere, legg til, fjern."""
    def __init__(self, config, current_user: dict, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.current_user = current_user
        self.setWindowTitle("Brukere i organisasjonen")
        self.setObjectName("settingsDialog")
        self.resize(500, 400)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.addWidget(QLabel("Brukere (kun for admin)"))
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("layoutList")
        root.addWidget(self.list_widget, 1)
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Legg til bruker")
        add_btn.setObjectName("secondaryButton")
        add_btn.clicked.connect(self._add_user)
        remove_btn = QPushButton("Fjern valgt")
        remove_btn.setObjectName("secondaryButton")
        remove_btn.clicked.connect(self._remove_user)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)
        close_btn = QPushButton("Lukk")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        self._load_users()

    def _load_users(self) -> None:
        try:
            from api_client import list_users, APIError
            users = list_users(self.config)
            self.list_widget.clear()
            for u in users:
                item = QListWidgetItem(f"{u.get('email', '')}  ({u.get('role', '')})")
                item.setData(Qt.ItemDataRole.UserRole, u.get("id"))
                self.list_widget.addItem(item)
        except Exception as e:
            from api_client import APIError
            self.list_widget.clear()
            self.list_widget.addItem(QListWidgetItem(f"Feil: {e}"))

    def _add_user(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Legg til bruker")
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("E-post"))
        email_in = QLineEdit()
        email_in.setObjectName("dialogInput")
        layout.addWidget(email_in)
        layout.addWidget(QLabel("Passord"))
        pw_in = QLineEdit()
        pw_in.setEchoMode(QLineEdit.EchoMode.Password)
        pw_in.setObjectName("dialogInput")
        layout.addWidget(pw_in)
        layout.addWidget(QLabel("Rolle"))
        role_combo = QComboBox()
        role_combo.addItems(["user", "admin"])
        layout.addWidget(role_combo)
        row = QHBoxLayout()
        ok = QPushButton("Opprett")
        ok.clicked.connect(dlg.accept)
        cancel = QPushButton("Avbryt")
        cancel.clicked.connect(dlg.reject)
        row.addWidget(cancel)
        row.addWidget(ok)
        layout.addLayout(row)
        if dlg.exec():
            try:
                from api_client import create_user, APIError
                create_user(self.config, email_in.text().strip(), pw_in.text(), role_combo.currentText())
                self._load_users()
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Brukere", str(e)[:200])

    def _remove_user(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        uid = item.data(Qt.ItemDataRole.UserRole)
        if uid == self.current_user.get("id"):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Brukere", "Du kan ikke fjerne deg selv.")
            return
        try:
            from api_client import delete_user
            delete_user(self.config, int(uid))
            self._load_users()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Brukere", str(e)[:200])


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
            "2x2+1": (2, 3),  # to rader, tre kolonner – spesialhåndteres i LayoutCanvas
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
