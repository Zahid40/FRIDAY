import os
import sys
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QApplication
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PyQt6.QtCore import Qt, QPoint, QTimer

# Import our custom status indicator pill
from friday.ui.orb import AnimatedOrb
from friday.ui.waveform import WaveformVisualizer

class PillWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Frameless, stays on top, taskbarless (Tool window type)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Compact dimensions for screen-notch design
        self.setFixedSize(320, 65)
        
        # Move window to absolute top-center of screen (notch style)
        self.position_top_center()
        
        # Auto-hide timer (4 seconds of idle before hiding)
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.hide_pill)
        
        self.init_ui()

    def position_top_center(self):
        screen = QApplication.primaryScreen().geometry()
        x = int((screen.width() - self.width()) / 2)
        y = 0  # Sits flush with the top screen edge
        self.move(x, y)

    def init_ui(self):
        # Vertical stack layout inside the notch
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 8, 15, 10)
        main_layout.setSpacing(2)
        
        # Row 1 (Top Line): Subtitle/transcription text (small, muted grey)
        self.sub_label = QLabel("Friday Active", self)
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("font-family: 'Inter', -apple-system, sans-serif; font-size: 11px; color: #8E8E93;")
        main_layout.addWidget(self.sub_label)
        
        # Row 2 (Bottom Line): Indicator + Main State Text + Waveform
        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        status_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Horizontal capsule indicator pill
        self.orb = AnimatedOrb(self)
        status_row.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        # Main State/Response Text (white, bold)
        self.state_label = QLabel("Online", self)
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.state_label.setStyleSheet("font-family: 'Inter', -apple-system, sans-serif; font-size: 13px; font-weight: 600; color: #FFFFFF;")
        status_row.addWidget(self.state_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        # Waveform Visualizer
        self.waveform = WaveformVisualizer(self)
        status_row.addWidget(self.waveform, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        main_layout.addLayout(status_row)
        self.setLayout(main_layout)

    # State update slots
    def update_state(self, state: str):
        self.orb.set_state(state)
        self.waveform.set_state(state)
        self.set_state_metadata(state)
        
        if state == "idle":
            self.auto_hide_timer.start(4000)
        else:
            self.auto_hide_timer.stop()
            if not self.isVisible():
                self.show()

    def set_state_metadata(self, state_str: str):
        try:
            from friday.ui.states import FridayState, STATE_META
            target_str = state_str.upper()
            if target_str == "HEARING":
                target_str = "LISTENING"
            
            state_enum = FridayState[target_str]
            meta = STATE_META[state_enum]
            
            # If not speaking/executing/error/success, set default label
            if state_enum not in [FridayState.SPEAKING, FridayState.EXECUTING, FridayState.ERROR, FridayState.SUCCESS]:
                self.state_label.setText(meta["label"])
                
            if state_enum in [FridayState.IDLE, FridayState.WAKE, FridayState.LISTENING]:
                self.sub_label.setText("Friday Active")
        except Exception:
            pass

    def update_text(self, text: str):
        clean_text = text.strip()
        
        # Reset sub_label for general states to keep the layout clean
        if clean_text in ["Listening...", "Hearing...", "Say Friday...", "Online."]:
            self.sub_label.setText("Friday Active")
            
        if clean_text == "Thinking...":
            self.orb.set_state("thinking")
            self.waveform.set_state("thinking")
            self.state_label.setText("Thinking")
        elif clean_text == "Listening...":
            self.orb.set_state("listening")
            self.waveform.set_state("listening")
            self.state_label.setText("Listening")
        elif clean_text == "Hearing...":
            self.orb.set_state("listening")
            self.waveform.set_state("listening")
            self.state_label.setText("Hearing")
        elif clean_text == "Say Friday...":
            self.orb.set_state("idle")
            self.waveform.set_state("idle")
            self.state_label.setText("Offline")
            self.sub_label.setText("Friday Active")
        elif clean_text == "Online.":
            self.orb.set_state("speaking")
            self.waveform.set_state("speaking")
            self.state_label.setText("Online")
        elif clean_text == "Error":
            self.orb.set_state("error")
            self.waveform.set_state("error")
            self.state_label.setText("Error")
            self.sub_label.setText("Operation Failed")
        elif clean_text == "Success":
            self.orb.set_state("success")
            self.waveform.set_state("success")
            self.state_label.setText("Success")
            self.sub_label.setText("Command Executed")
        elif clean_text.startswith("Heard:"):
            # Put transcription on the top sub-label
            self.sub_label.setText(clean_text)
            self.state_label.setText("Thinking")
        elif clean_text.startswith("Tool:"):
            # Extract tool action
            tool_action = clean_text[len("Tool:"):].strip()
            self.sub_label.setText(tool_action)
        else:
            # Main response text - truncate if too long for the minimal notch
            self.sub_label.setText("Friday Active")
            max_len = 38
            if len(clean_text) > max_len:
                display_text = clean_text[:max_len-3] + "..."
            else:
                display_text = clean_text
            self.state_label.setText(display_text)

    def update_time(self, seconds: int):
        # We don't display a running timer inside the minimal notch to keep it clean.
        pass

    def hide_pill(self):
        self.hide()

    # Paint event overrides to render flat-top, bottom-rounded capsule shape (Screen Notch / Island)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Solid black notch background
        bg_color = QColor(0, 0, 0, 255)
        painter.setBrush(bg_color)
        
        # Construct path: flat top, rounded bottom corners
        path = QPainterPath()
        w = float(self.width())
        h = float(self.height())
        r = 16.0  # Corner radius for bottom edge
        
        # Top-left corner (0,0)
        path.moveTo(0, 0)
        # Line to Top-right corner (w, 0)
        path.lineTo(w, 0)
        # Line to bottom-right corner start
        path.lineTo(w, h - r)
        # Curve around bottom-right corner
        path.quadTo(w, h, w - r, h)
        # Line to bottom-left corner start
        path.lineTo(r, h)
        # Curve around bottom-left corner
        path.quadTo(0, h, 0, h - r)
        # Close path back to Top-left
        path.closeSubpath()
        
        painter.drawPath(path)
