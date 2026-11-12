"""
PET - a telinha com olhinhos: janela transparente, desenho e mouse.

A janela é um quadrado transparente maior que o corpo, para caber o corpo
girado. Pixels transparentes deixam o clique passar para o que está embaixo.
A janela nunca pega o foco (o teclado continua no seu programa).
"""

import math
import random
import time

from PySide6.QtCore import QRect, QRectF, Qt, Signal, QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QPainter
from PySide6.QtWidgets import QWidget

from ..config import EMOTION_NAMES
from ..core.emotion import EYE_SHAPES
from ..core.physics import Body
from .. import plataforma
from ..ajustes import (
    LADO_JANELA_PET as WIN,
    TEMPO_MAX_CUTUCADA_MS as POKE_MAX_MS,
    DISTANCIA_INICIO_ARRASTE as DRAG_START_PX,
    VELOCIDADE_ARREMESSO as THROW_MIN_SPEED,
    JANELA_CARINHO as RUB_WINDOW,
    TROCAS_CARINHO as RUB_REVERSALS,
    DESLOCAMENTO_CARINHO as RUB_MIN_TRAVEL,
)

from .desenho_rosto import BODY_H, BODY_W, PADRAO, draw_face, draw_zzz, lerp_shape
from .membros import draw_arms, draw_legs

CX, CY = WIN / 2, WIN / 2 - 6   # centro do corpo dentro da janela



# carinho = passar o mouse para lá e para cá em cima dele, sem clicar


def set_no_activate(widget):
    """Garante que clicar/mostrar a janela não rouba o foco do programa atual (onde o sistema permite)."""
    try:
        plataforma.sem_foco_nativo(int(widget.winId()))
    except Exception:
        pass    # sem janela nativa (ex.: teste offscreen)


def overlay_flags():
    """Janela sem moldura, sempre por cima, que não aparece na barra de tarefas nem recebe foco ao aparecer."""
    return (
        Qt.FramelessWindowHint
        | Qt.Tool
        | Qt.WindowStaysOnTopHint
        | Qt.WindowDoesNotAcceptFocus
    )


class PetWindow(QWidget):
    """Janela do pet: desenha o PetState e traduz o mouse em gestos (sinais)."""

    poked = Signal()
    drag_started = Signal()
    drag_ended = Signal()
    thrown = Signal(float)          # velocidade do arremesso (px/s)
    menu_requested = Signal(object) # botão direito: posição global do clique
    radial_requested = Signal(object) # abre roda de opções estilo GTA/CS (pos global)
    radial_move = Signal(object)      # movimento direcional da mira na roda
    radial_released = Signal(object)  # soltura para executar opção da roda

    def __init__(self, x, y, state):
        """Janela transparente do pet: o rosto é desenhado aqui e o mouse vira gestos (cutucar, arrastar, arremessar)."""
        super().__init__(None, overlay_flags())
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(WIN, WIN)

        self.body = Body(x, y, BODY_W / 2, BODY_H / 2)
        self.state = state
        self.aparencia = PADRAO      # cores e acessórios do pet (pets/<pet>.json)
        self.next_blink = time.monotonic() + random.uniform(2.0, 5.0)

        self._press = None          # (pos global, tempo)
        self._grab = (0.0, 0.0)
        self._dragging = False
        self._samples = []          # (t, x, y) para a velocidade do arremesso
        self._held_angle = 0.0
        self._rub = []              # (t, x) do mouse passando sem clicar
        self.setMouseTracking(True)

        self._right_press = None
        self._radial_active = False
        self._radial_timer = QTimer(self)
        self._radial_timer.setSingleShot(True)
        self._radial_timer.timeout.connect(self._on_radial_timeout)

    def _on_radial_timeout(self):
        """Ao segurar o botão direito, abre a roda radial de opções."""
        if self._right_press is not None:
            self._radial_active = True
            self.radial_requested.emit(self._right_press[0])

    def _track_rub(self, x):
        """Detecta carinho: o mouse passando de um lado para o outro várias vezes, sem clicar, em cima do pet."""
        now = time.monotonic()
        self._rub.append((now, x))
        self._rub = [r for r in self._rub if now - r[0] < RUB_WINDOW]
        reversals, travel, last_dir = 0, 0.0, 0
        for (_, x0), (_, x1) in zip(self._rub, self._rub[1:]):
            step = x1 - x0
            if abs(step) < 2:
                continue
            direction = 1 if step > 0 else -1
            if last_dir and direction != last_dir:
                reversals += 1
            last_dir = direction
            travel += abs(step)
        if reversals >= RUB_REVERSALS and travel >= RUB_MIN_TRAVEL:
            self.state.mark_caress(now)

    def showEvent(self, event):
        """Ao aparecer, a janela já é marcada para não roubar o foco do programa que você está usando."""
        super().showEvent(event)
        set_no_activate(self)

    # ---------------- animação ----------------

    def animate(self, now):
        """Um quadro da animação: suaviza a forma dos olhos, pisca de tempos em tempos e reposiciona a janela."""
        st = self.state
        target = dict(EYE_SHAPES.get(st.emotion, EYE_SHAPES["observando"]))
        if st.emotion != "dormindo":
            droop = st.tone.lid_droop()             # DROWSE pesa as pálpebras, em qualquer emoção
            target["inner"] = min(0.8, target["inner"] + droop)
            target["outer"] = min(0.8, target["outer"] + droop)
        st.shape = lerp_shape(st.shape, target, 0.22)
        if now >= self.next_blink:
            st.blink_until = now + 0.13
            self.next_blink = now + random.uniform(2.5, 6.0)

        if self.body.held:
            vx = self._velocity()[0]
            sway = max(-35.0, min(35.0, -vx * 0.03))
            self.body.angle += (self._held_angle + sway - self.body.angle) * 0.25

        self.move(int(self.body.x - CX), int(self.body.y - CY))
        self.update()

    def paintEvent(self, _event):
        """Desenha o pet: corpo, olhos, acessórios e balanço; some atrás da tampa do notebook quando está sentado."""
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing)
            st = self.state
            if st.desk_top is not None:
                # sentado: o corpo some atrás da tampa do notebook (corta no nível dela, não depende da ordem das janelas)
                corte = int(st.desk_top - self.y())
                p.setClipRect(QRect(0, 0, self.width(), max(0, min(self.height(), corte))))
            shake = st.shake
            jitter_x = random.uniform(-shake, shake) if shake else 0.0
            jitter_y = random.uniform(-shake, shake) if shake else 0.0

            # SETTLE: balança devagarinho, de boa; a amplitude é a atividade da população
            sway = 0.0
            if self.body.grounded and st.emotion != "dormindo":
                sway = st.tone.sway() * math.sin(time.monotonic() * 2.2)
            if st.emotion == "dormindo":
                jitter_y += 1.5 * math.sin(time.monotonic() * 1.6)     # respirando devagar

            # Caminhada e ciclo de passos orgânicos (ritmo bípede suave, sem parecer aranha)
            is_walking = self.body.grounded and abs(self.body.vx) > 8.0 and st.emotion != "dormindo"
            if is_walking:
                # Cadência suave e cadenciada de personagem cartoon
                cadencia = min(5.5, max(2.5, abs(self.body.vx) * 0.012))
                st.walk_phase += cadencia * 0.016
                bob_y = -abs(math.sin(st.walk_phase)) * 2.5
            else:
                bob_y = 0.0

            # Ritmo de música no pet (Headbanging no Rock, dança no Pop/Funk, relax no Lo-Fi)
            modo_musica = getattr(st, "modo_musica", None)
            if modo_musica and self.body.grounded and st.emotion != "dormindo":
                now_t = time.monotonic()
                if modo_musica == "headbanging":
                    bob_y += math.sin(now_t * 14.0) * 4.5
                    sway += math.sin(now_t * 14.0) * 5.0
                elif modo_musica == "dancar":
                    sway += math.sin(now_t * 8.0) * 8.0
                    bob_y += abs(math.sin(now_t * 8.0)) * 3.0
                elif modo_musica == "lofi_chill":
                    sway += math.sin(now_t * 1.5) * 2.0

            gesture = st.active_gesture()
            if st.at_desk or st.desk_top is not None:
                gesture = "typing"
            elif gesture == "idle":
                if is_walking:
                    gesture = "walk"
                elif modo_musica == "headbanging":
                    gesture = "cheer"
                elif st.emotion == "bravo":
                    gesture = "cross"
                elif st.emotion == "curioso":
                    gesture = "scratch"

            BODY_OFFSET_Y = -14.0

            p.save()
            p.translate(CX + jitter_x, CY + jitter_y + bob_y)
            p.rotate(self.body.angle + sway)

            # 1. Perninhas com ciclo de passos (ancoradas e pisando firme na barra de tarefas)
            draw_legs(p, self.aparencia, st.walk_phase, is_walking, self.body.grounded,
                      sitting=(st.desk_top is not None or st.at_desk), body_offset_y=BODY_OFFSET_Y)

            # 2. Rosto, olhos, bochechas e moldura (elevado para expor as perninhas na base)
            p.save()
            p.translate(0.0, BODY_OFFSET_Y)
            blink = 0.08 if time.monotonic() < st.blink_until else 1.0
            draw_face(p, st.shape, st.gaze, blink, st.emotion, carinho=st.feliz_fechado(),
                      aparencia=self.aparencia, blush=st.is_blushing())

            # Adorno sazonal da data comemorativa atual (São João, Natal, Páscoa, Ano Novo, etc.)
            from .adorno import desenhar_adorno_sazonal
            from ..sense.contexto import obter_evento_sazonal
            evento = getattr(st, "evento_sazonal", None) or obter_evento_sazonal()
            if evento:
                desenhar_adorno_sazonal(p, evento, self.aparencia)

            p.restore()

            # 3. Bracinhos e mãozinhas com gestos (na frente do corpo!)
            draw_arms(p, self.aparencia, gesture, st.walk_phase, is_walking, body_offset_y=BODY_OFFSET_Y)

            # Notas musicais flutuando quando ouvindo música
            if modo_musica and st.emotion != "dormindo":
                p.save()
                p.setFont(QFont("Segoe UI Emoji", 10))
                t = time.monotonic()
                notas = ["🎵", "🎸" if modo_musica == "headbanging" else "🎶", "✨"]
                for idx, nota in enumerate(notas):
                    nx = math.sin(t * 2.2 + idx * 2.1) * 26.0
                    ny = -55.0 - ((t * 22.0 + idx * 28.0) % 36.0)
                    p.setPen(QColor(self.aparencia.olho))
                    p.drawText(QRectF(nx - 12, ny - 12, 24, 24), Qt.AlignCenter, nota)
                p.restore()

            p.restore()

            if st.emotion == "dormindo":
                draw_zzz(p, CX + jitter_x, CY + jitter_y + BODY_OFFSET_Y, time.monotonic(), self.aparencia.olho)

            if st.show_label:
                p.setPen(self.aparencia.olho)
                p.setFont(QFont("Consolas", 9, QFont.Bold))
                p.drawText(QRectF(0, WIN - 22, WIN, 20), Qt.AlignCenter, EMOTION_NAMES.get(st.emotion, st.emotion))
        finally:
            if p.isActive():
                p.end()

    # ---------------- mouse ----------------

    def mousePressEvent(self, event):
        """Início de um gesto: clique esquerdo (cutucar/arrastar) ou botão direito (roda radial/menu)."""
        pos = event.globalPosition()
        if event.button() == Qt.RightButton:
            self._right_press = (pos.toPoint(), time.monotonic())
            self._radial_active = False
            # 300 ms segurando o botão direito abre a roda radial de opções estilo GTA/CS!
            self._radial_timer.start(300)
            return

        if event.button() != Qt.LeftButton:
            return
        self.state.pressing = math.hypot(pos.x() - self.body.x, pos.y() - self.body.y) < 90
        self._press = (pos, time.monotonic())
        self._grab = (pos.x() - self.body.x, pos.y() - self.body.y)
        self._samples = [(time.monotonic(), pos.x(), pos.y())]

    def mouseMoveEvent(self, event):
        """Enquanto o botão está apertado, arrasta o pet ou mira na roda radial."""
        pos = event.globalPosition()

        # Mira na roda radial segurando o botão direito
        if self._right_press is not None:
            start_pos = self._right_press[0]
            dist = math.hypot(pos.x() - start_pos.x(), pos.y() - start_pos.y())
            if dist > 12.0 and not self._radial_active:
                # Começou a mover a mira: abre a roda radial imediatamente!
                self._radial_timer.stop()
                self._radial_active = True
                self.radial_requested.emit(start_pos)
            if self._radial_active:
                self.radial_move.emit(pos.toPoint())
            return

        if self._press is None:
            self._track_rub(pos.x())
            return
        if not self.state.allow_drag:
            return
        start = self._press[0]
        if not self._dragging:
            if math.hypot(pos.x() - start.x(), pos.y() - start.y()) < DRAG_START_PX:
                return
            self._dragging = True
            self._held_angle = self.body.angle
            self.body.held = True
            self.body.grounded = False
            self.body.platform = None
            self.drag_started.emit()

        self.body.x = pos.x() - self._grab[0]
        self.body.y = pos.y() - self._grab[1]
        now = time.monotonic()
        self._samples.append((now, pos.x(), pos.y()))
        self._samples = [s for s in self._samples if now - s[0] < 0.12]

    def cancel_interaction(self):
        """Cancela um toque ou arraste em andamento (pânico, esconder): o corpo volta a cair."""
        self._radial_timer.stop()
        self._right_press = None
        self._radial_active = False
        self._press = None
        self._samples = []
        self.state.pressing = False
        if self._dragging:
            self._dragging = False
            self.body.held = False
            self.body.vx = self.body.vy = 0.0
            self.body.grounded = False
            self.body.platform = None

    def mouseReleaseEvent(self, event):
        """Fim do gesto: soltura do botão direito (executa a roda) ou esquerdo (cutucada/arremesso)."""
        if event.button() == Qt.RightButton:
            self._radial_timer.stop()
            pos = event.globalPosition().toPoint()
            if self._radial_active:
                self._radial_active = False
                self.radial_released.emit(pos)
            else:
                # Clique rápido simples com o botão direito: abre o menu tradicional
                self.menu_requested.emit(pos)
            self._right_press = None
            return

        if event.button() != Qt.LeftButton or self._press is None:
            return
        self.state.pressing = False
        held_ms = (time.monotonic() - self._press[1]) * 1000.0
        if self._dragging:
            vx, vy = self._velocity()
            self.body.held = False
            self.body.vx = max(-2500.0, min(2500.0, vx))
            self.body.vy = max(-2500.0, min(2500.0, vy))
            self.body.omega += self.body.vx * 0.35
            self.drag_ended.emit()
            speed = math.hypot(self.body.vx, self.body.vy)
            if speed >= THROW_MIN_SPEED:
                self.thrown.emit(speed)
        elif held_ms <= POKE_MAX_MS and self.state.allow_poke:
            self.poked.emit()
        self._press = None
        self._dragging = False

    def contextMenuEvent(self, event):
        """Tratado no mouseReleaseEvent para suporte à roda radial."""
        pass

    def wheelEvent(self, event):
        """Rodinha do mouse gira o pet (segurando ou no ar)."""
        if not self.state.allow_drag:
            return
        step = event.angleDelta().y() / 120.0 * 20.0
        if self.body.held:
            self._held_angle += step
        else:
            self.body.omega += step * 12.0
            if self.body.grounded:
                self.body.jump(0.0, -250.0)

    def _velocity(self):
        """Velocidade média do mouse nas últimas amostras (para o arremesso e o balanço)."""
        if len(self._samples) < 2:
            return 0.0, 0.0
        t0, x0, y0 = self._samples[0]
        t1, x1, y1 = self._samples[-1]
        dt = max(t1 - t0, 1e-3)
        return (x1 - x0) / dt, (y1 - y0) / dt

    @property
    def dragging(self):
        """Verdadeiro enquanto você está arrastando o pet."""
        return self._dragging


def cursor_pos():
    """Posição atual do cursor em pixels (x, y)."""
    p = QCursor.pos()
    return p.x(), p.y()
