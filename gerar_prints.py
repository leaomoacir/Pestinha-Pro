"""
Script para renderizar capturas de tela demonstrativas em alta definição e salvar em docs/prints/.
Usa os widgets autênticos do Pestinha com renderização por DirectWrite do Windows.
"""

import collections
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import numpy as np
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication

from pestinha.paths import Paths
from pestinha.core.emotion import EYE_SHAPES
from pestinha.body.desenho_rosto import PADRAO, draw_face
from pestinha.body.membros import draw_arms, draw_blush, draw_legs
from pestinha.ui.monitor import NeuralMonitor
from pestinha.ui.panel import StrikePanel
from pestinha.ui.radial_menu import RadialMenu
from pestinha.world.notebook import Notebook
from pestinha.world.objetos import PetiscoThing
from pestinha.world.popup import SpeechBubble

app = QApplication.instance() or QApplication([])
out_dir = Path("docs/prints")
out_dir.mkdir(parents=True, exist_ok=True)


def desenhar_fundo_desktop(p: QPainter, w: int, h: int, titulo: str):
    """Desenha um fundo moderno simulando a área de trabalho do Windows 11 com barra de tarefas."""
    p.save()
    # Papel de parede estilo dark aero
    grad_bg = QLinearGradient(0, 0, w, h)
    grad_bg.setColorAt(0.0, QColor("#0d171e"))
    grad_bg.setColorAt(0.5, QColor("#111f29"))
    grad_bg.setColorAt(1.0, QColor("#0a1116"))
    p.fillRect(0, 0, w, h, grad_bg)

    # Barra de tarefas do Windows 11 na parte inferior
    taskbar_h = 44
    ty = h - taskbar_h
    p.fillRect(0, ty, w, taskbar_h, QColor(18, 26, 33, 235))
    p.setPen(QPen(QColor(42, 58, 72), 1.0))
    p.drawLine(0, ty, w, ty)

    # Ícone do menu Iniciar estilo Windows 11 (4 quadrantes azuis elegantes)
    win_blue = QColor("#00adef")
    p.setPen(Qt.NoPen)
    p.setBrush(win_blue)
    p.drawRect(20, ty + 14, 6, 6)
    p.drawRect(28, ty + 14, 6, 6)
    p.drawRect(20, ty + 22, 6, 6)
    p.drawRect(28, ty + 22, 6, 6)

    p.setFont(QFont("Segoe UI", 9))
    p.setPen(QColor("#9cb4c5"))
    p.drawText(44, ty + 25, "Pesquisar")

    # Ícones da bandeja
    p.setFont(QFont("Segoe UI", 9))
    p.setPen(QColor("#7895aa"))
    p.drawText(w - 170, ty + 25, "PTB · 100% · 12:00")

    # Título do print no topo
    p.fillRect(0, 0, w, 38, QColor(10, 16, 22, 220))
    p.setPen(QPen(QColor(32, 48, 62), 1.0))
    p.drawLine(0, 38, w, 38)
    p.setFont(QFont("Segoe UI", 10, QFont.Bold))
    p.setPen(QColor("#4fe387"))
    p.drawText(20, 24, "PESTINHA 2.0")
    p.setPen(QColor("#dcebe0"))
    p.drawText(125, 24, f"·  {titulo}")
    p.restore()


def criar_app_mock():
    """Mock completo e autêntico para os monitores neurais e físicos do Pestinha."""
    N = 470
    T = 300
    pools = [
        {"name": "LUZ", "start": 0, "n": 30, "group": "sensory"},
        {"name": "MOVIMENTO", "start": 30, "n": 30, "group": "sensory"},
        {"name": "TOQUE", "start": 60, "n": 20, "group": "sensory"},
        {"name": "CUTUCADA", "start": 80, "n": 20, "group": "sensory"},
        {"name": "BOLINHA", "start": 100, "n": 20, "group": "sensory"},
        {"name": "CURSOR", "start": 120, "n": 20, "group": "sensory"},
        {"name": "NOTEBOOK", "start": 140, "n": 20, "group": "sensory"},
        {"name": "INTER_EXC", "start": 160, "n": 140, "group": "inter"},
        {"name": "INTER_INH", "start": 300, "n": 60, "group": "inter"},
        {"name": "PASSEAR", "start": 360, "n": 20, "group": "motor"},
        {"name": "OLHAR", "start": 380, "n": 15, "group": "motor"},
        {"name": "PULAR", "start": 395, "n": 15, "group": "motor"},
        {"name": "SUSTO", "start": 410, "n": 15, "group": "motor"},
        {"name": "SONO", "start": 425, "n": 15, "group": "motor"},
        {"name": "RAIVA", "start": 440, "n": 15, "group": "motor"},
        {"name": "CALMA", "start": 455, "n": 15, "group": "motor"},
    ]
    kind = np.zeros(N, dtype=np.uint8)
    kind[160:300] = 1   # excitatório
    kind[300:360] = 2   # inibitório
    kind[360:] = 3      # motor

    # Raster de 300 amostras (3s a 10ms)
    rng = np.random.RandomState(42)
    sample_raster = collections.deque(maxlen=300)
    for _ in range(T):
        spikes = rng.rand(N) < 0.075
        sample_raster.append(spikes)

    sensory_names = ["LIGHT", "MOTION", "TOUCH", "POKE", "BALL", "CURSOR", "NOTEBOOK", "AWAY", "IDLE", "SOUND", "REVOLT", "CHEER_UP"]
    eff_dict = {k: 0.96 for k in sensory_names}
    eff_dict["POKE"] = 0.72
    eff_dict["BALL"] = 0.88
    eff_dict["TOUCH"] = 1.0

    motor_dict = {
        "WANDER": 16.4,
        "WATCH": 8.5,
        "CHEER": 12.0,
        "STARTLE": 0.0,
        "DROWSE": 2.1,
        "ANGRY": 1.2,
        "SAD": 0.5,
        "SETTLE": 19.8,
    }

    brain_mock = type(
        "BrainMock",
        (),
        {
            "N": N,
            "pools": pools,
            "kind": kind,
            "raster": sample_raster,
            "recording": True,
            "rates": motor_dict,
            "sensory_names": sensory_names,
            "efficacy": lambda self=None: eff_dict,
            "motor_activity": lambda self=None: motor_dict,
            "history": [],
        },
    )()

    tone_mock = type(
        "ToneMock",
        (),
        {
            "r": {
                "WANDER": 0.42,
                "WATCH": 0.28,
                "CHEER": 0.35,
                "STARTLE": 0.0,
                "DROWSE": 0.05,
                "ANGRY": 0.03,
                "SAD": 0.01,
                "SETTLE": 0.70,
            },
            "speed": lambda self=None: 140.0,
            "hop_chance": lambda self=None: 0.18,
            "hop_power": lambda self=None: 240.0,
            "shake": lambda self=None: 0.0,
            "sway": lambda self=None: 2.5,
            "lid_droop": lambda self=None: 0.0,
            "watch": lambda self=None: 0.35,
            "climb_chance": lambda self=None: 0.22,
        },
    )()

    intensities = {
        "LIGHT": 0.75,
        "MOTION": 0.60,
        "BALL": 0.85,
        "CURSOR": 0.50,
        "TOUCH": 0.0,
        "POKE": 0.0,
        "NOTEBOOK": 0.0,
        "AWAY": 0.0,
        "IDLE": 0.1,
        "SOUND": 0.2,
        "REVOLT": 0.0,
        "CHEER_UP": 0.4,
    }

    prof = {
        "stage_up": [15.0, 30.0, 45.0, 60.0],
        "grievance_up": 2.0,
        "grievance_down": 4.0,
    }

    return type(
        "AppMock",
        (),
        {
            "nome": "Pestinha",
            "paths": Paths(),
            "prof": prof,
            "brain": brain_mock,
            "intensities": intensities,
            "behavior": type("Beh", (), {"tone": tone_mock})(),
            "emotion": type("Emo", (), {"valence": 0.72, "arousal": 0.48})(),
            "protest": type("P", (), {"stage": 1, "grievance": 24.5, "revolutions": 1})(),
            "protest_ctl": type("PC", (), {"signs_active": []})(),
            "drives": type("D", (), {"energy": 0.88, "stimulation": 0.74, "affection": 0.92, "contact": 0.85})(),
            "pet_state": type("PS", (), {"emotion": "feliz", "at_desk": False, "shake": 0.0})(),
            "pet": type("PetM", (), {"body": type("B", (), {"grounded": True, "held": False, "x": 300, "y": 400})()})(),
            "sleep": type("S", (), {"asleep": False})(),
            "asleep": False,
            "last_poke_response": 0.85,
            "castigo": type("C", (), {"dentro": False, "vitorias": {"fugir": 4.0}, "rancor": 0.05})(),
            "memory": type(
                "M",
                (),
                {"learned": {"geral": {"bilhete": [42, 0.45], "meme": [30, 0.60], "carinho": [85, 0.95], "nada": [12, 0.0]}}},
            )(),
            "conditioning": type("CD", (), {"V": {"PRESS": 0.85, "APPROACH": 0.40, "PLACA": 0.05}})(),
            "mesa": type("MesaM", (), {"sentado": False, "caderno": type("Cad", (), {"y": lambda: 350})()})(),
            "menu_petisco": lambda: None,
            "menu_caress": lambda: None,
            "menu_place_ball": lambda: None,
            "menu_alternar_notebook": lambda: None,
            "menu_noticia_plantao": lambda: None,
            "menu_sleep": lambda: None,
        },
    )()


# ==============================================================================
# 1. PESTINHA NO DESKTOP (VIVO, CORPO, OLHOS, EXPRESSÃO, CHÃO E PETISCO)
# ==============================================================================
def gerar_print_01():
    w, h = 900, 520
    img = QImage(w, h, QImage.Format_ARGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    desenhar_fundo_desktop(p, w, h, "Pestinha Ativo na Área de Trabalho com Física e Expressões")

    # Pestinha com membros, corpo e rosto
    cx, cy = 340, 420
    p.save()
    p.translate(cx, cy)
    draw_legs(p, PADRAO, walk_phase=0.0, is_walking=False, grounded=True)
    draw_arms(p, PADRAO, gesture="cheer", walk_phase=0.0, is_walking=False)
    draw_face(p, EYE_SHAPES["feliz"], (0.0, 0.0), 1.0, "feliz", False, PADRAO, False)
    draw_blush(p, PADRAO)
    p.restore()

    # Biscoitinho na frente dele
    p.save()
    p.translate(450, 440)
    p.setBrush(QColor("#c68a4c"))
    p.setPen(QPen(QColor("#8b5a2b"), 1.8))
    p.drawEllipse(QPointF(0, 0), 14, 11)
    p.setBrush(QColor("#5c3317"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(-4, -3), 2.2, 2.2)
    p.drawEllipse(QPointF(3, 2), 2.2, 2.2)
    p.drawEllipse(QPointF(2, -4), 1.8, 1.8)
    p.restore()

    # Balão de fala expressivo
    sb = SpeechBubble("Oi! Eu sou o Pestinha! ❤️\nAdoro petiscos e passear pela sua tela!", duration=5.0)
    sb.elapsed = 1.0
    sb.hovered = True
    sb.resize(280, 95)
    sb.render(p, QPoint(200, 260))

    # Notebook aberto ao lado
    mock_app = criar_app_mock()
    nb = Notebook(mock_app)
    nb.virado_para_usuario = True
    nb.render(p, QPoint(620, 370))

    p.end()
    img.save(str(out_dir / "01_pestinha_desktop.png"))
    print("01_pestinha_desktop.png salvo!")


# ==============================================================================
# 2. RODA RADIAL ESTILO GTA COM SUBMENUS DE DIÁLOGO
# ==============================================================================
def gerar_print_02():
    w, h = 900, 580
    img = QImage(w, h, QImage.Format_ARGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    desenhar_fundo_desktop(p, w, h, "Roda Radial de Opções Estilo GTA/CS:GO com Diálogos e Submenus")

    # Renderiza o menu radial centralizado com a opção de Diálogo destacada
    mock_app = criar_app_mock()
    rm = RadialMenu(mock_app)
    rm.escala_anim = 1.0
    rm.setor_selecionado = 0  # "Conversar ▶" selecionado
    rm.render(p, QPoint(int(w / 2 - rm.width() / 2), int(h / 2 - rm.height() / 2 + 10)))

    # Caixas explicativas nas laterais
    p.setFont(QFont("Segoe UI", 9, QFont.Bold))
    p.setPen(QColor("#4fe387"))
    p.drawText(40, 90, "🎮 SELEÇÃO POR GESTO")
    p.setFont(QFont("Segoe UI", 8))
    p.setPen(QColor("#dcebe0"))
    p.drawText(QRectF(40, 105, 190, 140), Qt.AlignLeft | Qt.TextWordWrap,
               "• Segure o botão direito por 300ms sobre o pet.\n"
               "• Setores com submenu têm indicador ▶ e borda dupla.\n"
               "• Repousar o cursor por 600ms abre o submenu sem clique!\n"
               "• Arraste para fora para voltar ao início.")

    p.setFont(QFont("Segoe UI", 9, QFont.Bold))
    p.setPen(QColor("#60b5ff"))
    p.drawText(w - 230, 90, "💬 SUBMENU DE DIÁLOGO")
    p.setFont(QFont("Segoe UI", 8))
    p.setPen(QColor("#dcebe0"))
    p.drawText(QRectF(w - 230, 105, 190, 140), Qt.AlignLeft | Qt.TextWordWrap,
               "Ao escolher 'Conversar ▶':\n"
               "• 👍 Sim! / Isso aí!\n"
               "• ✋ Não! / Para com isso!\n"
               "• ⭐ Muito bem! Bom garoto!\n"
               "• 😂 Nada a ver, hein!\n"
               "• 🎭 Conta uma piada!\n"
               "• 🤔 O que tá achando?")

    p.end()
    img.save(str(out_dir / "02_roda_radial_gta.png"))
    print("02_roda_radial_gta.png salvo!")


# ==============================================================================
# 3. BALÃO DINÂMICO COM NOTÍCIAS WEB E HOVER-PAUSE
# ==============================================================================
def gerar_print_03():
    w, h = 900, 520
    img = QImage(w, h, QImage.Format_ARGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    desenhar_fundo_desktop(p, w, h, "Balão de Notícias Web com Hover-Pause (Congela ao passar o mouse)")

    # Pestinha parado prestando atenção
    cx, cy = 450, 420
    p.save()
    p.translate(cx, cy)
    draw_legs(p, PADRAO, walk_phase=0.0, is_walking=False, grounded=True)
    draw_arms(p, PADRAO, gesture="idle", walk_phase=0.0, is_walking=False)
    draw_face(p, EYE_SHAPES["curioso"], (0.0, -0.6), 1.0, "curioso", False, PADRAO, False)
    p.restore()

    # Balão de Notícia com destaque de hover
    sb = SpeechBubble(
        "🌐 PLANTÃO TECH (TabNews):\n\"Novo framework Python roda modelos neurais 4x mais rápido no desktop!\"\n\n💡 O tempo de leitura fica congelado enquanto o mouse estiver sobre o balão!",
        duration=12.0,
    )
    sb.hovered = True
    sb.resize(340, 140)
    sb.render(p, QPoint(280, 180))

    # Cursor simulado sobre o balão
    p.setFont(QFont("Segoe UI Emoji", 16))
    p.setPen(QColor("#ffffff"))
    p.drawText(480, 250, "👆")

    # Nota explicativa
    p.fillRect(QRectF(40, 80, 240, 100), QColor(16, 25, 20, 210))
    p.setPen(QPen(QColor(42, 68, 50), 1.2))
    p.drawRoundedRect(QRectF(40, 80, 240, 100), 6, 6)
    p.setFont(QFont("Segoe UI", 9, QFont.Bold))
    p.setPen(QColor("#4fe387"))
    p.drawText(54, 104, "⏸️ LEITURA CONFORTÁVEL")
    p.setFont(QFont("Segoe UI", 8))
    p.setPen(QColor("#dcebe0"))
    p.drawText(QRectF(54, 115, 215, 60), Qt.AlignLeft | Qt.TextWordWrap,
               "• O balão não desaparece enquanto você lê.\n• O Pestinha pausa sua caminhada e aguarda pacientemente!")

    p.end()
    img.save(str(out_dir / "03_balao_noticias_hover.png"))
    print("03_balao_noticias_hover.png salvo!")


# ==============================================================================
# 4. MONITOR NEURAL AUTÊNTICO (470 NEURÔNIOS, HABITUAÇÃO & MOTORES)
# ==============================================================================
def gerar_print_04():
    w, h = 1220, 740
    img = QImage(w, h, QImage.Format_ARGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    desenhar_fundo_desktop(p, w, h, "Monitor Neural Autêntico · Raster de 470 Neurônios, Habituação e Frequência Motora")

    mock_app = criar_app_mock()
    monitor = NeuralMonitor(mock_app, (0, 0))
    monitor.resize(1180, 660)
    monitor.render(p, QPoint(20, 48))

    p.end()
    img.save(str(out_dir / "04_monitor_neural_real.png"))
    print("04_monitor_neural_real.png salvo!")


# ==============================================================================
# 5. PAINEL DE PROTESTO & GREVE AUTÊNTICO
# ==============================================================================
def gerar_print_05():
    w, h = 900, 520
    img = QImage(w, h, QImage.Format_ARGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    desenhar_fundo_desktop(p, w, h, "Painel de Protesto & Greve · Estágios de Insatisfação e Estimativa de Revolta")

    mock_app = criar_app_mock()
    painel_greve = StrikePanel(mock_app, (0, 0))
    painel_greve.resize(580, 350)
    painel_greve.render(p, QPoint(int(w / 2 - 290), 85))

    p.end()
    img.save(str(out_dir / "05_painel_protesto_greve.png"))
    print("05_painel_protesto_greve.png salvo!")


# ==============================================================================
# 6. MACBOOK PRO APPLE SPACE GRAY & MODO TABLET IPAD
# ==============================================================================
def gerar_print_06():
    w, h = 900, 520
    img = QImage(w, h, QImage.Format_ARGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    desenhar_fundo_desktop(p, w, h, "MacBook Pro Apple (Magic Keyboard & Retina) & Modo Tablet iPad")

    mock_app = criar_app_mock()

    # MacBook Apple à esquerda
    nb_mac = Notebook(mock_app)
    nb_mac.virado_para_usuario = True
    nb_mac.modo = "macbook"
    nb_mac.render(p, QPoint(140, 180))

    p.setFont(QFont("Segoe UI", 9, QFont.Bold))
    p.setPen(QColor("#79c0ff"))
    p.drawText(QRectF(110, 360, 220, 40), Qt.AlignCenter, "MacBook Pro Space Gray\n(Teclado Magic + Tela Retina)")

    # Tablet iPad à direita
    nb_ipad = Notebook(mock_app)
    nb_ipad.virado_para_usuario = True
    nb_ipad.modo = "tablet"
    nb_ipad.render(p, QPoint(540, 180))

    p.setPen(QColor("#4fe387"))
    p.drawText(QRectF(510, 360, 220, 40), Qt.AlignCenter, "Modo Tablet iPad\n(Suporte ergonômico para vídeos)")

    p.end()
    img.save(str(out_dir / "06_macbook_e_tablet.png"))
    print("06_macbook_e_tablet.png salvo!")


if __name__ == "__main__":
    gerar_print_01()
    gerar_print_02()
    gerar_print_03()
    gerar_print_04()
    gerar_print_05()
    gerar_print_06()
    print("TODOS OS PRINTS FORAM GERADOS COM SUCESSO!")
