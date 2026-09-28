"""Generate the original vector-based app mark with Qt (no external artwork)."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qt_compat.QtCore import Qt, QPointF
from qt_compat.QtGui import QImage, QPainter, QColor, QPen, QPolygonF, QLinearGradient

root = Path(__file__).resolve().parents[1] / "assets"
root.mkdir(exist_ok=True)
image = QImage(256, 256, QImage.Format_ARGB32)
image.fill(Qt.transparent)
painter = QPainter(image)
painter.setRenderHint(QPainter.Antialiasing)
painter.setPen(Qt.NoPen)
gradient = QLinearGradient(0, 0, 256, 256)
gradient.setColorAt(0, QColor("#9882df"))
gradient.setColorAt(1, QColor("#eb4c9e"))
painter.setBrush(gradient)
painter.drawRoundedRect(8, 8, 240, 240, 56, 56)
painter.setPen(QPen(QColor("#ffffff"), 15, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
painter.drawPolyline(QPolygonF([QPointF(63, 177), QPointF(63, 79), QPointF(193, 177), QPointF(193, 79)]))
painter.setPen(Qt.NoPen)
painter.setBrush(QColor("#f4d6f0"))
for x, y in [(63, 79), (193, 177)]:
    painter.drawEllipse(QPointF(x, y), 17, 17)
painter.end()
image.save(str(root / "netdirector.png"))
image.save(str(root / "netdirector.ico"))
