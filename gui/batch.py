import os
import threading
import json
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QProgressBar, QCheckBox, QGroupBox, QTextEdit,
    QMessageBox, QFileDialog, QSplitter, QTreeWidget, QTreeWidgetItem,
    QScrollArea, QFrame
)
from PySide6.QtGui import QIcon

from tools import ToolWidget
from utility import load_images, modify_font
from report import generate_pdf_report

# Import all tool widgets for instantiation
from adjust import AdjustWidget
from cloning import CloningWidget
from comparison import ComparisonWidget
from contrast import ContrastWidget
from digest import DigestWidget
from echo import EchoWidget
from editor import EditorWidget
from ela import ElaWidget
from exif import ExifWidget
from frequency import FrequencyWidget
from gradient import GradientWidget
from header import HeaderWidget
from histogram import HistWidget
from location import LocationWidget
from magnifier import MagnifierWidget
from median import MedianWidget
from minmax import MinMaxWidget
from multiple import MultipleWidget
from noise import NoiseWidget
from original import OriginalWidget
from pca import PcaWidget
from planes import PlanesWidget
from plots import PlotsWidget
from quality import QualityWidget
from reverse import ReverseWidget
from space import SpaceWidget

# Try to import tensorflow-dependent modules
try:
    from splicing import SplicingWidget
    SPLICING_AVAILABLE = True
except ImportError:
    SPLICING_AVAILABLE = False

# TruFor is always available but shows setup message if not configured
from trufor import TruForWidget
TRUFOR_AVAILABLE = True

from stats import StatsWidget
from stereogram import StereoWidget
from thumbnail import ThumbWidget
from wavelets import WaveletWidget
from ghostmmaps import GhostmapWidget
from resampling import ResamplingWidget
from noise_estimmation import NoiseWaveletBlockingWidget


class BatchAnalysisWidget(ToolWidget):
    def __init__(self, parent=None):
        super(BatchAnalysisWidget, self).__init__(parent)
        self.images = []  # List of (filename, basename, image)
        self.selected_tools = []  # List of (group, tool) tuples
        self.results = {}  # Dict: image_basename -> {tool_name: data}
        self.executor = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Splitter for left (controls) and right (results)
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Load Images
        load_group = QGroupBox("Load Images")
        load_layout = QVBoxLayout()
        self.load_btn = QPushButton("Load Multiple Images")
        self.load_btn.clicked.connect(self.load_images)
        load_layout.addWidget(self.load_btn)
        self.image_list = QListWidget()
        load_layout.addWidget(self.image_list)
        load_group.setLayout(load_layout)
        left_layout.addWidget(load_group)

        # Select Tools
        tools_group = QGroupBox("Select Tools")
        tools_layout = QVBoxLayout()
        self.tools_tree = QTreeWidget()
        self.tools_tree.setHeaderLabel("Available Tools")
        self.populate_tools_tree()
        self.tools_tree.itemChanged.connect(self.on_tool_selected)
        tools_layout.addWidget(self.tools_tree)
        tools_group.setLayout(tools_layout)
        left_layout.addWidget(tools_group)

        # Run Analysis
        run_group = QGroupBox("Run Analysis")
        run_layout = QVBoxLayout()
        self.run_btn = QPushButton("Run Batch Analysis")
        self.run_btn.clicked.connect(self.run_analysis)
        run_layout.addWidget(self.run_btn)
        self.progress_bar = QProgressBar()
        run_layout.addWidget(self.progress_bar)
        self.status_label = QLabel("Ready")
        run_layout.addWidget(self.status_label)
        run_group.setLayout(run_layout)
        left_layout.addWidget(run_group)

        # Export Options
        export_group = QGroupBox("Export Results")
        export_layout = QVBoxLayout()
        self.export_pdf_btn = QPushButton("Export PDF Report")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        export_layout.addWidget(self.export_pdf_btn)
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        export_layout.addWidget(self.export_csv_btn)
        self.export_json_btn = QPushButton("Export JSON")
        self.export_json_btn.clicked.connect(self.export_json)
        export_layout.addWidget(self.export_json_btn)
        export_group.setLayout(export_layout)
        left_layout.addWidget(export_group)

        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

        # Right panel: Results
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        right_layout.addWidget(QLabel("Analysis Results Summary"))
        right_layout.addWidget(self.results_text)
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)

        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
        self.setLayout(layout)

    def populate_tools_tree(self):
        # Copy the tool structure from tools.py
        group_names = [
            "[General]", "[Metadata]", "[Inspection]", "[Detail]", "[Colors]",
            "[Noise]", "[JPEG]", "[Tampering]", "[AI Solutions]", "[Various]"
        ]
        tool_names = [
            ["Original Image", "File Digest", "Hex Editor", "Similarity Search"],
            ["Header Structure", "EXIF Full Dump", "Thumbnail Analysis", "Geolocation data"],
            ["Enhancing Magnifier", "Channel Histogram", "Global Adjustments", "Reference Comparison"],
            ["Luminance Gradient", "Echo Edge Filter", "Wavelet Threshold", "Frequency Split"],
            ["RGB/HSV Plots", "Space Conversion", "PCA Projection", "Pixel Statistics"],
            ["Signal Separation", "Min/Max Deviation", "Bit Plane Values", "Wavelet Blocking", "PRNU Identification"],
            ["Quality Estimation", "Error Level Analysis", "Multiple Compression", "JPEG Ghost Maps"],
            ["Contrast Enhancement", "Copy-Move Forgery", "Composite Splicing", "Image Resampling"],
            ["TruFor"],
            ["Median Filtering", "Illuminant Map", "Dead/Hot Pixels", "Stereogram Decoder"]
        ]

        for i, group in enumerate(group_names):
            group_item = QTreeWidgetItem()
            group_item.setText(0, group)
            modify_font(group_item, bold=True)
            for j, tool in enumerate(tool_names[i]):
                tool_item = QTreeWidgetItem(group_item)
                tool_item.setText(0, tool)
                tool_item.setData(0, Qt.UserRole, (i, j))
                tool_item.setCheckState(0, Qt.Unchecked)
            self.tools_tree.addTopLevelItem(group_item)
        self.tools_tree.expandAll()

    def on_tool_selected(self, item, column):
        if item.childCount() == 0:  # It's a tool item
            group_tool = item.data(0, Qt.UserRole)
            if item.checkState(0) == Qt.Checked:
                if group_tool not in self.selected_tools:
                    self.selected_tools.append(group_tool)
            else:
                if group_tool in self.selected_tools:
                    self.selected_tools.remove(group_tool)

    def load_images(self):
        images = load_images(self)
        if images:
            self.images = images
            self.image_list.clear()
            for _, basename, _ in images:
                self.image_list.addItem(basename)
            self.status_label.setText(f"Loaded {len(images)} images")

    def run_analysis(self):
        if not self.images:
            QMessageBox.warning(self, "No Images", "Please load images first.")
            return
        if not self.selected_tools:
            QMessageBox.warning(self, "No Tools Selected", "Please select at least one tool.")
            return

        self.results = {}
        self.progress_bar.setRange(0, len(self.images) * len(self.selected_tools))
        self.progress_bar.setValue(0)
        self.status_label.setText("Running analysis...")
        self.run_btn.setEnabled(False)

        # Run in thread to avoid freezing GUI
        self.analysis_thread = AnalysisThread(self.images, self.selected_tools, self)
        self.analysis_thread.progress.connect(self.update_progress)
        self.analysis_thread.finished.connect(self.on_analysis_finished)
        self.analysis_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_analysis_finished(self, results):
        self.results = results
        self.run_btn.setEnabled(True)
        self.status_label.setText("Analysis complete")
        self.display_results()

    def display_results(self):
        summary = ""
        for img_basename, tool_results in self.results.items():
            summary += f"Image: {img_basename}\n"
            for tool_name, data in tool_results.items():
                if 'text' in data:
                    summary += f"  {tool_name}: {data['text'][:100]}...\n"
                else:
                    summary += f"  {tool_name}: Data available\n"
            summary += "\n"
        self.results_text.setPlainText(summary)

    def export_pdf(self):
        if not self.results:
            QMessageBox.warning(self, "No Results", "Run analysis first.")
            return
        output_path = QFileDialog.getSaveFileName(self, "Save PDF Report", "", "PDF files (*.pdf)")[0]
        if output_path:
            try:
                from report import generate_batch_pdf_report
                images_data = [(basename, image) for _, basename, image in self.images]
                generate_batch_pdf_report("Batch Analysis", images_data, self.results, output_path)
                QMessageBox.information(self, "Exported", f"PDF saved to {output_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def export_csv(self):
        if not self.results:
            QMessageBox.warning(self, "No Results", "Run analysis first.")
            return
        output_path = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV files (*.csv)")[0]
        if output_path:
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Image", "Tool", "Result"])
                for img, tools in self.results.items():
                    for tool, data in tools.items():
                        result = data.get('text', 'Data available')
                        writer.writerow([img, tool, result])
            QMessageBox.information(self, "Exported", f"CSV saved to {output_path}")

    def export_json(self):
        if not self.results:
            QMessageBox.warning(self, "No Results", "Run analysis first.")
            return
        output_path = QFileDialog.getSaveFileName(self, "Save JSON", "", "JSON files (*.json)")[0]
        if output_path:
            with open(output_path, 'w') as jsonfile:
                json.dump(self.results, jsonfile, indent=4)
            QMessageBox.information(self, "Exported", f"JSON saved to {output_path}")


class AnalysisThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)

    def __init__(self, images, selected_tools, parent=None):
        super().__init__(parent)
        self.images = images
        self.selected_tools = selected_tools
        self.results = {}

    def run(self):
        total = len(self.images) * len(self.selected_tools)
        count = 0
        for filename, basename, image in self.images:
            self.results[basename] = {}
            for group, tool in self.selected_tools:
                tool_name = self.get_tool_name(group, tool)
                try:
                    widget = self.create_tool_widget(group, tool, filename, image)
                    if widget and hasattr(widget, 'get_report_data'):
                        data = widget.get_report_data()
                        if data:
                            self.results[basename][tool_name] = data
                except Exception as e:
                    self.results[basename][tool_name] = {'text': f"Error: {str(e)}"}
                count += 1
                self.progress.emit(count)
        self.finished.emit(self.results)

    def get_tool_name(self, group, tool):
        # Map back to name
        tool_names = [
            ["Original Image", "File Digest", "Hex Editor", "Similarity Search"],
            ["Header Structure", "EXIF Full Dump", "Thumbnail Analysis", "Geolocation data"],
            ["Enhancing Magnifier", "Channel Histogram", "Global Adjustments", "Reference Comparison"],
            ["Luminance Gradient", "Echo Edge Filter", "Wavelet Threshold", "Frequency Split"],
            ["RGB/HSV Plots", "Space Conversion", "PCA Projection", "Pixel Statistics"],
            ["Signal Separation", "Min/Max Deviation", "Bit Plane Values", "Wavelet Blocking", "PRNU Identification"],
            ["Quality Estimation", "Error Level Analysis", "Multiple Compression", "JPEG Ghost Maps"],
            ["Contrast Enhancement", "Copy-Move Forgery", "Composite Splicing", "Image Resampling"],
            ["TruFor"],
            ["Median Filtering", "Illuminant Map", "Dead/Hot Pixels", "Stereogram Decoder"]
        ]
        return tool_names[group][tool]

    def create_tool_widget(self, group, tool, filename, image):
        # Instantiate the widget based on group and tool
        if group == 0:
            if tool == 0:
                return OriginalWidget(image)
            elif tool == 1:
                return DigestWidget(filename, image)
            # Add others as needed, but for brevity, only key ones
        elif group == 1:
            if tool == 0:
                return HeaderWidget(filename)
            elif tool == 1:
                return ExifWidget(filename)
        # This would need to be expanded for all tools, but for demo, limited
        # For full implementation, copy the logic from look-dgc.py open_tool
        return None  # Placeholder
