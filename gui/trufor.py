"""
Edge-Based Manipulation Detection Tool

This module implements a lightweight heuristic approach for detecting potential
image manipulations based on edge density analysis. This is NOT the official TruFor
model from CVPR 2023, but rather a simple edge-based heuristic method.

IMPORTANT DISCLAIMER:
- This tool uses a basic edge-density heuristic, not deep learning or AI.
- Results should be interpreted as suggestive indicators, not definitive proof.
- High edge density does not necessarily indicate manipulation.
- This is intended as a quick preliminary analysis tool.

Algorithm Overview:
1. Convert the input image to grayscale
2. Compute Canny edge detection (thresholds: 50, 150)
3. Apply a 15x15 averaging kernel to smooth edge density
4. Normalize edge density to [0, 1] range
5. Generate a heatmap: red = high edge density, blue = low edge density
6. Derive manipulation probability from mean edge density (scaled to percentage)

Limitations:
- Textured regions naturally have high edge density (false positives)
- Smooth manipulations may not be detected (false negatives)
- Results are highly dependent on image content and compression

TODO: Future enhancement could integrate the actual TruFor deep learning model
      (https://github.com/grip-unina/TruFor) for more accurate detection.
      This would require PyTorch and the pre-trained TruFor weights.
"""

from PySide6.QtWidgets import QVBoxLayout, QLabel, QPushButton, QProgressBar, QHBoxLayout
from PySide6.QtCore import Qt, QThread, Signal
from tools import ToolWidget
from utility import modify_font
from viewer import ImageViewer
import cv2 as cv
import numpy as np
import os

class EdgeAnalysisWorker(QThread):
    """
    Background worker thread for edge-based manipulation detection.
    
    This worker performs edge density analysis in a separate thread to
    avoid blocking the UI during computation.
    
    Signals:
        finished: Emitted with (heatmap, probability) tuple on success
        error: Emitted with error message string on failure
        progress: Emitted with status message during analysis
    """
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self, filename, image):
        super().__init__()
        self.filename = filename
        self.image = image
        
    def run(self):
        """
        Execute edge-based manipulation detection.
        
        Algorithm steps:
        1. Convert image to grayscale
        2. Detect edges using Canny edge detector
        3. Compute local edge density using averaging kernel
        4. Generate heatmap visualization
        5. Calculate manipulation probability from mean edge density
        """
        try:
            self.progress.emit("Initializing edge-based analysis...")
            
            # NOTE: This is a heuristic method, NOT the actual TruFor deep learning model.
            # The edge-density approach provides a quick visual indicator but has limitations.
            
            self.progress.emit("Performing edge-based heuristic analysis...")
            
            # Step 1: Convert to grayscale for edge detection
            gray = cv.cvtColor(self.image, cv.COLOR_BGR2GRAY)
            
            # Step 2: Detect edges using Canny edge detector
            # Thresholds (50, 150) are empirically chosen for general images
            edges = cv.Canny(gray, 50, 150)
            
            # Step 3: Compute local edge density using 15x15 averaging kernel
            # Higher density regions appear more "active" in terms of edge content
            kernel = np.ones((15, 15), np.float32) / 225
            edge_density = cv.filter2D(edges.astype(np.float32), -1, kernel)
            
            # Step 4: Normalize edge density to [0, 1] range
            if edge_density.max() > 0:
                edge_density = edge_density / edge_density.max()
            
            # Step 5: Create color heatmap visualization
            # Red = high edge density, Blue = low edge density
            # Note: High edge density does NOT necessarily indicate manipulation
            heatmap = np.zeros((edge_density.shape[0], edge_density.shape[1], 3), dtype=np.uint8)
            heatmap[:, :, 2] = (edge_density * 255).astype(np.uint8)  # Red channel
            heatmap[:, :, 0] = ((1 - edge_density) * 255).astype(np.uint8)  # Blue channel
            
            # Step 6: Calculate heuristic "manipulation probability" from mean edge density
            # WARNING: This is a rough indicator only, not a reliable probability
            manipulation_prob = np.mean(edge_density) * 100
            
            self.progress.emit(f"Analysis complete. Edge density indicator: {manipulation_prob:.1f}%")
            self.finished.emit((heatmap, manipulation_prob))
            
        except Exception as e:
            self.error.emit(f"Analysis failed: {str(e)}")


# Keep TruForWidget name for backward compatibility with imports
# TODO: Consider renaming to EdgeAnalysisWidget in a future major version
class TruForWidget(ToolWidget):
    """
    Edge-Based Manipulation Detection Widget.
    
    This widget provides a UI for running edge-density based heuristic
    analysis on images. It displays a heatmap showing regions of high
    edge density and provides a rough indicator score.
    
    Note: This is a lightweight heuristic tool, NOT the official TruFor
    deep learning model. Results should be interpreted with caution.
    
    Attributes:
        filename: Path to the image file being analyzed
        image: OpenCV image array (BGR format)
    """
    def __init__(self, filename, image, parent=None):
        super(TruForWidget, self).__init__(parent)
        
        self.filename = filename
        self.image = image
        
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Edge-Based Manipulation Detection")
        modify_font(title_label, bold=True)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Info - clarify this is a heuristic, not AI
        info_label = QLabel("Lightweight heuristic based on edge density analysis")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #666666; margin: 10px;")
        main_layout.addWidget(info_label)
        
        # Disclaimer
        disclaimer_label = QLabel("Note: High edge density does not necessarily indicate manipulation")
        disclaimer_label.setAlignment(Qt.AlignCenter)
        disclaimer_label.setStyleSheet("color: #999999; font-size: 10px; margin-bottom: 5px;")
        main_layout.addWidget(disclaimer_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        self.analyze_button = QPushButton("Analyze Image")
        self.analyze_button.clicked.connect(self.start_analysis)
        controls_layout.addWidget(self.analyze_button)
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)
        
        # Progress
        self.progress_label = QLabel("Ready to analyze")
        main_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Results
        self.result_label = QLabel("")
        modify_font(self.result_label, bold=True)
        self.result_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.result_label)
        
        # Viewer
        self.viewer = ImageViewer(image, image, "Original vs Edge Density Heatmap")
        main_layout.addWidget(self.viewer)
        
        self.setLayout(main_layout)
        
    def start_analysis(self):
        """Start the edge-based analysis in a background thread."""
        self.analyze_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.result_label.setText("")
        
        self.worker = EdgeAnalysisWorker(self.filename, self.image)
        self.worker.finished.connect(self.on_analysis_complete)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.start()
        
    def on_analysis_complete(self, result):
        """
        Handle analysis completion and display results.
        
        Note: The "edge density indicator" is a heuristic measure, not a true
        probability. It reflects how much edge content exists in the image.
        """
        heatmap, prob = result
        
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        
        # Update result label with appropriate caveats
        # These levels are arbitrary thresholds for visual feedback only
        if prob < 30:
            status = "LOW EDGE DENSITY"
            color = "green"
        elif prob < 70:
            status = "MODERATE EDGE DENSITY"
            color = "orange"
        else:
            status = "HIGH EDGE DENSITY"
            color = "red"
            
        self.result_label.setText(f"Edge Density Indicator: {prob:.1f}% ({status})")
        self.result_label.setStyleSheet(f"color: {color}; font-size: 14px; margin: 10px;")
        
        # Update viewer with heatmap
        self.viewer.update_processed(heatmap)
        
    def on_analysis_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        self.progress_label.setText(f"Error: {error_msg}")
        self.progress_label.setStyleSheet("color: red;")
        
    def on_progress_update(self, message):
        self.progress_label.setText(message)
        self.progress_label.setStyleSheet("color: blue;")

