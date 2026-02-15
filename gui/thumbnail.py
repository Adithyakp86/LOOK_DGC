import subprocess

import cv2 as cv
from PySide6.QtCore import QTemporaryFile, Qt, QThread, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout

from tools import ToolWidget
from utility import modify_font, exiftool_exe
from viewer import ImageViewer
import os

class ThumbnailWorker(QThread):
    finished = Signal(object, object)
    error = Signal(str)
    
    def __init__(self, filename, image):
        super().__init__()
        self.filename = filename
        self.image = image
        
    def run(self):
        try:
            exiftool_path = exiftool_exe()
            if not exiftool_path:
                self.error.emit("ExifTool not found")
                return
            
            # Use absolute path
            abs_path = os.path.abspath(exiftool_path)
            if not os.path.exists(abs_path):
                self.error.emit("ExifTool executable not found")
                return
                
            temp_file = QTemporaryFile()
            if temp_file.open():
                try:
                    output = subprocess.check_output(
                        [abs_path, "-b", "-ThumbnailImage", self.filename],
                        timeout=10,
                        shell=True
                    )
                    if len(output) < 100:
                        self.error.emit("No embedded thumbnail found")
                        return
                        
                    temp_name = temp_file.fileName()
                    with open(temp_name, "wb") as file:
                        file.write(output)
                    thumb = cv.imread(temp_name, cv.IMREAD_COLOR)
                    if thumb is None:
                        self.error.emit("Thumbnail image not found!")
                        return
                        
                    resized = cv.resize(
                        thumb, self.image.shape[:-1][::-1], interpolation=cv.INTER_LANCZOS4
                    )
                    diff = cv.absdiff(self.image, resized)
                    self.finished.emit(resized, diff)
                except subprocess.TimeoutExpired:
                    self.error.emit("Thumbnail extraction timed out")
                except subprocess.CalledProcessError:
                    self.error.emit("No thumbnail data available")
        except Exception as e:
            self.error.emit(str(e))


class ThumbWidget(ToolWidget):
    def __init__(self, filename, image, parent=None):
        super(ThumbWidget, self).__init__(parent)
        
        self.loading_label = QLabel("Loading thumbnail...")
        layout = QVBoxLayout()
        layout.addWidget(self.loading_label)
        self.setLayout(layout)
        
        self.worker = ThumbnailWorker(filename, image)
        self.worker.finished.connect(self.on_data_ready)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        
    def on_data_ready(self, resized, diff):
        viewer = ImageViewer(resized, diff)
        
        # Clear layout and add viewer
        layout = self.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        layout.addWidget(viewer)
        
    def on_error(self, error_msg):
        self.show_error(error_msg)

    def show_error(self, message):
        error_label = QLabel(f"{message}\n\nPossible reasons:\n- This image format doesn't support embedded thumbnails\n- The thumbnail was removed during editing\n- The file was saved without thumbnail data\n\nSupported formats: JPEG, TIFF, RAW images")
        modify_font(error_label, bold=True)
        error_label.setStyleSheet("color: #FF6600; padding: 20px;")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setWordWrap(True)
        
        layout = self.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        layout.addWidget(error_label)
