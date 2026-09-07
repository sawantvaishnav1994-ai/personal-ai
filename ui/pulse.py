from __future__ import annotations

import math
import random

from PyQt6.QtCore import QPointF, QTimer, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt6.QtWidgets import QWidget


class PulseWidget(QWidget):
    """Personal AI Home V1 living neural field.

    The core is a broken, asymmetric lattice rather than a ring. Motion is
    semantic: each state changes flow, density, direction or connectivity.
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
        "idle": 0.38,
        "active": 0.52,
        "listening": 0.74,
        "understanding": 0.66,
        "thinking": 0.92,
        "memory": 0.84,
        "knowledge": 0.80,
        "acting": 0.86,
        "speaking": 0.78,
        "approval": 0.31,
        "error": 0.47,
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

    CORE_NODES = (
        (-0.28, -0.02),
        (-0.18, -0.24),
        (0.00, -0.31),
        (0.22, -0.19),
        (0.31, 0.00),
        (0.20, 0.24),
        (-0.03, 0.29),
        (-0.27, 0.16),
        (-0.10, -0.05),
        (0.08, -0.08),
        (0.12, 0.10),
        (-0.10, 0.12),
    )
    CORE_EDGES = (
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7),
        (0, 8), (1, 8), (8, 9), (2, 9), (9, 3), (9, 10), (10, 4),
        (10, 5), (10, 11), (11, 6), (11, 7), (8, 11),
    )
    FLOW_PATHS = (
        ((-0.34, 0.02), (-0.38, -0.19), (-0.14, -0.34), (0.02, -0.29)),
        ((-0.08, -0.30), (0.12, -0.39), (0.35, -0.24), (0.31, -0.03)),
        ((0.31, 0.02), (0.34, 0.17), (0.18, 0.33), (0.02, 0.28)),
        ((-0.05, 0.30), (-0.23, 0.35), (-0.35, 0.19), (-0.27, 0.08)),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.t = 0.0
        self.state = "idle"
        self.reduce_motion = False
        self.memory_labels = ("Project", "Person", "Decision", "Conversation")
        self.seed = [random.Random(101 + i).uniform(-1.0, 1.0) for i in range(32)]
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

    def _node_position(self, cx, cy, width, height, index, amplitude=None):
        nx, ny = self.CORE_NODES[index]
        amp = self.STATE_AMPLITUDE[self.state] if amplitude is None else amplitude
        if self.reduce_motion:
            amp *= 0.42
        seed = self.seed[index]
        phase = self.t * (0.62 + (index % 4) * 0.07) + seed * 2.4
        breath = 1.0 + math.sin(self.t * 0.72 + index * 0.17) * amp * 0.33
        dx = math.sin(phase) * width * amp * 0.075
        dy = math.cos(phase * 0.83) * height * amp * 0.080
        return QPointF(
            cx + nx * width * 0.82 * breath + dx,
            cy + ny * height * 0.92 * breath + dy,
        )

    def _curve_between(self, a, b, index):
        mx = (a.x() + b.x()) * 0.5
        my = (a.y() + b.y()) * 0.5
        vx = b.x() - a.x()
        vy = b.y() - a.y()
        length = max(1.0, math.hypot(vx, vy))
        direction = -1.0 if index % 2 else 1.0
        bend = (8.0 + (index % 5) * 3.0) * direction
        control = QPointF(mx - vy / length * bend, my + vx / length * bend)
        path = QPainterPath(a)
        path.quadTo(control, b)
        return path

    def _draw_flow_paths(self, painter, cx, cy, width, height, primary):
        energy = self.STATE_ENERGY[self.state]
        amp = self.STATE_AMPLITUDE[self.state] * (0.42 if self.reduce_motion else 1.0)
        for index, template in enumerate(self.FLOW_PATHS):
            phase = self.t * (0.34 + index * 0.025) + self.seed[20 + index]
            points = []
            for point_index, (nx, ny) in enumerate(template):
                wave_x = math.sin(phase + point_index * 1.2) * width * amp * 0.10
                wave_y = math.cos(phase * 0.9 + point_index) * height * amp * 0.11
                points.append(
                    QPointF(
                        cx + nx * width * 0.82 + wave_x,
                        cy + ny * height * 0.92 + wave_y,
                    )
                )
            path = QPainterPath(points[0])
            path.cubicTo(points[1], points[2], points[3])
            alpha = int((72 - index * 7) * energy)
            pen = QPen(QColor(primary.red(), primary.green(), primary.blue(), max(12, alpha)))
            pen.setWidthF(1.10 if index < 2 else 0.90)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

    def _draw_lattice(self, painter, cx, cy, width, height, primary):
        energy = self.STATE_ENERGY[self.state]
        points = [self._node_position(cx, cy, width, height, i) for i in range(len(self.CORE_NODES))]
        self._draw_flow_paths(painter, cx, cy, width, height, primary)

        for edge_index, (source, target) in enumerate(self.CORE_EDGES):
            alpha = int((34 + (edge_index % 4) * 8) * energy)
            if self.state in ("thinking", "understanding") and edge_index % 3 == int(self.t * 1.3) % 3:
                alpha += 34
            pen = QPen(QColor(primary.red(), primary.green(), primary.blue(), min(145, max(9, alpha))))
            pen.setWidthF(0.70 + (edge_index % 3) * 0.12)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self._curve_between(points[source], points[target], edge_index))

        count = 8 if self.state == "background" else len(points)
        for index, point in enumerate(points[:count]):
            alpha = int((56 + (index % 4) * 12) * energy)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(primary.red(), primary.green(), primary.blue(), max(10, alpha)))
            radius = 1.5 + (index % 3) * 0.35
            if self.state == "thinking" and index % 4 == int(self.t * 1.7) % 4:
                radius += 1.0
            painter.drawEllipse(point, radius, radius)

    def _draw_listening(self, painter, cx, cy, width, height, primary):
        if self.state != "listening":
            return
        targets = (1, 3, 5, 7)
        origins = ((0.12, -0.48), (0.46, -0.04), (0.10, 0.48), (-0.46, 0.08))
        for i, (target_index, (ox, oy)) in enumerate(zip(targets, origins)):
            progress = (self.t * 0.38 + i * 0.17) % 1.0
            target = self._node_position(cx, cy, width, height, target_index)
            origin = QPointF(cx + ox * width, cy + oy * height)
            sx = origin.x() + (target.x() - origin.x()) * progress
            sy = origin.y() + (target.y() - origin.y()) * progress
            alpha = int(94 * (1.0 - progress * 0.45))
            painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), alpha), 0.95))
            painter.drawLine(QPointF(sx, sy), target)

    def _draw_thinking(self, painter, cx, cy, width, height, primary):
        if self.state not in ("understanding", "thinking"):
            return
        signal_count = 5 if self.state == "thinking" else 3
        for i in range(signal_count):
            edge_index = (i * 3 + int(self.t * 2.0)) % len(self.CORE_EDGES)
            source_index, target_index = self.CORE_EDGES[edge_index]
            a = self._node_position(cx, cy, width, height, source_index)
            b = self._node_position(cx, cy, width, height, target_index)
            q = (self.t * 0.22 + i * 0.19) % 1.0
            x = a.x() + (b.x() - a.x()) * q
            y = a.y() + (b.y() - a.y()) * q
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(primary.red(), primary.green(), primary.blue(), 118))
            painter.drawEllipse(QPointF(x, y), 2.0, 2.0)

    def _draw_memory(self, painter, cx, cy, width, height, primary):
        if self.state != "memory":
            return
        source_nodes = (1, 3, 5, 7)
        anchors = ((-0.40, -0.34), (0.42, -0.28), (0.40, 0.34), (-0.42, 0.32))
        font = QFont()
        font.setPointSizeF(8.5)
        painter.setFont(font)
        for index, (source_index, (ax, ay)) in enumerate(zip(source_nodes, anchors)):
            source = self._node_position(cx, cy, width, height, source_index)
            endpoint = QPointF(cx + ax * width, cy + ay * height)
            mx = (source.x() + endpoint.x()) * 0.5
            my = (source.y() + endpoint.y()) * 0.5
            path = QPainterPath(source)
            path.quadTo(QPointF(mx + (index - 1.5) * 8.0, my), endpoint)
            painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 92), 0.95))
            painter.drawPath(path)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(primary.red(), primary.green(), primary.blue(), 158))
            painter.drawEllipse(endpoint, 2.8, 2.8)
            label = self.memory_labels[index % len(self.memory_labels)]
            painter.setPen(QColor(primary.red(), primary.green(), primary.blue(), 132))
            tx = 10 if ax >= 0 else -74
            painter.drawText(int(endpoint.x() + tx), int(endpoint.y() - 7), label)

    def _draw_knowledge(self, painter, cx, cy, width, height, primary):
        if self.state != "knowledge":
            return
        for i, target_index in enumerate((1, 2, 3)):
            source = QPointF(width * (0.18 + i * 0.32), height * 0.03)
            target = self._node_position(cx, cy, width, height, target_index)
            path = QPainterPath(source)
            path.cubicTo(
                QPointF(source.x(), source.y() + height * 0.11),
                QPointF(target.x(), target.y() - height * 0.13),
                target,
            )
            painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 70), 0.9))
            painter.drawPath(path)

    def _draw_action(self, painter, cx, cy, width, height, primary):
        if self.state != "acting":
            return
        start = self._node_position(cx, cy, width, height, 4)
        end = QPointF(width * 0.91, height * 0.40)
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 116), 1.15))
        painter.drawLine(start, end)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(primary.red(), primary.green(), primary.blue(), 166))
        painter.drawEllipse(end, 3.1, 3.1)

    def _draw_speaking(self, painter, cx, cy, width, height, primary):
        if self.state != "speaking":
            return
        source_indices = (2, 3, 4, 5, 6)
        for i, source_index in enumerate(source_indices):
            source = self._node_position(cx, cy, width, height, source_index)
            angle = -1.00 + i * 0.50
            reach = 0.18 + 0.025 * math.sin(self.t * 2.4 + i)
            end = QPointF(
                source.x() + math.cos(angle) * width * reach,
                source.y() + math.sin(angle) * height * reach * 0.58,
            )
            painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 58 + i * 10), 0.9))
            painter.drawLine(source, end)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        cx, cy = width * 0.50, height * 0.50
        primary, secondary = self._palette()
        energy = self.STATE_ENERGY[self.state]

        glow = QRadialGradient(QPointF(cx, cy), min(width, height) * 0.48)
        glow.setColorAt(
            0,
            QColor(primary.red(), primary.green(), primary.blue(), int(24 * energy)),
        )
        glow.setColorAt(
            0.52,
            QColor(secondary.red(), secondary.green(), secondary.blue(), int(10 * energy)),
        )
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(
            QPointF(cx, cy),
            min(width, height) * 0.45,
            min(width, height) * 0.34,
        )

        self._draw_lattice(painter, cx, cy, width, height, primary)
        self._draw_listening(painter, cx, cy, width, height, primary)
        self._draw_thinking(painter, cx, cy, width, height, primary)
        self._draw_memory(painter, cx, cy, width, height, primary)
        self._draw_knowledge(painter, cx, cy, width, height, primary)
        self._draw_action(painter, cx, cy, width, height, primary)
        self._draw_speaking(painter, cx, cy, width, height, primary)
