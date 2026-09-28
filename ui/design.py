"""Reference-inspired vector controls; the gauges display real adapter counters."""
from qt_compat.QtCore import Qt, QRectF, QPointF, QSize, Signal
from qt_compat.QtGui import QColor, QIcon, QPixmap, QPainter, QPen, QPainterPath, QFont, QLinearGradient
from qt_compat.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QFrame, QGraphicsDropShadowEffect, QApplication, QSizePolicy
from ui.widgets import label


def draw_symbol(p, name, color="#ddd1f2", width=1.1):
    p.setPen(QPen(QColor(color), width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    def line(a, b, c, d):
        p.drawLine(QPointF(a, b), QPointF(c, d))
    def path(points):
        shape = QPainterPath(QPointF(*points[0]))
        for point in points[1:]:
            shape.lineTo(*point)
        p.drawPath(shape)
    if name == "home":
        path([(3,11),(12,3),(21,11)])
        path([(5,10),(5,21),(10,21),(10,15),(14,15),(14,21),(19,21),(19,10)])
    elif name in ("apps", "add"):
        for x,y in [(4,4),(14,4),(4,14)]:
            p.drawRoundedRect(QRectF(x,y,6,6),1.2,1.2)
        if name == "add":
            line(14,17,20,17)
            line(17,14,17,20)
        else:
            p.drawRoundedRect(QRectF(14,14,6,6),1.2,1.2)
    elif name == "profiles":
        path([(3,8),(3,5),(10,5),(12,8),(21,8),(21,20),(3,20),(3,8),(21,8)])
        line(8,12,16,12)
        line(8,16,13,16)
    elif name == "network":
        p.drawRoundedRect(QRectF(8,2,8,6),1,1)
        line(12,8,12,13)
        path([(5,16),(5,13),(19,13),(19,16)])
        for x in (2,9,16):
            p.drawRoundedRect(QRectF(x,16,6,5),1,1)
    elif name == "wifi":
        for r in (10,6.5,3):
            p.drawArc(QRectF(12-r,16-r,r*2,r*2),40*16,100*16)
        p.drawEllipse(QPointF(12,19),0.8,0.8)
    elif name == "traffic":
        path([(3,5),(3,19),(22,19)])
        path([(5,14),(9,10),(12,13),(17,5),(21,8)])
    elif name == "shield":
        shape = QPainterPath(QPointF(12,2))
        shape.cubicTo(15,5,19,5,21,6)
        shape.cubicTo(21,14,17,19,12,22)
        shape.cubicTo(7,19,3,14,3,6)
        shape.cubicTo(5,5,9,5,12,2)
        p.drawPath(shape)
        path([(8,12),(11,15),(16,9)])
    elif name == "settings":
        p.drawEllipse(QPointF(12,12),6,6)
        p.drawEllipse(QPointF(12,12),2.3,2.3)
        for angle in range(0,360,45):
            p.save()
            p.translate(12,12)
            p.rotate(angle)
            line(0,8,0,10)
            p.restore()
    elif name == "refresh":
        p.drawArc(QRectF(4,4,16,16),30*16,285*16)
        path([(20,3),(20,9),(14,9)])
    elif name in ("download","upload"):
        if name == "upload":
            p.translate(24,24)
            p.rotate(180)
        line(12,3,12,17)
        path([(7,12),(12,17),(17,12)])
        path([(4,18),(4,21),(20,21),(20,18)])
    elif name == "pause":
        p.drawRoundedRect(QRectF(6,4,4,16),1,1)
        p.drawRoundedRect(QRectF(15,4,4,16),1,1)
    elif name == "route":
        p.drawEllipse(QPointF(5,5),3,3)
        p.drawEllipse(QPointF(19,19),3,3)
        path([(5,8),(5,14),(19,10),(19,16)])
    elif name == "user":
        p.drawEllipse(QPointF(12,7),3.5,3.5)
        p.drawRoundedRect(QRectF(5,13,14,8),4,4)
    else:
        p.drawEllipse(QPointF(12,12),9,9)
        line(12,10,12,17)
        p.drawPoint(QPointF(12,6))


def line_icon(name, color="#ede3fa", size=32):
    pixmap = QPixmap(size*2,size*2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.scale(size*2/24,size*2/24)
    draw_symbol(painter,name,color)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


class NavigationBar(QWidget):
    currentRowChanged = Signal(int)

    def __init__(self):
        super().__init__()
        self.index = -1
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(6)
        self.buttons = []
        for index,(text,icon) in enumerate([("Overview","home"),("Apps","apps"),("Profiles","profiles"),
                                           ("Networks","network"),("Traffic","traffic"),("Diagnostics","shield"),
                                           ("Settings","settings"),("About","info")]):
            item = QPushButton(line_icon(icon,size=24),"")
            item.setObjectName("navButton")
            item.setCheckable(True)
            item.setIconSize(QSize(24,24))
            item.setFixedSize(54,48)
            item.setToolTip(text)
            item.setAccessibleName(text)
            item.clicked.connect(lambda checked=False,i=index:self.setCurrentRow(i))
            layout.addWidget(item)
            self.buttons.append(item)

    def setCurrentRow(self,index):
        if not 0 <= index < len(self.buttons):
            return
        for i,item in enumerate(self.buttons):
            item.setChecked(i == index)
        if self.index != index:
            self.index = index
            self.currentRowChanged.emit(index)

    def currentRow(self):
        return self.index


def panel():
    frame = QFrame()
    frame.setObjectName("surface")
    shadow = QGraphicsDropShadowEffect(frame)
    shadow.setBlurRadius(28)
    shadow.setOffset(0,8)
    shadow.setColor(QColor(9,14,36,65))
    frame.setGraphicsEffect(shadow)
    return frame


class ActionTile(QPushButton):
    def __init__(self,text,symbol,callback,featured=False):
        super().__init__()
        self.setObjectName("featuredTile" if featured else "actionTile")
        self.setMinimumSize(100,128)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(text)
        self.setAccessibleName(text)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8,21,8,17)
        layout.setSpacing(14)
        self.symbol,self.featured = symbol,featured
        self.icon_label = label("")
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label,1)
        text_label = label(text,"tileText")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)
        for child in (self.icon_label,text_label):
            child.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.clicked.connect(callback)
        self.recolor()

    def recolor(self):
        dark = bool(QApplication.instance().property("netdirectorDark"))
        color = "#fff1fc" if self.featured else ("#c5a5de" if dark else "#8770ac")
        self.icon_label.setPixmap(line_icon(self.symbol,color,43).pixmap(43,43))

    def changeEvent(self,event):
        super().changeEvent(event)
        if hasattr(self,"icon_label"):
            self.recolor()


class TrafficGauge(QWidget):
    """Decorative arc, not a utilization percentage."""
    def __init__(self,direction,color):
        super().__init__()
        self.direction,self.color,self.value = direction,color,None
        self.setMinimumSize(160,174)
        self.setToolTip("Measured adapter traffic in Mbps. The ring is decorative, not a utilization percentage.")

    def set_value(self,value):
        if self.value != value:
            self.value = value
            self.update()

    def paintEvent(self,event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        diameter = min(self.width()-12,self.height()-10,194)
        p.translate((self.width()-diameter)/2,(self.height()-diameter)/2)
        p.scale(diameter/200,diameter/200)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("#516080"),2))
        p.drawArc(QRectF(5,5,190,190),-42*16,304*16)
        gradient = QLinearGradient(10,190,180,10)
        gradient.setColorAt(0,QColor(self.color))
        gradient.setColorAt(1,QColor("#eddef6"))
        p.setPen(QPen(gradient,4,Qt.SolidLine,Qt.RoundCap))
        p.drawArc(QRectF(6,6,188,188),20*16,225*16)
        p.setPen(QPen(QColor("#8791aa"),1))
        p.drawEllipse(QRectF(18,18,164,164))
        p.setBrush(QColor("#faf4fb"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(25,25,150,150))
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("#c5bad2"),1))
        p.drawEllipse(QRectF(30,30,140,140))
        p.save()
        p.translate(88,47)
        draw_symbol(p,self.direction,"#4c4963",1)
        p.restore()
        p.setPen(QColor("#424055"))
        p.setFont(QFont("Segoe UI Light",29))
        text = "—" if self.value is None else (f"{self.value:.1f}" if self.value < 100 else f"{self.value:.0f}")
        p.drawText(QRectF(30,79,140,54),Qt.AlignCenter,text)
        p.setFont(QFont("Segoe UI",9))
        p.drawText(QRectF(30,132,140,22),Qt.AlignCenter,"Mbps")
        p.setBrush(QColor("#fff4fd"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(190,72),5,5)
        p.end()
