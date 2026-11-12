"""
ADORNO - Adornos sazonais para datas comemorativas no pet.

Camada `body`: desenha adornos e acessórios de época diretamente sobre a carcaça.
"""

import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF


def desenhar_adorno_sazonal(p: QPainter, evento: str, aparencia):
    """
    Desenha o adorno temático proceduralmente no topo da carcaça do pet.
    Origem do painter está no topo da cabeça do pet (y = -45).
    """
    if not evento:
        return

    p.save()
    p.setRenderHint(QPainter.Antialiasing)

    if evento == "sao_joao":
        # Chapéu de palha trançado caipira com fita vermelha
        y_chapeu = -45.0
        # Aba do chapéu
        p.setPen(QPen(QColor("#8d6e3f"), 1.5))
        p.setBrush(QColor("#d4b16a"))
        p.drawRoundedRect(QRectF(-36, y_chapeu - 7, 72, 8), 4, 4)

        # Fiapos de palha na beirada
        p.setPen(QPen(QColor("#b5934e"), 1.2))
        for fx in range(-32, 34, 6):
            p.drawLine(QPointF(fx, y_chapeu - 2), QPointF(fx + random.choice([-2, 2]), y_chapeu + 2))

        # Copa do chapéu
        p.setPen(QPen(QColor("#8d6e3f"), 1.5))
        p.setBrush(QColor("#e8c983"))
        copa = QPainterPath()
        copa.moveTo(-20, y_chapeu - 6)
        copa.lineTo(-16, y_chapeu - 26)
        copa.quadTo(0, y_chapeu - 30, 16, y_chapeu - 26)
        copa.lineTo(20, y_chapeu - 6)
        copa.closeSubpath()
        p.drawPath(copa)

        # Fita vermelha na copa
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#d32f2f"))
        p.drawRoundedRect(QRectF(-19, y_chapeu - 12, 38, 5.5), 2, 2)

    elif evento == "natal":
        # Gorro de Papai Noel vermelho curvado com pompom branco
        y_gorro = -45.0
        gorro = QPainterPath()
        gorro.moveTo(-26, y_gorro - 5)
        gorro.quadTo(-10, y_gorro - 35, 20, y_gorro - 30)
        gorro.quadTo(35, y_gorro - 22, 30, y_gorro - 10)
        gorro.lineTo(-26, y_gorro - 5)
        gorro.closeSubpath()

        p.setPen(QPen(QColor("#8b0000"), 1.5))
        p.setBrush(QColor("#d32f2f"))
        p.drawPath(gorro)

        # Borda felpuda branca do gorro
        p.setPen(QPen(QColor("#d0d0d0"), 1.0))
        p.setBrush(QColor("#ffffff"))
        p.drawRoundedRect(QRectF(-30, y_gorro - 7, 56, 8), 4, 4)

        # Pompom branco na ponta
        p.drawEllipse(QPointF(32, y_gorro - 10), 6.5, 6.5)

    elif evento == "ano_novo":
        # Mini cartola preta elegante com fita dourada
        y_cartola = -45.0
        # Aba
        p.setPen(QPen(QColor("#111111"), 1.2))
        p.setBrush(QColor("#212121"))
        p.drawRoundedRect(QRectF(-28, y_cartola - 6, 56, 6), 3, 3)

        # Copa da cartola
        p.drawRoundedRect(QRectF(-18, y_cartola - 26, 36, 21), 2, 2)

        # Fita dourada de réveillon
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffd700"))
        p.drawRect(QRectF(-18, y_cartola - 11, 36, 4))

        # Estrelinha dourada no topo
        p.setFont(QFont("Segoe UI Emoji", 9))
        p.setPen(QColor("#ffd700"))
        p.drawText(QRectF(-10, y_cartola - 38, 20, 14), Qt.AlignCenter, "✨")

    elif evento == "pascoa":
        # Orelhinhas compridas de coelhinho
        y_orelhas = -45.0
        for side in (-1, 1):
            ox = side * 16.0
            # Parte externa branca da orelha
            p.setPen(QPen(QColor("#d0d0d0"), 1.5))
            p.setBrush(QColor("#ffffff"))
            p.drawEllipse(QRectF(ox - 6, y_orelhas - 28, 12, 26))

            # Interior cor de rosa
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#ff80ab"))
            p.drawEllipse(QRectF(ox - 3.5, y_orelhas - 23, 7, 18))

    elif evento == "carnaval":
        # Máscara carnavalesca veneziana com brilho
        p.setPen(QPen(QColor("#ffd700"), 1.5))
        p.setBrush(QColor("#7c4dff"))
        mascara = QPainterPath()
        mascara.addRoundedRect(QRectF(-32, -18, 64, 18), 8, 8)
        p.drawPath(mascara)
        # Recorte dos olhos da máscara
        p.setPen(QPen(QColor("#ffd700"), 1.2))
        p.setBrush(QColor("#101512"))
        for side in (-1, 1):
            p.drawEllipse(QRectF(side * 16 - 7, -14, 14, 10))

    elif evento == "halloween":
        # Mini chapéu de bruxinha cônico
        y_bruxa = -45.0
        # Aba
        p.setPen(QPen(QColor("#1b122c"), 1.2))
        p.setBrush(QColor("#311b92"))
        p.drawRoundedRect(QRectF(-30, y_bruxa - 6, 60, 6), 3, 3)
        # Cone
        cone = QPolygonF([QPointF(-18, y_bruxa - 6), QPointF(18, y_bruxa - 6), QPointF(4, y_bruxa - 32)])
        p.drawPolygon(cone)
        # Fita laranja de halloween
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ff6d00"))
        p.drawRect(QRectF(-16, y_bruxa - 11, 32, 4))

    elif evento == "programador":
        # Óculos Matrix estilo hacker com reflexo verde
        p.setPen(QPen(QColor("#00e676"), 1.5))
        p.setBrush(QColor(0, 230, 118, 45))
        for side in (-1, 1):
            p.drawRoundedRect(QRectF(side * 24 - 15, -16, 30, 16), 3, 3)
        p.drawLine(QPointF(-9, -8), QPointF(9, -8))

    p.restore()

