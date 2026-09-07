from __future__ import annotations

import math
import random

from PyQt6.QtCore import QPointF, QTimer, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt6.QtWidgets import QWidget


class PulseWidget(QWidget):
    """Personal AI Home V1 living neural field.

    The core is intentionally incomplete, asymmetric and non-metallic. Motion is
    semantic: each state changes direction, density, amplitude or connectivity
    instead of playing a generic spinner.
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
        "active": 0.022,
        "listening": 0.046,
        "understanding": 0.038,
        "thinking": 0.061,
        "memory": 0.042,
        "knowledge": 0.048,
        "acting": 0.072,
        "speaking": 0.052,
        "approval": 0.010,
        "error": 0.026,
        "background": 0.006,
    }
    STATE_ENERGY = {
        "idle": 0.36,
        "active": 0.50,
        "listening": 0.72,
        "understanding": 0.64,
        "thinking": 0.92,
        "memory": 0.82,
        "knowledge": 0.78,
        "acting": 0.86,
        "speaking": 0.76,
        "approval": 0.30,
        "error": 0.46,
        "background": 0.18,
    }
    STATE_AMPLITUDE = {
        "idle": 0.014,
        "active": 0.019,
        "listening": 0.029,
        "understanding": 0.024,
        "thinking": 0.038,
        "memory": 0.031,
        "knowledge": 0.028,
        "acting": 0.026,
        "speaking": 0.032,
        "approval": 0.011,
        "error": 0.020,
        "background": 0.007,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.t = 0.0
        self.state = "idle"
        self.reduce_motion = False
        self.memory_labels = ("Project", "Person", "Decision", "Conversation")
        self.seed = [random.Random(101 + i).uniform(-1.0, 1.0) for i in range(24)]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
        self.setAccessibleName("Personal AI living core")

    @classmethod
    def normalize_state(cls, state: str) -> str:
        key = str(state or "idle").strip().lower().replace("-", "_").replace(" ", "_")
        return cls.STATE_ALIASES.get(key, key if key in cls.STATE_SPEEDS else "idle")

    def set_state(self, state):
        self.state = self.normalize_state(state)
        self.update()

    def set_memory_labels(self, labels):
        cleaned = [str(item).strip() for item in labels if str(item).strip()]
        if cleaned:
            self.memory_labels = tuple(cleaned[:4])
        self.update()

    def set_reduce_motion(self, value: bool):
        self.reduce_motion = bool(value)
        self.timer.setInterval(120 if self.reduce_motion else 16)
        self.update()

    def tick(self):
        speed = self.STATE_SPEEDS[self.state]
        self.t += speed * (0.18 if self.reduce_motion else 1.0)
        self.update()

    def _palette(self):
        if self.state == "error":
            return QColor(234, 158, 143), QColor(184, 102, 92)
        if self.state == "approval":
            return QColor(214, 205, 166), QColor(154, 144, 104)
        if self.state == "memory":
            return QColor(155, 220, 216), QColor(84, 154, 153)
        if self.state == "knowledge":
            return QColor(171, 206, 233), QColor(95, 136, 171)
        return QColor(164, 224, 236), QColor(83, 151, 169)

    def _point_on_field(self, cx, cy, rx, ry, theta, layer, amplitude):
        seed = self.seed[layer % len(self.seed)]
        phase = self.t * (1.0 + layer * 0.021)
        wave = math.sin(theta * 3.0 + phase + seed * 1.7)
        micro = math.sin(theta * 7.0 - phase * 0.73 + layer * 0.58)
        asym = math.sin(theta * 2.0 + layer * 0.31) * 0.040 + seed * 0.018
        rx2 = rx * (1.0 + asym + wave * amplitude * 0.55)
        ry2 = ry * (1.0 - asym * 0.55 + micro * amplitude * 0.42)
        x = cx + math.cos(theta) * rx2 + math.sin(theta * 1.7 + phase) * rx * amplitude * 0.24
        y = cy + math.sin(theta) * ry2 + math.cos(theta * 2.1 - phase) * ry * amplitude * 0.20
        return QPointF(x, y)

    def _draw_contours(self, painter, cx, cy, width, height, primary):
        energy = self.STATE_ENERGY[self.state]
        amp = self.STATE_AMPLITUDE[self.state] * (0.42 if self.reduce_motion else 1.0)
        layers = 7 if self.state in ("background", "approval") else 9
        segments = ((-2.80, -0.62), (-0.28, 1.20), (1.62, 2.72))
        base_rx = min(width * 0.285, height * 0.55)
        base_ry = min(height * 0.37, width * 0.205)

        for layer in range(layers):
            scale = 0.70 + layer * 0.048
            alpha = int((34 + (layers - layer) * 8) * energy)
            pen = QPen(QColor(primary.red(), primary.green(), primary.blue(), max(10, alpha)))
            pen.setWidthF(max(0.55, 1.48 - layer * 0.07))
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            for seg_index, (start, end) in enumerate(segments):
                path = QPainterPath()
                steps = 74
                for i in range(steps):
                    q = i / (steps - 1)
                    theta = start + (end - start) * q
                    theta += math.sin(self.t * 0.23 + layer + seg_index) * 0.014
                    point = self._point_on_field(
                        cx,
                        cy,
                        base_rx * scale * (1.0 + seg_index * 0.012),
                        base_ry * scale * (1.0 - seg_index * 0.018),
                        theta,
                        layer + seg_index * 3,
                        amp,
                    )
                    if i == 0:
                        path.moveTo(point)
                    else:
                        path.lineTo(point)
                painter.drawPath(path)

    def _draw_neural_points(self, painter, cx, cy, width, height, primary):
        energy = self.STATE_ENERGY[self.state]
        count = 10 if self.state == "background" else 17
        for n in range(count):
            angle = n * 1.31 + self.t * (0.12 + (n % 3) * 0.018)
            radial = 0.13 + (n % 7) * 0.034
            x = cx + math.cos(angle * 1.03) * width * radial
            y = cy + math.sin(angle * 0.89) * height * radial * 0.58
            alpha = int((34 + (n % 5) * 11) * energy)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(primary.red(), primary.green(), primary.blue(), max(8, alpha)))
            radius = 1.15 + (n % 3) * 0.42
            painter.drawEllipse(QPointF(x, y), radius, radius)

    def _draw_listening(self, painter, cx, cy, width, height, primary):
        if self.state != "listening":
            return
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(3):
            progress = (self.t * 0.35 + i / 3.0) % 1.0
            rx = width * (0.41 - progress * 0.15)
            ry = height * (0.36 - progress * 0.13)
            alpha = int(52 * (1.0 - progress))
            painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), alpha), 1.0))
            for start, end in ((-2.55, -1.48), (-0.18, 0.82), (1.72, 2.58)):
                path = QPainterPath()
                for step in range(34):
                    q = step / 33
                    theta = start + (end - start) * q
                    point = QPointF(cx + math.cos(theta) * rx, cy + math.sin(theta) * ry)
                    if step == 0:
                        path.moveTo(point)
                    else:
                        path.lineTo(point)
                painter.drawPath(path)

    def _draw_thinking(self, painter, cx, cy, width, height, primary):
        if self.state not in ("understanding", "thinking"):
            return
        regions = 5 if self.state == "thinking" else 3
        for i in range(regions):
            a1 = i * 1.19 + self.t * (0.21 + i * 0.012)
            a2 = a1 + 0.63 + math.sin(self.t + i) * 0.12
            r1 = width * (0.11 + i * 0.017)
            r2 = width * (0.17 + (i % 3) * 0.018)
            p1 = QPointF(cx + math.cos(a1) * r1, cy + math.sin(a1) * height * 0.09)
            p2 = QPointF(cx + math.cos(a2) * r2, cy + math.sin(a2) * height * 0.14)
            alpha = 54 + i * 9
            painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), alpha), 0.85))
            painter.drawLine(p1, p2)

    def _draw_memory(self, painter, cx, cy, width, height, primary):
        if self.state != "memory":
            return
        anchors = (
            (-0.78, 0.36, -16, -9),
            (-0.10, 0.40, 10, -7),
            (0.64, 0.35, 10, 12),
            (2.42, 0.34, -78, 14),
        )
        font = QFont()
        font.setPointSizeF(8.5)
        painter.setFont(font)
        for index, (angle, radius, tx, ty) in enumerate(anchors):
            ex = cx + math.cos(angle) * width * radius
            ey = cy + math.sin(angle) * height * radius * 0.62
            mx = cx + math.cos(angle) * width * 0.23
            my = cy + math.sin(angle) * height * 0.15
            path = QPainterPath(QPointF(cx, cy))
            bend = QPointF((cx + mx) * 0.5 + math.sin(angle) * 14, (cy + my) * 0.5)
            path.quadTo(bend, QPointF(mx, my))
            path.quadTo(QPointF((mx + ex) * 0.5, (my + ey) * 0.5), QPointF(ex, ey))
            painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 86), 0.95))
            painter.drawPath(path)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(primary.red(), primary.green(), primary.blue(), 150))
            painter.drawEllipse(QPointF(ex, ey), 2.8, 2.8)
            label = self.memory_labels[index % len(self.memory_labels)]
            painter.setPen(QColor(primary.red(), primary.green(), primary.blue(), 126))
            painter.drawText(int(ex + tx), int(ey + ty), label)

    def _draw_knowledge(self, painter, cx, cy, width, height, primary):
        if self.state != "knowledge":
            return
        starts = ((0.18, 0.08), (0.50, 0.02), (0.82, 0.11))
        for i, (nx, ny) in enumerate(starts):
            sx, sy = width * nx, height * ny
            ex = cx + (i - 1) * width * 0.08
            ey = cy - height * 0.08
            painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 62), 0.9))
            path = QPainterPath(QPointF(sx, sy))
            path.cubicTo(
                QPointF(sx, sy + height * 0.10),
                QPointF(ex, ey - height * 0.12),
                QPointF(ex, ey),
            )
            painter.drawPath(path)

    def _draw_action(self, painter, cx, cy, width, height, primary):
        if self.state != "acting":
            return
        angle = -0.18
        start = QPointF(cx + width * 0.16, cy + height * 0.015)
        end = QPointF(cx + math.cos(angle) * width * 0.41, cy + math.sin(angle) * height * 0.28)
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 108), 1.2))
        painter.drawLine(start, end)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(primary.red(), primary.green(), primary.blue(), 156))
        painter.drawEllipse(end, 3.1, 3.1)

    def _draw_speaking(self, painter, cx, cy, width, height, primary):
        if self.state != "speaking":
            return
        for i in range(5):
            angle = -1.10 + i * 0.55
            pulse = 0.22 + 0.028 * math.sin(self.t * 2.4 + i)
            start = QPointF(
                cx + math.cos(angle) * width * 0.17,
                cy + math.sin(angle) * height * 0.10,
            )
            end = QPointF(
                cx + math.cos(angle) * width * pulse,
                cy + math.sin(angle) * height * pulse * 0.62,
            )
            painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 56 + i * 9), 0.9))
            painter.drawLine(start, end)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        cx, cy = width * 0.50, height * 0.49
        primary, secondary = self._palette()
        energy = self.STATE_ENERGY[self.state]

        glow = QRadialGradient(QPointF(cx, cy), min(width, height) * 0.52)
        glow.setColorAt(
            0,
            QColor(
                primary.red(),
                primary.green(),
                primary.blue(),
                int(28 * energy),
            ),
        )
        glow.setColorAt(
            0.48,
            QColor(
                secondary.red(),
                secondary.green(),
                secondary.blue(),
                int(12 * energy),
            ),
        )
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(
            QPointF(cx, cy),
            min(width, height) * 0.50,
            min(width, height) * 0.37,
        )

        self._draw_contours(painter, cx, cy, width, height, primary)
        self._draw_neural_points(painter, cx, cy, width, height, primary)
        self._draw_listening(painter, cx, cy, width, height, primary)
        self._draw_thinking(painter, cx, cy, width, height, primary)
        self._draw_memory(painter, cx, cy, width, height, primary)
        self._draw_knowledge(painter, cx, cy, width, height, primary)
        self._draw_action(painter, cx, cy, width, height, primary)
        self._draw_speaking(painter, cx, cy, width, height, primary)
