from __future__ import annotations

from datetime import datetime
from typing import List
import socket
import json

from PySide6.QtCore import QSize, QTimer, Qt, QPoint
from PySide6.QtGui import QPixmap, QGuiApplication, QIcon, QMouseEvent
import uuid

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMenu,
)

from app_styles import AMBER, BLUE, GREEN, RED, get_stylesheet
from data_loader import load_data_from_file
from models import AppConfig, PersonnelRecord, load_config, save_config
from settings_dialog import SettingsDialog
from widgets import CreateLayoutDialog, DataTable, DraggablePanelCard, LayoutCanvas, LayoutWelcomeScreen, LoginScreen, MediaPanel, PanelCard, SectionTitle, ToolbarButton, UsersDialog
from api_client import get_me, logout as api_logout, NotAuthenticatedError
from offline_sync import get_cached_user, set_cached_user

APP_NAME = "OPS Monitor"


class OperationsCenterWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config: AppConfig = load_config()
        self.records: List[PersonnelRecord] = []
        self._ensure_layout_store()
        self._drag_pos: QPoint | None = None
        # Bruk standard OS-vindusramme.
        self.setWindowTitle(APP_NAME)
        # Sørg for at vinduet faktisk kan resizes fritt
        self.setMinimumSize(900, 600)

        # Startstørrelse tilpasses skjermens tilgjengelige areal
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
            start_w = min(1600, max(1024, geo.width() - 80))
            start_h = min(900, max(720, geo.height() - 80))
            self.resize(start_w, start_h)
        else:
            self.resize(1400, 840)

        self.edit_mode = False

        # Timer for automatisk dataoppdatering
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)

        # Nettverksindikator i statuslinjen (online / offline)
        self.net_status_label = QLabel("Sjekker nett…")
        self.net_status_label.setObjectName("netStatusLabel")
        self.statusBar().addPermanentWidget(self.net_status_label)
        self.net_timer = QTimer(self)
        self.net_timer.timeout.connect(self._update_network_status)
        self.net_timer.start(10000)

        self.current_user: dict | None = None
        # Bruk standard OS-vindu, men med vår moderne app-stil.
        self.setStyleSheet(get_stylesheet())
        self.statusBar().showMessage("")
        self._ensure_logged_in()

    def _show_login_screen(self, status_message: str = "Logg inn for å bruke OPS Monitor") -> None:
        """Vis en ny login-skjerm. Bruker QueuedConnection så setCentralWidget
        alltid kjøres mellom event-loop-iterasjoner – aldri inne i en slot-stack."""
        self.current_user = None
        self.statusBar().showMessage(status_message)
        self.login_screen = LoginScreen(self)
        self.setCentralWidget(self.login_screen)
        # QueuedConnection: loginSuccess leveres via event-køen, aldri synkront
        # inne i worker-sloten. Garanterer at setCentralWidget er trygt å kalle.
        self.login_screen.loginSuccess.connect(
            self._on_login_success,
            Qt.ConnectionType.QueuedConnection,
        )

    def build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("windowRoot")
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        main = QWidget()
        main.setObjectName("mainShell")
        ml = QVBoxLayout(main)
        ml.setContentsMargins(18, 16, 18, 18)
        ml.setSpacing(14)

        topbar = QFrame()
        topbar.setObjectName("topBar")
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(14, 10, 14, 10)
        tl.setSpacing(10)
        # Bruk topbar som egendefinert tittel-linje (for drag).
        self.topbar = topbar
        self.topbar.installEventFilter(self)

        self.logo_primary = QLabel()
        self.logo_primary.setObjectName("brandLogo")
        self.logo_secondary = QLabel()
        self.logo_secondary.setObjectName("brandLogo")
        tl.addWidget(self.logo_primary)
        tl.addWidget(self.logo_secondary)

        active_title = self._active_layout().get("title", "Dashboard")
        self.header_title = SectionTitle(active_title, "Build med moduler • Drag & drop")
        tl.addWidget(self.header_title)
        tl.addStretch()

        back_btn = ToolbarButton("Bytt layout", "grid")
        back_btn.clicked.connect(self._back_to_welcome)
        tl.addWidget(back_btn)

        modules_btn = ToolbarButton("Moduler", "grid")
        modules_btn.clicked.connect(self.toggle_modules_drawer)
        tl.addWidget(modules_btn)

        log_btn = ToolbarButton("Logg", "log")
        log_btn.clicked.connect(self.open_log_dialog)
        tl.addWidget(log_btn)

        self.clock_label = QLabel("")
        self.clock_label.setObjectName("clockLabel")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        tl.addWidget(self.clock_label)

        settings_btn = ToolbarButton("", "settings")
        settings_btn.clicked.connect(self.open_settings_dialog)
        tl.addWidget(settings_btn)

        # Global konto-"chip" med avatar + navn/e-post
        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("userAvatar")
        self.avatar_label.setFixedSize(28, 28)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setCursor(Qt.CursorShape.PointingHandCursor)
        # Reroute klikkhendelse til egen handler for konto-meny
        self.avatar_label.mousePressEvent = self._avatar_clicked  # type: ignore[assignment]
        tl.addWidget(self.avatar_label)
        self._update_avatar()

        ml.addWidget(topbar)

        cols_cfg = self.config.columns
        name_col = cols_cfg.get("name", "Navn")
        radio_col = cols_cfg.get("radio", "Sambandsnummer")
        team_col = cols_cfg.get("team", "Team")
        area_col = cols_cfg.get("area", "Område")
        planned_on_col = cols_cfg.get("planned_on", "PlanlagtPåtropp")

        self.status_table = DataTable(["Status", name_col, radio_col, team_col, area_col, "Tid"])
        self.patropp_table = DataTable([name_col, "Tid", "Avvik", "Status"])
        self.avtropp_table = DataTable([name_col, "Tid", "Avvik", "Status"])
        self.late_table = DataTable([name_col, planned_on_col, "Forsinkelse", "Status"])
        self.media_panel = MediaPanel()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setObjectName("logView")

        self.canvas = LayoutCanvas()
        # Viktig: panel-biblioteket må være klart før vi gjenoppretter lagret layout,
        # ellers har ikke canvas noe å bygge modulene fra.
        self.canvas.set_panel_library(self._build_canvas_panel_library())
        self._apply_active_layout_to_canvas()
        self.canvas.layoutChanged.connect(self._save_slot_assignments)
        ml.addWidget(self.canvas, 1)
        shell.addWidget(main, 1)

        # Right-side modules drawer som overlay (ikke en del av layout-bredden)
        self.modules_drawer = QFrame(root)
        self.modules_drawer.setObjectName("modulesDrawer")
        self.modules_drawer.setFixedWidth(320)
        dl = QVBoxLayout(self.modules_drawer)
        dl.setContentsMargins(14, 14, 14, 14)
        dl.setSpacing(12)
        dl.addWidget(SectionTitle("Moduler", "Dra inn i drop-zones"))
        dl.addWidget(self._build_panel_library(), 1)
        self.modules_drawer.setVisible(False)

        self._load_branding()
        self.media_panel.set_files([a.path for a in (self.config.assets or [])])
        self._start_clock()

    def _back_to_welcome(self) -> None:
        """Gå tilbake til velkomstskjermen for å velge/bytte layout."""
        self.edit_mode = False
        self.timer.stop()
        if hasattr(self, "modules_drawer"):
            self.modules_drawer.setVisible(False)
        self.statusBar().showMessage("Velg et dashboard for å starte")
        self._show_welcome_or_dashboard()

    def _build_panel_library(self) -> QWidget:
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Lightweight draggable cards (disse er kun “handles”, ikke selve panelene)
        layout.addWidget(DraggablePanelCard("patropp", "Påtropp", "10 siste • avvik • status", QWidget()))
        layout.addWidget(DraggablePanelCard("avtropp", "Avtropp", "10 siste • avvik • status", QWidget()))
        layout.addWidget(DraggablePanelCard("late", "Forsinket", "ikke skannet / avvik", QWidget()))
        layout.addWidget(DraggablePanelCard("media", "Bilder / dokumenter", "operativ visning", QWidget()))
        layout.addStretch()
        return wrap

    def _build_canvas_panel_library(self) -> dict:
        self.panel_patropp = PanelCard("patropp", "Påtropp – 10 siste", "Navn / tidspunkt / avvik / status", self.patropp_table, tone="green")
        self.panel_avtropp = PanelCard("avtropp", "Avtropp – 10 siste", "Navn / tidspunkt / avvik / status", self.avtropp_table, tone="red")
        self.panel_late = PanelCard("late", "Forsinket / ikke skannet", "Krever oppfølging", self.late_table, tone="amber")
        self.panel_media = PanelCard("media", "Visning av bilder / dokumenter", "Operative filer fra innstillinger", self.media_panel, tone="blue")
        return {
            "patropp": self.panel_patropp,
            "avtropp": self.panel_avtropp,
            "late": self.panel_late,
            "media": self.panel_media,
        }

    def _ensure_layout_store(self) -> None:
        layout = self.config.layout
        layout.setdefault("layouts", [])
        if not layout.get("active_layout_id"):
            layout["active_layout_id"] = ""

        # Migrate legacy single-layout fields into layouts list once.
        if not layout["layouts"]:
            legacy_assignments = layout.get("slot_assignments") or {}
            rows = int(layout.get("rows", 2))
            cols = int(layout.get("cols", 2))
            title = layout.get("title", "Operasjonssentral")
            template = layout.get("template", "2x2")
            layout_id = "layout_" + uuid.uuid4().hex[:8]
            layout["layouts"] = [{
                "id": layout_id,
                "title": title,
                "template": template,
                "rows": rows,
                "cols": cols,
                "slot_assignments": legacy_assignments or {
                    "slot_0": "patropp",
                    "slot_1": "avtropp",
                    "slot_2": "late",
                    "slot_3": "media",
                },
            }]
            layout["active_layout_id"] = layout_id

        if not layout["active_layout_id"]:
            layout["active_layout_id"] = layout["layouts"][0]["id"]
        save_config(self.config)

    def _active_layout(self) -> dict:
        layout = self.config.layout
        active_id = layout.get("active_layout_id", "")
        for entry in layout.get("layouts", []):
            if entry.get("id") == active_id:
                return entry
        return layout.get("layouts", [{}])[0] if layout.get("layouts") else {}

    def _ensure_logged_in(self) -> None:
        """Vis innlogging hvis ikke autentisert; bruk offline cache ved nettfeil."""
        try:
            user = get_me(self.config)
            if user:
                self.current_user = user
                set_cached_user(user)
                self.statusBar().showMessage(f"Logget inn som {user.get('email', '')}  •  {user.get('organization_name', '')}")
                self._show_welcome_or_dashboard()
                return
        except NotAuthenticatedError:
            self._show_login_screen("Logg inn for å bruke OPS Monitor")
            return
        except Exception:
            pass
        # Nettfeil – prøv offline cache
        cached = get_cached_user()
        from auth_store import load_tokens
        tokens = load_tokens()
        if cached and tokens.get("access_token"):
            self.current_user = cached
            self.statusBar().showMessage(f"Offline – {cached.get('email', '')}  •  Synkroniseres ved tilkobling")
            self._update_avatar()
            self._show_welcome_or_dashboard()
            return
        self._show_login_screen("Kunne ikke koble til – sjekk nett og API, eller logg inn")

    def _on_login_success(self, user: dict) -> None:
        """Kalt via QueuedConnection – alltid trygt å bytte centralWidget her."""
        if not user:
            return
        self.current_user = user
        set_cached_user(user)
        self.statusBar().showMessage(
            f"Logget inn som {user.get('email', '')}  •  {user.get('organization_name', '')}"
        )
        self._update_avatar()
        self._show_welcome_or_dashboard()

    def _show_welcome_or_dashboard(self) -> None:
        """Vis alltid velkomstskjerm i appen der bruker velger/lagrer dashboards."""
        layouts = self.config.layout.get("layouts", [])
        self.welcome_screen = LayoutWelcomeScreen(layouts, self)
        self.setCentralWidget(self.welcome_screen)
        self.welcome_screen.layoutSelected.connect(self._on_layout_selected)
        self.welcome_screen.createLayoutRequested.connect(self._on_create_layout_from_welcome)

    def _on_layout_selected(self, layout_id: str) -> None:
        """Bruker har valgt et layout fra velkomstskjermen."""
        if not layout_id:
            return
        self.config.layout["active_layout_id"] = layout_id
        save_config(self.config)
        # Bytt ut velkomstskjermen med selve dashboardet.
        self.build_ui()
        self.statusBar().showMessage("Klar")
        self.refresh_data()
        self.timer.start(15000)

    def _on_create_layout_from_welcome(self) -> None:
        """Åpne dialog for å opprette nytt layout fra velkomstskjermen."""
        layouts = self.config.layout.get("layouts", [])
        base = layouts[-1] if layouts else {"title": "Nytt dashboard", "template": "2x2", "rows": 2, "cols": 2}
        current_title = base.get("title", "Operasjonssentral")
        current_template = base.get("template", "2x2")
        rows = int(base.get("rows", 2))
        cols = int(base.get("cols", 2))
        dlg = CreateLayoutDialog(current_title, current_template, rows, cols, self)
        if not dlg.exec():
            return
        template, r, c = dlg.values()
        new_id = "layout_" + uuid.uuid4().hex[:8]
        entry = {
            "id": new_id,
            "title": dlg.title_value() or f"Dashboard {len(self.config.layout.get('layouts', [])) + 1}",
            "template": template,
            "rows": int(r),
            "cols": int(c),
            "slot_assignments": {},
        }
        self.config.layout.setdefault("layouts", []).append(entry)
        self.config.layout["active_layout_id"] = new_id
        self.config.layout["title"] = entry["title"]
        save_config(self.config)
        # Gå direkte inn i det nye layoutet
        self.build_ui()
        self.statusBar().showMessage("Klar")
        self.refresh_data()
        self.timer.start(15000)

    def _apply_active_layout_to_canvas(self) -> None:
        active = self._active_layout()
        rows = int(active.get("rows", 2))
        cols = int(active.get("cols", 2))
        template = active.get("template", "")
        self.canvas.configure_grid(rows, cols, template)
        # Viktig: vi laster kun lagret layout inn i canvas,
        # vi skal IKKE trigge lagring tilbake til config her.
        self.canvas.restore_assignments(active.get("slot_assignments", {}), emit=False)
        # Sørg for at canvas kjenner til gjeldende edit-mode
        self.canvas.set_edit_mode(self.edit_mode)

    def _update_avatar(self) -> None:
        """Oppdater visuell avatar basert på innlogget bruker."""
        if not hasattr(self, "avatar_label") or self.avatar_label is None:
            return
        if not self.current_user:
            self.avatar_label.setText("")
            self.avatar_label.setToolTip("")
            self.avatar_label.setStyleSheet("")
            return
        email = self.current_user.get("email", "") or ""
        name = self.current_user.get("organization_name", "") or ""
        initial = (email[0].upper() if email else "?")
        self.avatar_label.setText(initial)
        tooltip = email
        if name:
            tooltip = f"{name} – {email}"
        self.avatar_label.setToolTip(tooltip)
        # Moderne, kompakt avatar-chip
        self.avatar_label.setStyleSheet(
            """
            #userAvatar {
                border-radius: 14px;
                background-color: #1d4ed8;
                color: white;
                font-weight: 600;
            }
            """
        )

    def eventFilter(self, obj, event):  # noqa: N802
        # OS håndterer nå dragging / maksimering via standard tittel-linje;
        # vi bruker ikke lenger topbaren som window chrome.
        return super().eventFilter(obj, event)

    def _avatar_clicked(self, event: QMouseEvent) -> None:
        """Vis en profesjonell konto-meny når avatar-klikkes."""
        if event.button() != Qt.MouseButton.LeftButton:
            return
        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #020617;
                border: 1px solid #1f2937;
                border-radius: 8px;
                padding: 4px 0;
            }
            QMenu::item {
                padding: 6px 14px;
                border-radius: 6px;
                color: #e5e7eb;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #1d4ed8;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                margin: 4px 10px;
                background: #111827;
            }
            """
        )
        email = (self.current_user or {}).get("email", "")
        org = (self.current_user or {}).get("organization_name", "")
        header = menu.addAction(email or "Ingen bruker")
        header.setEnabled(False)
        if org:
            org_action = menu.addAction(org)
            org_action.setEnabled(False)
        menu.addSeparator()
        users_action = None
        if self.current_user and self.current_user.get("role") == "admin":
            users_action = menu.addAction("Administrer brukere")
        logout_action = menu.addAction("Logg ut")
        # Åpne menyen under avataren, ikke over.
        global_pos = self.avatar_label.mapToGlobal(self.avatar_label.rect().bottomLeft())
        chosen = menu.exec(global_pos)
        if chosen is users_action:
            self._open_users_dialog()
        elif chosen is logout_action:
            self._do_logout()

    def _refresh_layout_tabs(self) -> None:
        """Oppdater tab-bar med ett faneblad per layout + en «+»-fane."""
        if not self.tab_bar:
            return
        self.tab_bar.blockSignals(True)
        # QTabBar har ikke clear() i alle Qt-bindinger; fjern faner manuelt.
        for i in range(self.tab_bar.count() - 1, -1, -1):
            self.tab_bar.removeTab(i)

        layouts = self.config.layout.get("layouts", [])
        active_id = self.config.layout.get("active_layout_id", "")
        active_index = -1
        for idx, entry in enumerate(layouts):
            title = entry.get("title", "Dashboard")
            tab_index = self.tab_bar.addTab(title)
            self.tab_bar.setTabData(tab_index, entry.get("id"))
            if entry.get("id") == active_id:
                active_index = tab_index

        # Siste fane er alltid "+" for å opprette nytt layout
        plus_index = self.tab_bar.addTab("+")
        self.tab_bar.setTabData(plus_index, None)

        if active_index >= 0:
            self.tab_bar.setCurrentIndex(active_index)
        else:
            self.tab_bar.setCurrentIndex(0 if layouts else plus_index)

        self.tab_bar.blockSignals(False)

    def _on_tab_changed(self, index: int) -> None:
        """Bytt aktivt layout når bruker klikker på en fane."""
        if not self.tab_bar or index < 0:
            return
        layout_id = self.tab_bar.tabData(index)
        # "+"-fane → opprett nytt layout
        if layout_id is None:
            self.open_create_layout_dialog()
            return
        if layout_id == self.config.layout.get("active_layout_id"):
            return
        self.config.layout["active_layout_id"] = layout_id
        active = self._active_layout()
        self.config.layout["title"] = active.get("title", "Dashboard")
        save_config(self.config)
        self._apply_active_layout_to_canvas()
        if hasattr(self, "header_title"):
            self.header_title.set_title(self.config.layout["title"], "Build med moduler • Drag & drop")
        # Ved bytte av faner vil bruker ofte forvente oppdatert data
        self.refresh_data()

    def _on_tab_close_requested(self, index: int) -> None:
        """Lukk (slett) et layout når X på fanen klikkes."""
        if not self.tab_bar or index < 0:
            return
        layout_id = self.tab_bar.tabData(index)
        # Ikke støtt å lukke "+"-fanen
        if layout_id is None:
            return
        # Sett dette layoutet som aktivt og bruk eksisterende slettelogikk
        self.config.layout["active_layout_id"] = layout_id
        save_config(self.config)
        self.delete_current_layout()
        # delete_current_layout oppdaterer aktivt layout; sørg for at faner følger etter
        self._refresh_layout_tabs()

    def _position_modules_drawer(self) -> None:
        if not hasattr(self, "modules_drawer") or not self.modules_drawer.isVisible():
            return
        root = self.centralWidget()
        if not root:
            return
        margin = 18
        drawer_width = self.modules_drawer.width()
        w = root.width()
        h = root.height()
        x = max(margin, w - drawer_width - margin)
        y = margin
        self.modules_drawer.setGeometry(x, y, drawer_width, max(0, h - 2 * margin))

    def _save_slot_assignments(self, assignments: dict) -> None:
        """Lagre slot-assignments lokalt og, hvis mulig, til server (per organisasjon)."""
        active = self._active_layout()
        active["slot_assignments"] = dict(assignments or {})
        save_config(self.config)
        # Forsøk å synkronisere til backend når vi er online og har en bruker
        if not self.current_user:
            return
        try:
            from api_client import update_layout_remote, create_layout_remote, APIError
            remote_id = active.get("remote_id")
            payload = {
                "id": active.get("id"),
                "title": active.get("title", "Dashboard"),
                "template": active.get("template", "2x2"),
                "rows": int(active.get("rows", 2)),
                "cols": int(active.get("cols", 2)),
                "slot_assignments": active.get("slot_assignments", {}) or {},
            }
            if remote_id:
                update_layout_remote(self.config, int(remote_id), payload)
            else:
                created = create_layout_remote(self.config, payload)
                active["remote_id"] = created.get("id")
                save_config(self.config)
        except Exception:
            # Ved feil lar vi bare lokal lagring gjelde; offline-sync kan utvides senere.
            return

    def toggle_modules_drawer(self) -> None:
        self.modules_drawer.setVisible(not self.modules_drawer.isVisible())
        if self.modules_drawer.isVisible():
            self._position_modules_drawer()

    def set_edit_mode(self, enabled: bool) -> None:
        self.edit_mode = enabled
        mode_label = "EDIT MODE" if enabled else "Build med moduler • Drag & drop"
        if hasattr(self, "header_title"):
            self.header_title.set_title(self.config.layout.get("title", "Dashboard"), mode_label)
        self.canvas.set_edit_mode(enabled)

    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            dialog.apply_to_config()
            save_config(self.config)
            self._load_branding()
            self.media_panel.set_files([a.path for a in (self.config.assets or [])])
            self.refresh_data()

    def open_log_dialog(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Hendelseslogg")
        dlg.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        layout.addWidget(SectionTitle("Hendelseslogg", "Systemlogg og hendelser"))
        view = QTextEdit()
        view.setReadOnly(True)
        view.setObjectName("logView")
        view.setPlainText(self.log.toPlainText())
        layout.addWidget(view, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = ToolbarButton("Lukk", "✕")
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dlg.resize(820, 520)
        dlg.exec()

    def export_layout_file(self) -> None:
        """Eksporter aktivt layout til en .opsmonitor-fil."""
        active = self._active_layout()
        if not active:
            QMessageBox.information(self, APP_NAME, "Ingen aktivt layout å eksportere.")
            return
        suggested = (active.get("title") or "dashboard").replace(" ", "_") + ".opsmonitor"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Eksporter layout",
            suggested,
            "OPS Monitor layout (*.opsmonitor);;Alle filer (*.*)",
        )
        if not path:
            return
        bundle = {
            "version": 1,
            "organization_id": self.current_user.get("organization_id") if self.current_user else None,
            "organization_name": self.current_user.get("organization_name", "") if self.current_user else "",
            "layouts": [active],
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(bundle, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, APP_NAME, "Layout eksportert.")
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Kunne ikke eksportere layout:\n{exc}")

    def import_layout_file(self) -> None:
        """Importer ett eller flere layouts fra en .opsmonitor-fil."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importer layout",
            "",
            "OPS Monitor layout (*.opsmonitor);;JSON (*.json);;Alle filer (*.*)",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Kunne ikke lese fil:\n{exc}")
            return
        layouts = data.get("layouts")
        if not isinstance(layouts, list) or not layouts:
            QMessageBox.warning(self, APP_NAME, "Filen inneholder ingen layouts.")
            return
        existing_ids = {l.get("id") for l in self.config.layout.get("layouts", [])}
        imported = []
        for entry in layouts:
            if not isinstance(entry, dict):
                continue
            layout_id = entry.get("id") or "layout_" + uuid.uuid4().hex[:8]
            if layout_id in existing_ids:
                layout_id = "layout_" + uuid.uuid4().hex[:8]
            entry = dict(entry)
            entry["id"] = layout_id
            imported.append(entry)
            existing_ids.add(layout_id)
        if not imported:
            QMessageBox.information(self, APP_NAME, "Ingen gyldige layouts å importere.")
            return
        self.config.layout.setdefault("layouts", []).extend(imported)
        # sett aktivt layout til første importerte
        self.config.layout["active_layout_id"] = imported[0]["id"]
        self.config.layout["title"] = imported[0].get("title", "Dashboard")
        save_config(self.config)
        self._show_welcome_or_dashboard()

    def delete_current_layout(self) -> None:
        layouts = list(self.config.layout.get("layouts", []))
        if not layouts:
            return
        active_id = self.config.layout.get("active_layout_id", "")
        if len(layouts) == 1:
            QMessageBox.warning(self, APP_NAME, "Kan ikke slette eneste layout.\nOpprett et nytt først.")
            return
        title = self._active_layout().get("title", "Dashboard")
        reply = QMessageBox.question(
            self,
            APP_NAME,
            f"Vil du slette layoutet «{title}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        new_layouts = [l for l in layouts if l.get("id") != active_id]
        if not new_layouts:
            return
        self.config.layout["layouts"] = new_layouts
        self.config.layout["active_layout_id"] = new_layouts[0]["id"]
        self.config.layout["title"] = new_layouts[0].get("title", "Dashboard")
        save_config(self.config)
        self._refresh_layout_tabs()
        self._apply_active_layout_to_canvas()
        if hasattr(self, "header_title"):
            self.header_title.set_title(self.config.layout["title"], "Build med moduler • Drag & drop")

    def open_create_layout_dialog(self) -> None:
        active = self._active_layout()
        current_title = active.get("title", "Operasjonssentral")
        current_template = active.get("template", "2x2")
        rows = int(active.get("rows", 2))
        cols = int(active.get("cols", 2))
        dlg = CreateLayoutDialog(current_title, current_template, rows, cols, self)
        if dlg.exec():
            template, r, c = dlg.values()
            new_id = "layout_" + uuid.uuid4().hex[:8]
            entry = {
                "id": new_id,
                "title": dlg.title_value() or f"Dashboard {len(self.config.layout.get('layouts', [])) + 1}",
                "template": template,
                "rows": int(r),
                "cols": int(c),
                # nye layouts skal ALLTID starte helt tomme
                "slot_assignments": {},
            }
            self.config.layout.setdefault("layouts", []).append(entry)
            self.config.layout["active_layout_id"] = new_id
            self.config.layout["title"] = entry["title"]
            save_config(self.config)
            self._refresh_layout_tabs()
            self._apply_active_layout_to_canvas()
            if hasattr(self, "header_title"):
                self.header_title.set_title(entry["title"], "Build med moduler • Drag & drop")

    def refresh_data(self) -> None:
        self.records = self.load_records()
        self.render_tables()
        self.append_log("Data oppdatert")
        self._update_statusbar()

    def _update_statusbar(self) -> None:
        """Oppdater enkel statuslinje nederst i vinduet."""
        layout_title = self._active_layout().get("title", "Dashboard")
        now_txt = datetime.now().strftime("%H:%M:%S")
        self.statusBar().showMessage(f"Layout: {layout_title}  •  Sist oppdatert: {now_txt}")

    def _update_network_status(self) -> None:
        """Oppdater indikator for om enheten har nettverkstilkobling."""
        try:
            # Forsøk en rask TCP-tilkobling til en kjent DNS (ingen data sendes)
            socket.create_connection(("8.8.8.8", 53), timeout=1.0)
            online = True
        except OSError:
            online = False

        if online:
            self.net_status_label.setText("Online")
            self.net_status_label.setStyleSheet("color: #22c55e;")  # grønn
        else:
            self.net_status_label.setText("Offline")
            self.net_status_label.setStyleSheet("color: #f97373;")  # rød

    def load_records(self) -> List[PersonnelRecord]:
        records: List[PersonnelRecord] = []
        try:
            if self.config.patropp_url:
                records.extend(load_data_from_file(self.config.patropp_url, self.config.patropp_sheet, self.config.columns))
            if self.config.avtropp_url and self.config.avtropp_url != self.config.patropp_url:
                records.extend(load_data_from_file(self.config.avtropp_url, self.config.avtropp_sheet, self.config.columns))
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Kunne ikke laste data fra kilde:\n{exc}")
            self.append_log(f"Feil ved lasting av data: {exc}")
        return records

    def render_tables(self) -> None:
        now = datetime.now()
        on = [r for r in self.records if r.actual_on and not r.actual_off]
        soon = [
            r
            for r in self.records
            if not r.actual_on
            and r.planned_on
            and 0 <= int((r.planned_on - now).total_seconds() / 60) <= 60
        ]
        # Forsinket / ikke skannet: planlagt tid har passert og ingen faktisk påtropp
        late_unscanned = [
            r for r in self.records if (not r.actual_on and r.planned_on and r.planned_on < now)
        ]
        # Forsinket, men skannet inn: faktisk påtropp senere enn planlagt
        late_scanned = [
            r
            for r in self.records
            if r.actual_on and r.planned_on and r.actual_on > r.planned_on
        ]
        off = [r for r in self.records if r.actual_off]

        # Oppdater statistikk i panel-headerne
        if hasattr(self, "panel_patropp"):
            patropp_last = sorted([r for r in self.records if r.actual_on], key=lambda x: x.actual_on, reverse=True)[:10]
            self.panel_patropp.set_header_title(f"Påtropp – 10 siste ({len(patropp_last)})", "Navn / tidspunkt / avvik / status")
        if hasattr(self, "panel_avtropp"):
            avtropp_last = sorted(off, key=lambda x: x.actual_off, reverse=True)[:10]
            self.panel_avtropp.set_header_title(f"Avtropp – 10 siste ({len(avtropp_last)})", "Navn / tidspunkt / avvik / status")
        if hasattr(self, "panel_late"):
            self.panel_late.set_header_title(
                f"Forsinket / ikke skannet ({len(late_unscanned) + len(late_scanned)})",
                "Krever oppfølging",
            )

        # Fyll tabellene med rader basert på PersonnelRecord
        self.status_table.load_rows(
            [["PÅ", r.name, r.radio, r.team, r.area, r.actual_on.strftime("%H:%M") if r.actual_on else ""]
             for r in on[:30]]
            + [["SNART", r.name, r.radio, r.team, r.area, r.planned_on.strftime("%H:%M") if r.planned_on else ""]
               for r in soon[:30]]
        )

        patropp_last = sorted([r for r in self.records if r.actual_on], key=lambda x: x.actual_on, reverse=True)[:10]
        avtropp_last = sorted(off, key=lambda x: x.actual_off, reverse=True)[:10]

        self.patropp_table.load_rows(
            [[
                r.name,
                r.actual_on.strftime("%H:%M") if r.actual_on else "",
                self.deviation_text(r.actual_on, r.planned_on),
                self.scan_status(r.actual_on, r.planned_on),
            ] for r in patropp_last],
            [i for i, r in enumerate(patropp_last) if self.is_late(r.actual_on, r.planned_on)],
        )

        self.avtropp_table.load_rows(
            [[
                r.name,
                r.actual_off.strftime("%H:%M") if r.actual_off else "",
                self.deviation_text(r.actual_off, r.planned_off),
                self.scan_status(r.actual_off, r.planned_off),
            ] for r in avtropp_last],
            [i for i, r in enumerate(avtropp_last) if self.is_late(r.actual_off, r.planned_off)],
        )

        # Kombiner både ikke-skannede og skannede forsinkede i Forsinket-modulen
        late_rows = []
        alarm_indices = []
        idx = 0
        for r in late_unscanned[:30]:
            late_rows.append([
                r.name,
                r.planned_on.strftime("%H:%M") if r.planned_on else "",
                f"{int((now - r.planned_on).total_seconds() / 60)} min" if r.planned_on else "",
                "Ikke skannet",
            ])
            alarm_indices.append(idx)
            idx += 1
        for r in late_scanned[:30]:
            late_rows.append([
                r.name,
                r.planned_on.strftime("%H:%M") if r.planned_on else "",
                self.deviation_text(r.actual_on, r.planned_on),
                "Skannet forsinket",
            ])
            alarm_indices.append(idx)
            idx += 1

        self.late_table.load_rows(late_rows, alarm_indices)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        # Flytt overlay-draweren, men la OS styre maks vindusstørrelse som for andre apper
        self._position_modules_drawer()

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        menu = QMenu(self)
        edit_action = menu.addAction("Edit mode")
        display_action = menu.addAction("Display mode")
        new_window_action = menu.addAction("Åpne nytt vindu")
        export_action = menu.addAction("Eksporter layout…")
        import_action = menu.addAction("Importer layout…")
        users_action = None
        if self.current_user and self.current_user.get("role") == "admin":
            users_action = menu.addAction("Administrer brukere")
        menu.addSeparator()
        logout_action = menu.addAction("Logg ut")
        if self.edit_mode:
            edit_action.setEnabled(False)
        else:
            display_action.setEnabled(False)

        chosen = menu.exec(event.globalPos())
        if chosen is edit_action:
            self.set_edit_mode(True)
        elif chosen is display_action:
            self.set_edit_mode(False)
        elif chosen is new_window_action:
            self.open_new_window()
        elif chosen is export_action:
            self.export_layout_file()
        elif chosen is import_action:
            self.import_layout_file()
        elif chosen is users_action:
            self._open_users_dialog()
        elif chosen is logout_action:
            self._do_logout()

    def _open_users_dialog(self) -> None:
        if not self.current_user or self.current_user.get("role") != "admin":
            return
        dlg = UsersDialog(self.config, self.current_user, self)
        dlg.exec()

    def open_new_window(self) -> None:
        """Åpne et nytt hovedvindu (for flere dashboard-visninger samtidig)."""
        app = QApplication.instance()
        if app is None:
            return
        win = OperationsCenterWindow()
        win.show()

    def _do_logout(self) -> None:
        """Logg brukeren robust ut av klienten og vis innloggingsskjerm."""
        api_logout()  # sletter tokens + offline-cache på disk
        self.current_user = None
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()
        if hasattr(self, "modules_drawer"):
            self.modules_drawer.setVisible(False)
        self._update_avatar()
        self.statusBar().showMessage("Logg inn for å bruke OPS Monitor")

        # Vis en helt ny innloggingsskjerm uten å forsøke automatisk /me-kall.
        self._show_login_screen("Logg inn for å bruke OPS Monitor")

    def deviation_text(self, actual, planned) -> str:
        if not planned:
            return "-"
        if not actual:
            return "Ikke skannet"
        delta = int((actual - planned).total_seconds() / 60)
        if delta == 0:
            return "0 min"
        return f"{delta:+} min"

    def scan_status(self, actual, planned) -> str:
        if not actual:
            return "Ikke skannet"
        if planned and actual > planned:
            return "Forsinket"
        return "OK"

    def is_late(self, actual, planned) -> bool:
        return bool(actual and planned and actual > planned)

    def append_log(self, text: str) -> None:
        self.log.append(f"[{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] {text}")

    def _start_clock(self) -> None:
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._tick_clock)
        self.clock_timer.start(1000)
        self._tick_clock()

    def _tick_clock(self) -> None:
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S"))

    def _load_branding(self) -> None:
        def set_logo(label: QLabel, path: str) -> None:
            label.clear()
            label.setFixedHeight(28)
            label.setMinimumWidth(28)
            if not path:
                label.setVisible(False)
                return
            pix = QPixmap(path)
            if pix.isNull():
                label.setVisible(False)
                return
            label.setVisible(True)
            label.setPixmap(pix.scaledToHeight(28, Qt.TransformationMode.SmoothTransformation))

        set_logo(self.logo_primary, self.config.branding.get("logo_primary", ""))
        set_logo(self.logo_secondary, self.config.branding.get("logo_secondary", ""))


def main() -> None:
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    # Sett globalt app-ikon til opsmonitor-logoen for desktop/dock
    app.setWindowIcon(QIcon("assets/opsmonitor.svg"))
    window = OperationsCenterWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
