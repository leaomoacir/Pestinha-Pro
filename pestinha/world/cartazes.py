"""
CARTAZES - os cartazes e a bandeira que o pet levanta. Só desenho e animação procedural.

Gera variações visuais dinâmicas 100% em Python via QPainter:
- Padrões de textura: grade milimetrada, caderno pautado, papel kraft rústico, listras de alerta diagonal, recorte serrilhado e fita adesiva.
- Fita adesiva translúcida texturizada em X ou diagonal, pregos de fixação no cabo e carimbos temáticos de humor.
- Bandeira da revolução tremulante em tempo real com simulação física de ondas e variações de cor/emblema.
"""

import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen

from .objetos import Thing

STICK = 34  # px do cabo até o corpo dele


class SignThing(Thing):
    """Cartaz num cabo, preso em cima do pet, com variações ricas de textura procedurais em Python."""

    def __init__(self, text, style, scale=1.0):
        self.text, self.style, self.scale = text, style, scale
        w = int({"small": 116, "march": 150, "strike": 132, "end": 150, "sad": 116, "castigo": 190}[style] * scale)
        h = int({"small": 48, "march": 58, "strike": 54, "end": 54, "sad": 48, "castigo": 86}[style] * scale)
        self.board_w, self.board_h = w, h
        super().__init__(w + 16, h + STICK + 8)
        self.tilt = 0.0
        self.setToolTip("")

        # Variações procedurais baseadas no hash do texto (determinístico e infinito)
        hval = hash(text)
        self.textura = ["grade", "pautado", "kraft", "alerta", "durex", "liso"][abs(hval) % 6]
        self.carimbo = [
            "URGENTE!", "PROTESTO", "BUG DETECTED", "TOP SECRET",
            "SINDICATO", "404 NOT FOUND", "CLT JÁ!", None
        ][abs(hval >> 3) % 8]

    def paintEvent(self, _event):
        """Desenha a placa com cabo de madeira, texturas, pregos e carimbos procedurais."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx = self.width() / 2
        p.translate(cx, 4)
        p.rotate(self.tilt)

        # 1. Cabo de madeira torneada com chanfro e textura
        cabo_x = 0
        p.setPen(QPen(QColor("#4a3219"), 6, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(cabo_x, self.board_h - 6), QPointF(cabo_x, self.board_h + STICK))
        p.setPen(QPen(QColor("#7d562f"), 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(cabo_x, self.board_h - 4), QPointF(cabo_x, self.board_h + STICK - 2))

        # 2. Placa do cartaz
        board = QRectF(-self.board_w / 2, 0, self.board_w, self.board_h)

        # Sombra suave da placa
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 50))
        p.drawRoundedRect(board.translated(2, 2.5), 5, 5)

        fill, ink = {
            "strike": ("#c9302c", "#ffffff"),
            "end": ("#e8f7ea", "#1f7a36"),
            "sad": ("#d9e8ff", "#1d3a66"),
            "castigo": ("#fff4d6", "#222222")
        }.get(self.style, ("#f7f1df", "#222222"))

        if self.textura == "kraft" and self.style not in ("strike", "end"):
            fill = "#e0cca8"

        p.setPen(QPen(QColor("#3a2f1f"), 2))
        p.setBrush(QColor(fill))
        p.drawRoundedRect(board, 4, 4)

        # 3. Texturas procedurais de fundo (Python QPainter)
        if self.style not in ("strike", "end"):
            if self.textura == "grade":
                # Grade técnica milimetrada de desenvolvedor
                p.setPen(QPen(QColor(0, 0, 0, 16), 0.8))
                for gx in range(int(board.left()) + 8, int(board.right()), 10):
                    p.drawLine(gx, int(board.top()) + 3, gx, int(board.bottom()) - 3)
                for gy in range(int(board.top()) + 8, int(board.bottom()), 10):
                    p.drawLine(int(board.left()) + 3, gy, int(board.right()) - 3, gy)
            elif self.textura == "pautado":
                # Linhas pautadas azuis de caderno escolar
                p.setPen(QPen(QColor(60, 120, 200, 24), 0.8))
                for gy in range(int(board.top()) + 14, int(board.bottom()) - 4, 9):
                    p.drawLine(int(board.left()) + 5, gy, int(board.right()) - 5, gy)
                # Margem vermelha clássica de caderno
                p.setPen(QPen(QColor(220, 50, 50, 45), 1))
                p.drawLine(int(board.left()) + 14, int(board.top()) + 3, int(board.left()) + 14, int(board.bottom()) - 3)
            elif self.textura == "alerta":
                # Faixas diagonais amarelas e pretas de aviso nas beiradas
                p.save()
                p.setClipRect(board)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#fbc02d"))
                p.drawRect(QRectF(board.left(), board.top(), board.width(), 4))
                p.drawRect(QRectF(board.left(), board.bottom() - 4, board.width(), 4))
                p.setPen(QPen(QColor("#212121"), 3))
                for ax in range(int(board.left()) - 10, int(board.right()) + 10, 8):
                    p.drawLine(ax, int(board.top()), ax + 4, int(board.top()) + 4)
                    p.drawLine(ax, int(board.bottom()) - 4, ax + 4, int(board.bottom()))
                p.restore()
            elif self.textura == "kraft":
                # Textura rústica pontilhada de papel reciclado
                p.setPen(QPen(QColor(100, 70, 30, 20), 1))
                for s in range(12):
                    px = board.left() + ((s * 37) % int(board.width()))
                    py = board.top() + ((s * 19) % int(board.height()))
                    p.drawPoint(int(px), int(py))

        # 4. Fitas adesivas nos cantos superiores
        if self.textura in ("durex", "kraft") or self.style == "castigo":
            p.save()
            cor_fita = QColor(240, 235, 200, 160)
            p.setPen(QPen(QColor(200, 190, 150, 100), 1))
            p.setBrush(cor_fita)
            # Fita esquerda
            p.translate(board.left() + 4, board.top() - 2)
            p.rotate(-22)
            p.drawRect(QRectF(-8, -4, 16, 8))
            p.restore()

            # Fita direita
            p.save()
            p.translate(board.right() - 4, board.top() - 2)
            p.rotate(22)
            p.setPen(QPen(QColor(200, 190, 150, 100), 1))
            p.setBrush(cor_fita)
            p.drawRect(QRectF(-8, -4, 16, 8))
            p.restore()

        # 5. Pregos de fixação metálicos no centro do cabo
        p.setPen(QPen(QColor("#222222"), 1))
        p.setBrush(QColor("#9e9e9e"))
        p.drawEllipse(QPointF(0, 10), 2.2, 2.2)
        p.drawEllipse(QPointF(0, self.board_h - 10), 2.2, 2.2)

        # 6. Carimbo de humor translúcido em ângulo
        if self.carimbo and self.style != "strike":
            p.save()
            p.translate(board.right() - 30, board.bottom() - 14)
            p.rotate(-14)
            p.setPen(QPen(QColor(198, 40, 40, 75), 1.5))
            p.setBrush(Qt.NoBrush)
            p.setFont(QFont("Arial Black", 7))
            rc = QRectF(-30, -7, 60, 14)
            p.drawRoundedRect(rc, 2, 2)
            p.drawText(rc, Qt.AlignCenter, self.carimbo)
            p.restore()

        # 7. Texto principal
        p.setPen(QColor(ink))
        area = board.adjusted(6, 4, -6, -4)
        size = 13 if self.style == "castigo" else int((10 if self.style == "small" else 12) * self.scale)
        while size > 6 and QFontMetrics(QFont("Arial Black", size)).boundingRect(
                area.toRect(), Qt.AlignCenter | Qt.TextWordWrap, self.text).height() > area.height():
            size -= 1
        p.setFont(QFont("Arial Black", max(7, size)))
        p.drawText(area, Qt.AlignCenter | Qt.TextWordWrap, self.text)
        p.end()


class FlagThing(Thing):
    """Bandeira tremulando num mastro com animação orgânica de ondas de tecido calculada em tempo real."""

    def __init__(self, text, scale=1.0):
        self.text, self.scale = text, scale
        self.flag_w, self.flag_h = int(190 * scale), int(110 * scale)
        self.pole = int(self.flag_h + 70 * scale)
        super().__init__(self.flag_w + 30, self.pole + 10)
        self.tilt = 0.0
        self.setToolTip("")

        # Variações procedurais da bandeira
        hval = hash(text)
        cores_tema = [
            ("#e53935", "#b71c1c", "#d32f2f", "⚡"),  # Vermelho de revolução
            ("#1e293b", "#0f172a", "#334155", "💻"),  # Preto cyberpunk / dev
            ("#7c3aed", "#581c87", "#9333ea", "✊"),  # Roxo movimento
            ("#0284c7", "#0369a1", "#38bdf8", "📢"),  # Azul protesto
        ]
        self.c_top, self.c_mid, self.c_bot, self.emblema = cores_tema[abs(hval) % len(cores_tema)]

    def paintEvent(self, _event):
        """Desenha a bandeira tremulando com ondas físicas e gradiente de dobras de tecido."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        now = time.monotonic()
        x0, y0 = 10, 6

        # Mastro de madeira com ponteira dourada
        p.setPen(QPen(QColor("#6b4a2b"), max(4, int(5 * self.scale)), Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x0, y0), QPointF(x0, y0 + self.pole))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#fbc02d"))
        p.drawEllipse(QPointF(x0, y0), 4 * self.scale, 4 * self.scale)

        # Tecido com ondas senoidais realistas calculadas dinamicamente
        path = QPainterPath()
        steps = 28
        wave = 7.5 * self.scale
        top = [(x0 + self.flag_w * i / steps,
                y0 + wave * math.sin(now * 5.2 - i / steps * 6.5) * (i / steps)) for i in range(steps + 1)]
        path.moveTo(*top[0])
        for x, y in top[1:]:
            path.lineTo(x, y)
        for x, y in reversed(top):
            path.lineTo(x, y + self.flag_h)
        path.closeSubpath()

        # Gradiente dramático de tecido com iluminação senoidal
        grad = QLinearGradient(x0, y0, x0 + self.flag_w, y0 + self.flag_h)
        grad.setColorAt(0.0, QColor(self.c_top))
        grad.setColorAt(0.5, QColor(self.c_mid))
        grad.setColorAt(1.0, QColor(self.c_bot))

        p.setPen(QPen(QColor(self.c_mid).darker(130), 2))
        p.setBrush(grad)
        p.drawPath(path)

        # Símbolo do protesto em marca d'água no tecido
        p.save()
        p.setFont(QFont("Segoe UI Emoji", int(28 * self.scale)))
        p.setPen(QColor(255, 255, 255, 45))
        p.drawText(QRectF(x0 + 16, y0 + 14, self.flag_w - 32, self.flag_h - 28),
                   Qt.AlignRight | Qt.AlignVCenter, self.emblema)
        p.restore()

        # Texto da bandeira
        p.setPen(QColor("#ffffff"))
        box = QRectF(x0 + 8, y0 + 6, self.flag_w - 16, self.flag_h - 12)
        flags = Qt.AlignCenter | Qt.TextWordWrap
        size = max(8, int(13 * self.scale))
        while size > 6:
            font = QFont("Arial Black", size)
            if QFontMetrics(font).boundingRect(box.toRect(), flags, self.text).height() <= box.height():
                break
            size -= 1
        p.setFont(QFont("Arial Black", size))
        p.drawText(box, flags, self.text)
        p.end()


def criar_cartaz(info):
    """Monta o widget do cartaz (ou da bandeira) a partir do que o Protesto escolheu."""
    if info["bandeira"]:
        return FlagThing(info["texto"], info["escala"])
    return SignThing(info["texto"], info["estilo"], info["escala"])
