import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QColorDialog, QFileDialog,
    QFrame, QMessageBox, QSizePolicy, QStackedWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QColor, QImage, QDragEnterEvent, QDropEvent
from PIL import Image

# 落ち着いたトーンのカラーパレット（デフォルトは完全な白）
PALETTE_COLORS = [
    (245,245,245), # very light gray
    (200,200,200), # light gray
    (160,140,120), # beige
    (120,130,140), # blue gray
    (100,120,100), # olive green
    (140,170,180), # dusty blue
    (180,160,180), # muted purple
    (180,140,120), # brown
    (210,180,160), # pale peach
    (170,180,170), # sage
]

# デフォルト背景色は完全な白
DEFAULT_BG_COLOR = (255,255,255)

def pil2pixmap(im):
    im = im.convert("RGB")
    data = im.tobytes("raw", "RGB")
    qimg = QImage(data, im.width, im.height, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg)

class UploadArea(QFrame):
    def __init__(self, upload_callback):
        super().__init__()
        self.upload_callback = upload_callback
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #bfc4cc;
                border-radius: 18px;
                background: #fcfcfd;
                min-width: 380px;
                min-height: 220px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label = QLabel("<span style='font-size:18pt;font-weight:600;color:#222;'>Drag & drop images here</span>")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.button = QPushButton("Browse files")
        self.button.setStyleSheet("QPushButton{background:#5c5ce6;color:#fff;border-radius:8px;font-size:14pt;padding:8px 32px;font-weight:600;}QPushButton:hover{background:#3a3ad6;}")
        self.button.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.button)
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self.setStyleSheet("QFrame{border:2px solid #5c5ce6;border-radius:18px;background:#f0f0ff;min-width:380px;min-height:220px;}")
            event.accept()
        else:
            event.ignore()
    def dragLeaveEvent(self, event):
        self.setStyleSheet("QFrame{border:2px dashed #bfc4cc;border-radius:18px;background:#fcfcfd;min-width:380px;min-height:220px;}")
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("QFrame{border:2px dashed #bfc4cc;border-radius:18px;background:#fcfcfd;min-width:380px;min-height:220px;}")
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.upload_callback(files)
    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "画像を選択", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        self.upload_callback(files)

class ThumbWidget(QWidget):
    def __init__(self, image_path, remove_callback, select_callback, selected=False):
        super().__init__()
        self.image_path = image_path
        self.remove_callback = remove_callback
        self.select_callback = select_callback
        self.setFixedSize(80, 80)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2,2,2,2)
        layout.setSpacing(0)
        pixmap = QPixmap(image_path).scaled(64,64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.label = QLabel()
        self.label.setPixmap(pixmap)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"border-radius: 8px; background: #f5f5f7; border: {'2px solid #5c5ce6' if selected else '2px solid transparent'};")
        layout.addWidget(self.label)
        btn = QPushButton("✕")
        btn.setFixedSize(18,18)
        btn.setStyleSheet("QPushButton{background:#fff;border-radius:9px;border:1px solid #ccc;font-size:10pt;}QPushButton:hover{background:#ff3b30;color:#fff;}")
        btn.clicked.connect(lambda: self.remove_callback(self.image_path))
        btn.move(60, 0)
        btn.setParent(self)
        self.label.mousePressEvent = lambda e: self.select_callback(self.image_path)

class ColorCircle(QPushButton):
    def __init__(self, color, select_callback, selected=False):
        super().__init__("")
        self.color = color
        self.select_callback = select_callback
        self.setFixedSize(28,28)
        self.setStyleSheet(f"border-radius:14px;background:rgb{color};border:{'2px solid #5c5ce6' if selected else '2px solid #eee'};")
        self.clicked.connect(lambda: self.select_callback(self.color))

class ColorPickerCircle(QPushButton):
    def __init__(self, select_callback):
        super().__init__("＋")
        self.select_callback = select_callback
        self.setFixedSize(28,28)
        self.setStyleSheet("border-radius:14px;background:#f5f5f7;border:2px solid #eee;font-size:14pt;color:#888;")
        self.clicked.connect(self.open_picker)
    def open_picker(self):
        color = QColorDialog.getColor(QColor(245,245,245), self, "色を選択")
        if color.isValid():
            self.select_callback((color.red(), color.green(), color.blue()))

class InfoLabel(QFrame):
    def __init__(self, text):
        super().__init__()
        self.setStyleSheet(f"QFrame{{border-radius:16px;background:#f5f5f7;border:1px solid #eee;}}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16,2,16,2)
        label = QLabel(text)
        label.setStyleSheet(f"font-size:11pt;color:#333;font-weight:bold;")
        layout.addWidget(label)
        layout.addStretch()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Square Photo Maker")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("QMainWindow{background:#f7f8fa;}")
        self.images = []
        self.selected_image = None
        self.bg_color = QColor(*DEFAULT_BG_COLOR)
        self.pil_cache = {}  # 画像キャッシュ
        self.stacked = QStackedWidget()
        self.upload_area = UploadArea(self.add_images)
        self.stacked.addWidget(self.upload_area)
        self.main_widget = QWidget()
        self.stacked.addWidget(self.main_widget)
        self.setCentralWidget(self.stacked)
        self.init_main_ui()
        self.show_upload_area()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_images(files)

    def show_upload_area(self):
        self.stacked.setCurrentWidget(self.upload_area)

    def show_main_ui(self):
        self.stacked.setCurrentWidget(self.main_widget)

    def init_main_ui(self):
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(32,24,32,24)
        main_layout.setSpacing(24)
        thumb_row = QHBoxLayout()
        thumb_row.setSpacing(12)
        self.thumb_widgets = []
        self.thumb_container = QWidget()
        self.thumb_layout = QHBoxLayout(self.thumb_container)
        self.thumb_layout.setContentsMargins(0,0,0,0)
        self.thumb_layout.setSpacing(12)
        thumb_row.addWidget(self.thumb_container)
        add_btn = QPushButton("＋")
        add_btn.setFixedSize(64,64)
        add_btn.setStyleSheet("border-radius:12px;background:#f5f5f7;font-size:32pt;color:#bbb;border:2px dashed #ddd;")
        add_btn.clicked.connect(self.select_images)
        thumb_row.addWidget(add_btn)
        thumb_row.addStretch()
        main_layout.addLayout(thumb_row)
        preview_row = QHBoxLayout()
        preview_row.setSpacing(32)
        orig_panel = QFrame()
        orig_panel.setStyleSheet("QFrame{border-radius:16px;background:#fff;border:1px solid #eee;}")
        orig_layout = QVBoxLayout(orig_panel)
        orig_layout.setContentsMargins(24,24,24,24)
        orig_layout.setSpacing(12)
        self.orig_label = QLabel()
        self.orig_label.setFixedSize(340,340)
        self.orig_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.orig_label.setStyleSheet("border-radius:12px;background:#f5f5f7;border:1px solid #eee;")
        orig_layout.addWidget(self.orig_label)
        self.orig_info = InfoLabel("")
        orig_layout.addWidget(self.orig_info)
        preview_row.addWidget(orig_panel)
        sq_panel = QFrame()
        sq_panel.setStyleSheet("QFrame{border-radius:16px;background:#fff;border:1px solid #eee;}")
        sq_layout = QVBoxLayout(sq_panel)
        sq_layout.setContentsMargins(24,24,24,24)
        sq_layout.setSpacing(12)
        self.sq_label = QLabel()
        self.sq_label.setFixedSize(340,340)
        self.sq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sq_label.setStyleSheet("border-radius:12px;background:#f5f5f7;border:1px solid #eee;")
        sq_layout.addWidget(self.sq_label)
        self.sq_info = InfoLabel("")
        sq_layout.addWidget(self.sq_info)
        preview_row.addWidget(sq_panel)
        main_layout.addLayout(preview_row)
        palette_row = QHBoxLayout()
        palette_row.setSpacing(8)
        palette_row.addWidget(QLabel("Background Color:"))
        self.palette_btns = []
        for i, c in enumerate(PALETTE_COLORS):
            btn = ColorCircle(c, self.set_bg_color, selected=(i==0))
            self.palette_btns.append(btn)
            palette_row.addWidget(btn)
        picker_btn = ColorPickerCircle(self.set_bg_color)
        palette_row.addWidget(picker_btn)
        palette_row.addStretch()
        main_layout.addLayout(palette_row)
        save_row = QHBoxLayout()
        self.save_current_btn = QPushButton("現在の画像を保存")
        self.save_current_btn.setStyleSheet("QPushButton{background:#5c5ce6;color:#fff;border-radius:8px;font-size:12pt;padding:8px 24px;font-weight:600;}QPushButton:hover{background:#3a3ad6;}")
        self.save_current_btn.clicked.connect(self.save_current)
        save_row.addWidget(self.save_current_btn)
        self.save_all_btn = QPushButton("全画像を保存")
        self.save_all_btn.setStyleSheet("QPushButton{background:#b7cbbf;color:#fff;border-radius:8px;font-size:12pt;padding:8px 24px;font-weight:600;}QPushButton:hover{background:#7ca982;}")
        self.save_all_btn.clicked.connect(self.save_all)
        save_row.addWidget(self.save_all_btn)
        save_row.addStretch()
        main_layout.addLayout(save_row)

    def select_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "画像を選択", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        self.add_images(files)

    def add_images(self, files):
        added = False
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')) and f not in self.images:
                self.images.append(f)
                added = True
        if added:
            if not self.selected_image:
                self.selected_image = self.images[0]
            self.cache_images()
            self.refresh_thumbnails()
            self.update_previews()
            self.show_main_ui()

    def cache_images(self):
        for img_path in self.images:
            if img_path not in self.pil_cache:
                try:
                    img = Image.open(img_path).convert("RGB")
                    self.pil_cache[img_path] = img.copy()
                    img.close()
                except Exception:
                    pass

    def refresh_thumbnails(self):
        for i in reversed(range(self.thumb_layout.count())):
            w = self.thumb_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        self.thumb_widgets = []
        for img in self.images:
            widget = ThumbWidget(img, self.remove_image, self.select_image, selected=(img==self.selected_image))
            self.thumb_widgets.append(widget)
            self.thumb_layout.addWidget(widget)

    def remove_image(self, image_path):
        if image_path in self.images:
            idx = self.images.index(image_path)
            self.images.remove(image_path)
            if image_path in self.pil_cache:
                del self.pil_cache[image_path]
            if self.selected_image == image_path:
                self.selected_image = self.images[idx-1] if idx>0 else (self.images[0] if self.images else None)
            self.refresh_thumbnails()
            self.update_previews()
            if not self.images:
                self.show_upload_area()

    def select_image(self, image_path):
        self.selected_image = image_path
        self.refresh_thumbnails()
        self.update_previews()

    def set_bg_color(self, color_tuple):
        self.bg_color = QColor(*color_tuple)
        for btn in self.palette_btns:
            btn.setStyleSheet(f"border-radius:14px;background:rgb{btn.color};border:{'2px solid #5c5ce6' if btn.color==color_tuple else '2px solid #eee'};")
        self.update_previews()

    def update_previews(self):
        if self.selected_image and self.selected_image in self.pil_cache:
            img = self.pil_cache[self.selected_image]
            pixmap = pil2pixmap(img).scaled(340,340, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.orig_label.setPixmap(pixmap)
            info = f"before : {img.width} × {img.height}px"
            self.orig_info.layout().itemAt(0).widget().setText(info)
            sq_img = self.create_square_image(self.selected_image)
            sq_pixmap = pil2pixmap(sq_img).scaled(340,340, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.sq_label.setPixmap(sq_pixmap)
            sq_info = f"after : {sq_img.width} × {sq_img.height}px"
            self.sq_info.layout().itemAt(0).widget().setText(sq_info)
        else:
            self.orig_label.clear()
            self.orig_info.layout().itemAt(0).widget().setText("")
            self.sq_label.clear()
            self.sq_info.layout().itemAt(0).widget().setText("")

    def create_square_image(self, image_path):
        img = self.pil_cache[image_path] if image_path in self.pil_cache else Image.open(image_path).convert("RGB")
        size = max(img.size)
        square_img = Image.new('RGB', (size, size), self.bg_color.getRgb()[:3])
        # box座標を厳密に（負値や端溢れなし）
        offset_x = max((size - img.size[0]) // 2, 0)
        offset_y = max((size - img.size[1]) // 2, 0)
        square_img.paste(img, (offset_x, offset_y))
        return square_img

    def save_current(self):
        if not self.selected_image:
            QMessageBox.warning(self, "警告", "画像が選択されていません。")
            return
        save_dir = QFileDialog.getExistingDirectory(self, "保存先フォルダを選択")
        if not save_dir:
            return
        img = self.create_square_image(self.selected_image)
        filename = os.path.basename(self.selected_image)
        name, ext = os.path.splitext(filename)
        save_path = os.path.join(save_dir, f"{name}_square{ext}")
        img.save(save_path)
        QMessageBox.information(self, "保存完了", f"{save_path} に保存しました。")

    def save_all(self):
        if not self.images:
            QMessageBox.warning(self, "警告", "画像が選択されていません。")
            return
        save_dir = QFileDialog.getExistingDirectory(self, "保存先フォルダを選択")
        if not save_dir:
            return
        for image_path in self.images:
            img = self.create_square_image(image_path)
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            save_path = os.path.join(save_dir, f"{name}_square{ext}")
            img.save(save_path)
        QMessageBox.information(self, "保存完了", f"全画像を{save_dir}に保存しました。")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 