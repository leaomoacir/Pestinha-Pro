"""
NOTEBOOK & TABLET - Notebook Pro e Tablet Digital em alumínio unibody.

Design realista de alta imersão:
- Posição original e natural: A tampa do notebook fica virada DE COSTAS para nós (tela virada para o pet).
  O pet senta atrás, olha para a tela dele, com o emblema tech estilizado virado para a frente e o brilho
  da tela iluminando o rosto dele por trás da tampa.
- Interatividade 'Virar Tela': Clique no notebook para ele virar a tela para você (mostrando o código/IDE)
  ou virar de volta para o pet!
- Modo Tablet: Alternável pelo menu do notebook para quando o pet estiver assistindo vídeos ou ouvindo música.
"""

import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QMenu
from .arrastavel import FloatingWidget

NOTEBOOK_W, NOTEBOOK_H = 144, 88
MARGEM_TELA = 24


def _default_position(size):
    """Canto inferior direito da tela, onde o notebook começa."""
    screen = QGuiApplication.primaryScreen().availableGeometry()
    return (screen.right() - size[0] - MARGEM_TELA, screen.bottom() - size[1] - MARGEM_TELA)


class Notebook(FloatingWidget):
    """Computador do pet: Notebook Pro em alumínio grafite (virado para ele) e modo Tablet Digital."""

    def __init__(self, app):
        size = (NOTEBOOK_W, NOTEBOOK_H)
        super().__init__(app, "notebook", f"Notebook do {app.nome}", size, size, _default_position(size))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Notebook do pet (Arraste para mover • Botão direito para opções)")

        self.working = False
        self.virado_para_usuario = False  # Padrão: tela virada para o pet, tampa de costas para nós (como no notebook.png)
        self.modo = "notebook"            # "notebook" ou "tablet"
        self.code_cursor_blink = 0.0
        self.particles = []

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._step_anim)
        self.anim_timer.start(33)

    def set_working(self, working):
        """Ativa a tela e iluminação quando o pet trabalha."""
        if working != self.working:
            self.working = working
            if working:
                # Quando o pestinha senta para programar, a tela fica virada para ele digitar
                self.virado_para_usuario = False
                if hasattr(self.app, "mostrar_popup") and not self.app.asleep and random.random() < 0.4:
                    falas_trabalho = [
                        "Hora de codar! Abrindo o editor... 💻⚡",
                        "Deixa eu compilar isso aqui rapidinho... 💻☕",
                        "Foco total no código agora! 🚀",
                    ]
                    self.app.mostrar_popup(random.choice(falas_trabalho), duracao=3.0)
            self.update()

    def virar_tela(self):
        """Gira o notebook para mostrar a tela para o usuário ou voltar para o pet."""
        self.virado_para_usuario = not self.virado_para_usuario
        if self.virado_para_usuario:
            self.setToolTip("Tela virada para você (Arraste para mover • Botão direito para opções)")
            if hasattr(self.app, "mostrar_popup") and not self.app.asleep:
                falas = [
                    "Olha só o que eu programei! 💻✨",
                    "Rodando 100% sem erros! Dá uma olhada! 🚀",
                    "Centralizei a div no CSS! Vitória! 🏆",
                    "Compilei de primeira! Não mexe em nada! 👀",
                ]
                self.app.mostrar_popup(random.choice(falas), duracao=3.5)
        else:
            self.setToolTip("Notebook do pet (Arraste para mover • Botão direito para opções)")
        self.update()

    def alternar_modo(self):
        """Alterna entre Notebook e Tablet Digital."""
        self.modo = "tablet" if self.modo == "notebook" else "notebook"
        self.update()

    def mousePressEvent(self, event):
        """Clique esquerdo arrasta o notebook; clique direito abre menu de opções."""
        if event.button() == Qt.LeftButton:
            super().mousePressEvent(event)
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.RightButton:
            menu = QMenu(self)
            act_virar = menu.addAction("Virar tela para cá 🔄" if not self.virado_para_usuario else "Virar tela para o pet 💻")
            act_virar.triggered.connect(self.virar_tela)
            act_modo = menu.addAction("Usar Modo Tablet 📱" if self.modo == "notebook" else "Usar Modo Notebook 💻")
            act_modo.triggered.connect(self.alternar_modo)
            menu.addSeparator()
            act_esconder = menu.addAction("Esconder notebook")
            act_esconder.triggered.connect(self.app.menu_alternar_notebook)
            menu.exec(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        """Arrasta o notebook suavemente pela tela."""
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Solta o notebook, salva a nova posição e restaura o cursor."""
        super().mouseReleaseEvent(event)
        self.setCursor(Qt.PointingHandCursor)

    def _step_anim(self):
        now = time.monotonic()
        if self.working:
            self.code_cursor_blink = (now * 3.2) % 1.0

            if random.random() < 0.22 and len(self.particles) < 10:
                self.particles.append({
                    "x": random.uniform(32, NOTEBOOK_W - 32),
                    "y": 42.0 if not self.virado_para_usuario else 52.0,
                    "vy": random.uniform(-18.0, -30.0),
                    "vx": random.uniform(-3.5, 3.5),
                    "born": now,
                    "dur": random.uniform(1.2, 1.8),
                    "char": random.choice(["⚡", "code", "def", "git", "01", "{ }", "run", "fn"]),
                    "cor": random.choice(["#a8b3be", "#63e56f", "#80d8ff", "#ffd54f", "#ff7b72"]),
                })

        vivas = []
        for p in self.particles:
            prog = (now - p["born"]) / p["dur"]
            if prog < 1.0:
                p["y"] += p["vy"] * 0.033
                p["x"] += p["vx"] * 0.033
                vivas.append(p)
        self.particles = vivas

        if self.working or self.particles:
            self.update()

    def paintEvent(self, _event):
        """Desenha o computador na posição correta: de costas para nós (tela virada para ele), virado para cá ou tablet."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        if self.modo == "tablet":
            self._desenhar_tablet(p)
        elif self.virado_para_usuario:
            self._desenhar_notebook_aberto(p)
        else:
            self._desenhar_notebook_de_costas(p)

        # Partículas de código flutuando
        if self.particles:
            p.setFont(QFont("Consolas", 8, QFont.Bold))
            now = time.monotonic()
            for part in self.particles:
                prog = (now - part["born"]) / part["dur"]
                alpha = int(255 * (1.0 - prog) * min(1.0, prog * 4))
                if alpha <= 0:
                    continue
                cor = QColor(part["cor"])
                cor.setAlpha(alpha)
                p.setPen(cor)
                p.drawText(QRectF(part["x"] - 16, part["y"] - 8, 32, 16), Qt.AlignCenter, part["char"])

        p.end()

    # ---------------- 1. MODO ORIGINAL: NOTEBOOK DE COSTAS PARA O USUÁRIO (TELA PRO PET) ----------------

    def _desenhar_notebook_de_costas(self, p: QPainter):
        """
        Posição clássica e realista: o pet senta atrás do notebook e a tela fica virada para ele.
        Nós vemos a tampa traseira de alumínio grafite com o emblema tech polido virado para a frente,
        e o brilho da tela iluminando o rosto do pet por trás.
        """
        # Brilho de tela saindo de trás da tampa quando trabalhando (ilumina o pet)
        if self.working:
            p.save()
            grad_luz = QLinearGradient(NOTEBOOK_W / 2, 8.0, NOTEBOOK_W / 2, 40.0)
            grad_luz.setColorAt(0.0, QColor(99, 229, 111, 75))
            grad_luz.setColorAt(0.6, QColor(64, 196, 255, 35))
            grad_luz.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(grad_luz)
            p.drawEllipse(QRectF(NOTEBOOK_W / 2 - 58, 6.0, 116, 40))
            p.restore()

        # Base do notebook assentada na mesa
        base_w = 132
        base_h = 10.0
        base_x = (NOTEBOOK_W - base_w) / 2
        base_y = NOTEBOOK_H - 18.0
        rect_base = QRectF(base_x, base_y, base_w, base_h)

        # Sombra sob a base
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 60))
        p.drawRoundedRect(rect_base.translated(0, 3.0), 3.0, 3.0)

        # Chassi inferior de alumínio grafite
        grad_chassi = QLinearGradient(rect_base.topLeft(), rect_base.bottomLeft())
        grad_chassi.setColorAt(0.0, QColor("#3f4347"))
        grad_chassi.setColorAt(1.0, QColor("#1e2022"))
        p.setPen(QPen(QColor("#161819"), 1.0))
        p.setBrush(grad_chassi)
        p.drawRoundedRect(rect_base, 3.0, 3.0)

        # Tampa da tela aberta em ângulo (vista traseira)
        tampa_w = 122
        tampa_h = 56
        tampa_x = (NOTEBOOK_W - tampa_w) / 2
        tampa_y = base_y - tampa_h + 3.0
        rect_tampa = QRectF(tampa_x, tampa_y, tampa_w, tampa_h)

        # Sombra da tampa projetada na base
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 45))
        p.drawRoundedRect(rect_tampa.translated(0, 2.0), 6.0, 6.0)

        # Carcaça de alumínio anodizado da tampa traseira
        grad_tampa = QLinearGradient(rect_tampa.topLeft(), rect_tampa.bottomLeft())
        grad_tampa.setColorAt(0.0, QColor("#54585d"))
        grad_tampa.setColorAt(0.4, QColor("#3e4246"))
        grad_tampa.setColorAt(1.0, QColor("#282a2d"))

        p.setPen(QPen(QColor("#18191a"), 1.2))
        p.setBrush(grad_tampa)
        p.drawRoundedRect(rect_tampa, 6.0, 6.0)

        # Chanfro usinado de alumínio (reflexo fino nas arestas)
        p.setPen(QPen(QColor(255, 255, 255, 60), 0.9))
        p.drawRoundedRect(rect_tampa.adjusted(0.7, 0.7, -0.7, -0.7), 5.5, 5.5)

        # Dobradiça cilíndrica central de conexão
        dobr_w, dobr_h = 76, 4.5
        dobr_x = (NOTEBOOK_W - dobr_w) / 2
        dobr_y = base_y - 2.0
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#131516"))
        p.drawRoundedRect(QRectF(dobr_x, dobr_y, dobr_w, dobr_h), 2.0, 2.0)

        # Emblema estilizado de tecnologia no centro da tampa
        cx, cy = rect_tampa.center().x(), rect_tampa.center().y() - 1.0
        p.setFont(QFont("Segoe UI Emoji", 14))

        if self.working:
            # Emblema iluminado sutilmente quando trabalhando
            p.setPen(QColor(255, 255, 255, 240))
        else:
            # Emblema cromado espelhado
            p.setPen(QColor(210, 215, 222, 175))

        p.drawText(QRectF(cx - 16, cy - 16, 32, 32), Qt.AlignCenter, "⚡")

        # Pés de borracha sutis embaixo da base
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#0e0f10"))
        p.drawRoundedRect(QRectF(base_x + 8, base_y + base_h - 1.5, 12, 2.5), 1.0, 1.0)
        p.drawRoundedRect(QRectF(base_x + base_w - 20, base_y + base_h - 1.5, 12, 2.5), 1.0, 1.0)

    # ---------------- 2. MODO APRESENTAÇÃO: NOTEBOOK VIRADO PARA NÓS (TELA VISÍVEL) ----------------

    def _desenhar_notebook_aberto(self, p: QPainter):
        """Modo virado: o pet vira o notebook para a frente para mostrar o código na tela IPS HD."""
        tampa_w, tampa_h = 124, 48
        tampa_x = (NOTEBOOK_W - tampa_w) / 2
        tampa_y = 4.0
        rect_tampa = QRectF(tampa_x, tampa_y, tampa_w, tampa_h)

        # Sombra suave da tela
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 55))
        p.drawRoundedRect(rect_tampa.translated(0, 3), 6, 6)

        # Carcaça Grafite
        grad_tampa = QLinearGradient(rect_tampa.topLeft(), rect_tampa.bottomLeft())
        grad_tampa.setColorAt(0.0, QColor("#484c50"))
        grad_tampa.setColorAt(1.0, QColor("#232527"))
        p.setPen(QPen(QColor("#18191a"), 1.2))
        p.setBrush(grad_tampa)
        p.drawRoundedRect(rect_tampa, 6, 6)

        # Tela interna
        visor = rect_tampa.adjusted(3.5, 3.5, -3.5, -3.5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#0d1117"))
        p.drawRoundedRect(visor, 3.5, 3.5)

        # Barra do Editor
        p.setBrush(QColor("#161b22"))
        p.drawRoundedRect(QRectF(visor.left(), visor.top(), visor.width(), 8.0), 3.5, 3.5)
        p.drawRect(QRectF(visor.left(), visor.top() + 4.0, visor.width(), 4.0))

        # Bolinhas de controle de janela
        p.setBrush(QColor("#ff5f56"))
        p.drawEllipse(QPointF(visor.left() + 6.0, visor.top() + 4.0), 2.2, 2.2)
        p.setBrush(QColor("#ffbd2e"))
        p.drawEllipse(QPointF(visor.left() + 12.0, visor.top() + 4.0), 2.2, 2.2)
        p.setBrush(QColor("#27c93f"))
        p.drawEllipse(QPointF(visor.left() + 18.0, visor.top() + 4.0), 2.2, 2.2)

        # Borda e webcam
        p.setBrush(QColor("#000000"))
        p.drawRoundedRect(QRectF(visor.center().x() - 6.5, visor.top(), 13.0, 3.8), 1.5, 1.5)
        p.setBrush(QColor("#34c759"))
        p.drawEllipse(QPointF(visor.center().x() + 3.0, visor.top() + 1.8), 0.7, 0.7)

        # Linhas de código
        p.setRenderHint(QPainter.Antialiasing, False)
        linhas = [
            (6, 12, "#ff7b72", 18), (28, 12, "#79c0ff", 36), (68, 12, "#7ee787", 22),
            (12, 17, "#d2a8ff", 28), (44, 17, "#ffa657", 32),
            (12, 22, "#79c0ff", 42), (58, 22, "#ff7b72", 24),
            (6, 27, "#ff7b72", 16), (26, 27, "#7ee787", 34),
        ]
        for lx, ly, lcor, lw in linhas:
            p.setBrush(QColor(lcor))
            p.drawRect(QRectF(visor.left() + lx, visor.top() + ly, lw, 2.2))
        p.setRenderHint(QPainter.Antialiasing, True)

        # Dobradiça
        dobr_w, dobr_h = 80, 4.0
        dobr_x = (NOTEBOOK_W - dobr_w) / 2
        dobr_y = tampa_y + tampa_h - 1.5
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#141517"))
        p.drawRoundedRect(QRectF(dobr_x, dobr_y, dobr_w, dobr_h), 2, 2)

        # Base do teclado
        base_top_w, base_bot_w = 126, 140
        base_top_y, base_bot_y = dobr_y + 1.2, NOTEBOOK_H - 7.0
        poly_base = QPolygonF([
            QPointF((NOTEBOOK_W - base_top_w) / 2, base_top_y),
            QPointF((NOTEBOOK_W + base_top_w) / 2, base_top_y),
            QPointF((NOTEBOOK_W + base_bot_w) / 2, base_bot_y),
            QPointF((NOTEBOOK_W - base_bot_w) / 2, base_bot_y),
        ])
        grad_base = QLinearGradient(QPointF(0, base_top_y), QPointF(0, base_bot_y))
        grad_base.setColorAt(0.0, QColor("#4c5055"))
        grad_base.setColorAt(1.0, QColor("#242628"))
        p.setPen(QPen(QColor("#1a1c1d"), 1.0))
        p.setBrush(grad_base)
        p.drawPolygon(poly_base)

        # Teclado escuro chiclet
        well_w, well_h = 104, 20.0
        well_x = (NOTEBOOK_W - well_w) / 2
        well_y = base_top_y + 2.2
        p.setPen(QPen(QColor("#111214"), 0.8))
        p.setBrush(QColor("#131416"))
        p.drawRoundedRect(QRectF(well_x, well_y, well_w, well_h), 2.0, 2.0)

        # Teclas chiclet
        for row in range(3):
            ry = well_y + 4.8 + row * 4.8
            for col in range(13 if row < 2 else 9):
                rx = well_x + 2.2 + col * 7.7
                p.setPen(QPen(QColor(255, 255, 255, 18), 0.5))
                p.setBrush(QColor("#222428"))
                p.drawRoundedRect(QRectF(rx, ry, 6.4, 4.0), 1.0, 1.0)

        # Trackpad
        track_w, track_h = 46, 8.5
        p.setPen(QPen(QColor("#45494e"), 0.7))
        p.setBrush(QColor("#2b2e31"))
        p.drawRoundedRect(QRectF((NOTEBOOK_W - track_w) / 2, well_y + well_h + 1.6, track_w, track_h), 2.0, 2.0)

    # ---------------- 3. MODO TABLET DIGITAL ----------------

    def _desenhar_tablet(self, p: QPainter):
        """Desenha um tablet em suporte de mesa: perfeito para assistir vídeos ou curtir músicas."""
        tab_w, tab_h = 112, 70
        tab_x = (NOTEBOOK_W - tab_w) / 2
        tab_y = NOTEBOOK_H - tab_h - 10.0
        rect_tab = QRectF(tab_x, tab_y, tab_w, tab_h)

        # Suporte metálico traseiro
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#212426"))
        poly_stand = QPolygonF([
            QPointF(NOTEBOOK_W / 2 - 18, tab_y + tab_h),
            QPointF(NOTEBOOK_W / 2 + 18, tab_y + tab_h),
            QPointF(NOTEBOOK_W / 2 + 28, NOTEBOOK_H - 4),
            QPointF(NOTEBOOK_W / 2 - 28, NOTEBOOK_H - 4),
        ])
        p.drawPolygon(poly_stand)

        # Sombra do tablet
        p.setBrush(QColor(0, 0, 0, 50))
        p.drawRoundedRect(rect_tab.translated(0, 3), 7, 7)

        # Carcaça de alumínio do tablet
        grad_pad = QLinearGradient(rect_tab.topLeft(), rect_tab.bottomLeft())
        grad_pad.setColorAt(0.0, QColor("#4e5257"))
        grad_pad.setColorAt(1.0, QColor("#2c2f32"))
        p.setPen(QPen(QColor("#1a1c1e"), 1.2))
        p.setBrush(grad_pad)
        p.drawRoundedRect(rect_tab, 7, 7)

        # Vidro da tela do tablet (bordas finas)
        tela = rect_tab.adjusted(4.0, 4.0, -4.0, -4.0)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#0b0d0f"))
        p.drawRoundedRect(tela, 5, 5)

        # Conteúdo na tela: player de vídeo ou ondas de música
        now = time.monotonic()
        p.setPen(Qt.NoPen)

        # Mini barra de reprodução
        p.setBrush(QColor("#ff0000"))
        p.drawRect(QRectF(tela.left() + 6, tela.bottom() - 6, (tela.width() - 12) * ((now * 0.1) % 1.0), 2.5))

        # Ícone de play vermelho de vídeo ou equalizador de música
        cx, cy = tela.center().x(), tela.center().y()
        p.setBrush(QColor("#ff0000"))
        p.drawRoundedRect(QRectF(cx - 14, cy - 10, 28, 20), 4, 4)
        # Triângulo branco de play
        p.setBrush(QColor("#ffffff"))
        tri = QPolygonF([QPointF(cx - 4, cy - 6), QPointF(cx + 6, cy), QPointF(cx - 4, cy + 6)])
        p.drawPolygon(tri)

        # Notificação sutil no topo do tablet
        p.setFont(QFont("Arial", 6))
        p.setPen(QColor(255, 255, 255, 160))
        p.drawText(QRectF(tela.left(), tela.top() + 3, tela.width(), 10), Qt.AlignCenter, "Mídia · Pestinha Player")
