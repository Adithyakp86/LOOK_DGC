import numpy as np
import cv2 as cv
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QProgressDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt

from tools import ToolWidget
from viewer import ImageViewer

# Try to import noiseprint module
try:
    from noiseprint.noiseprint_blind import noiseprint_blind_file, genMappUint8
    NOISEPRINT_AVAILABLE = True
except ImportError:
    NOISEPRINT_AVAILABLE = False


class PRNUWidget(ToolWidget):
    def __init__(self, filename, image, parent=None):
        super(PRNUWidget, self).__init__(parent)

        if not NOISEPRINT_AVAILABLE:
            QMessageBox.warning(
                self,
                "Feature Unavailable",
                "PRNU Identification requires TensorFlow to be installed."
            )
            return

        self.filename = filename
        self.image = image
        self.processed_image = None

        # UI Controls
        controls_layout = QHBoxLayout()
        
        self.model_label = QLabel(self.tr("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["net"])
        self.model_combo.setEnabled(False)  # Only 'net' model available
        
        controls_layout.addWidget(self.model_label)
        controls_layout.addWidget(self.model_combo)
        controls_layout.addStretch()

        # Create viewer
        self.viewer = ImageViewer(self.image, self.image)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.viewer)
        self.setLayout(main_layout)

        # Process the image
        self.process()

    def process(self):
        """Process the image to extract PRNU noise pattern"""
        try:
            progress = QProgressDialog(
                self.tr("Computing PRNU map..."), None, 0, 100, self
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.setValue(10)
            
            # Convert image to grayscale for processing
            if len(self.image.shape) == 3:
                gray = cv.cvtColor(self.image, cv.COLOR_BGR2GRAY)
            else:
                gray = self.image.copy()
            
            progress.setValue(20)
            
            # Estimate JPEG quality factor
            try:
                from noiseprint.utility.utilityRead import jpeg_qtableinv
                QF = jpeg_qtableinv(self.filename)
            except:
                QF = 101  # Default to high quality if can't determine
            
            progress.setValue(30)
            
            # Generate noiseprint
            from noiseprint.noiseprint import genNoiseprint
            noiseprint = genNoiseprint(gray.astype(np.float32) / 255.0, QF, "net")
            
            progress.setValue(60)
            
            # Process the result for visualization
            # Normalize noiseprint to 0-255 range
            noiseprint_normalized = ((noiseprint - noiseprint.min()) / 
                                     (noiseprint.max() - noiseprint.min()) * 255).astype(np.uint8)
            
            progress.setValue(80)
            
            # Apply colormap for better visualization
            colored_map = cv.applyColorMap(noiseprint_normalized, cv.COLORMAP_JET)
            
            progress.setValue(100)
            
            # Update viewer with the PRNU map
            self.viewer.update_processed(colored_map)
            self.processed_image = colored_map
            
            self.info_message.emit(self.tr(f"PRNU Identification completed (QF={QF})"))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process PRNU: {str(e)}")
            self.info_message.emit(self.tr("PRNU Identification failed"))

    def get_report_data(self):
        """Return data for PDF report generation"""
        if self.processed_image is not None:
            return {
                'text': "PRNU Identification: Sensor pattern noise analysis for camera identification",
                'image': self.processed_image
            }
        return {'text': "PRNU Identification: No result available"}
