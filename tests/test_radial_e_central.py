"""
Testes para a Roda Radial de Opções (RadialMenu com submenus) e a Central Unificada (CentralPainel com 4 abas).
"""

import collections
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QImage, QMouseEvent, QPainter
from PySide6.QtWidgets import QApplication

from pestinha.ui.central_painel import CentralPainel
from pestinha.ui.radial_menu import RAIO_CANCELAR, RAIO_EXTERNO, RadialMenu


def test_radial_menu_calculo_setores_e_submenus():
    app_qt = QApplication.instance() or QApplication([])
    app_mock = MagicMock()
    app_mock.nome = "Pestinha"

    menu = RadialMenu(app_mock)
    cx, cy = menu.width() / 2, menu.height() / 2

    # Centro deve cancelar (distância menor que RAIO_CANCELAR)
    assert menu.calcular_setor_mouse(QPointF(cx, cy)) == -1
    assert menu.calcular_setor_mouse(QPointF(cx + 5, cy + 5)) == -1

    # Direção Topo (item 0: submenu_falar)
    p_topo = QPointF(cx, cy - (RAIO_EXTERNO - 20))
    assert menu.calcular_setor_mouse(p_topo) == 0

    # Escolher item 0 ("submenu_falar") entra no submenu de diálogo
    menu.fechar_com_escolha(0)
    assert menu.menu_atual == "submenu_falar"
    assert len(menu.items) == 8

    # Teste de abertura automática por repouso (hover 600ms)
    menu.menu_atual = "principal"
    menu.processar_posicao_mira(p_topo)
    assert menu.timer_submenu_hover.isActive()
    menu._abrir_submenu_hover()
    assert menu.menu_atual == "submenu_falar"

    # Teste de arrastar para fora (dist > RAIO_EXTERNO + 40): volta ao principal
    p_fora = QPointF(cx, cy - (RAIO_EXTERNO + 60))
    menu.processar_posicao_mira(p_fora)
    assert menu.menu_atual == "principal"

    # No submenu de diálogo, escolher "falar_sim"
    menu.menu_atual = "submenu_falar"
    recebido = []
    menu.acao_selecionada.connect(lambda a: recebido.append(a))
    menu.fechar_com_escolha(0)  # item 0 é "falar_sim"
    assert recebido == ["falar_sim"]

    # Teste de retorno: escolher voltar
    menu.menu_atual = "submenu_falar"
    menu.fechar_com_escolha(7)  # item 7 é "voltar"
    assert menu.menu_atual == "principal"

    # Renderiza sem erro
    img = QImage(menu.width(), menu.height(), QImage.Format_ARGB32)
    p = QPainter(img)
    try:
        menu.setor_selecionado = 1  # petisco
        menu.paintEvent(None)
        menu.setor_selecionado = -1
        menu.paintEvent(None)
    finally:
        p.end()
    menu.close()


def test_central_painel_4_abas_e_interatividade():
    app_qt = QApplication.instance() or QApplication([])
    app_mock = MagicMock()
    app_mock.nome = "Pestinha"
    app_mock.paths = MagicMock()
    app_mock.paths.memory = Path("memory")
    app_mock.paths.panels = Path("memory/panels.json")

    # Mock neural com raster e pools
    N = 470
    pools = [
        {"name": "Sensores", "start": 0, "n": 80, "group": "sensory"},
        {"name": "Inter", "start": 80, "n": 240, "group": "inter"},
        {"name": "Motores", "start": 320, "n": 150, "group": "motor"},
    ]
    raster = collections.deque(maxlen=300)
    for _ in range(50):
        raster.append(np.zeros(N, dtype=bool))

    app_mock.brain.N = N
    app_mock.brain.pools = pools
    app_mock.brain.kind = np.zeros(N, dtype=np.uint8)
    app_mock.brain.raster = raster
    app_mock.brain.rates = {"WANDER": 15.0, "WATCH": 5.0}

    # Mocks para o estado de humor e homeostase
    app_mock.protest.stage = 1
    app_mock.protest.grievance = 35.0
    app_mock.protest.revolutions = 0
    app_mock.drives.energy = 0.8
    app_mock.drives.stimulation = 0.5
    app_mock.drives.affection = 0.7
    app_mock.pet_state.emotion = "feliz"
    app_mock.pet_state.at_desk = False
    app_mock.pet_state.shake = 0.0
    app_mock.pet.body.grounded = True
    app_mock.pet.body.held = False
    app_mock.sleep.asleep = False
    app_mock.castigo.dentro = False
    app_mock.castigo.vitorias = {"fugir": 2.0}
    app_mock.castigo.rancor = 0.1
    app_mock.conditioning.V = {"PRESS": 0.5, "APPROACH": 0.2}

    painel = CentralPainel(app_mock, (50, 50))
    assert painel.aba_ativa == 0
    assert len(painel.abas) == 4

    img = QImage(painel.width(), painel.height(), QImage.Format_ARGB32)
    p = QPainter(img)
    try:
        # Testa renderização de todas as 4 abas
        for aba_idx in range(4):
            painel.aba_ativa = aba_idx
            painel.paintEvent(None)
    finally:
        p.end()

    # Clique na aba 1 (Cérebro & Sinapses)
    assert len(painel.tab_rects) == 4
    tab1_pos = painel.tab_rects[1].center()
    click_tab1 = QMouseEvent(QMouseEvent.MouseButtonPress, tab1_pos, tab1_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    painel.mousePressEvent(click_tab1)
    assert painel.aba_ativa == 1

    # Clique na aba 0 de volta
    tab0_pos = painel.tab_rects[0].center()
    click_tab0 = QMouseEvent(QMouseEvent.MouseButtonPress, tab0_pos, tab0_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    painel.mousePressEvent(click_tab0)
    assert painel.aba_ativa == 0

    # Clique em ação rápida
    petisco_btn_pos = painel.btn_rects["petisco"].center()
    click_petisco = QMouseEvent(QMouseEvent.MouseButtonPress, petisco_btn_pos, petisco_btn_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    painel.mousePressEvent(click_petisco)
    app_mock.menu_petisco.assert_called_once()

    painel.close()
