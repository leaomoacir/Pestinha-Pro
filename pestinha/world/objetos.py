"""
OBJETOS - os post-its, memes e fotos que o pet traz, como janelas na tela.

Só desenho e clique. Quem decide criar, largar e remover fica em mischief.py.
Inclui botão interativo de curtir (❤️) com hover, pulso e partículas flutuantes.
"""

import math
import random
import time

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from ..body.pet import overlay_flags, set_no_activate
from ..ajustes import GRAVIDADE as GRAVITY

NOTE_SIZE = (180, 150)


class Thing(QWidget):
    """Objeto genérico na tela (post-it, meme ou foto): uma janela sem moldura que pode ser clicada, arrastada e cai."""
    clicked = Signal(object)
    liked = Signal(object)

    def __init__(self, w, h):
        """Cria a janela do objeto com o tamanho `w` x `h`, transparente e sem foco."""
        super().__init__(None, overlay_flags())
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(w, h)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Clique para fechar | Botão direito ou ❤️ para curtir")
        self.born = time.monotonic()
        self.x = self.y = 0.0     # centro
        self.vy = 0.0
        self.carried = False
        self.resting = True
        self.tilt = random.uniform(-6.0, 6.0)

        # Interatividade do like
        self.hover_heart = False
        self.liked_at = 0.0
        self.particles = []
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._step_particles)

    def showEvent(self, event):
        """Ao aparecer, o objeto não rouba o foco do programa que você está usando."""
        super().showEvent(event)
        set_no_activate(self)

    def heart_rect(self):
        """Retângulo do botão de coração no canto inferior direito."""
        return QRectF(self.width() - 36, self.height() - 36, 30, 30)

    def mouseMoveEvent(self, event):
        pos = event.position()
        in_heart = self.heart_rect().contains(pos)
        if in_heart != self.hover_heart:
            self.hover_heart = in_heart
            self.update()

    def leaveEvent(self, event):
        if self.hover_heart:
            self.hover_heart = False
            self.update()

    def trigger_like_effect(self):
        """Dispara a animação visual de pulso e partículas flutuantes de coração."""
        now = time.monotonic()
        self.liked_at = now
        hr = self.heart_rect()
        cx, cy = hr.center().x(), hr.center().y()

        # Cria partículas de coração subindo
        self.particles.clear()
        for _ in range(6):
            self.particles.append({
                "x": cx + random.uniform(-6, 6),
                "y": cy + random.uniform(-4, 4),
                "vx": random.uniform(-25, 25),
                "vy": random.uniform(-70, -120),
                "rot": random.uniform(-20, 20),
                "scale": random.uniform(0.7, 1.2),
                "born": now,
                "dur": random.uniform(0.7, 1.1),
                "text": random.choice(["❤️", "❤️", "✨", "+1"]),
            })
        if not self._anim_timer.isActive():
            self._anim_timer.start(16)
        self.update()
        self.liked.emit(self)

    def _step_particles(self):
        """Atualiza a física das partículas até sumirem."""
        now = time.monotonic()
        dt = 0.016
        vivas = []
        for p in self.particles:
            elapsed = now - p["born"]
            if elapsed < p["dur"]:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vy"] += 15.0 * dt  # desaceleração suave
                vivas.append(p)
        self.particles = vivas
        if not vivas and now - self.liked_at > 0.4:
            self._anim_timer.stop()
        self.update()

    def place(self, x, y, bounds=None):
        """Põe o objeto com o centro lógico em (x, y), garantindo que a janela fique contida na tela."""
        self.x, self.y = x, y
        w, h = self.width(), self.height()
        vx, vy = int(x - w / 2), int(y - h / 2)
        if bounds is not None:
            left, top, right, bottom = bounds
            vx = max(int(left), min(int(right - w), vx))
            vy = max(int(top), min(int(bottom - h), vy))
        else:
            app = QGuiApplication.instance()
            if app:
                pt = QPoint(int(x), int(y))
                screen = QGuiApplication.screenAt(pt) or QGuiApplication.primaryScreen()
                if screen:
                    g = screen.availableGeometry()
                    vx = max(g.left(), min(g.left() + g.width() - w, vx))
                    vy = max(g.top(), min(g.top() + g.height() - h, vy))
        self.move(vx, vy)

    def mousePressEvent(self, event):
        """Clique no objeto: botão direito ou botão de coração curte com efeito; botão esquerdo fora fecha."""
        if event.button() == Qt.RightButton:
            self.trigger_like_effect()
        elif event.button() == Qt.LeftButton:
            pos = event.position()
            if self.heart_rect().contains(pos):
                self.trigger_like_effect()
            else:
                self.clicked.emit(self)

    def fall(self, dt, floor):
        """Física simples: o objeto cai até `floor` (o chão do pet), se não estiver sendo carregado."""
        if self.carried or self.resting:
            return
        self.vy += GRAVITY * dt
        y = self.y + self.vy * dt
        if y + self.height() / 2 >= floor:
            y = floor - self.height() / 2
            self.vy = -self.vy * 0.25 if self.vy > 300 else 0.0
            self.resting = self.vy == 0.0
        self.place(self.x, y)

    def draw_heart_button(self, p: QPainter):
        """Desenha o botão de coração com hover e pulso elástico ao ser clicado."""
        hr = self.heart_rect()
        cx, cy = hr.center().x(), hr.center().y()
        now = time.monotonic()

        # Pulso elástico quando clicado
        liked_dt = now - self.liked_at
        if liked_dt < 0.35:
            pulse = 1.0 + 0.35 * math.sin(liked_dt / 0.35 * math.pi)
        elif self.hover_heart:
            pulse = 1.15
        else:
            pulse = 1.0

        p.save()
        p.translate(cx, cy)
        p.scale(pulse, pulse)

        # Fundo arredondado do botão (pill/círculo)
        cor_fundo = QColor(255, 64, 129, 210) if self.hover_heart else QColor(30, 30, 30, 160)
        p.setPen(QPen(QColor(255, 255, 255, 180), 1.2))
        p.setBrush(cor_fundo)
        p.drawEllipse(QRectF(-13, -13, 26, 26))

        # Ícone do coração
        p.setFont(QFont("Segoe UI Emoji", 10 if not self.hover_heart else 11))
        p.setPen(QColor("#ffffff"))
        p.drawText(QRectF(-12, -12, 24, 24), Qt.AlignCenter, "❤️")
        p.restore()

        # Desenha as partículas flutuantes
        self._draw_particles(p)

    def _draw_particles(self, p: QPainter):
        """Desenha as partículas subindo com fade out."""
        if not self.particles:
            return
        now = time.monotonic()
        p.save()
        for part in self.particles:
            prog = (now - part["born"]) / part["dur"]
            if prog >= 1.0:
                continue
            alpha = int(255 * (1.0 - prog))
            scale = part["scale"] * (1.0 + prog * 0.4)

            p.save()
            p.translate(part["x"], part["y"])
            p.scale(scale, scale)
            p.rotate(part["rot"] + prog * 15.0)

            if part["text"] == "+1":
                p.setFont(QFont("Segoe UI", 9, QFont.Bold))
                p.setPen(QColor(255, 64, 129, alpha))
                p.drawText(QRectF(-15, -10, 30, 20), Qt.AlignCenter, "+1")
            else:
                p.setFont(QFont("Segoe UI Emoji", 9))
                p.drawText(QRectF(-10, -10, 20, 20), Qt.AlignCenter, part["text"])
            p.restore()
        p.restore()


class ImageThing(Thing):
    """Objeto com uma imagem (meme ou foto), reduzida para caber no tamanho máximo."""
    def __init__(self, path, max_side):
        """Carrega a imagem; se o arquivo estiver corrompido, `valida` fica falso e ele não aparece."""
        pix = QPixmap(str(path))
        self.valida = not pix.isNull()
        if pix.isNull():
            pix = QPixmap(10, 10)
            pix.fill(Qt.transparent)
        self.pix = pix.scaled(max_side, max_side, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pad = 20
        super().__init__(self.pix.width() + pad, self.pix.height() + pad)

    def paintEvent(self, _event):
        """Desenha a imagem suavizada e o botão de curtir no canto."""
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setRenderHint(QPainter.Antialiasing)
        p.save()
        p.translate(self.width() / 2, self.height() / 2)
        p.rotate(self.tilt * 0.5)

        # Sombra suave da imagem
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 45))
        p.drawRoundedRect(QRectF(-self.pix.width() / 2 + 2, -self.pix.height() / 2 + 3,
                                 self.pix.width(), self.pix.height()), 6, 6)

        p.drawPixmap(-self.pix.width() // 2, -self.pix.height() // 2, self.pix)
        p.restore()

        # Botão interativo de curtir no canto inferior direito
        self.draw_heart_button(p)
        p.end()


class NoteThing(Thing):
    """Post-it com uma frase, num papel amarelo."""
    def __init__(self, text, small=False):
        """Monta o post-it com o texto; `small` é o tamanho de canto (bilhete de revolta)."""
        w, h = NOTE_SIZE
        if small:
            w, h = int(w * 0.75), int(h * 0.75)
        super().__init__(w + 24, h + 24)
        self.text = text
        self.small = small
        self.note_w, self.note_h = w, h

    def paintEvent(self, _event):
        """Desenha o papel, texto e o botão de curtir interativo."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.save()
        p.translate(self.width() / 2, self.height() / 2)
        p.rotate(self.tilt)
        rect = QRectF(-self.note_w / 2, -self.note_h / 2, self.note_w, self.note_h)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 50))
        p.drawRect(rect.translated(3, 4))
        p.setBrush(QColor("#ffe97a"))
        p.drawRect(rect)
        p.setBrush(QColor("#f5d84f"))
        p.drawRect(QRectF(rect.left(), rect.top(), rect.width(), 14))
        p.setPen(QColor("#3a3320"))
        p.setFont(QFont("Segoe Print", 9 if self.small else 11))
        p.drawText(rect.adjusted(10, 18, -10, -8), Qt.AlignCenter | Qt.TextWordWrap, self.text)
        p.restore()

        # Botão de curtir com hover e partículas
        self.draw_heart_button(p)
        p.end()


class PetiscoThing(Thing):
    """Um petisco (cookie/biscoitinho 🍪) que você solta na tela para recompensar o pet."""
    def __init__(self):
        super().__init__(40, 40)
        self.setToolTip("Petisco gostoso para o seu pet! Clique para tirar")
        self.resting = False
        self.born = time.monotonic()
        # Partículas de brilho dourado ao aparecer
        self.trigger_like_effect()

        # Consumo automático após alguns segundos para não acumular na tela
        self.eat_timer = QTimer(self)
        self.eat_timer.setSingleShot(True)
        self.eat_timer.timeout.connect(self._auto_consumir)
        self.eat_timer.start(4500)

    def _auto_consumir(self):
        self.clicked.emit(self)

    def paintEvent(self, _event):
        """Desenha um biscoito apetitoso dourado com gotas de chocolate e brilho."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)

        # Sombra de oclusão
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 45))
        p.drawEllipse(QRectF(-15, -13, 30, 28))

        # Biscoito dourado crocante
        p.setPen(QPen(QColor("#a87328"), 1.2))
        p.setBrush(QColor("#d49b4b"))
        p.drawEllipse(QRectF(-16, -16, 32, 32))

        # Gotas de chocolate ricas em relevo
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#3d1f0d"))
        for cx, cy, r in [(-6, -6, 3.2), (4, -8, 2.8), (5, 4, 3.2), (-4, 5, 2.8), (0, -1, 2.2)]:
            p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Mordidinha no canto
        p.setPen(Qt.NoPen)
        p.setBrush(Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_Clear)
        p.drawEllipse(QRectF(8, -18, 10, 10))
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # Desenha partículas flutuantes se houver
        if self.particles:
            p.setFont(QFont("Segoe UI Emoji", 8))
            for part in self.particles:
                cor = QColor("#ffb300")
                p.setPen(cor)
                p.drawText(QRectF(part["x"] - 20 - 8, part["y"] - 20 - 8, 16, 16), Qt.AlignCenter, "✨")

        p.end()
