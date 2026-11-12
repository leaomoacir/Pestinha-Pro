"""
Testes para os membros animados (braços, pernas, gestos) e popups de fala (SpeechBubble).
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter, QImage
from PySide6.QtCore import Qt

from pestinha.body.desenho_rosto import PADRAO
from pestinha.body.membros import draw_legs, draw_arms, draw_blush, _calcular_bracos
from pestinha.body.pet_state import PetState
from pestinha.core.physics import Body
from pestinha.world.popup import SpeechBubble
from pestinha.world.objetos import NoteThing, ImageThing, PetiscoThing


def test_membros_renderizam_sem_erro():
    app = QApplication.instance() or QApplication([])
    img = QImage(200, 200, QImage.Format_ARGB32)
    img.fill(Qt.transparent)

    p = QPainter(img)
    try:
        # Testa pernas paradas e andando
        draw_legs(p, PADRAO, walk_phase=0.0, is_walking=False, grounded=True)
        draw_legs(p, PADRAO, walk_phase=1.5, is_walking=True, grounded=True)
        draw_legs(p, PADRAO, walk_phase=0.0, is_walking=False, grounded=False)

        # Testa todos os gestos de braços
        for gesture in ("idle", "walk", "cheer", "wave", "cross", "scratch", "hold_ball", "juggle"):
            draw_arms(p, PADRAO, gesture=gesture, walk_phase=1.0, is_walking=(gesture == "walk"))

        # Testa bochechas
        draw_blush(p, PADRAO)
    finally:
        p.end()


def test_pet_state_gestos_e_celebrate():
    st = PetState()
    assert st.active_gesture() == "idle"
    assert not st.is_blushing()

    st.celebrate(duration=1.5, now=10.0)
    assert st.active_gesture(now=10.5) == "cheer"
    assert st.is_blushing(now=10.5)
    assert st.feliz_fechado(now=10.5)

    # Expirado
    assert st.active_gesture(now=12.0) == "idle"
    assert not st.is_blushing(now=12.0)


def test_speech_bubble_criacao_e_posicao():
    app = QApplication.instance() or QApplication([])
    bubble = SpeechBubble("Olá mundo! Teste de fala ❤️", duration=2.0)
    assert bubble.text == "Olá mundo! Teste de fala ❤️"
    assert bubble.width() >= 90
    assert bubble.height() >= 40

    body = Body(500.0, 400.0, 60, 45)
    bubble.attach_to_pet(body, screen_bounds=(0, 0, 1920, 1080))
    assert bubble.x() > 0
    assert bubble.y() < 400.0

    # Atualiza posição quando o pet anda
    body.x = 600.0
    bubble.update_position(body, screen_bounds=(0, 0, 1920, 1080))
    bubble.close()


def test_speech_bubble_hover_e_pausa():
    from PySide6.QtGui import QEnterEvent
    from PySide6.QtCore import QPointF, QEvent
    app = QApplication.instance() or QApplication([])
    bubble = SpeechBubble("Notícia super interessante que precisa de tempo para ser lida!", duration=1.0)
    assert not bubble.hovered

    # Simula passar o mouse em cima (enterEvent)
    event_enter = QEnterEvent(QPointF(10, 10), QPointF(10, 10), QPointF(10, 10))
    bubble.enterEvent(event_enter)
    assert bubble.hovered is True
    assert bubble.remaining >= 4.0

    # Passos de animação com mouse em cima não deixam expirar
    for _ in range(20):
        bubble._step_anim()
    assert bubble.isVisible() or bubble.remaining >= 4.0

    # Com mouse em cima, movimento do pet não arrasta o balão para longe do cursor
    x_antes = bubble.x()
    body = Body(999.0, 999.0, 60, 45)
    bubble.update_position(body, screen_bounds=(0, 0, 1920, 1080))
    assert bubble.x() == x_antes

    # Simula tirar o mouse (leaveEvent)
    event_leave = QEvent(QEvent.Leave)
    bubble.leaveEvent(event_leave)
    assert bubble.hovered is False
    assert bubble.remaining >= 3.0

    # Renderiza com efeito hovered
    bubble.hovered = True
    img = QImage(bubble.width(), bubble.height(), QImage.Format_ARGB32)
    p = QPainter(img)
    try:
        bubble.paintEvent(None)
    finally:
        p.end()
    bubble.close()


def test_like_button_hover_e_efeito(tmp_path):
    app = QApplication.instance() or QApplication([])
    note = NoteThing("Bilhete com like interativo")
    assert not note.hover_heart

    hr = note.heart_rect()
    assert hr.width() > 0 and hr.height() > 0

    # Dispara o efeito de like
    note.trigger_like_effect()
    assert note.liked_at > 0
    assert len(note.particles) > 0

    # Renderiza com o botão e partículas
    img = QImage(note.width(), note.height(), QImage.Format_ARGB32)
    p = QPainter(img)
    try:
        note.draw_heart_button(p)
    finally:
        p.end()
    note.close()

