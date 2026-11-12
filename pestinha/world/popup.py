"""
POPUP - balão de fala e pensamento flutuante sobre a cabeça do pet.

Aparece suavemente acima do pet com reações rápidas, pensamentos, agradecimento por
carinho/like ou tiradas engraçadas, acompanhando o movimento do pet pela tela.
"""

import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from ..body.pet import overlay_flags, set_no_activate


class SpeechBubble(QWidget):
    """Balão de fala expressivo com rabicho que acompanha a cabeça do pet."""

    closed = Signal()

    def __init__(self, text: str, duration: float = 3.5, kind: str = "fala"):
        super().__init__(None, overlay_flags())
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.text = text
        self.kind = kind  # "fala" (rabicho pontudo) ou "pensamento" (bolinhas)
        self.duration = duration
        self.remaining = duration
        self.elapsed = 0.0
        self._last_tick = time.monotonic()
        self.born = time.monotonic()
        self.fade_duration = 0.35
        self.hovered = False

        self.setMouseTracking(True)

        # Mede o texto para calcular a dimensão ideal do balão
        font = QFont("Segoe UI", 10, QFont.Medium)
        fm = QFontMetrics(font)
        # Largura máxima de 260px
        rect_text = fm.boundingRect(0, 0, 240, 1000, Qt.AlignCenter | Qt.TextWordWrap, text)

        self.pad_h = 16
        self.pad_v = 12
        self.bubble_w = max(90, rect_text.width() + self.pad_h * 2)
        self.bubble_h = max(42, rect_text.height() + self.pad_v * 2)
        self.tail_h = 10

        self.setFixedSize(self.bubble_w + 20, self.bubble_h + self.tail_h + 16)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Clique para fechar")

        self.pet_ref = None
        self.target_x = 0
        self.target_y = 0

        # Timer de animação suave (60 FPS durante o ciclo de vida)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._step_anim)
        self.anim_timer.start(16)

    def showEvent(self, event):
        super().showEvent(event)
        set_no_activate(self)

    def attach_to_pet(self, pet_body, screen_bounds=None):
        """Posiciona e ancora o balão sobre o pet."""
        bx = pet_body.x
        by = pet_body.y - 65 - self.bubble_h

        # Mantém dentro da tela se bounds fornecido
        if screen_bounds:
            l, t, r, b = screen_bounds
            bx = max(l + self.width() / 2 + 10, min(r - self.width() / 2 - 10, bx))
            by = max(t + 10, min(b - self.height() - 10, by))

        self.target_x = int(bx - self.width() / 2)
        self.target_y = int(by)
        self.move(self.target_x, self.target_y)

    def enterEvent(self, event):
        """Ao passar o mouse sobre o balão, pausa o timer para o usuário poder ler com calma."""
        try:
            super().enterEvent(event)
        except Exception:
            pass
        self.hovered = True
        self.remaining = max(self.remaining, 4.0)
        self.setToolTip("Lendo... (Clique para fechar)")
        self.update()

    def leaveEvent(self, event):
        """Ao tirar o mouse do balão, garante pelo menos 3.0s antes de sumir."""
        try:
            super().leaveEvent(event)
        except Exception:
            pass
        self.hovered = False
        self.remaining = max(self.remaining, 3.0)
        self.setToolTip("Clique para fechar")
        self.update()

    def update_position(self, pet_body, screen_bounds=None):
        """Atualiza a posição suavemente para manter o rabicho ancorado na cabeça do pet."""
        if self.hovered or self.underMouse():
            return

        bx = pet_body.x
        by = pet_body.y - 65 - self.bubble_h

        if screen_bounds:
            l, t, r, b = screen_bounds
            bx = max(l + self.width() / 2 + 10, min(r - self.width() / 2 - 10, bx))
            by = max(t + 10, min(b - self.height() - 10, by))

        tx = int(bx - self.width() / 2)
        ty = int(by)
        # Interpolação suave para não tremer
        nx = int(self.x() + (tx - self.x()) * 0.35)
        ny = int(self.y() + (ty - self.y()) * 0.35)
        self.move(nx, ny)

    def _step_anim(self):
        """Passo de animação de entrada, tempo de vida e saída."""
        now = time.monotonic()
        dt = min(0.1, max(0.001, now - self._last_tick))
        self._last_tick = now

        # Se o cursor estiver sobre o balão, CONGELA o tempo de vida!
        if self.underMouse() or self.hovered:
            self.hovered = True
            self.remaining = max(self.remaining, 4.0)
            self.elapsed = min(self.elapsed, max(0.0, self.duration - self.fade_duration - 0.1))
        else:
            self.hovered = False
            self.remaining -= dt
            self.elapsed += dt

        if self.remaining <= 0.0:
            self.anim_timer.stop()
            self.closed.emit()
            self.close()
            return
        self.update()

    def mousePressEvent(self, event):
        """Clique no balão fecha ele imediatamente."""
        self.anim_timer.stop()
        self.closed.emit()
        self.close()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Efeito de pop-in inicial e fade-out no final
        if self.hovered:
            scale = 1.02
            alpha = 255
        elif self.elapsed < self.fade_duration:
            prog = self.elapsed / self.fade_duration
            scale = 0.75 + 0.25 * math.sin(prog * math.pi / 2)
            alpha = int(255 * prog)
        elif self.remaining < self.fade_duration:
            prog = max(0.0, self.remaining / self.fade_duration)
            scale = 0.95 + 0.05 * prog
            alpha = int(255 * prog)
        else:
            scale = 1.0
            alpha = 255

        if alpha <= 0:
            return

        cx = self.width() / 2
        cy = (self.bubble_h) / 2 + 6

        p.save()
        p.translate(cx, cy)
        p.scale(scale, scale)

        # Retângulo do corpo do balão
        bw, bh = self.bubble_w, self.bubble_h
        rect = QRectF(-bw / 2, -bh / 2, bw, bh)

        # Monta a forma do balão com rabicho apontando para baixo
        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)

        if self.kind == "fala":
            # Rabicho triangular estilizado
            rabicho = QPainterPath()
            rabicho.moveTo(-8, bh / 2 - 1)
            rabicho.lineTo(0, bh / 2 + self.tail_h)
            rabicho.lineTo(8, bh / 2 - 1)
            rabicho.closeSubpath()
            path = path.united(rabicho)

        # Sombra suave
        sombra_cor = QColor(0, 0, 0, int((50 if self.hovered else 35) * (alpha / 255)))
        p.setPen(Qt.NoPen)
        p.setBrush(sombra_cor)
        p.drawPath(path.translated(0, 3.5))

        # Fundo do balão (estilo elegante escuro/translúcido suave com toque ciber)
        cor_fundo = QColor(32, 45, 38, int(248 * (alpha / 255))) if self.hovered else QColor(28, 36, 31, int(235 * (alpha / 255)))
        cor_borda = QColor(100, 255, 160, int(255 * (alpha / 255))) if self.hovered else QColor(62, 232, 119, int(200 * (alpha / 255)))

        p.setPen(QPen(cor_borda, 2.0 if self.hovered else 1.6))
        p.setBrush(cor_fundo)
        p.drawPath(path)

        if self.kind == "pensamento":
            # Duas bolinhas de pensamento abaixo do balão
            p.setBrush(cor_fundo)
            p.setPen(QPen(cor_borda, 1.2))
            p.drawEllipse(QPointF(0, bh / 2 + 5), 4, 4)
            p.drawEllipse(QPointF(4, bh / 2 + 11), 2.5, 2.5)

        # Botãozinho sutil de fechar quando o mouse está em cima
        if self.hovered:
            p.setPen(QColor(150, 255, 180, 160))
            p.setFont(QFont("Segoe UI", 7, QFont.Bold))
            p.drawText(QRectF(rect.right() - 16, rect.top() + 4, 12, 12), Qt.AlignCenter, "✕")

        # Texto interno
        cor_texto = QColor(255, 255, 255, alpha) if self.hovered else QColor(240, 255, 244, alpha)
        p.setPen(cor_texto)
        p.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        p.drawText(rect, Qt.AlignCenter | Qt.TextWordWrap, self.text)

        p.restore()
        p.end()

