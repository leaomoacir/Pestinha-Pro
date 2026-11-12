"""
Testes para o sistema sazonal, datas comemorativas, contexto musical/vídeo e notícias dinâmicas.
"""

from datetime import datetime
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
from pestinha.body.adorno import desenhar_adorno_sazonal
from pestinha.sense.contexto import (
    obter_evento_sazonal,
    analisar_contexto_ativo,
    obter_noticia_dinamica,
)
from pestinha.world.objetos import PetiscoThing


def test_deteccao_eventos_sazonais():
    # São João (junho)
    dt_sj = datetime(2026, 6, 24, 12, 0)
    assert obter_evento_sazonal(dt_sj) == "sao_joao"

    # Natal (dezembro)
    dt_natal = datetime(2026, 12, 25, 12, 0)
    assert obter_evento_sazonal(dt_natal) == "natal"

    # Ano Novo (1 de janeiro)
    dt_ano_novo = datetime(2027, 1, 1, 0, 1)
    assert obter_evento_sazonal(dt_ano_novo) == "ano_novo"

    # Dia do Programador (12 de setembro)
    dt_dev = datetime(2026, 9, 12, 12, 0)
    assert obter_evento_sazonal(dt_dev) == "programador"

    # Halloween (31 de outubro)
    dt_hall = datetime(2026, 10, 31, 20, 0)
    assert obter_evento_sazonal(dt_hall) == "halloween"


def test_renderizacao_adornos_sem_erro():
    app = QApplication.instance() or QApplication([])
    img = QImage(200, 200, QImage.Format_ARGB32)
    img.fill(Qt.transparent)

    p = QPainter(img)
    try:
        for evento in ("sao_joao", "natal", "ano_novo", "carnaval", "pascoa", "halloween", "programador"):
            desenhar_adorno_sazonal(p, evento, PADRAO)
    finally:
        p.end()


def test_analise_contexto_musica_e_video():
    # Rock / Metal
    cat, subcat, reacao, fala = analisar_contexto_ativo("spotify.exe", "Master of Puppets - Metallica")
    assert cat == "musica" and subcat == "rock" and reacao == "headbanging"
    assert "🎸" in fala or "🤘" in fala

    # Lo-fi / Jazz
    cat, subcat, reacao, fala = analisar_contexto_ativo("chrome.exe", "lofi hip hop radio - beats to relax/study to")
    assert cat == "musica" and subcat == "lofi" and reacao == "lofi_chill"

    # Streaming / Vídeo
    cat, subcat, reacao, fala = analisar_contexto_ativo("msedge.exe", "Trailer Oficial - YouTube")
    assert cat == "video" and reacao == "pipoca"
    assert any(e in fala for e in ("🍿", "🥤", "🎬"))


def test_noticias_dinamicas():
    noticia = obter_noticia_dinamica()
    assert isinstance(noticia, str)
    assert len(noticia) > 10

    from pestinha.sense.contexto import obter_fala_do_dia
    fala = obter_fala_do_dia()
    assert isinstance(fala, str)
    assert len(fala) > 5


def test_notebook_virar_tela_e_tablet():
    from unittest.mock import MagicMock
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QPointF
    from pestinha.world.notebook import Notebook
    app_mock = MagicMock()
    app_mock.nome = "Pestinha"
    nb = Notebook(app_mock)
    assert nb.virado_para_usuario is False
    assert nb.modo == "macbook"

    # Clique esquerdo arrasta (não vira a tela)
    press_event = QMouseEvent(QMouseEvent.MouseButtonPress, QPointF(10, 10), QPointF(100, 100), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    nb.mousePressEvent(press_event)
    assert nb.virado_para_usuario is False
    assert nb._grab is not None

    # Mover arrasta
    move_event = QMouseEvent(QMouseEvent.MouseMove, QPointF(20, 20), QPointF(110, 110), Qt.NoButton, Qt.LeftButton, Qt.NoModifier)
    nb.mouseMoveEvent(move_event)

    # Soltar finaliza arrasto
    release_event = QMouseEvent(QMouseEvent.MouseButtonRelease, QPointF(20, 20), QPointF(110, 110), Qt.LeftButton, Qt.NoButton, Qt.NoModifier)
    nb.mouseReleaseEvent(release_event)
    assert nb._grab is None

    # Vira para o usuário via virar_tela() (menu)
    nb.virar_tela()
    assert nb.virado_para_usuario is True

    # Quando o pet começa a usar (set_working=True), tela vira para o pet
    nb.set_working(True)
    assert nb.virado_para_usuario is False

    # Alterna para modo tablet
    nb.alternar_modo()
    assert nb.modo == "tablet"

    # Renderiza sem erro
    img = QImage(144, 88, QImage.Format_ARGB32)
    p = QPainter(img)
    try:
        nb.paintEvent(None)
    finally:
        p.end()
    nb.close()


def test_petisco_sem_crash():
    app = QApplication.instance() or QApplication([])
    treat = PetiscoThing()
    assert treat.width() == 40
    treat.close()
