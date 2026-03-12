BG = "#0b1118"
PANEL = "#111922"
PANEL_2 = "#172230"
TEXT = "#e7eef8"
MUTED = "#8b98ab"
ACCENT = "#2dd4bf"
GREEN = "#32d583"
BLUE = "#53b1fd"
AMBER = "#fdb022"
RED = "#ff5d73"


# Tverrplatform font-stack: macOS (San Francisco), Windows (Segoe UI), ChromeOS (Roboto)
FONT_FAMILY = (
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
    '"Helvetica Neue", Arial, sans-serif'
)


def get_stylesheet() -> str:
    return f"""
    * {{
        color: {TEXT};
        font-family: {FONT_FAMILY};
        font-size: 14px;
        font-weight: 400;
        border: none;
        outline: none;
    }}
    QMainWindow, QWidget {{
        background: {BG};
    }}
    #topBar {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f1722, stop:1 #0b1118);
        border: 1px solid #1d2a39;
        border-radius: 16px;
    }}
    #modulesDrawer {{
        background: #0c131c;
        border-left: 1px solid #1d2a39;
    }}
    #sectionTitle {{
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    #sectionSubtitle {{
        color: {MUTED};
        font-size: 13px;
        font-weight: 500;
    }}
    #toolbarButton, #sideButton {{
        background: #192432;
        border-radius: 12px;
        padding: 10px 12px;
        text-align: left;
        font-weight: 600;
    }}
    #toolbarButton:hover, #sideButton:hover {{
        background: #203040;
    }}
    #panel, #statCard {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PANEL}, stop:1 {PANEL_2});
        border: 1px solid #223245;
        border-radius: 16px;
    }}
    #panel[tone="green"] {{
        border: 1px solid rgba(50, 213, 131, 0.35);
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #101d1a, stop:1 {PANEL_2});
    }}
    #panel[tone="red"] {{
        border: 1px solid rgba(255, 93, 115, 0.32);
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #231318, stop:1 {PANEL_2});
    }}
    #panel[tone="amber"] {{
        border: 1px solid rgba(253, 176, 34, 0.30);
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #211a12, stop:1 {PANEL_2});
    }}
    #panel[tone="blue"] {{
        border: 1px solid rgba(83, 177, 253, 0.28);
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #111a24, stop:1 {PANEL_2});
    }}
    #statTitle {{
        color: {MUTED};
        font-size: 12px;
        font-weight: 600;
    }}
    #statValue {{
        font-size: 32px;
        font-weight: 800;
    }}
    #statSubtitle {{
        color: {MUTED};
        font-size: 12px;
        font-weight: 500;
    }}
    #panelClose {{
        background: rgba(255, 255, 255, 0.04);
        color: {MUTED};
        border-radius: 11px;
        font-size: 11px;
        padding: 0;
        min-width: 0;
    }}
    #panelClose:hover {{
        background: rgba(255, 93, 115, 0.35);
        color: {TEXT};
    }}
    /* Avoid "dark boxes behind text" by default; panels define their own surfaces */
    QLineEdit, QTextEdit, QListWidget, QComboBox {{
        background: transparent;
    }}
    #dataTable, #logView, #dashboardBuilder, #mediaList, #mediaPreview {{
        background: transparent;
        border-radius: 10px;
    }}
    QTableWidget {{
        alternate-background-color: #0e1721;
    }}
    #dropSlot {{
        background: rgba(15, 24, 34, 0.55);
        border: 1px dashed #2a3a4f;
        border-radius: 16px;
    }}
    #dropSlot[dragActive="true"] {{
        background: rgba(45, 212, 191, 0.09);
        border: 2px solid {ACCENT};
    }}
    #dropPlaceholder {{
        color: {MUTED};
        font-size: 13px;
        font-weight: 500;
    }}
    QHeaderView::section {{
        background: transparent;
        color: {MUTED};
        padding: 8px;
        font-size: 12px;
        font-weight: 600;
        border: none;
    }}
    QTableWidget {{
        padding: 4px;
        gridline-color: transparent;
    }}
    QTableWidget::item {{
        padding: 6px 8px;
        border-radius: 8px;
    }}
    QTableWidget::item:selected {{
        background: rgba(45, 212, 191, 0.20);
        color: {TEXT};
    }}
    QLineEdit {{
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(34, 50, 69, 0.85);
        border-radius: 12px;
        padding: 10px 12px;
        font-weight: 400;
    }}

    QDialog {{
        background: {BG};
    }}
    QTabWidget::pane {{
        border: 1px solid #223245;
        border-radius: 14px;
        top: -1px;
        background: #0f1822;
    }}
    QTabWidget::tab-bar {{
        left: 10px;
    }}
    QTabBar::tab {{
        background: #101923;
        border: 1px solid #223245;
        padding: 10px 12px;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
        margin-right: 6px;
        color: {MUTED};
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background: #0f1822;
        color: {TEXT};
        border-bottom-color: #0f1822;
    }}
    QLabel {{
        color: {TEXT};
        background: transparent;
        font-weight: 400;
    }}
    QMessageBox {{
        background: {BG};
    }}
    QPushButton {{
        padding: 10px 12px;
        border-radius: 12px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background: rgba(255, 255, 255, 0.04);
    }}
    #clockLabel {{
        font-size: 18px;
        font-weight: 700;
        letter-spacing: 0.05em;
        padding: 0 10px;
        color: {TEXT};
    }}
    #layoutCombo {{
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(34, 50, 69, 0.85);
        border-radius: 12px;
        padding: 8px 10px;
        min-width: 160px;
    }}
    #kpiPill {{
        padding: 6px 10px;
        border-radius: 999px;
        font-weight: 900;
        font-size: 12px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(34, 50, 69, 0.85);
        min-width: 64px;
    }}
    #kpiPill[tone="green"] {{
        border: 1px solid rgba(50, 213, 131, 0.45);
        background: rgba(50, 213, 131, 0.10);
    }}
    #kpiPill[tone="red"] {{
        border: 1px solid rgba(255, 93, 115, 0.42);
        background: rgba(255, 93, 115, 0.10);
    }}
    #kpiPill[tone="amber"] {{
        border: 1px solid rgba(253, 176, 34, 0.40);
        background: rgba(253, 176, 34, 0.10);
    }}
    #brandLogo {{
        padding-left: 6px;
        padding-right: 6px;
    }}
    QListWidget::item {{
        margin: 4px;
    }}

    /* Statusbar nederst – litt lysere/egen flate enn hovedpanelet */
    QStatusBar {{
        background: #050910;
        border-top: 1px solid #1b2433;
        padding: 4px 10px;
        color: {MUTED};
        font-weight: 500;
    }}
    QStatusBar QLabel {{
        color: {MUTED};
        font-weight: 500;
    }}

    /* Velkomstskjerm */
    #welcomeScreen {{
        background: {BG};
    }}
    #welcomeLogo {{
        margin-right: 16px;
    }}
    #welcomeCard {{
        background: #0f1822;
        border-radius: 20px;
        border: 1px solid #243549;
        min-width: 520px;
        max-width: 720px;
    }}
    #welcomeTitle {{
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    #welcomeSubtitle {{
        color: {MUTED};
        font-size: 13px;
        font-weight: 500;
    }}
    #layoutList {{
        background: #050910;
        border-radius: 12px;
        padding: 4px;
    }}
    #layoutList::item {{
        margin: 2px 0;
        padding: 8px 10px;
        border-radius: 8px;
    }}
    #layoutList::item:selected {{
        background: rgba(45, 212, 191, 0.16);
    }}
    /* Hovedknapp på velkomstskjermen – høy kontrast */
    #welcomeOpenButton {{
        background: #e7eef8;
        color: #0b1118;
        border: none;
        border-radius: 14px;
        padding: 14px 20px;
        font-weight: 700;
        font-size: 15px;
    }}
    #welcomeOpenButton:hover {{
        background: #f0f4fa;
        color: #0b1118;
    }}

    /* Create layout dialog + innstillinger */
    #dialogTitle {{
        font-size: 18px;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    #dialogClose {{
        background: transparent;
        color: {ACCENT};
        font-size: 16px;
        padding: 6px 10px;
        border-radius: 10px;
    }}
    #dialogClose:hover {{
        background: rgba(45, 212, 191, 0.12);
    }}
    #dialogCard {{
        background: #101923;
        border: 1px solid #223245;
        border-radius: 16px;
    }}
    #dialogInput {{
        background: #182433;
        border: 1px solid #243549;
        border-radius: 12px;
        padding: 12px 12px;
        font-size: 14px;
        font-weight: 400;
    }}
    #dialogSectionLabel {{
        color: {MUTED};
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.02em;
        margin-top: 6px;
    }}
    #templateRow {{
        background: #101923;
        border-bottom: 1px solid #1b2a3c;
    }}
    #templateRow[selected="true"] {{
        background: #111e2a;
    }}
    #templateIcon {{
        color: {MUTED};
        font-size: 14px;
        min-width: 22px;
    }}
    #templateLabel {{
        font-size: 13px;
        font-weight: 700;
    }}
    #templateCheck {{
        color: {ACCENT};
        font-size: 16px;
        font-weight: 900;
        min-width: 16px;
    }}
    #primaryButton {{
        background: {ACCENT};
        color: #031513;
        border-radius: 14px;
        padding: 14px 16px;
        font-weight: 700;
        font-size: 14px;
    }}
    #primaryButton:hover {{
        background: #36e0d2;
    }}
    #secondaryButton {{
        background: #192432;
        border: 1px solid #243549;
        border-radius: 14px;
        padding: 12px 16px;
        font-weight: 600;
        font-size: 14px;
    }}
    #secondaryButton:hover {{
        background: #203040;
        border-color: #2a3a4f;
    }}

    /* Media */
    #mediaList {{
        background: #0f1822;
        border-radius: 12px;
    }}
    #mediaPreview {{
        background: #0f1822;
        border-radius: 12px;
    }}
    #mediaImage {{
        color: {MUTED};
        font-size: 13px;
        font-weight: 500;
    }}
    """
