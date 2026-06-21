import math
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import QTimer, Qt, QRectF, QVariantAnimation
from friday.ui.states import FridayState, STATE_META

class WaveformVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(55, 20)  # Compact size on the right side of the notch
        
        self.current_state = FridayState.IDLE
        self.time_counter = 0.0
        self._color = QColor(STATE_META[FridayState.IDLE]["color"])
        
        # Waveform layout settings
        self.num_bars = 5
        self.bar_width = 3
        self.bar_spacing = 4
        self.max_height = 16
        self.min_height = 3
        
        self.current_heights = [self.min_height] * self.num_bars
        
        # Color transition animation
        self.color_anim = QVariantAnimation(self)
        self.color_anim.setDuration(300)
        self.color_anim.valueChanged.connect(self.set_waveform_color)
        
        # 60fps Animation Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(16)
        
        # Microphone input stream variables
        self.mic_level = 0.0
        self.stream = None

    def set_waveform_color(self, color):
        self._color = color
        self.update()

    def set_state(self, state_str: str):
        try:
            target_state = FridayState[state_str.upper()]
        except KeyError:
            # Fallback variations
            if state_str == "thinking":
                target_state = FridayState.THINKING
            elif state_str in ["listening", "hearing"]:
                target_state = FridayState.LISTENING
            elif state_str == "speaking":
                target_state = FridayState.SPEAKING
            elif state_str == "idle":
                target_state = FridayState.IDLE
            else:
                return
                
        if target_state == self.current_state:
            return
            
        self.current_state = target_state
        
        # Start color transition
        self.color_anim.stop()
        self.color_anim.setStartValue(self._color)
        self.color_anim.setEndValue(QColor(STATE_META[self.current_state]["color"]))
        self.color_anim.start()
        
        # Handle microphone stream based on state
        if self.current_state == FridayState.LISTENING:
            self.start_mic_stream()
        else:
            self.stop_mic_stream()

    def start_mic_stream(self):
        self.stop_mic_stream()
        try:
            import sounddevice as sd
            import numpy as np
            
            def callback(indata, frames, time, status):
                rms = np.sqrt(np.mean(indata**2))
                self.mic_level = float(rms)
                
            self.stream = sd.InputStream(callback=callback, channels=1, samplerate=16000)
            self.stream.start()
        except Exception:
            # Fallback if mic device is locked or unavailable
            self.stream = None

    def stop_mic_stream(self):
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
            self.mic_level = 0.0

    def update_wave(self):
        self.time_counter += 0.12
        
        # 1. LISTENING state: React to sounddevice amplitude input
        if self.current_state == FridayState.LISTENING:
            if self.stream:
                # Scale RMS level (0.0 to 1.0) into waveform height range
                target_base = self.min_height + self.mic_level * 180.0
                target_base = min(self.max_height, max(self.min_height, target_base))
                for i in range(self.num_bars):
                    # Add natural fluctuations across bars
                    bar_factor = 0.6 + 0.5 * math.sin(self.time_counter * 2.0 + i * 1.2)
                    target = self.min_height + (target_base - self.min_height) * abs(bar_factor)
                    self.current_heights[i] = self.current_heights[i] * 0.4 + target * 0.6
            else:
                # Fallback to random audio simulation
                for i in range(self.num_bars):
                    target = self.min_height + random.uniform(0.0, 9.0)
                    self.current_heights[i] = self.current_heights[i] * 0.6 + target * 0.4
                    
        # 2. SPEAKING state: Sine wave frequency offsets
        elif self.current_state == FridayState.SPEAKING:
            for i in range(self.num_bars):
                # heights = abs(sin(time * freq + i * phase_offset))
                wave = math.sin(self.time_counter * 1.5 + i * 0.8)
                target = self.min_height + (self.max_height - self.min_height) * abs(wave)
                self.current_heights[i] = self.current_heights[i] * 0.5 + target * 0.5
                
        # 3. SEARCHING state: Sweep single tall bar from left to right
        elif self.current_state == FridayState.SEARCHING:
            sweep_idx = int(self.time_counter * 1.2) % self.num_bars
            for i in range(self.num_bars):
                if i == sweep_idx:
                    target = self.max_height
                else:
                    target = self.min_height
                self.current_heights[i] = self.current_heights[i] * 0.5 + target * 0.5
                
        # 4. EXECUTING state: Progress bar filling sequentially
        elif self.current_state == FridayState.EXECUTING:
            progress_limit = int(self.time_counter * 0.8) % (self.num_bars + 1)
            for i in range(self.num_bars):
                if i < progress_limit:
                    target = self.max_height - 3.0
                else:
                    target = self.min_height
                self.current_heights[i] = self.current_heights[i] * 0.5 + target * 0.5
                
        # 5. IDLE state: Flatline (smoothly return to minimum heights)
        elif self.current_state == FridayState.IDLE:
            for i in range(self.num_bars):
                self.current_heights[i] = max(self.min_height, self.current_heights[i] - 1.0)
                
        # 6. Other states: Gentle pulsing breathing waves
        else:
            for i in range(self.num_bars):
                wave = math.sin(self.time_counter * 0.6 + i * 0.4)
                target = self.min_height + (self.max_height - self.min_height) * 0.25 * (wave + 1.0)
                self.current_heights[i] = self.current_heights[i] * 0.7 + target * 0.3
                
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate start position to center the bars
        total_width = (self.num_bars * self.bar_width) + ((self.num_bars - 1) * self.bar_spacing)
        start_x = (self.width() - total_width) / 2.0
        center_y = self.height() / 2.0
        
        # Draw waveform bars
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        for i in range(self.num_bars):
            h = self.current_heights[i]
            x = start_x + i * (self.bar_width + self.bar_spacing)
            y = center_y - (h / 2.0)
            
            # Smooth capsule shape
            painter.drawRoundedRect(
                int(x), int(y), 
                self.bar_width, int(h), 
                self.bar_width / 2.0, self.bar_width / 2.0
            )

    def closeEvent(self, event):
        self.stop_mic_stream()
        super().closeEvent(event)
