"""
Main Window - النافذة الرئيسية
================================
النافذة الرئيسية مع شريط جانبي للتنقل.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QStatusBar, QSizePolicy, QApplication, QMessageBox,
    QSpacerItem
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QIcon
import logging

from app.gui.styles import DARK_THEME_QSS, COLORS
from app.gui.pdf_tab import PDFTab
from app.gui.image_tab import ImageTab
from app.gui.settings_tab import SettingsTab, load_settings, save_settings
from app.gui.workers import OCRLoadWorker
from app.utils.arabic_utils import tr

from app.core.ocr_engine import OCREngine
from app.core.image_processor import ImageProcessor

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """النافذة الرئيسية للبرنامج."""
    
    def __init__(self):
        super().__init__()
        
        # تحميل الإعدادات
        self.settings = load_settings()
        self._current_lang = self.settings.get('language', 'ar')
        
        # إنشاء المحرك
        self.ocr_engine = OCREngine(
            languages=self.settings.get('ocr_languages', ['ar', 'en']),
            gpu=False
        )
        self.image_processor = ImageProcessor()
        
        # إعداد النافذة
        self._setup_window()
        self._setup_ui()
        
        # تحميل OCR في الخلفية
        QTimer.singleShot(500, self._load_ocr_engine)
    
    def _setup_window(self):
        """إعداد خصائص النافذة."""
        self.setWindowTitle(tr('app_title', self._current_lang))
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # تطبيق الثيم الداكن
        self.setStyleSheet(DARK_THEME_QSS)
        
        # ضبط اتجاه الواجهة
        self._apply_layout_direction()
    
    def _apply_layout_direction(self):
        """تطبيق اتجاه الواجهة حسب اللغة."""
        if self._current_lang == 'ar':
            QApplication.instance().setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            QApplication.instance().setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    
    def _setup_ui(self):
        """بناء واجهة المستخدم."""
        # الـ widget المركزي
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ===== الشريط الجانبي =====
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        # ===== المحتوى الرئيسي =====
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # الشريط العلوي
        top_bar = self._create_top_bar()
        content_layout.addWidget(top_bar)
        
        # منطقة الصفحات
        self._stack = QStackedWidget()
        
        # إنشاء التبويبات
        self._pdf_tab = PDFTab(self.ocr_engine, self.image_processor, self.settings)
        self._image_tab = ImageTab(self.ocr_engine, self.image_processor, self.settings)
        self._settings_tab = SettingsTab(self.settings)
        self._settings_tab.language_changed.connect(self._on_language_changed)
        self._settings_tab.settings_changed.connect(self._on_settings_changed)
        
        self._stack.addWidget(self._pdf_tab)
        self._stack.addWidget(self._image_tab)
        self._stack.addWidget(self._settings_tab)
        
        content_layout.addWidget(self._stack, 1)
        
        main_layout.addWidget(content_area, 1)
        
        # ===== شريط الحالة =====
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_label = QLabel(tr('ready', self._current_lang))
        self._status_bar.addWidget(self._status_label)
        
        # تحديد الصفحة الافتراضية
        self._switch_tab(0)
    
    def _create_sidebar(self) -> QWidget:
        """إنشاء الشريط الجانبي."""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"""
            QWidget#sidebar {{
                background-color: {COLORS['bg_sidebar']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(8)
        
        # الشعار
        logo_label = QLabel("🔒")
        logo_label.setStyleSheet("font-size: 36px; border: none;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        
        app_name = QLabel(tr('app_title', self._current_lang))
        app_name.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 14px;
            font-weight: bold;
            border: none;
        """)
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setWordWrap(True)
        layout.addWidget(app_name)
        self._app_name_label = app_name
        
        layout.addSpacing(24)
        
        # أزرار التنقل
        self._nav_buttons = []
        
        nav_items = [
            ("📄", tr('tab_pdf', self._current_lang)),
            ("🖼️", tr('tab_images', self._current_lang)),
            ("⚙️", tr('tab_settings', self._current_lang)),
        ]
        
        for i, (icon, text) in enumerate(nav_items):
            btn = QPushButton(f"  {icon}  {text}")
            btn.setObjectName("sidebar_btn")
            btn.setMinimumHeight(48)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._get_nav_btn_style(False))
            btn.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            layout.addWidget(btn)
            self._nav_buttons.append(btn)
        
        layout.addStretch()
        
        # حقوق الملكية (Developer Info)
        dev_frame = QFrame()
        dev_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        dev_layout = QVBoxLayout(dev_frame)
        dev_layout.setContentsMargins(10, 10, 10, 10)
        dev_layout.setSpacing(4)
        
        dev_title = QLabel("تم التطوير بواسطة:")
        dev_title.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none; background: transparent;")
        dev_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        dev_charity = QLabel("تم تطوير هذا العمل لوجه الله تعالى\nبشكل مجاني للعمل أوفلاين بدون إنترنت")
        dev_charity.setStyleSheet(f"color: {COLORS['success']}; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        dev_charity.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_charity.setWordWrap(True)
        
        dev_name = QLabel("Mohamed Saleh")
        dev_name.setStyleSheet(f"color: {COLORS['primary']}; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        dev_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        dev_phone = QLabel("📞 01025794796")
        dev_phone.setStyleSheet(f"color: {COLORS['accent']}; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        dev_phone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        dev_email = QLabel("📧 abosalehworld@gmail.com")
        dev_email.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px; border: none; background: transparent;")
        dev_email.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        dev_links = QLabel("<a href='https://github.com/abosalehworld-oss/Smart-Document-Converter' style='color:#3498db;text-decoration:none;'>GitHub</a> | <a href='https://linkedin.com/in/mr-mohamed-saleh' style='color:#3498db;text-decoration:none;'>LinkedIn</a>")
        dev_links.setOpenExternalLinks(True)
        dev_links.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_links.setStyleSheet("border: none; background: transparent;")
        
        dev_rights = QLabel("© حقوق الملكية محفوظة 2026")
        dev_rights.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none; background: transparent;")
        dev_rights.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        dev_layout.addWidget(dev_charity)
        dev_layout.addWidget(dev_title)
        dev_layout.addWidget(dev_name)
        dev_layout.addWidget(dev_phone)
        dev_layout.addWidget(dev_email)
        dev_layout.addWidget(dev_links)
        dev_layout.addWidget(dev_rights)
        
        layout.addWidget(dev_frame)
        
        # معلومات الإصدار
        version_label = QLabel("v2.0.0 | Offline & Secure")
        version_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
            border: none;
            margin-top: 5px;
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        return sidebar
    
    def _create_top_bar(self) -> QWidget:
        """إنشاء الشريط العلوي."""
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_darkest']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # عنوان الصفحة الحالية
        self._page_title = QLabel(tr('tab_pdf', self._current_lang))
        self._page_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: bold;
            border: none;
        """)
        layout.addWidget(self._page_title)
        
        layout.addStretch()
        
        # حالة OCR
        self._ocr_status = QLabel("⏳ " + tr('loading_ocr', self._current_lang))
        self._ocr_status.setStyleSheet(f"""
            color: {COLORS['warning']};
            font-size: 12px;
            border: none;
        """)
        layout.addWidget(self._ocr_status)
        
        layout.addSpacing(16)
        
        # زر تبديل اللغة
        self._lang_btn = QPushButton("AR | EN")
        self._lang_btn.setFixedSize(80, 32)
        self._lang_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_hover']};
                border-color: {COLORS['primary']};
            }}
        """)
        self._lang_btn.clicked.connect(self._toggle_language)
        layout.addWidget(self._lang_btn)
        
        return bar
    
    def _get_nav_btn_style(self, active: bool) -> str:
        """إرجاع ستايل زر التنقل."""
        if active:
            return f"""
                QPushButton {{
                    background-color: {COLORS['primary']};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 16px;
                    text-align: left;
                    font-size: 14px;
                    font-weight: bold;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_secondary']};
                    border: none;
                    border-radius: 10px;
                    padding: 12px 16px;
                    text-align: left;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_card']};
                    color: {COLORS['text_primary']};
                }}
            """
    
    def _switch_tab(self, index: int):
        """تبديل التبويب المعروض."""
        self._stack.setCurrentIndex(index)
        
        # تحديث أزرار التنقل
        for i, btn in enumerate(self._nav_buttons):
            btn.setStyleSheet(self._get_nav_btn_style(i == index))
        
        # تحديث عنوان الصفحة
        titles = [
            tr('tab_pdf', self._current_lang),
            tr('tab_images', self._current_lang),
            tr('tab_settings', self._current_lang),
        ]
        if index < len(titles):
            self._page_title.setText(titles[index])
    
    def _toggle_language(self):
        """تبديل اللغة بين العربي والإنجليزي."""
        new_lang = 'en' if self._current_lang == 'ar' else 'ar'
        self._on_language_changed(new_lang)
    
    def _on_language_changed(self, lang: str):
        """معالجة تغيير اللغة."""
        self._current_lang = lang
        self.settings['language'] = lang
        save_settings(self.settings)
        
        # تطبيق الاتجاه
        self._apply_layout_direction()
        
        # تحديث العنوان
        self.setWindowTitle(tr('app_title', lang))
        self._app_name_label.setText(tr('app_title', lang))
        
        # تحديث أزرار التنقل
        nav_texts = [
            ("📄", tr('tab_pdf', lang)),
            ("🖼️", tr('tab_images', lang)),
            ("⚙️", tr('tab_settings', lang)),
        ]
        for i, (icon, text) in enumerate(nav_texts):
            self._nav_buttons[i].setText(f"  {icon}  {text}")
        
        # تحديث عنوان الصفحة
        current_idx = self._stack.currentIndex()
        titles = [tr('tab_pdf', lang), tr('tab_images', lang), tr('tab_settings', lang)]
        if current_idx < len(titles):
            self._page_title.setText(titles[current_idx])
        
        # تحديث حالة OCR
        if self.ocr_engine.is_loaded:
            self._ocr_status.setText("✅ " + tr('ocr_loaded', lang))
        else:
            self._ocr_status.setText("⏳ " + tr('loading_ocr', lang))
        
        # تحديث شريط الحالة
        self._status_label.setText(tr('ready', lang))
    
    def _on_settings_changed(self, settings: dict):
        """معالجة تغيير الإعدادات."""
        self.settings.update(settings)
        
        # تحديث لغات OCR إذا تغيرت
        new_langs = settings.get('ocr_languages', ['ar', 'en'])
        if set(new_langs) != set(self.ocr_engine.languages):
            self.ocr_engine.languages = new_langs
            # إعادة تحميل OCR سيتم عند الاستخدام التالي
            self.ocr_engine._is_loaded = False
            self.ocr_engine._reader = None
            self._load_ocr_engine()
    
    def _load_ocr_engine(self):
        """تحميل محرك OCR في الخلفية."""
        self._ocr_status.setText("⏳ " + tr('loading_ocr', self._current_lang))
        self._ocr_status.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12px; border: none;")
        
        self._ocr_worker = OCRLoadWorker(self.ocr_engine)
        self._ocr_worker.progress.connect(lambda msg: self._status_label.setText(msg))
        self._ocr_worker.finished.connect(self._on_ocr_loaded)
        self._ocr_worker.start()
    
    def _on_ocr_loaded(self, success: bool, message: str):
        """عند اكتمال تحميل OCR."""
        if success:
            self._ocr_status.setText("✅ " + tr('ocr_loaded', self._current_lang))
            self._ocr_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px; border: none;")
            self._status_label.setText(tr('ready', self._current_lang))
        else:
            self._ocr_status.setText("❌ " + message)
            self._ocr_status.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px; border: none;")
            self._status_label.setText(message)
    
    def closeEvent(self, event):
        """عند إغلاق النافذة."""
        # حفظ الإعدادات
        save_settings(self.settings)
        
        # تنظيف الملفات المؤقتة
        from app.utils.file_handler import get_temp_manager
        get_temp_manager().cleanup()
        
        event.accept()
