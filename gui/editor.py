import os
import webbrowser
from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, 
                               QFileDialog, QMessageBox, QTextEdit, QLabel)
from PySide6.QtWebEngineWidgets import QWebEngineView

from tools import ToolWidget


class EditorWidget(ToolWidget):
    def __init__(self, parent=None):
        super(EditorWidget, self).__init__(parent)
        
        main_layout = QVBoxLayout()
        
        # Header with instructions
        header_label = QLabel("Hex Editor - Binary File Analysis")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px; background-color: #f0f0f0;")
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Info label
        info_label = QLabel("Select a file to view its hexadecimal representation")
        info_label.setStyleSheet("color: #666; padding: 5px; font-style: italic;")
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Built-in viewer button (primary)
        builtin_btn = QPushButton("Open File in Hex Viewer")
        builtin_btn.clicked.connect(self.show_builtin_viewer)
        builtin_btn.setToolTip("Select a file to view in built-in hex viewer")
        builtin_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        button_layout.addWidget(builtin_btn)
        
        # Online HexEd.it button
        online_btn = QPushButton("Open HexEd.it Online")
        online_btn.clicked.connect(self.open_online_editor)
        online_btn.setToolTip("Open online hex editor with editing capabilities")
        button_layout.addWidget(online_btn)
        
        main_layout.addLayout(button_layout)
        
        # Web view for online editor
        self.web_view = QWebEngineView()
        self.web_view.hide()
        main_layout.addWidget(self.web_view)
        
        # Built-in hex viewer
        self.hex_viewer = QTextEdit()
        self.hex_viewer.setFont(self.get_monospace_font())
        self.hex_viewer.setReadOnly(True)
        self.hex_viewer.setLineWrapMode(QTextEdit.NoWrap)
        self.hex_viewer.hide()
        main_layout.addWidget(self.hex_viewer)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; padding: 10px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
        
    def get_monospace_font(self):
        """Get a monospace font for hex display"""
        from PySide6.QtGui import QFont, QFontDatabase
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        if not font.fixedPitch():
            for family in ['Consolas', 'Courier New', 'Monaco', 'Menlo', 'DejaVu Sans Mono']:
                font = QFont(family)
                if QFontDatabase.isFixedPitch(family):
                    break
        font.setPointSize(11)
        return font
        
    def open_online_editor(self):
        """Open HexEd.it in web view with zoom"""
        try:
            self.web_view.setZoomFactor(1.2)
            self.web_view.load(QUrl("https://hexed.it/"))
            self.hex_viewer.hide()
            self.status_label.hide()
            self.web_view.show()
        except Exception as e:
            try:
                webbrowser.open("https://hexed.it/")
                self.status_label.setText("Opened HexEd.it in your default browser")
            except Exception as e2:
                QMessageBox.warning(self, "Error", f"Cannot open online editor: {str(e2)}")
                self.status_label.setText("Failed to open online editor")

    
    def show_builtin_viewer(self):
        """Show built-in hex viewer"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select File for Hex Viewing",
            "",
            "All Files (*.*)"
        )
        if not file_path:
            return
        
        try:
            self.display_hex_dump(file_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot read file: {str(e)}")
    
    def display_hex_dump(self, file_path):
        """Display hex dump of file"""
        try:
            with open(file_path, 'rb') as f:
                chunk_size = 16
                offset = 0
                hex_lines = []
                
                # Add header
                hex_lines.append("="*100)
                hex_lines.append("  LOOK-DGC Built-in Hex Viewer - Binary File Analysis")
                hex_lines.append("="*100)
                hex_lines.append(f"File: {os.path.basename(file_path)}")
                hex_lines.append(f"Path: {file_path}")
                hex_lines.append(f"Size: {os.path.getsize(file_path):,} bytes")
                hex_lines.append("="*100)
                hex_lines.append("")
                hex_lines.append("Offset      00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F    ASCII")
                hex_lines.append("-"*100)
                
                max_lines = 2048
                line_count = 0
                
                while line_count < max_lines:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # Format hex bytes with grouping
                    hex_part1 = ' '.join(f'{b:02X}' for b in chunk[:8])
                    hex_part2 = ' '.join(f'{b:02X}' for b in chunk[8:])
                    hex_part1 = hex_part1.ljust(23)
                    hex_part2 = hex_part2.ljust(23)
                    
                    # Format ASCII representation
                    ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
                    
                    # Create line with proper alignment
                    line = f"{offset:08X}    {hex_part1} {hex_part2}   {ascii_repr}"
                    hex_lines.append(line)
                    
                    offset += len(chunk)
                    line_count += 1
                
                if line_count >= max_lines:
                    hex_lines.append("")
                    hex_lines.append("-"*100)
                    hex_lines.append("  Display limited to first 32KB for performance")
                    hex_lines.append("  Use 'Open HexEd.it Online' for full file editing and analysis")
                    hex_lines.append("-"*100)
                
                # Display in text widget
                self.hex_viewer.setPlainText('\n'.join(hex_lines))
                self.hex_viewer.show()
                self.web_view.hide()
                self.status_label.setText(f"Hex view: {os.path.basename(file_path)} ({offset:,} bytes displayed)")
                
        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")