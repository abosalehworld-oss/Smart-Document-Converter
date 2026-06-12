"""
Styles - الثيم الداكن الاحترافي
=================================
ألوان وأنماط QSS لواجهة PySide6.
"""

# ============================================
# لوحة الألوان
# ============================================
COLORS = {
    'bg_darkest': '#0a0a14',
    'bg_dark': '#0f0f1e',
    'bg_medium': '#161630',
    'bg_card': '#1c1c3a',
    'bg_card_hover': '#242450',
    'bg_input': '#12122a',
    'bg_sidebar': '#0d0d1f',
    
    'primary': '#6c5ce7',
    'primary_hover': '#7f70f0',
    'primary_dark': '#4834d4',
    
    'accent': '#00cec9',
    'accent_hover': '#00e6e0',
    
    'success': '#00b894',
    'success_bg': '#00b89422',
    
    'danger': '#e94560',
    'danger_hover': '#ff5a7a',
    'danger_bg': '#e9456022',
    
    'warning': '#fdcb6e',
    'warning_bg': '#fdcb6e22',
    
    'text_primary': '#e8e8f0',
    'text_secondary': '#8888aa',
    'text_muted': '#555570',
    
    'border': '#2a2a50',
    'border_hover': '#3a3a65',
    'border_focus': '#6c5ce7',
    
    'scrollbar': '#2a2a50',
    'scrollbar_hover': '#3a3a65',
}


# ============================================
# QSS Stylesheet الرئيسي
# ============================================
DARK_THEME_QSS = f"""
/* ===== الخلفية العامة ===== */
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}

QWidget {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Simplified Arabic', Arial;
    font-size: 13px;
}}

/* ===== الأزرار ===== */
QPushButton {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_muted']};
}}

QPushButton#btn_danger {{
    background-color: {COLORS['danger']};
}}

QPushButton#btn_danger:hover {{
    background-color: {COLORS['danger_hover']};
}}

QPushButton#btn_success {{
    background-color: {COLORS['success']};
}}

QPushButton#btn_secondary {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
}}

QPushButton#btn_secondary:hover {{
    background-color: {COLORS['bg_card_hover']};
    border-color: {COLORS['border_hover']};
}}

/* ===== الشريط الجانبي ===== */
QWidget#sidebar {{
    background-color: {COLORS['bg_sidebar']};
    border-right: 1px solid {COLORS['border']};
}}

QPushButton#sidebar_btn {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    border: none;
    border-radius: 8px;
    padding: 14px 16px;
    text-align: left;
    font-size: 14px;
}}

QPushButton#sidebar_btn:hover {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
}}

QPushButton#sidebar_btn_active {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 14px 16px;
    text-align: left;
    font-size: 14px;
    font-weight: bold;
}}

/* ===== حقول الإدخال ===== */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    selection-background-color: {COLORS['primary']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['border_focus']};
}}

/* ===== القوائم المنسدلة ===== */
QComboBox {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 14px;
    min-height: 20px;
}}

QComboBox:hover {{
    border-color: {COLORS['border_hover']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    selection-background-color: {COLORS['primary']};
}}

/* ===== التبويبات ===== */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['bg_dark']};
}}

QTabBar::tab {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    padding: 10px 20px;
    margin-right: 2px;
    font-size: 13px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['primary']};
    color: white;
    font-weight: bold;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['bg_card_hover']};
}}

/* ===== شريط التقدم ===== */
QProgressBar {{
    background-color: {COLORS['bg_input']};
    border: none;
    border-radius: 10px;
    min-height: 20px;
    text-align: center;
    color: white;
    font-weight: bold;
}}

QProgressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']},
        stop:1 {COLORS['accent']}
    );
    border-radius: 10px;
}}

/* ===== العناوين ===== */
QLabel#title {{
    color: {COLORS['text_primary']};
    font-size: 22px;
    font-weight: bold;
}}

QLabel#subtitle {{
    color: {COLORS['text_secondary']};
    font-size: 14px;
}}

QLabel#card_title {{
    color: {COLORS['text_primary']};
    font-size: 16px;
    font-weight: bold;
}}

QLabel#status_label {{
    color: {COLORS['accent']};
    font-size: 13px;
}}

QLabel#error_label {{
    color: {COLORS['danger']};
    font-size: 13px;
}}

/* ===== البطاقات (Cards) ===== */
QFrame#card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px;
}}

QFrame#card:hover {{
    border-color: {COLORS['border_hover']};
}}

/* ===== شريط التمرير ===== */
QScrollBar:vertical {{
    background-color: {COLORS['bg_dark']};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['scrollbar']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['scrollbar_hover']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_dark']};
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['scrollbar']};
    border-radius: 5px;
    min-width: 30px;
}}

/* ===== Spin Box ===== */
QSpinBox {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px;
}}

/* ===== Check Box ===== */
QCheckBox {{
    color: {COLORS['text_primary']};
    font-size: 13px;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid {COLORS['border']};
    background-color: {COLORS['bg_input']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}

/* ===== Group Box ===== */
QGroupBox {{
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 4px 12px;
    background-color: {COLORS['bg_dark']};
    border-radius: 4px;
}}

/* ===== Status Bar ===== */
QStatusBar {{
    background-color: {COLORS['bg_sidebar']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
    font-size: 12px;
    padding: 4px;
}}

/* ===== Menu Bar ===== */
QMenuBar {{
    background-color: {COLORS['bg_sidebar']};
    color: {COLORS['text_primary']};
    border-bottom: 1px solid {COLORS['border']};
}}

QMenuBar::item:selected {{
    background-color: {COLORS['primary']};
    border-radius: 4px;
}}

/* ===== Tool Tip ===== */
QToolTip {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px;
    font-size: 12px;
}}

/* ===== List Widget ===== */
QListWidget {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}

QListWidget::item {{
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px;
}}

QListWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

QListWidget::item:hover:!selected {{
    background-color: {COLORS['bg_card']};
}}
"""
