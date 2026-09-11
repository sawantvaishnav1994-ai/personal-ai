from __future__ import annotations

import math
import random

from PyQt6.QtCore import QPointF, QTimer, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt6.QtWidgets import QWidget


class PulseWidget(QWidget):
    """Cinematic, asymmetric living neural field for Personal AI Home.

    The visual is drawn entirely in code. It deliberately avoids a metallic
    HUD/orb look: the identity is a fluid field of luminous neural filaments,
    particles and state-dependent motion.
    """

    STATE_ALIASES = {
        "memory_retrieval": "memory",
        "retrieving_memory": "memory",
        "knowledge_retrieval": "knowledge",
        "retrieving_knowledge": "knowledge",
        "tool": "acting",
        "action": "acting",
        "responding": "speaking",
        "response": "speaking",
        "needs_approval": "approval",
        "waiting_approval": "approval",
        "ready": "active",
    }
    STATE_SPEEDS = {
        "idle": 0.012,
        "active": 0.020,
        "listening": 0.045,
        "understanding": 0.037,
        "thinking": 0.060,
        "memory": 0.040,
        "knowledge": 0.047,
        "acting": 0.070,
        "speaking": 0.052,
        "approval": 0.010,
        "error": 0.026,
        "background": 0.006,
    }
    STATE_ENERGY = {
        "idle": 0.56,
        "active": 0.70,
        "listening": 0.94,
        "understanding": 0.84,
        "thinking": 1.00,
        "memory": 0.92,
        "knowledge": 0.88,
        "acting": 0.98,
        "speaking": 0.94,
        "approval": 0.44,
        "error": 0.62,
        "background": 0.26,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.t = 0.0
        self.state = "idle"
        self.reduce_motion = False
        self._rng = random.Random(240917)
        self._stars = [
            (self._rng.random(), self._rng.random(), self._rng.uniform(0.35, 1.0), self._rng.random() * math.tau)
            for _ in range(170)
        ]
        self._filaments = []
        for i in range(52):
            side = -1 if i % 2 == 0 else 1
            y = self._rng.uniform(-0.34, 0.34)
            spread = self._rng.uniform(0.72, 1.25)
            phase = self._rng.random() * math.tau
            width = self._rng.uniform(0.55, 1.65)
            self._filaments.append((side, y, spread, phase, width))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
        self.setMinimumHeight(330)
        self.setAccessibleName("Personal AI living neural field")

    @classmethod
    def normalize_state(cls, state: str) -> str:
        key = str(state or "idle").strip().lower().replace("-", "_").replace(" ", "_")
        return cls.STATE_ALIASES.get(key, key if key in cls.STATE_SPEEDS else "idle")

    def set_state(self, state):
        self.state = self.normalize_state(state)
        self.update()

    def set_memory_labels(self, _labels):
        self.update()

    def set_reduce_motion(self, value: bool):
        self.reduce_motion = bool(value)
        self.timer.setInterval(90 if self.reduce_motion else 16)

    def tick(self):
        speed = self.STATE_SPEEDS[self.state]
        self.t += speed * (0.20 if self.reduce_motion else 1.0)
        self.update()

    def _palette(self):
        if self.state == "error":
            return QColor(255, 118, 128), QColor(176, 74, 255), QColor(90, 154, 255)
        if self.state == "approval":
            return QColor(242, 214, 148), QColor(157, 122, 255), QColor(78, 149, 255)
        if self.state == "memory":
            return QColor(104, 240, 224), QColor(137, 113, 255), QColor(70, 169, 255)
        if self.state == "knowledge":
            return QColor(137, 204, 255), QColor(126, 100, 255), QColor(64, 159, 255)
        return QColor(226, 239, 255), QColor(136, 105, 255), QColor(61, 165, 255)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = float(self.width()), float(self.height())
        if w <= 2 or h <= 2:
            return

        painter.fillRect(self.rect(), QColor(1, 4, 9))
        self._draw_ambient(painter, w, h)
        self._draw_stars(painter, w, h)
        self._draw_neural_field(painter, w, h)
        self._draw_core(painter, w, h)
        self._draw_state_signal(painter, w, h)

    def _draw_ambient(self, painter, w, h):
        glow = QRadialGradient(QPointF(w * 0.52, h * 0.46), max(w, h) * 0.58)
        glow.setColorAt(0.0, QColor(26, 63, 126, 58))
        glow.setColorAt(0.32, QColor(35, 24, 91, 34))
        glow.setColorAt(1.0, QColor(1, 3, 8, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawRect(self.rect())

    def _draw_stars(self, painter, w, h):
        energy = self.STATE_ENERGY[self.state]
        painter.setPen(Qt.PenStyle.NoPen)
        for x, y, strength, phase in self._stars:
            pulse = 0.52 + 0.48 * math.sin(self.t * 0.75 + phase)
            alpha = int((16 + 82 * strength * pulse) * energy)
            r = 0.55 + strength * 1.15
            painter.setBrush(QColor(131, 192, 255, max(8, alpha)))
            painter.drawEllipse(QPointF(x * w, y * h), r, r)

    def _curve(self, p0, c1, c2, p3):
        path = QPainterPath(p0)
        path.cubicTo(c1, c2, p3)
        return path

    def _draw_neural_field(self, painter, w, h):
        white, violet, blue = self._palette()
        energy = self.STATE_ENERGY[self.state]
        cx, cy = w * 0.52, h * 0.47
        scale = min(w, h)

        for i, (side, y0, spread, phase, width) in enumerate(self._filaments):
            wobble = math.sin(self.t * (0.55 + (i % 7) * 0.035) + phase)
            ywave = math.cos(self.t * 0.48 + phase * 1.3)
            end_x = cx + side * w * (0.34 + 0.17 * spread)
            end_y = cy + y0 * h + ywave * 13.0
            start = QPointF(cx + math.sin(phase) * scale * 0.045, cy + math.cos(phase * 1.17) * scale * 0.050)
            c1 = QPointF(cx + side * w * (0.08 + 0.035 * spread), cy + y0 * h * 0.35 + wobble * 30)
            c2 = QPointF(cx + side * w * (0.23 + 0.07 * spread), cy + y0 * h * 0.82 - wobble * 38)
            end = QPointF(end_x, end_y)
            path = self._curve(start, c1, c2, end)

            mix = i % 3
            base = (blue, violet, white)[mix]
            alpha = int((46 + (i % 6) * 9) * energy)
            pen = QPen(QColor(base.red(), base.green(), base.blue(), min(190, alpha)))
            pen.setWidthF(width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

            if i % 4 == 0:
                halo = QPen(QColor(base.red(), base.green(), base.blue(), int(18 * energy)))
                halo.setWidthF(width + 5.5)
                painter.setPen(halo)
                painter.drawPath(path)

            if i % 3 == 0:
                q = (self.t * 0.11 + i * 0.071) % 1.0
                point = path.pointAtPercent(q)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(205, 231, 255, int(170 * energy)))
                painter.drawEllipse(point, 1.5 + energy, 1.5 + energy)

        for i in range(20):
            a = i / 19.0
            x1 = cx - w * (0.26 - a * 0.18)
            y1 = cy + math.sin(i * 1.43 + self.t * 0.7) * h * 0.19
            x2 = cx + w * (0.25 - a * 0.16)
            y2 = cy + math.cos(i * 1.17 + self.t * 0.6) * h * 0.17
            path = QPainterPath(QPointF(x1, y1))
            path.cubicTo(QPointF(cx - 40, y1), QPointF(cx + 40, y2), QPointF(x2, y2))
            painter.setPen(QPen(QColor(125, 176, 255, int(22 + 32 * energy)), 0.65))
            painter.drawPath(path)

    def _draw_core(self, painter, w, h):
        white, violet, blue = self._palette()
        energy = self.STATE_ENERGY[self.state]
        cx = w * 0.52 + math.sin(self.t * 0.37) * 8
        cy = h * 0.47 + math.cos(self.t * 0.41) * 5
        radius = min(w, h) * (0.12 + 0.008 * math.sin(self.t * 1.6))
        gradient = QRadialGradient(QPointF(cx, cy), radius * 2.6)
        gradient.setColorAt(0.0, QColor(white.red(), white.green(), white.blue(), int(105 * energy)))
        gradient.setColorAt(0.18, QColor(blue.red(), blue.green(), blue.blue(), int(80 * energy)))
        gradient.setColorAt(0.42, QColor(violet.red(), violet.green(), violet.blue(), int(42 * energy)))
        gradient.setColorAt(1.0, QColor(4, 8, 18, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(QPointF(cx, cy), radius * 2.5, radius * 2.5)

        for i in range(7):
            angle = i * 0.92 + self.t * 0.32
            ox = math.cos(angle) * radius * (0.28 + (i % 2) * 0.11)
            oy = math.sin(angle * 1.21) * radius * (0.22 + (i % 3) * 0.07)
            rr = radius * (0.20 + (i % 3) * 0.045)
            c = (blue, violet, white)[i % 3]
            painter.setBrush(QColor(c.red(), c.green(), c.blue(), int((34 + i * 7) * energy)))
            painter.drawEllipse(QPointF(cx + ox, cy + oy), rr * 1.35, rr)

    def _draw_state_signal(self, painter, w, h):
        if self.state not in ("listening", "speaking", "thinking", "acting"):
            return
        energy = self.STATE_ENERGY[self.state]
        y = h * 0.82
        center = w * 0.52
        span = min(w * 0.34, 430.0)
        path = QPainterPath(QPointF(center - span / 2, y))
        samples = 96
        for i in range(1, samples + 1):
            q = i / samples
            x = center - span / 2 + q * span
            envelope = math.sin(math.pi * q) ** 1.35
            amp = (7 + 15 * energy) * envelope
            yy = y + math.sin(q * 28 + self.t * 8.0) * amp * (0.55 + 0.45 * math.sin(q * 43 + self.t * 2.4))
            path.lineTo(x, yy)
        gradient = QLinearGradient(center - span / 2, y, center + span / 2, y)
        gradient.setColorAt(0.0, QColor(57, 126, 255, 30))
        gradient.setColorAt(0.5, QColor(194, 225, 255, 180))
        gradient.setColorAt(1.0, QColor(126, 88, 255, 30))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(gradient, 1.2))
        painter.drawPath(path)
