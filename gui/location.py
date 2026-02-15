from PySide6.QtCore import QUrl, QTemporaryDir, Qt, QThread, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QLabel

from pyexiftool import exiftool
from tools import ToolWidget
from utility import exiftool_exe, modify_font
import os

class LocationWorker(QThread):
    finished = Signal(float, float)
    error = Signal(str)
    
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        
    def run(self):
        try:
            exiftool_path = exiftool_exe()
            if not exiftool_path or not os.path.exists(exiftool_path):
                self.error.emit("ExifTool not found")
                return
                
            with exiftool.ExifTool(exiftool_path) as et:
                metadata = et.get_metadata(self.filename)
                
                # Try multiple GPS tag formats
                lat = (metadata.get("Composite:GPSLatitude") or 
                      metadata.get("GPS:GPSLatitude") or 
                      metadata.get("EXIF:GPSLatitude"))
                lon = (metadata.get("Composite:GPSLongitude") or 
                      metadata.get("GPS:GPSLongitude") or 
                      metadata.get("EXIF:GPSLongitude"))
                
                if lat is None or lon is None:
                    # Check for decimal degree format
                    lat = metadata.get("GPS:GPSLatitudeRef")
                    lon = metadata.get("GPS:GPSLongitudeRef")
                    
                if lat is None or lon is None:
                    self.error.emit("No GPS coordinates found in image metadata")
                    return
                    
                try:
                    lat_float = float(lat)
                    lon_float = float(lon)
                    self.finished.emit(lat_float, lon_float)
                except (ValueError, TypeError):
                    self.error.emit(f"Invalid GPS coordinates: {lat}, {lon}")
        except Exception as e:
            self.error.emit(str(e))


class LocationWidget(ToolWidget):
    def __init__(self, filename, parent=None):
        super(LocationWidget, self).__init__(parent)
        
        self.loading_label = QLabel("Loading location data...")
        layout = QVBoxLayout()
        layout.addWidget(self.loading_label)
        self.setLayout(layout)
        
        self.temp_dir = QTemporaryDir()
        self.worker = LocationWorker(filename)
        self.worker.finished.connect(self.on_data_ready)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        
    def on_data_ready(self, lat, lon):
        url = (
            f"https://www.google.com/maps/place/{lat},{lon}/@{lat},{lon},17z/"
            f"data=!4m5!3m4!1s0x0:0x0!8m2!3d{lat}!4d{lon}"
        )
        web_view = QWebEngineView()
        web_view.load(QUrl(url))
        
        # Clear layout and add web view
        layout = self.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        layout.addWidget(web_view)
        
    def on_error(self, error_msg):
        label = QLabel(f"{error_msg}\n\nThis image does not contain GPS location data.\n\nGPS coordinates are typically found in photos taken with:\n- Smartphones with location services enabled\n- Cameras with GPS modules\n- Images with manually added geotags")
        modify_font(label, bold=True)
        label.setStyleSheet("color: #FF6600; padding: 20px;")
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        
        layout = self.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        layout.addWidget(label)
