import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient, QPainterPath
from PyQt6.QtCore import QTimer, Qt, QRectF, QPointF, pyqtProperty, QPropertyAnimation, QEasingCurve, QVariantAnimation
from gui.states import FridayState, STATE_META

class AnimatedOrb(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 20)  # Room for icons and glow
        
        # State variables
        self.current_state = FridayState.IDLE
        self.time_counter = 0.0
        
        # Animatable properties
        self._scale = 1.0
        self._opacity = 1.0
        self._rotation_angle = 0.0
        self._color = QColor(STATE_META[FridayState.IDLE]["color"])
        
        # Core property animations for transitions
        self.scale_anim = QPropertyAnimation(self, b"scale", self)
        self.scale_anim.setDuration(300)
        self.scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        
        self.opacity_anim = QPropertyAnimation(self, b"opacity", self)
        self.opacity_anim.setDuration(300)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Color transition animation (QVariantAnimation handles QColor interpolation)
        self.color_anim = QVariantAnimation(self)
        self.color_anim.setDuration(300)
        self.color_anim.valueChanged.connect(self.set_orb_color)
        
        # Spin animation for THINKING state
        self.spin_anim = QPropertyAnimation(self, b"rotation_angle", self)
        self.spin_anim.setDuration(1000)
        self.spin_anim.setStartValue(0.0)
        self.spin_anim.setEndValue(360.0)
        self.spin_anim.setLoopCount(-1)
        
        # 60fps refresh timer for real-time waves/pulses
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)

    # Property definitions for QPropertyAnimation
    @pyqtProperty(float)
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, val):
        self._scale = val
        self.update()

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, val):
        self._opacity = val
        self.update()

    @pyqtProperty(float)
    def rotation_angle(self):
        return self._rotation_angle

    @rotation_angle.setter
    def rotation_angle(self, val):
        self._rotation_angle = val
        self.update()

    def set_orb_color(self, color):
        self._color = color
        self.update()

    def set_state(self, state_str: str):
        # Map string name to Enum
        try:
            target_state = FridayState[state_str.upper()]
        except KeyError:
            # Check for thinking/hearing variations
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
        
        # Stop previous transition animations
        self.scale_anim.stop()
        self.opacity_anim.stop()
        self.spin_anim.stop()
        self.color_anim.stop()
        
        # Set up color transition
        self.color_anim.setStartValue(self._color)
        self.color_anim.setEndValue(QColor(STATE_META[self.current_state]["color"]))
        self.color_anim.start()
        
        # Run scale/opacity pop transition
        self.scale_anim.setStartValue(0.6)
        self.scale_anim.setEndValue(1.0)
        self.scale_anim.start()
        
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.start()
        
        # Start state-specific animations
        if self.current_state == FridayState.THINKING:
            self.spin_anim.start()

    def update_animation(self):
        self.time_counter += 0.05
        self.update()

    def draw_glow(self, painter, cx, cy, radius, alpha):
        grad = QRadialGradient(cx, cy, radius)
        c_glow = QColor(self._color)
        c_glow.setAlpha(int(alpha * self._opacity))
        grad.setColorAt(0.0, c_glow)
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius*2, radius*2))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        
        # Apply transition scaling
        painter.translate(cx, cy)
        painter.scale(self._scale, self._scale)
        painter.translate(-cx, -cy)
        
        # Setup base drawing variables
        color = QColor(self._color)
        color.setAlpha(int(color.alpha() * self._opacity))
        
        # 1. IDLE State
        if self.current_state == FridayState.IDLE:
            self.draw_glow(painter, cx, cy, 12.0, 40)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            # Small dim capsule
            w, h = 12.0, 5.0
            painter.drawRoundedRect(QRectF(cx - w/2, cy - h/2, w, h), h/2, h/2)
            
        # 2. WAKE State
        elif self.current_state == FridayState.WAKE:
            self.draw_glow(painter, cx, cy, 14.0, 70)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            w, h = 16.0, 7.0
            painter.drawRoundedRect(QRectF(cx - w/2, cy - h/2, w, h), h/2, h/2)
            
        # 3. LISTENING State
        elif self.current_state == FridayState.LISTENING:
            # Active blue pulse
            pulse = 0.90 + 0.15 * math.sin(self.time_counter * 3.0)
            self.draw_glow(painter, cx, cy, 16.0 * pulse, 60)
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            w, h = 15.0 * pulse, 6.5 * pulse
            painter.drawRoundedRect(QRectF(cx - w/2, cy - h/2, w, h), h/2, h/2)
            
        # 4. THINKING State (Spinning Arc Spinner)
        elif self.current_state == FridayState.THINKING:
            self.draw_glow(painter, cx, cy, 12.0, 35)
            
            pen = QPen(color, 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            r = 6.0
            rect = QRectF(cx - r, cy - r, r*2, r*2)
            start_angle = int(self._rotation_angle * 16)
            span_angle = int(270 * 16)
            painter.drawArc(rect, start_angle, span_angle)
            
        # 5. SPEAKING State (Expanding concentric ripple rings)
        elif self.current_state == FridayState.SPEAKING:
            self.draw_glow(painter, cx, cy, 14.0, 50)
            
            # Ripple rings
            for i in range(2):
                r_val = (self.time_counter * 0.4 + i * 0.5) % 1.0
                r_radius = 5.0 + r_val * 11.0
                r_alpha = int(140 * (1.0 - r_val) * self._opacity)
                
                r_color = QColor(color)
                r_color.setAlpha(r_alpha)
                painter.setPen(QPen(r_color, 1.2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QRectF(cx - r_radius, cy - r_radius, r_radius*2, r_radius*2))
                
            # Solid center core
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            w, h = 12.0, 5.0
            painter.drawRoundedRect(QRectF(cx - w/2, cy - h/2, w, h), h/2, h/2)
            
        # 6. SEARCHING State (Scanning line moving left/right inside capsule)
        elif self.current_state == FridayState.SEARCHING:
            self.draw_glow(painter, cx, cy, 14.0, 40)
            
            # Background capsule track
            pen_track = QPen(color, 1.2)
            painter.setPen(pen_track)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            w, h = 20.0, 8.0
            painter.drawRoundedRect(QRectF(cx - w/2, cy - h/2, w, h), h/2, h/2)
            
            # Sweeping scan line
            sweep = (math.sin(self.time_counter * 1.5) + 1.0) / 2.0
            scan_x = (cx - w/2 + 2.0) + sweep * (w - 4.0)
            painter.setPen(QPen(color, 1.8))
            painter.drawLine(QPointF(scan_x, cy - h/2 + 1.5), QPointF(scan_x, cy + h/2 - 1.5))
            
        # 7. READING State (Minimalist eye looking left/right)
        elif self.current_state == FridayState.READING:
            self.draw_glow(painter, cx, cy, 12.0, 40)
            
            # Eye shape paths
            path = QPainterPath()
            w, h = 18.0, 10.0
            path.moveTo(cx - w/2, cy)
            path.quadTo(cx, cy - h/2, cx + w/2, cy)
            path.quadTo(cx, cy + h/2, cx - w/2, cy)
            
            painter.setPen(QPen(color, 1.2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
            
            # Scanning pupil
            look = math.sin(self.time_counter * 0.8) * 2.5
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx + look - 2.0, cy - 2.0, 4.0, 4.0))
            
        # 8. PLANNING State (Grid of 4 animating dots)
        elif self.current_state == FridayState.PLANNING:
            self.draw_glow(painter, cx, cy, 12.0, 30)
            
            dots = [
                (cx - 4.5, cy - 4.5, 0),
                (cx + 4.5, cy - 4.5, 1),
                (cx + 4.5, cy + 4.5, 2),
                (cx - 4.5, cy + 4.5, 3)
            ]
            painter.setPen(Qt.PenStyle.NoPen)
            for x, y, idx in dots:
                dot_alpha = int(127 + 128 * math.sin(self.time_counter * 1.8 - idx * 1.5))
                dot_color = QColor(color)
                dot_color.setAlpha(int(max(40, dot_alpha) * self._opacity))
                painter.setBrush(QBrush(dot_color))
                painter.drawEllipse(QRectF(x - 1.8, y - 1.8, 3.6, 3.6))
                
        # 9. TYPING State (Minimalist keyboard frame with blinking typing dots)
        elif self.current_state == FridayState.TYPING:
            self.draw_glow(painter, cx, cy, 14.0, 40)
            
            # Keyboard frame
            w, h = 18.0, 11.0
            painter.setPen(QPen(color, 1.2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(cx - w/2, cy - h/2, w, h), 2, 2)
            
            # 3 typing dots
            painter.setPen(Qt.PenStyle.NoPen)
            for i in range(3):
                dot_x = cx - 5.0 + i * 5.0
                dot_alpha = int(127 + 128 * math.sin(self.time_counter * 2.0 - i * 1.0))
                dot_color = QColor(color)
                dot_color.setAlpha(int(max(40, dot_alpha) * self._opacity))
                painter.setBrush(QBrush(dot_color))
                painter.drawEllipse(QRectF(dot_x - 1.2, cy - 1.2, 2.4, 2.4))
                
        # 10. EXECUTING State (Progress bar filling up)
        elif self.current_state == FridayState.EXECUTING:
            self.draw_glow(painter, cx, cy, 14.0, 40)
            
            # Background track
            w, h = 22.0, 6.0
            rect_bg = QRectF(cx - w/2, cy - h/2, w, h)
            painter.setPen(Qt.PenStyle.NoPen)
            bg_track = QColor(color)
            bg_track.setAlpha(int(50 * self._opacity))
            painter.setBrush(QBrush(bg_track))
            painter.drawRoundedRect(rect_bg, h/2, h/2)
            
            # Foreground progress fill (animated loop)
            prog = (self.time_counter * 0.15) % 1.0
            w_fill = w * prog
            if w_fill > 0.0:
                rect_fill = QRectF(cx - w/2, cy - h/2, w_fill, h)
                painter.setBrush(QBrush(color))
                painter.drawRoundedRect(rect_fill, h/2, h/2)
                
        # 11. ERROR State (Red flashing capsule)
        elif self.current_state == FridayState.ERROR:
            # Toggle flash every 250ms
            flash = int(self.time_counter * 4.0) % 2
            err_color = QColor(color)
            if flash == 0:
                err_color.setAlpha(int(80 * self._opacity))
            else:
                self.draw_glow(painter, cx, cy, 14.0, 70)
                
            painter.setBrush(QBrush(err_color))
            painter.setPen(Qt.PenStyle.NoPen)
            w, h = 15.0, 6.5
            painter.drawRoundedRect(QRectF(cx - w/2, cy - h/2, w, h), h/2, h/2)
            
        # 12. SUCCESS State (Green capsule pulsing rapidly)
        elif self.current_state == FridayState.SUCCESS:
            pulse = 0.90 + 0.15 * abs(math.sin(self.time_counter * 3.5))
            self.draw_glow(painter, cx, cy, 16.0 * pulse, 70)
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            w, h = 15.0 * pulse, 6.5 * pulse
            painter.drawRoundedRect(QRectF(cx - w/2, cy - h/2, w, h), h/2, h/2)
