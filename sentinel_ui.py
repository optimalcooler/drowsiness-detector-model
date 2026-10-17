"""
SENTINEL // Autonomous Driver Fatigue & Distraction Copilot
Ultra-Futuristic Chrome & Liquid-Metal Interface powered by PySide6.
Engineered with cognitive psychology & automotive safety standards:
- Polished chrome, glassmorphic obsidian, and specular neon lighting
- Biometric road vs. mirror gaze sector tape (Euro NCAP / NHTSA aligned)
- 1.8s Distraction Hazard Alert without false alarms during mirror checks
- 1.5s Micro-Sleep Emergency Alarm
- Liquid Chrome Neural Vigilance Core & AI Copilot Trip Guidance
"""

import sys
import time
import math
from collections import deque
from typing import Optional, List, Tuple

import numpy as np

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal, Slot, QSize, QLineF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient,
    QRadialGradient, QPolygonF, QImage, QPainterPath
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QSlider, QFrame,
    QGridLayout, QGraphicsDropShadowEffect, QSizePolicy, QCheckBox,
    QProgressBar
)

from sentinel_engine import TelemetrySnapshot, EyeMetric, SentinelPipelineWorker


# =====================================================================
# CHROME & CYBERNETIC COLOR PALETTE
# =====================================================================

BG_OBSIDIAN = "#05070D"
BG_CHROME_PANEL = "#090E17"
BG_CHROME_CARD = "#0E1524"
BORDER_DARK = "#1E2A3E"

# Specular Chrome & Liquid Metal Gradients
CHROME_WHITE    = QColor(255, 255, 255)
CHROME_PLATINUM = QColor(226, 232, 240)
CHROME_SILVER   = QColor(148, 163, 184)
CHROME_STEEL    = QColor(51, 65, 85)

# Luminous Cyber Signaling
COLOR_CYAN_GLOW = QColor(0, 242, 254)      # #00F2FE: Focused Safety / Hologram
COLOR_EMERALD   = QColor(16, 185, 129)     # #10B981: 100% Alert, Optimal
COLOR_AMBER     = QColor(245, 158, 11)     # #F59E0B: Mirror Glance / Caution
COLOR_CRIMSON   = QColor(255, 30, 86)      # #FF1E56: Emergency Hazard
COLOR_PURPLE    = QColor(168, 85, 247)     # #A855F7: Neural Core Accent


# =====================================================================
# 1. CHROME HOLOGRAPHIC CAMERA HUD (With Mirror vs Road Sector Tape)
# =====================================================================

class ChromeCameraHUDWidget(QWidget):
    """
    Cinematic Chrome HUD featuring:
    - Avionic Road vs. Mirror Gaze Tape at the top of the canvas
    - Specular chrome corner brackets and holographic reticles
    - Vertical laser biometric scanning beam
    - 3D Chrome Attitude Gyroscope
    - Multi-Hazard Emergency Strobe (Micro-sleep & Distraction)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(f"background: {BG_OBSIDIAN}; border: 1px solid #1E293B; border-radius: 12px;")
        
        self.current_frame: Optional[QImage] = None
        self.telemetry: TelemetrySnapshot = TelemetrySnapshot()
        self.laser_sweep_y = 0.0
        self.laser_dir = 1
        self.pulse_phase = 0.0

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._on_anim_tick)
        self.anim_timer.start(25)

    def update_frame(self, q_img: QImage, telemetry: TelemetrySnapshot):
        self.current_frame = q_img
        self.telemetry = telemetry
        self.update()

    def _on_anim_tick(self):
        self.laser_sweep_y += 3.5 * self.laser_dir
        h = max(self.height(), 100)
        if self.laser_sweep_y >= h - 10:
            self.laser_dir = -1
        elif self.laser_sweep_y <= 10:
            self.laser_dir = 1

        self.pulse_phase = (self.pulse_phase + 0.1) % (2 * math.pi)
        if self.telemetry.alert_level >= 2 or not self.current_frame:
            self.update()

    def paintEvent(self, event):
        painter = QPainter()
        if not painter.begin(self):
            return

        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)

            w, h = self.width(), self.height()
            painter.fillRect(0, 0, w, h, QColor(BG_OBSIDIAN))

            if self.current_frame and not self.current_frame.isNull():
                img_w = self.current_frame.width()
                img_h = self.current_frame.height()
                if img_w > 0 and img_h > 0:
                    scale = min(w / img_w, h / img_h)
                    draw_w = int(img_w * scale)
                    draw_h = int(img_h * scale)
                    off_x = (w - draw_w) // 2
                    off_y = (h - draw_h) // 2

                    painter.drawImage(QRectF(off_x, off_y, draw_w, draw_h), self.current_frame)

                    # 1. Top Gaze Tape (Road vs Mirrors)
                    self._draw_road_mirror_gaze_tape(painter, off_x, off_y, draw_w)

                    # 2. Sweeping Laser Biometric Beam
                    self._draw_laser_scan_beam(painter, off_x, off_y, draw_w, draw_h)

                    # 3. Chrome Holographic Eye Reticles
                    self._draw_chrome_reticles(painter, off_x, off_y, scale)

                    # 4. Chrome Attitude Gyroscope
                    self._draw_chrome_gyro(painter, w - 110, 48)
            else:
                self._draw_standby_visual(painter, w, h)

            # Polished Chrome Outer Framing
            self._draw_chrome_frame_brackets(painter, w, h)

            # Multi-Hazard Emergency Strobe Banner
            if self.telemetry.alert_level >= 2:
                self._draw_hazard_strobe_banner(painter, w, h)

        except Exception:
            pass
        finally:
            painter.end()

    def _draw_road_mirror_gaze_tape(self, p: QPainter, off_x: int, off_y: int, dw: int):
        """
        Renders an avionic horizontal sector tape:
        [◀ LEFT MIRROR] ── [ ROAD AHEAD ] ── [RIGHT MIRROR ▶]
        Tracks the driver's head yaw in real time with a polished chrome beacon.
        """
        tape_w = min(420, dw - 40)
        tape_h = 24
        tape_x = off_x + (dw - tape_w) // 2
        tape_y = off_y + 12

        # Smoked chrome capsule background
        tape_rect = QRectF(tape_x, tape_y, tape_w, tape_h)
        p.fillRect(tape_rect, QColor(9, 14, 23, 220))
        
        # Chrome border with top specular bevel
        p.setPen(QPen(QColor(148, 163, 184, 120), 1))
        p.drawRoundedRect(tape_rect, 12, 12)

        # Sector Labels
        p.setFont(QFont("Segoe UI", 7, QFont.Bold))
        
        # Left Mirror sector
        p.setPen(QColor(100, 116, 139) if self.telemetry.head_yaw > -15 else COLOR_AMBER)
        p.drawText(QRectF(tape_x + 10, tape_y + 4, 85, 16), Qt.AlignCenter, "◀ L-MIRROR")

        # Road Center sector
        center_color = COLOR_EMERALD if abs(self.telemetry.head_yaw) <= 22 else QColor(100, 116, 139)
        p.setPen(center_color)
        p.drawText(QRectF(tape_x + (tape_w - 90) // 2, tape_y + 4, 90, 16), Qt.AlignCenter, "◉ ROAD AHEAD")

        # Right Mirror sector
        p.setPen(QColor(100, 116, 139) if self.telemetry.head_yaw < 15 else COLOR_AMBER)
        p.drawText(QRectF(tape_x + tape_w - 95, tape_y + 4, 85, 16), Qt.AlignCenter, "R-MIRROR ▶")

        # Real-time Gaze Pointer Needle (glides along tape)
        norm_yaw = np.clip(self.telemetry.head_yaw / 45.0, -1.0, 1.0)
        beacon_x = tape_x + tape_w / 2 + norm_yaw * (tape_w / 2 - 20)

        # Beacon color shifts: Emerald on road -> Amber on mirror -> Crimson if distracted >= 1.8s
        if self.telemetry.is_distracted:
            beacon_col = COLOR_CRIMSON
        elif self.telemetry.distraction_state == "MIRROR CHECK":
            beacon_col = COLOR_AMBER
        else:
            beacon_col = COLOR_CYAN_GLOW

        p.setPen(QPen(beacon_col, 2))
        p.setBrush(QBrush(beacon_col))
        p.drawEllipse(QPointF(beacon_x, tape_y + tape_h / 2), 5, 5)

    def _draw_laser_scan_beam(self, p: QPainter, off_x: int, off_y: int, dw: int, dh: int):
        cur_y = off_y + (self.laser_sweep_y % dh)
        grad = QLinearGradient(off_x, cur_y - 14, off_x, cur_y + 14)
        grad.setColorAt(0.0, QColor(0, 242, 254, 0))
        grad.setColorAt(0.5, QColor(0, 242, 254, 45))
        grad.setColorAt(1.0, QColor(0, 242, 254, 0))
        p.fillRect(QRectF(off_x, cur_y - 14, dw, 28), QBrush(grad))

        p.setPen(QPen(QColor(0, 242, 254, 90), 1.5))
        p.drawLine(off_x, int(cur_y), off_x + dw, int(cur_y))

    def _draw_chrome_reticles(self, p: QPainter, off_x: int, off_y: int, scale: float):
        for eye, label in [(self.telemetry.left_eye, "L-EYE"), (self.telemetry.right_eye, "R-EYE")]:
            x1, y1, x2, y2 = eye.box
            if x2 <= x1 or y2 <= y1:
                continue

            rx1 = int(off_x + x1 * scale)
            ry1 = int(off_y + y1 * scale)
            rx2 = int(off_x + x2 * scale)
            ry2 = int(off_y + y2 * scale)
            rw = rx2 - rx1
            rh = ry2 - ry1
            cx = (rx1 + rx2) // 2
            cy = (ry1 + ry2) // 2
            radius = max(rw, rh) // 2 + 10

            is_drowsy = (eye.state == "DROWSY")
            color = COLOR_CRIMSON if is_drowsy else COLOR_CYAN_GLOW

            # 1. Specular Chrome Orbital Arcs
            p.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 150), 2.0))
            p.setBrush(Qt.NoBrush)
            rot = int((self.pulse_phase * 35) % 360)
            p.drawArc(QRectF(cx - radius, cy - radius, radius * 2, radius * 2), rot * 16, 75 * 16)
            p.drawArc(QRectF(cx - radius, cy - radius, radius * 2, radius * 2), (rot + 180) * 16, 75 * 16)

            # 2. Chrome Beveled Corner Brackets
            c_len = max(8, int(rw * 0.30))
            p.setPen(QPen(color, 2.5))
            p.drawLine(rx1, ry1, rx1 + c_len, ry1)
            p.drawLine(rx1, ry1, rx1, ry1 + c_len)
            p.drawLine(rx2, ry1, rx2 - c_len, ry1)
            p.drawLine(rx2, ry1, rx2, ry1 + c_len)
            p.drawLine(rx1, ry2, rx1 + c_len, ry2)
            p.drawLine(rx1, ry2, rx1, ry2 - c_len)
            p.drawLine(rx2, ry2, rx2 - c_len, ry2)
            p.drawLine(rx2, ry2, rx2, ry2 - c_len)

            # 3. Pupil Laser Crosshair
            px, py = eye.pupil
            if px > 0 and py > 0:
                rpx = int(off_x + px * scale)
                rpy = int(off_y + py * scale)
                p.setPen(QPen(color, 1.2, Qt.DashLine))
                p.drawEllipse(QPointF(rpx, rpy), 5, 5)
                p.drawLine(rpx - 8, rpy, rpx + 8, rpy)
                p.drawLine(rpx, rpy - 8, rpx, rpy + 8)

            # 4. Floating Chrome Pill Badge
            badge_rect = QRectF(rx1 - 6, ry2 + 6, rw + 12, 18)
            p.fillRect(badge_rect, QColor(9, 14, 23, 210))
            p.setPen(QPen(QColor(148, 163, 184, 100), 1))
            p.drawRoundedRect(badge_rect, 4, 4)

            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            p.setPen(color)
            txt = f"{label}: {eye.aperture_pct}%" if not is_drowsy else f"{label}: CLOSED"
            p.drawText(badge_rect, Qt.AlignCenter, txt)

    def _draw_chrome_gyro(self, p: QPainter, cx: int, cy: int):
        radius = 32
        p.save()
        try:
            p.translate(cx + radius, cy + radius)
            
            # Polished chrome gimbal casing
            p.setPen(QPen(QColor(148, 163, 184, 180), 1.5))
            p.setBrush(QBrush(QColor(9, 14, 23, 210)))
            p.drawEllipse(QPointF(0, 0), radius, radius)

            # Horizon & crosshairs
            p.setPen(QPen(QColor(100, 116, 139, 90), 1, Qt.DotLine))
            p.drawLine(-radius + 4, 0, radius - 4, 0)
            p.drawLine(0, -radius + 4, 0, radius - 4)

            yaw = 0.0 if math.isnan(self.telemetry.head_yaw) else self.telemetry.head_yaw
            pitch = 0.0 if math.isnan(self.telemetry.head_pitch) else self.telemetry.head_pitch
            max_off = float(radius - 8)
            yo = float(np.clip(yaw / 40.0 * max_off, -max_off, max_off))
            po = float(np.clip(pitch / 40.0 * max_off, -max_off, max_off))

            dot_col = COLOR_CRIMSON if self.telemetry.is_distracted else (COLOR_AMBER if self.telemetry.distraction_state == "MIRROR CHECK" else COLOR_CYAN_GLOW)
            p.setPen(QPen(dot_col, 2))
            p.setBrush(QBrush(dot_col))
            p.drawEllipse(QPointF(yo, po), 4, 4)

            p.setFont(QFont("Segoe UI", 7, QFont.Bold))
            p.setPen(CHROME_SILVER)
            p.drawText(-22, radius + 14, "HEAD GYRO")
        finally:
            p.restore()

    def _draw_chrome_frame_brackets(self, p: QPainter, w: int, h: int):
        # Top-left and bottom-right metallic brackets
        p.setPen(QPen(COLOR_CYAN_GLOW, 1.8))
        p.setBrush(Qt.NoBrush)
        bl = 24
        p.drawLine(10, 10, 10 + bl, 10)
        p.drawLine(10, 10, 10, 10 + bl)
        p.drawLine(w - 10, 10, w - 10 - bl, 10)
        p.drawLine(w - 10, 10, w - 10, 10 + bl)
        p.drawLine(10, h - 10, 10 + bl, h - 10)
        p.drawLine(10, h - 10, 10, h - 10 - bl)
        p.drawLine(w - 10, h - 10, w - 10 - bl, h - 10)
        p.drawLine(w - 10, h - 10, w - 10, h - 10 - bl)

        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.setPen(CHROME_PLATINUM)
        p.drawText(20, h - 16, "SENTINEL BIO-SENSORY HUD // ACTIVE")

    def _draw_hazard_strobe_banner(self, p: QPainter, w: int, h: int):
        banner_h = 56
        by = 46
        banner_rect = QRectF(0, by, w, banner_h)
        
        flash_alpha = int(195 + 60 * math.sin(self.pulse_phase * 4))
        
        if self.telemetry.alert_reason == "DISTRACTION":
            bg_col = QColor(255, 30, 86, flash_alpha)
            main_msg = f"⚠ DISTRACTION ALERT: EYES OFF ROAD ({self.telemetry.distraction_duration:.1f}s)!"
            sub_msg = "FOCUS ON THE ROAD AHEAD IMMEDIATELY"
        elif self.telemetry.alert_reason == "MICROSLEEP":
            bg_col = QColor(255, 30, 86, flash_alpha)
            main_msg = f"⚠ CRITICAL WARNING: WAKE UP! (EYES CLOSED {self.telemetry.closure_duration:.1f}s)"
            sub_msg = "PULL OVER TO A SAFE LOCATION IMMEDIATELY"
        else:
            bg_col = QColor(245, 158, 11, flash_alpha)
            main_msg = "⚠ ATTENTION: SLUGGISH APERTURE ADVISORY"
            sub_msg = "REST ADVICE: TAKE A BREAK SOON"

        p.fillRect(banner_rect, bg_col)

        # Warning Stripes
        p.setPen(QPen(QColor(0, 0, 0, 65), 3))
        for sx in range(0, w + banner_h, 24):
            p.drawLine(sx, by, sx - banner_h, by + banner_h)

        p.setFont(QFont("Segoe UI", 13, QFont.Bold))
        p.setPen(Qt.white)
        p.drawText(QRectF(0, by + 6, w, 22), Qt.AlignCenter, main_msg)

        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.drawText(QRectF(0, by + 30, w, 18), Qt.AlignCenter, sub_msg)

    def _draw_standby_visual(self, p: QPainter, w: int, h: int):
        p.setFont(QFont("Segoe UI", 12, QFont.Bold))
        p.setPen(COLOR_CYAN_GLOW)
        p.drawText(QRectF(0, h // 2 - 30, w, 30), Qt.AlignCenter, "INITIALIZING AI GUARDIAN VISION...")
        p.setFont(QFont("Segoe UI", 10))
        p.setPen(CHROME_SILVER)
        p.drawText(QRectF(0, h // 2 + 4, w, 30), Qt.AlignCenter, "Looking for operator facial anchors.")


# =====================================================================
# 2. LIQUID CHROME VIGILANCE CORE (Polished Metallic Reactor)
# =====================================================================

class ChromeVigilanceCoreWidget(QWidget):
    """
    Polished double-bezel chrome reactor dial showing overall alertness (0-100%).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.alertness_pct = 100
        self.status_title = "OPTIMAL"
        self.setMinimumSize(175, 175)

    def set_alertness(self, score_0_to_1: float, alert_level: int, reason: str):
        self.alertness_pct = int(np.clip((1.0 - score_0_to_1) * 100, 0, 100))
        if alert_level == 3:
            self.status_title = "DISTRACTED" if reason == "DISTRACTION" else "CRITICAL"
        elif alert_level == 2:
            self.status_title = "WARNING"
        elif self.alertness_pct < 65:
            self.status_title = "FATIGUED"
        elif self.alertness_pct < 85:
            self.status_title = "ATTENTIVE"
        else:
            self.status_title = "OPTIMAL"
        self.update()

    def paintEvent(self, event):
        p = QPainter()
        if not p.begin(self):
            return
        try:
            p.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()
            side = min(w, h) - 22
            cx, cy = w / 2, h / 2 - 4
            rect = QRectF(cx - side / 2, cy - side / 2, side, side)

            if self.alertness_pct >= 75:
                accent_color = COLOR_EMERALD
            elif self.alertness_pct >= 45:
                accent_color = COLOR_AMBER
            else:
                accent_color = COLOR_CRIMSON

            # Polished Chrome Outer Bezel (Linear Metallic Gradient)
            grad_bezel = QLinearGradient(0, 0, w, h)
            grad_bezel.setColorAt(0.0, QColor(226, 232, 240, 180))
            grad_bezel.setColorAt(0.5, QColor(51, 65, 85, 220))
            grad_bezel.setColorAt(1.0, QColor(148, 163, 184, 180))
            p.setPen(QPen(QBrush(grad_bezel), 11, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, int(-220 * 16), int(-260 * 16))

            # Dynamic Energy Arc
            span = int(-260 * (self.alertness_pct / 100.0) * 16)
            p.setPen(QPen(accent_color, 7, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, int(-220 * 16), span)

            # Center Numerical Readout with Specular Chrome Highlight
            p.setFont(QFont("Segoe UI", 27, QFont.Bold))
            p.setPen(CHROME_WHITE)
            p.drawText(QRectF(cx - side / 2, cy - 26, side, 34), Qt.AlignCenter, f"{self.alertness_pct}%")

            # Status Subtitle
            p.setFont(QFont("Segoe UI", 9, QFont.Bold))
            p.setPen(accent_color)
            p.drawText(QRectF(cx - side / 2, cy + 12, side, 18), Qt.AlignCenter, self.status_title)

            # Bottom Chrome Tag
            p.setFont(QFont("Segoe UI", 7, QFont.Bold))
            p.setPen(CHROME_SILVER)
            p.drawText(QRectF(0, h - 14, w, 14), Qt.AlignCenter, "NEURAL VIGILANCE CORE")
        finally:
            p.end()


# =====================================================================
# 3. CHROME ROAD FOCUS & GAZE MONITOR
# =====================================================================

class ChromeGazeFocusWidget(QWidget):
    """
    Displays current Driver Gaze State:
    - [ROAD AHEAD] (Safe, Emerald)
    - [MIRROR CHECK: 0.8s] (Safe glance, Amber)
    - [DISTRACTION: 1.8s] (Alert, Crimson)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = "FORWARD ROAD"
        self.duration = 0.0
        self.yaw = 0.0
        self.setMinimumHeight(64)

    def set_gaze(self, state: str, dur: float, yaw: float):
        self.state = state
        self.duration = dur
        self.yaw = yaw
        self.update()

    def paintEvent(self, event):
        p = QPainter()
        if not p.begin(self):
            return
        try:
            p.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()
            
            # Chrome Capsule Card
            p.fillRect(0, 0, w, h, QColor(BG_CHROME_CARD))
            p.setPen(QPen(QColor(BORDER_DARK), 1))
            p.drawRoundedRect(0, 0, w - 1, h - 1, 6, 6)

            if self.state == "DISTRACTED":
                status_col = COLOR_CRIMSON
                status_txt = f"⚠ DISTRACTION DETECTED: {self.duration:.1f}s"
                desc_txt = "Eyes turned away for over 1.8s! Focus on road!"
            elif self.state == "MIRROR CHECK":
                status_col = COLOR_AMBER
                status_txt = f"MIRROR GLANCE ({self.duration:.1f}s / 1.8s MAX)"
                desc_txt = "Active rearview/side mirror check (Normal glance)"
            else:
                status_col = COLOR_EMERALD
                status_txt = "ROAD AHEAD (FOCUS OPTIMAL)"
                desc_txt = "Gaze locked on forward roadway"

            p.setFont(QFont("Segoe UI", 10, QFont.Bold))
            p.setPen(status_col)
            p.drawText(12, 22, status_txt)

            p.setFont(QFont("Segoe UI", 8))
            p.setPen(CHROME_SILVER)
            p.drawText(12, 40, desc_txt)

            # Progress bar towards 1.8s limit
            bar_w = w - 24
            p.fillRect(12, 48, bar_w, 4, QColor(30, 41, 59))
            if self.duration > 0:
                prog_w = int(min(self.duration / 1.80, 1.0) * bar_w)
                p.fillRect(12, 48, prog_w, 4, status_col)
        finally:
            p.end()


# =====================================================================
# 4. CHROME 1.5s EMERGENCY TIMER
# =====================================================================

class ChromeEmergencyTimerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 0.0
        self.is_closed = False
        self.setMinimumSize(140, 115)

    def set_duration(self, seconds: float, is_closed: bool):
        self.duration = seconds
        self.is_closed = is_closed
        self.update()

    def paintEvent(self, event):
        p = QPainter()
        if not p.begin(self):
            return
        try:
            p.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()
            radius = min(w, h) / 2 - 14
            cx, cy = w / 2, h / 2 - 8
            rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

            # Base Chrome ring
            p.setPen(QPen(QColor(30, 41, 59), 6))
            p.drawEllipse(QPointF(cx, cy), radius, radius)

            # Emergency Countdown Arc
            norm_val = min(self.duration / 1.50, 1.0)
            span_angle = int(-360 * norm_val * 16)
            sweep_col = COLOR_CRIMSON if self.duration >= 1.50 else (COLOR_AMBER if self.duration >= 0.70 else COLOR_EMERALD)
            p.setPen(QPen(sweep_col, 6, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, 90 * 16, span_angle)

            # Numerical Seconds
            p.setFont(QFont("Consolas", 15, QFont.Bold))
            p.setPen(COLOR_CRIMSON if self.duration >= 1.50 else CHROME_WHITE)
            p.drawText(QRectF(cx - radius, cy - 14, radius * 2, 28), Qt.AlignCenter, f"{self.duration:.2f}s")

            p.setFont(QFont("Segoe UI", 7, QFont.Bold))
            p.setPen(CHROME_SILVER)
            cap = "1.5s MICRO-SLEEP ALARM" if not self.is_closed else "EYES CLOSED COUNTDOWN"
            p.drawText(0, h - 8, w, 14, Qt.AlignCenter, cap)
        finally:
            p.end()


# =====================================================================
# 5. CHROME VITAL RHYTHM WAVEFORM (Specular Silver Ribbon)
# =====================================================================

class ChromeVitalWaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = deque(maxlen=180)
        self.setMinimumHeight(65)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def add_sample(self, fatigue_val: float):
        self.history.append(fatigue_val)
        self.update()

    def paintEvent(self, event):
        p = QPainter()
        if not p.begin(self):
            return
        try:
            p.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()

            # Obsidian metallic background
            p.fillRect(0, 0, w, h, QColor(BG_CHROME_CARD))
            p.setPen(QPen(QColor(BORDER_DARK), 1))
            p.drawRoundedRect(0, 0, w - 1, h - 1, 6, 6)

            # Ambient grid
            p.setPen(QPen(QColor(255, 255, 255, 10), 1, Qt.DotLine))
            for gx in range(0, w, 45):
                p.drawLine(gx, 0, gx, h)
            p.drawLine(0, int(h * 0.5), w, int(h * 0.5))

            # Amber Risk Ceiling (50%)
            thresh_y = int(h * (1.0 - 0.50))
            p.setPen(QPen(QColor(245, 158, 11, 90), 1, Qt.DashLine))
            p.drawLine(0, thresh_y, w, thresh_y)
            p.setFont(QFont("Segoe UI", 7, QFont.Bold))
            p.setPen(QColor(245, 158, 11, 140))
            p.drawText(8, thresh_y - 2, "SAFETY THRESHOLD")

            if len(self.history) < 2:
                return

            pts = []
            step = w / max(len(self.history) - 1, 1)
            for i, val in enumerate(self.history):
                px = i * step
                py = h - 6 - val * (h - 12)
                pts.append(QPointF(px, py))

            # Filled Chrome/Cyan gradient ribbon
            path = QPainterPath()
            path.moveTo(0, h)
            for pt in pts:
                path.lineTo(pt)
            path.lineTo(w, h)
            path.closeSubpath()

            grad = QLinearGradient(0, 0, 0, h)
            grad.setColorAt(0.0, QColor(0, 242, 254, 75))
            grad.setColorAt(1.0, QColor(0, 242, 254, 0))
            p.fillPath(path, QBrush(grad))

            # Specular crest line
            p.setPen(QPen(CHROME_WHITE, 2.0))
            for i in range(len(pts) - 1):
                p.drawLine(pts[i], pts[i + 1])
        finally:
            p.end()


# =====================================================================
# MAIN WINDOW: SENTINEL CHROME EDITION
# =====================================================================

class SentinelMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SENTINEL // Cyber-Avionics Driver Copilot")
        self.resize(1380, 860)
        self.setStyleSheet(f"""
            QMainWindow {{ background: {BG_OBSIDIAN}; }}
            QWidget {{ color: #F1F5F9; font-family: 'Segoe UI', sans-serif; }}
            QLabel {{ font-size: 11px; }}
            QFrame {{ border: none; }}
        """)

        self.worker = SentinelPipelineWorker()
        self.worker.frame_ready.connect(self.on_frame_received)
        self.worker.error_signal.connect(self.on_worker_error)

        self._init_layout()
        self.worker.start()

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()

    def _init_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_vbox = QVBoxLayout(central_widget)
        main_vbox.setContentsMargins(14, 12, 14, 12)
        main_vbox.setSpacing(10)

        main_vbox.addWidget(self._build_top_bar())

        workspace_hbox = QHBoxLayout()
        workspace_hbox.setSpacing(12)

        workspace_hbox.addWidget(self._build_left_rail())

        self.center_stack = QStackedWidget()
        self.camera_hud = ChromeCameraHUDWidget()
        self.center_stack.addWidget(self.camera_hud)                         # 0: Live HUD
        self.center_stack.addWidget(self._build_trip_safety_page())          # 1: Trip Safety
        self.center_stack.addWidget(self._build_ai_brain_page())             # 2: AI Brain
        self.center_stack.addWidget(self._build_settings_page())             # 3: Preferences
        workspace_hbox.addWidget(self.center_stack, stretch=7)

        workspace_hbox.addWidget(self._build_right_panel(), stretch=3)

        main_vbox.addLayout(workspace_hbox, stretch=1)
        main_vbox.addWidget(self._build_bottom_strip())

    def _build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet(f"""
            QFrame {{
                background: {BG_CHROME_PANEL};
                border: 1px solid {BORDER_DARK};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        hbox = QHBoxLayout(bar)
        hbox.setContentsMargins(16, 6, 16, 6)

        title_box = QVBoxLayout()
        brand_row = QHBoxLayout()
        logo_icon = QLabel("🛡")
        logo_icon.setStyleSheet("font-size: 16px; margin-right: 4px;")
        brand_row.addWidget(logo_icon)

        title_lbl = QLabel("SENTINEL // CHROME COPILOT")
        title_lbl.setStyleSheet(f"font-size: 15px; font-weight: bold; letter-spacing: 2px; color: {CHROME_WHITE.name()};")
        brand_row.addWidget(title_lbl)
        brand_row.addStretch()
        title_box.addLayout(brand_row)

        sub_lbl = QLabel("BIO-SENSORY DRIVER SHIELD // 1.5S MICRO-SLEEP & 1.8S DISTRACTION SENSOR")
        sub_lbl.setStyleSheet("font-size: 8px; color: #64748B; letter-spacing: 1.5px;")
        title_box.addWidget(sub_lbl)
        hbox.addLayout(title_box)

        hbox.addStretch()

        self.shield_status_lbl = QLabel("● SHIELD: ACTIVE & WATCHING")
        self.shield_status_lbl.setStyleSheet("background: rgba(16, 185, 129, 0.15); border: 1px solid #10B981; border-radius: 14px; padding: 5px 14px; font-size: 10px; font-weight: bold; color: #34D399;")
        hbox.addWidget(self.shield_status_lbl)

        self.cam_pill = QLabel("CAMERA: 1080P REAL-TIME")
        self.cam_pill.setStyleSheet("background: #0E1524; border: 1px solid #1E293B; border-radius: 14px; padding: 5px 12px; font-size: 10px; font-weight: bold; color: #94A3B8;")
        hbox.addWidget(self.cam_pill)

        self.fps_lbl = QLabel("FPS: --")
        self.fps_lbl.setStyleSheet("background: #0E1524; border: 1px solid #1E293B; border-radius: 14px; padding: 5px 12px; font-size: 10px; font-weight: bold; color: #38BDF8;")
        hbox.addWidget(self.fps_lbl)

        return bar

    def _build_left_rail(self) -> QWidget:
        rail = QFrame()
        rail.setFixedWidth(168)
        rail.setStyleSheet(f"""
            QFrame {{
                background: {BG_CHROME_PANEL};
                border: 1px solid {BORDER_DARK};
                border-radius: 8px;
            }}
            QPushButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
                padding: 11px 12px;
                text-align: left;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
                color: #94A3B8;
            }}
            QPushButton:hover {{
                background: #1E293B;
                color: #F8FAFC;
                border-color: #334155;
            }}
            QPushButton:checked {{
                background: rgba(0, 242, 254, 0.12);
                border-color: {COLOR_CYAN_GLOW.name()};
                color: {COLOR_CYAN_GLOW.name()};
            }}
        """)
        vbox = QVBoxLayout(rail)
        vbox.setContentsMargins(10, 14, 10, 14)
        vbox.setSpacing(8)

        dock_lbl = QLabel("NAVIGATION DOCK")
        dock_lbl.setStyleSheet("font-size: 8px; font-weight: bold; letter-spacing: 1.5px; color: #475569; margin-bottom: 4px;")
        vbox.addWidget(dock_lbl)

        self.btn_nav_hud = QPushButton("👁 LIVE COPILOT")
        self.btn_nav_hud.setCheckable(True)
        self.btn_nav_hud.setChecked(True)
        self.btn_nav_hud.clicked.connect(lambda: self._switch_tab(0, self.btn_nav_hud))
        vbox.addWidget(self.btn_nav_hud)

        self.btn_nav_analytics = QPushButton("📊 TRIP METRICS")
        self.btn_nav_analytics.setCheckable(True)
        self.btn_nav_analytics.clicked.connect(lambda: self._switch_tab(1, self.btn_nav_analytics))
        vbox.addWidget(self.btn_nav_analytics)

        self.btn_nav_model = QPushButton("🧠 AI NEURAL BRAIN")
        self.btn_nav_model.setCheckable(True)
        self.btn_nav_model.clicked.connect(lambda: self._switch_tab(2, self.btn_nav_model))
        vbox.addWidget(self.btn_nav_model)

        self.btn_nav_settings = QPushButton("⚙ PREFERENCES")
        self.btn_nav_settings.setCheckable(True)
        self.btn_nav_settings.clicked.connect(lambda: self._switch_tab(3, self.btn_nav_settings))
        vbox.addWidget(self.btn_nav_settings)

        vbox.addStretch()

        btn_test_audio = QPushButton("🔊 TEST ALARM")
        btn_test_audio.setStyleSheet("background: rgba(245, 158, 11, 0.15); border: 1px solid #F59E0B; color: #F59E0B; text-align: center; border-radius: 6px;")
        btn_test_audio.clicked.connect(self.worker.test_audio)
        vbox.addWidget(btn_test_audio)

        self.mute_check = QCheckBox("MUTE AUDIO")
        self.mute_check.setStyleSheet("font-size: 9px; font-weight: bold; color: #94A3B8; padding: 4px;")
        self.mute_check.toggled.connect(lambda val: self.worker.set_muted(val))
        vbox.addWidget(self.mute_check)

        return rail

    def _switch_tab(self, index: int, active_btn: QPushButton):
        self.center_stack.setCurrentIndex(index)
        for btn in [self.btn_nav_hud, self.btn_nav_analytics, self.btn_nav_model, self.btn_nav_settings]:
            btn.setChecked(btn == active_btn)

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background: {BG_CHROME_PANEL};
                border: 1px solid {BORDER_DARK};
                border-radius: 8px;
            }}
        """)
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(14, 14, 14, 14)
        vbox.setSpacing(10)

        # 1. Liquid Chrome Vigilance Core
        vbox.addWidget(self._make_section_header("NEURAL VIGILANCE CORE"))
        self.vigilance_core = ChromeVigilanceCoreWidget()
        vbox.addWidget(self.vigilance_core, alignment=Qt.AlignCenter)

        # 2. Road Focus & Mirror Awareness Sensor
        vbox.addWidget(self._make_section_header("GAZE & MIRROR AWARENESS"))
        self.gaze_widget = ChromeGazeFocusWidget()
        vbox.addWidget(self.gaze_widget)

        # 3. Dual Eye Scanner Bars
        vbox.addWidget(self._make_section_header("OPTICAL APERTURE"))
        eyes_card = QFrame()
        eyes_card.setStyleSheet("background: #0E1524; border: 1px solid #1E293B; border-radius: 6px; padding: 6px;")
        eyes_layout = QVBoxLayout(eyes_card)
        eyes_layout.setSpacing(6)

        # Left Eye
        l_row = QHBoxLayout()
        l_row.addWidget(QLabel("LEFT EYE:"))
        self.lbl_l_state = QLabel("100% OPEN")
        self.lbl_l_state.setStyleSheet("font-weight: bold; color: #34D399; font-size: 11px;")
        l_row.addWidget(self.lbl_l_state, alignment=Qt.AlignRight)
        eyes_layout.addLayout(l_row)

        self.bar_left_eye = QProgressBar()
        self.bar_left_eye.setRange(0, 100)
        self.bar_left_eye.setValue(100)
        self.bar_left_eye.setTextVisible(False)
        self.bar_left_eye.setFixedHeight(5)
        self.bar_left_eye.setStyleSheet("QProgressBar { background: #1E293B; border-radius: 2px; } QProgressBar::chunk { background: #00F2FE; border-radius: 2px; }")
        eyes_layout.addWidget(self.bar_left_eye)

        # Right Eye
        r_row = QHBoxLayout()
        r_row.addWidget(QLabel("RIGHT EYE:"))
        self.lbl_r_state = QLabel("100% OPEN")
        self.lbl_r_state.setStyleSheet("font-weight: bold; color: #34D399; font-size: 11px;")
        r_row.addWidget(self.lbl_r_state, alignment=Qt.AlignRight)
        eyes_layout.addLayout(r_row)

        self.bar_right_eye = QProgressBar()
        self.bar_right_eye.setRange(0, 100)
        self.bar_right_eye.setValue(100)
        self.bar_right_eye.setTextVisible(False)
        self.bar_right_eye.setFixedHeight(5)
        self.bar_right_eye.setStyleSheet("QProgressBar { background: #1E293B; border-radius: 2px; } QProgressBar::chunk { background: #00F2FE; border-radius: 2px; }")
        eyes_layout.addWidget(self.bar_right_eye)

        vbox.addWidget(eyes_card)

        # 4. 1.5s Emergency Timer Ring
        vbox.addWidget(self._make_section_header("1.5s MICRO-SLEEP ALARM"))
        self.emergency_timer_widget = ChromeEmergencyTimerWidget()
        vbox.addWidget(self.emergency_timer_widget, alignment=Qt.AlignCenter)

        vbox.addStretch()
        return panel

    def _build_bottom_strip(self) -> QWidget:
        strip = QFrame()
        strip.setStyleSheet(f"""
            QFrame {{
                background: {BG_CHROME_PANEL};
                border: 1px solid {BORDER_DARK};
                border-radius: 8px;
            }}
        """)
        hbox = QHBoxLayout(strip)
        hbox.setContentsMargins(16, 8, 16, 8)
        hbox.setSpacing(16)

        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(8)

        self.lbl_drive_time = QLabel("DRIVE TIME: 00:00:00")
        self.lbl_drive_time.setStyleSheet("font-family: Consolas; font-weight: bold; font-size: 11px; color: #38BDF8;")
        metrics_grid.addWidget(self.lbl_drive_time, 0, 0)

        self.lbl_blinks = QLabel("BLINKS: 0 (0.0/min)")
        self.lbl_blinks.setStyleSheet("font-family: Consolas; font-weight: bold; font-size: 11px; color: #F1F5F9;")
        metrics_grid.addWidget(self.lbl_blinks, 0, 1)

        self.lbl_microsleeps = QLabel("DROWSY EVENTS: 0")
        self.lbl_microsleeps.setStyleSheet("font-family: Consolas; font-weight: bold; font-size: 11px; color: #F59E0B;")
        metrics_grid.addWidget(self.lbl_microsleeps, 1, 0)

        self.lbl_distractions = QLabel("DISTRACTIONS: 0")
        self.lbl_distractions.setStyleSheet("font-family: Consolas; font-size: 11px; font-weight: bold; color: #34D399;")
        metrics_grid.addWidget(self.lbl_distractions, 1, 1)

        hbox.addLayout(metrics_grid, stretch=3)

        self.vital_waveform = ChromeVitalWaveformWidget()
        hbox.addWidget(self.vital_waveform, stretch=7)

        return strip

    def _make_section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 8px; font-weight: bold; letter-spacing: 1.5px; color: #64748B; margin-top: 2px;")
        return lbl

    def _build_trip_safety_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background: {BG_CHROME_CARD}; border: 1px solid {BORDER_DARK}; border-radius: 8px; padding: 24px;")
        vbox = QVBoxLayout(page)

        lbl = QLabel("TRIP SAFETY & FATIGUE SCOREBOARD")
        lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {CHROME_WHITE.name()};")
        vbox.addWidget(lbl)

        desc = QLabel("Comprehensive overview of your driving alertness, mirror checks, and road focus.")
        desc.setStyleSheet("color: #94A3B8; font-size: 12px; margin-bottom: 24px;")
        vbox.addWidget(desc)

        self.trip_summary_lbl = QLabel(
            "• Active Journey Duration: 00:00:00\n\n"
            "• Natural Blink Rate: 0.0 Blinks / Minute\n\n"
            "• Micro-Sleep Incidents: 0\n\n"
            "• Prolonged Distractions (>1.8s): 0\n\n"
            "• Copilot Verdict: Your reaction time and focus are in peak condition."
        )
        self.trip_summary_lbl.setStyleSheet("font-size: 13px; line-height: 2.0; color: #E2E8F0; font-family: 'Segoe UI';")
        vbox.addWidget(self.trip_summary_lbl)
        vbox.addStretch()
        return page

    def _build_ai_brain_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background: {BG_CHROME_CARD}; border: 1px solid {BORDER_DARK}; border-radius: 8px; padding: 24px;")
        vbox = QVBoxLayout(page)

        lbl = QLabel("HOW THE SENTINEL COPILOT PROTECTS YOU")
        lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {CHROME_WHITE.name()};")
        vbox.addWidget(lbl)

        desc = QLabel("Sentinel acts as an intelligent co-driver, tracking your alertness and head orientation while fully respecting normal mirror checks.")
        desc.setStyleSheet("color: #94A3B8; font-size: 12px; margin-bottom: 20px;")
        vbox.addWidget(desc)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(14)

        # Card 1: Mirror Check Tolerance
        c1 = QFrame()
        c1.setStyleSheet("background: #090E17; border: 1px solid #1E293B; border-radius: 6px; padding: 14px;")
        l1 = QVBoxLayout(c1)
        t1 = QLabel("1. Mirror-Check Intelligent Tolerance")
        t1.setStyleSheet("font-weight: bold; color: #F59E0B; font-size: 12px;")
        p1 = QLabel("Checking side or rearview mirrors is normal driving behavior. Glances under 1.8 seconds are recognized as safe and never trigger false alarms.")
        p1.setStyleSheet("color: #94A3B8; font-size: 10px;")
        p1.setWordWrap(True)
        l1.addWidget(t1)
        l1.addWidget(p1)
        cards_layout.addWidget(c1, 0, 0)

        # Card 2: 1.8s Distraction Alarm
        c2 = QFrame()
        c2.setStyleSheet("background: #090E17; border: 1px solid #1E293B; border-radius: 6px; padding: 14px;")
        l2 = QVBoxLayout(c2)
        t2 = QLabel("2. 1.8-Second Distraction Lifesaver")
        t2.setStyleSheet("font-weight: bold; color: #FF1E56; font-size: 12px;")
        p2 = QLabel("Looking away from the road (e.g. texting or rubbernecking) for 1.8 seconds continuous triggers an urgent alert to return eyes to the road.")
        p2.setStyleSheet("color: #94A3B8; font-size: 10px;")
        p2.setWordWrap(True)
        l2.addWidget(t2)
        l2.addWidget(p2)
        cards_layout.addWidget(c2, 0, 1)

        # Card 3: 1.5s Micro-sleep Alarm
        c3 = QFrame()
        c3.setStyleSheet("background: #090E17; border: 1px solid #1E293B; border-radius: 6px; padding: 14px;")
        l3 = QVBoxLayout(c3)
        t3 = QLabel("3. 1.5-Second Micro-Sleep Sensor")
        t3.setStyleSheet("font-weight: bold; color: #00F2FE; font-size: 12px;")
        p3 = QLabel("Continuous eye closure for 1.5 seconds immediately sounds the dual-tone cockpit emergency siren to snap the driver awake.")
        p3.setStyleSheet("color: #94A3B8; font-size: 10px;")
        p3.setWordWrap(True)
        l3.addWidget(t3)
        l3.addWidget(p3)
        cards_layout.addWidget(c3, 1, 0)

        # Card 4: 100% On-Device Privacy
        c4 = QFrame()
        c4.setStyleSheet("background: #090E17; border: 1px solid #1E293B; border-radius: 6px; padding: 14px;")
        l4 = QVBoxLayout(c4)
        t4 = QLabel("4. 100% Private & Local Processing")
        t4.setStyleSheet("font-weight: bold; color: #10B981; font-size: 12px;")
        p4 = QLabel("Zero video or telemetry ever leaves your computer. All neural and biometric calculations occur locally in real time.")
        p4.setStyleSheet("color: #94A3B8; font-size: 10px;")
        p4.setWordWrap(True)
        l4.addWidget(t4)
        l4.addWidget(p4)
        cards_layout.addWidget(c4, 1, 1)

        vbox.addLayout(cards_layout)
        vbox.addStretch()
        return page

    def _build_settings_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background: {BG_CHROME_CARD}; border: 1px solid {BORDER_DARK}; border-radius: 8px; padding: 24px;")
        vbox = QVBoxLayout(page)

        lbl = QLabel("COPILOT SENSITIVITY & PREFERENCES")
        lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {CHROME_WHITE.name()};")
        vbox.addWidget(lbl)

        vbox.addWidget(QLabel("Eye Openness Sensitivity (Default: 0.24):"))
        self.slider_ear = QSlider(Qt.Horizontal)
        self.slider_ear.setRange(15, 35)
        self.slider_ear.setValue(24)
        vbox.addWidget(self.slider_ear)

        vbox.addWidget(QLabel("Distraction Warning Threshold (Default: 1.80 seconds):"))
        self.slider_dist = QSlider(Qt.Horizontal)
        self.slider_dist.setRange(12, 30)
        self.slider_dist.setValue(18)
        vbox.addWidget(self.slider_dist)

        vbox.addWidget(QLabel("Micro-Sleep Alarm Trigger Time (Default: 1.50 seconds):"))
        self.slider_emerg = QSlider(Qt.Horizontal)
        self.slider_emerg.setRange(80, 250)
        self.slider_emerg.setValue(150)
        vbox.addWidget(self.slider_emerg)

        save_btn = QPushButton("SAVE SENSITIVITY PREFERENCES")
        save_btn.setStyleSheet(f"background: {COLOR_CYAN_GLOW.name()}; color: #07090E; font-weight: bold; padding: 11px; border-radius: 6px; margin-top: 20px;")
        save_btn.clicked.connect(self._apply_settings)
        vbox.addWidget(save_btn)

        vbox.addStretch()
        return page

    def _apply_settings(self):
        ear_val = self.slider_ear.value() / 100.0
        emerg_val = self.slider_emerg.value() / 100.0
        self.worker.update_sensitivity(ear_val, 0.60, 0.70, emerg_val)

    @Slot(QImage, TelemetrySnapshot)
    def on_frame_received(self, q_img: QImage, tel: TelemetrySnapshot):
        try:
            self.camera_hud.update_frame(q_img, tel)
            self.fps_lbl.setText(f"FPS: {tel.fps}")

            # 1. Update Liquid Chrome Vigilance Core
            self.vigilance_core.set_alertness(tel.fatigue_score, tel.alert_level, tel.alert_reason)

            # 2. Update Gaze & Mirror Awareness Card
            self.gaze_widget.set_gaze(tel.distraction_state, tel.distraction_duration, tel.head_yaw)

            # 3. Update Eye Aperture Bars
            self.bar_left_eye.setValue(tel.left_eye.aperture_pct)
            self.bar_right_eye.setValue(tel.right_eye.aperture_pct)

            l_txt = "CLOSED" if tel.left_eye.state == "DROWSY" else f"{tel.left_eye.aperture_pct}% OPEN"
            r_txt = "CLOSED" if tel.right_eye.state == "DROWSY" else f"{tel.right_eye.aperture_pct}% OPEN"
            l_col = "#FF1E56" if tel.left_eye.state == "DROWSY" else "#34D399"
            r_col = "#FF1E56" if tel.right_eye.state == "DROWSY" else "#34D399"

            self.lbl_l_state.setText(l_txt)
            self.lbl_l_state.setStyleSheet(f"font-weight: bold; color: {l_col}; font-size: 11px;")
            self.lbl_r_state.setText(r_txt)
            self.lbl_r_state.setStyleSheet(f"font-weight: bold; color: {r_col}; font-size: 11px;")

            # 4. Update 1.5s Emergency Timer Ring
            self.emergency_timer_widget.set_duration(tel.closure_duration, tel.is_closed)

            # 5. Top Bar Shield Indicator
            if tel.alert_level == 3:
                if tel.alert_reason == "DISTRACTION":
                    self.shield_status_lbl.setText("● WARNING: EYES OFF ROAD (>1.8s)")
                else:
                    self.shield_status_lbl.setText("● HAZARD: CRITICAL MICRO-SLEEP")
                self.shield_status_lbl.setStyleSheet("background: #FF1E56; color: white; border-radius: 14px; padding: 5px 14px; font-size: 10px; font-weight: bold;")
            elif tel.alert_level == 2:
                self.shield_status_lbl.setText("● WARNING: EARLY FATIGUE DETECTED")
                self.shield_status_lbl.setStyleSheet("background: rgba(245, 158, 11, 0.2); border: 1px solid #F59E0B; border-radius: 14px; padding: 5px 14px; font-size: 10px; font-weight: bold; color: #F59E0B;")
            elif tel.distraction_state == "MIRROR CHECK":
                self.shield_status_lbl.setText("● SAFE GLANCE: CHECKING MIRROR")
                self.shield_status_lbl.setStyleSheet("background: rgba(0, 242, 254, 0.15); border: 1px solid #00F2FE; border-radius: 14px; padding: 5px 14px; font-size: 10px; font-weight: bold; color: #00F2FE;")
            else:
                self.shield_status_lbl.setText("● SHIELD: ACTIVE & WATCHING")
                self.shield_status_lbl.setStyleSheet("background: rgba(16, 185, 129, 0.15); border: 1px solid #10B981; border-radius: 14px; padding: 5px 14px; font-size: 10px; font-weight: bold; color: #34D399;")

            # 6. Bottom Strip Summary
            sec = int(tel.session_elapsed_sec)
            h_str = f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"
            self.lbl_drive_time.setText(f"DRIVE TIME: {h_str}")
            self.lbl_blinks.setText(f"BLINKS: {tel.total_blinks} ({tel.blinks_per_min:.1f}/min)")
            self.lbl_microsleeps.setText(f"DROWSY EVENTS: {tel.microsleep_events}")
            self.lbl_distractions.setText(f"DISTRACTIONS: {tel.distraction_events}")

            self.vital_waveform.add_sample(tel.fatigue_score)

            # Trip Safety Summary
            alertness_val = int(np.clip((1.0 - tel.fatigue_score) * 100, 0, 100))
            self.trip_summary_lbl.setText(
                f"• Active Journey Duration: {h_str}\n\n"
                f"• Natural Blink Rate: {tel.blinks_per_min:.1f} Blinks / Minute\n\n"
                f"• Micro-Sleep Incidents: {tel.microsleep_events}\n\n"
                f"• Prolonged Distractions (>1.8s): {tel.distraction_events}\n\n"
                f"• Driver Alertness Index: {alertness_val}% ({self.vigilance_core.status_title})\n\n"
                f"• Current Road Focus: {tel.distraction_state}"
            )
        finally:
            self.worker.gui_busy = False

    @Slot(str)
    def on_worker_error(self, err_msg: str):
        self.shield_status_lbl.setText(f"CAMERA WARNING: {err_msg}")
        self.shield_status_lbl.setStyleSheet("background: #FF1E56; color: white; border-radius: 14px; padding: 5px 14px; font-size: 10px; font-weight: bold;")


def main():
    app = QApplication(sys.argv)
    window = SentinelMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
