from PySide6.QtWidgets import QWidget, QRubberBand, QApplication
from PySide6.QtCore import Qt, QRect, Signal, QPoint, QSize
from PySide6.QtGui import QPainter, QColor, QScreen

class SnippetOverlay(QWidget):
    """
    نافذة شفافة لتصوير الشاشة وتحديد جزء منها بالماوس.
    """
    # ترسل الصورة المقصوصة عند الانتهاء
    on_snippet_taken = Signal(object) # QImage
    on_cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.ToolTip
        )
        # تحديد الألوان لتبدو وكأن الشاشة مظللة
        self.setStyleSheet("background-color: transparent;")
        
        # أخذ لقطة كاملة للشاشة
        screen = QApplication.primaryScreen()
        self.original_pixmap = screen.grabWindow(0)
        
        self.setGeometry(screen.geometry())
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.origin = QPoint()
        self.is_drawing = False

    def paintEvent(self, event):
        """رسم خلفية الشاشة وتظليلها."""
        painter = QPainter(self)
        # رسم الصورة الأصلية
        painter.drawPixmap(self.rect(), self.original_pixmap)
        
        # رسم طبقة شفافة سوداء لتظليل الشاشة
        overlay_color = QColor(0, 0, 0, 100) # أسود شفاف
        painter.fillRect(self.rect(), overlay_color)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()
            self.is_drawing = True
        elif event.button() == Qt.MouseButton.RightButton:
            # إلغاء إذا ضغط كليك يمين
            self.on_cancelled.emit()
            self.close()

    def mouseMoveEvent(self, event):
        if not self.origin.isNull() and self.is_drawing:
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False
            rect = self.rubber_band.geometry()
            self.rubber_band.hide()
            
            # التأكد من أن التحديد له حجم
            if rect.width() > 10 and rect.height() > 10:
                # قص الجزء من الصورة الأصلية
                cropped_pixmap = self.original_pixmap.copy(rect)
                image = cropped_pixmap.toImage()
                self.on_snippet_taken.emit(image)
            else:
                self.on_cancelled.emit()
                
            self.close()
