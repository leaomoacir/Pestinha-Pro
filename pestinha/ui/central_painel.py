"""
CENTRAL UNIFICADA DO PESTINHA (HUMOR, PROTESTO, CÉREBRO & MEMÓRIA) - pestinha/ui/central_painel.py

Dashboard interativo completo de alta resolução que unifica todo o ecossistema mental do pet:
  - Aba 0: 🧭 Visão Geral (Resumo 360°, mini-raster vivo, necessidades e botões de ação rápida)
  - Aba 1: 🧠 Cérebro & Sinapses (Raster completo dos 470 neurônios, habituação e motores)
  - Aba 2: 🎭 Humor & Emoções (Termômetro de insatisfação, estágio de greve, cantinho do castigo)
  - Aba 3: 📚 Memória & Conexão Web (Q-Learning de ações aprendidas, reflexos e notícias em cache)
"""

import math
import numpy as np

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen
from ..world.arrastavel import FloatingWidget

from ..config import EMOTION_NAMES
from ..core.protesto import STAGE_NAMES, STAGE_UP, MAX_GRIEVANCE
from .rotulos import nome_canal

BG = QColor("#0a0f0c")
PANEL = QColor("#111a14")
PANEL_HEADER = QColor("#16231a")
TEXT = QColor("#e0eee4")
MUTED = QColor("#7d9685")
ACCENT = QColor("#4fe387")
BORDER = QColor("#223326")
WARN = QColor("#ffb347")
RED = QColor("#ff595e")
BLUE = QColor("#60b5ff")
YELLOW = QColor("#ffd84d")
PINK = QColor("#ff70a6")

# Cor do disparo neural por tipo: 0 sensor, 1 excitatório, 2 inibitório, 3 motor
KIND_RGB = {0: (79, 179, 255), 1: (95, 224, 122), 2: (255, 140, 90), 3: (255, 216, 77)}

MOTOR_EFFECT = {
    "WANDER": "velocidade e passeios",
    "WATCH": "fixação no cursor",
    "CHEER": "pulinhos de alegria",
    "STARTLE": "pulo de susto",
    "DROWSE": "lentidão e sono",
    "ANGRY": "tremor e raiva",
    "SAD": "isolamento e desânimo",
    "SETTLE": "balanço calmo",
}


class CentralPainel(FloatingWidget):
    """Dashboard integrado de diagnóstico emocional, neural e cognitivo do pet."""

    def __init__(self, app, default_pos=None):
        screen_pos = default_pos or (80, 70)
        super().__init__(
            app,
            "painel_central",
            f"{app.nome} · Central de Humor & Monitor Neural",
            (960, 620),
            (840, 540),
            screen_pos,
        )
        self.setMouseTracking(True)
        self.aba_ativa = 0
        self.aba_hovered = -1
        self.botao_hovered = None

        self.abas = [
            ("🧭 Visão Geral", "Resumo completo 360°, necessidades e atalhos"),
            ("🧠 Cérebro & Sinapses", "Disparo dos 470 neurônios e habituação"),
            ("🎭 Humor & Greve", "Insatisfação, revoluções e cantinho"),
            ("📚 Memória & Conexão Web", "Ações aprendidas e notícias em cache"),
        ]

        self.tab_rects = []
        self.btn_rects = {}
        self.close_rect = QRectF(0, 0, 0, 0)

        # Relógio de atualização em tempo real (30 FPS suave)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(33)

    def showEvent(self, event):
        super().showEvent(event)
        self.app.brain.recording = True

    def hideEvent(self, event):
        self.app.brain.recording = False
        super().hideEvent(event)

    def mousePressEvent(self, event):
        """Alterna abas, clica em botões de ação ou arrasta o painel."""
        pos = event.position()

        # 1. Botão Fechar no canto superior direito
        if self.close_rect.contains(pos):
            self.hide()
            return

        # 2. Clique nas Abas superiores
        for i, r in enumerate(self.tab_rects):
            if r.contains(pos):
                self.aba_ativa = i
                self.update()
                return

        # 3. Botões de Ação Rápida na Aba 0
        if self.aba_ativa == 0:
            for btn_id, r in self.btn_rects.items():
                if r.contains(pos):
                    self._executar_acao_rapida(btn_id)
                    self.update()
                    return

        # 4. Caso contrário, arrasta o painel
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position()
        old_tab = self.aba_hovered
        old_btn = self.botao_hovered

        self.aba_hovered = -1
        for i, r in enumerate(self.tab_rects):
            if r.contains(pos):
                self.aba_hovered = i
                break

        self.botao_hovered = None
        if self.aba_ativa == 0:
            for btn_id, r in self.btn_rects.items():
                if r.contains(pos):
                    self.botao_hovered = btn_id
                    break

        if self.aba_hovered != old_tab or self.botao_hovered != old_btn:
            if self.aba_hovered >= 0 or self.botao_hovered or self.close_rect.contains(pos):
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            self.update()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        from ..world.arrastavel import save_position
        save_position(self.app.paths.panels, "greve", self.x(), self.y())
        save_position(self.app.paths.panels, "neural", self.x(), self.y())
        save_position(self.app.paths.panels, "painel_central", self.x(), self.y())

    def _executar_acao_rapida(self, btn_id):
        app = self.app
        if btn_id == "petisco":
            app.menu_petisco()
        elif btn_id == "carinho":
            app.menu_caress()
        elif btn_id == "bolinha":
            app.menu_place_ball()
        elif btn_id == "notebook":
            app.menu_alternar_notebook()
        elif btn_id == "noticia":
            app.menu_noticia_plantao()
        elif btn_id == "dormir":
            app.menu_sleep()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 1. Fundo geral com borda
        p.fillRect(self.rect(), BG)
        p.setPen(QPen(BORDER, 1.5))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))

        # 2. Barra de Abas Superior & Botão Fechar
        self._desenhar_cabecalho_abas(p)

        # 3. Conteúdo da aba ativa
        rect_conteudo = QRectF(16, 56, self.width() - 32, self.height() - 72)
        if self.aba_ativa == 0:
            self._desenhar_aba_visao_geral(p, rect_conteudo)
        elif self.aba_ativa == 1:
            self._desenhar_aba_neural(p, rect_conteudo)
        elif self.aba_ativa == 2:
            self._desenhar_aba_humor(p, rect_conteudo)
        else:
            self._desenhar_aba_memoria(p, rect_conteudo)

        p.end()

    # ---------------- CABEÇALHO DE ABAS ----------------

    def _desenhar_cabecalho_abas(self, p: QPainter):
        p.fillRect(QRectF(0, 0, self.width(), 48), PANEL_HEADER)
        p.setPen(BORDER)
        p.drawLine(0, 48, self.width(), 48)

        # Botão Fechar no canto direito
        self.close_rect = QRectF(self.width() - 38, 10, 28, 28)
        close_hover = self.close_rect.contains(self.mapFromGlobal(self.cursor().pos()))
        p.setBrush(QColor("#ff595e") if close_hover else QColor("#223326"))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.close_rect, 4, 4)
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.setPen(QColor("#ffffff") if close_hover else MUTED)
        p.drawText(self.close_rect, Qt.AlignCenter, "✕")

        # Abas de navegação
        self.tab_rects = []
        tab_area_w = self.width() - 60
        largura_aba = tab_area_w / len(self.abas)

        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        for i, (titulo, _desc) in enumerate(self.abas):
            rx = 12 + i * largura_aba
            rect_aba = QRectF(rx, 6, largura_aba - 8, 36)
            self.tab_rects.append(rect_aba)

            ativa = (i == self.aba_ativa)
            hover = (i == self.aba_hovered)

            if ativa:
                p.setBrush(PANEL)
                p.setPen(QPen(ACCENT, 2.0))
                p.drawRoundedRect(rect_aba, 5, 5)
                p.setPen(QColor("#ffffff"))
            elif hover:
                p.setBrush(QColor("#1a2b20"))
                p.setPen(QPen(QColor("#3d5e46"), 1.2))
                p.drawRoundedRect(rect_aba, 5, 5)
                p.setPen(TEXT)
            else:
                p.setBrush(QColor(16, 24, 19, 160))
                p.setPen(QPen(BORDER, 1.0))
                p.drawRoundedRect(rect_aba, 5, 5)
                p.setPen(MUTED)

            p.drawText(rect_aba, Qt.AlignCenter, titulo)

    # ---------------- ABA 0: VISÃO GERAL (DASHBOARD 360°) ----------------

    def _desenhar_aba_visao_geral(self, p: QPainter, rect: QRectF):
        app = self.app
        w, h = rect.width(), rect.height()
        top_h = int(h * 0.44)
        bot_h = h - top_h - 75

        # Linha 1: Três cards superiores
        card_w = (w - 24) / 3.0

        # Card 1: Estado & Emoção
        r1 = QRectF(rect.left(), rect.top(), card_w, top_h)
        self._desenhar_card(p, r1, "🐾 Estado & Emoção Atual")
        emo = app.pet_state.emotion
        nome_emo = EMOTION_NAMES.get(emo, emo).capitalize()
        icone_emo = {"feliz": "😄", "contente": "😊", "bravo": "😡", "triste": "😢", "dormindo": "💤", "observando": "👀", "curioso": "🤔"}.get(emo, "✨")

        p.setFont(QFont("Segoe UI Emoji", 26))
        p.setPen(QColor("#ffffff"))
        p.drawText(r1.left() + 20, r1.top() + 72, icone_emo)

        p.setFont(QFont("Segoe UI", 12, QFont.Bold))
        p.setPen(ACCENT)
        p.drawText(r1.left() + 70, r1.top() + 60, nome_emo)

        p.setFont(QFont("Segoe UI", 8))
        p.setPen(MUTED)
        local = "No notebook" if app.pet_state.at_desk else ("No cantinho" if app.castigo.dentro else "Passeando livre")
        p.drawText(r1.left() + 70, r1.top() + 78, f"Status: {local}")

        p.setFont(QFont("Segoe UI", 8))
        p.setPen(TEXT)
        detalhes_pet = (
            f"• No chão: {'Sim' if app.pet.body.grounded else 'No ar / pulando'}\n"
            f"• Segurado pelo mouse: {'Sim' if app.pet.body.held else 'Não'}\n"
            f"• Modo de sono: {'Dormindo zzz' if app.sleep.asleep else 'Acordado ativo'}"
        )
        p.drawText(QRectF(r1.left() + 18, r1.top() + 102, r1.width() - 36, 75), Qt.AlignLeft | Qt.TextWordWrap, detalhes_pet)

        # Card 2: Termômetro de Insatisfação & Greve
        r2 = QRectF(rect.left() + card_w + 12, rect.top(), card_w, top_h)
        self._desenhar_card(p, r2, "🚨 Insatisfação & Greve")
        pr = app.protest
        estagio = pr.stage
        nomes_estagio = ["0 - Calmo", "1 - Reclamação", "2 - Manifestação", "3 - Greve Geral", "4 - Revolução"]
        cor_estagio = ACCENT if estagio == 0 else (WARN if estagio < 3 else RED)

        p.setFont(QFont("Segoe UI", 9))
        p.setPen(TEXT)
        p.drawText(r2.left() + 18, r2.top() + 54, "Estágio de Greve:")
        p.setPen(cor_estagio)
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(r2.left() + 130, r2.top() + 54, nomes_estagio[min(estagio, 4)])

        pct = min(1.0, max(0.0, pr.grievance / MAX_GRIEVANCE))
        bar_r = QRectF(r2.left() + 18, r2.top() + 70, r2.width() - 36, 16)
        p.setBrush(QColor("#18231c"))
        p.setPen(BORDER)
        p.drawRoundedRect(bar_r, 4, 4)
        p.setBrush(cor_estagio)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(bar_r.left() + 1, bar_r.top() + 1, (bar_r.width() - 2) * pct, bar_r.height() - 2), 3, 3)

        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.setPen(QColor("#ffffff"))
        p.drawText(bar_r, Qt.AlignCenter, f"{pct * 100:.0f}% ({pr.grievance:.1f}/{MAX_GRIEVANCE})")

        p.setFont(QFont("Segoe UI", 8))
        p.setPen(MUTED)
        p.drawText(QRectF(r2.left() + 18, r2.top() + 98, r2.width() - 36, 80), Qt.AlignLeft | Qt.TextWordWrap,
                   f"• Revoluções já feitas: {pr.revolutions}\n"
                   f"• Cantinho do castigo: {'PRESO' if app.castigo.dentro else 'Livre'}\n"
                   f"• Dica: Dê carinho ou brinque de bolinha para acalmá-lo.")

        # Card 3: Necessidades Homeostáticas
        r3 = QRectF(rect.left() + (card_w + 12) * 2, rect.top(), card_w, top_h)
        self._desenhar_card(p, r3, "❤️ Necessidades Vitais")
        drives = app.drives
        drives_list = [
            ("⚡ Energia", drives.energy, "#4fe387"),
            ("🎯 Estímulo", drives.stimulation, "#60b5ff"),
            ("💖 Afeição", drives.affection, "#ff70a6"),
        ]
        dy = r3.top() + 48
        for rot, val, cor in drives_list:
            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            p.setPen(TEXT)
            p.drawText(r3.left() + 18, dy + 11, rot)

            br = QRectF(r3.left() + 95, dy, r3.width() - 115, 14)
            p.setBrush(QColor("#18231c"))
            p.setPen(BORDER)
            p.drawRoundedRect(br, 3, 3)
            p.setBrush(QColor(cor))
            p.setPen(Qt.NoPen)
            v_cl = min(1.0, max(0.0, float(val)))
            p.drawRoundedRect(QRectF(br.left() + 1, br.top() + 1, (br.width() - 2) * v_cl, br.height() - 2), 2, 2)

            p.setFont(QFont("Segoe UI", 7, QFont.Bold))
            p.setPen(QColor("#ffffff"))
            p.drawText(br, Qt.AlignCenter, f"{v_cl * 100:.0f}%")
            dy += 34

        # Linha 2: Mini-Raster Cerebral à esquerda e Conexão Web à direita
        mid_y = rect.top() + top_h + 12
        esq_w = int(w * 0.58)
        dir_w = w - esq_w - 12

        # Mini-Raster vivo
        r_raster = QRectF(rect.left(), mid_y, esq_w, bot_h)
        self._desenhar_card(p, r_raster, "⚡ Mini-Osciloscópio Neural (Últimos disparos em tempo real)")
        self._desenhar_mini_raster(p, QRectF(r_raster.left() + 14, r_raster.top() + 40, r_raster.width() - 28, r_raster.height() - 50))

        # Conexão Web & Notícias
        r_web = QRectF(rect.left() + esq_w + 12, mid_y, dir_w, bot_h)
        self._desenhar_card(p, r_web, "🌐 Conexão Web & IA")
        from ..sense.noticias_web import carregar_cache_noticias
        cache = carregar_cache_noticias(app.paths)
        status_web = cache.get("status", "ONLINE")
        itens = cache.get("itens", [])
        cor_web = ACCENT if "ONLINE" in status_web else (WARN if "CACHE" in status_web else RED)

        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(cor_web)
        p.drawText(r_web.left() + 18, r_web.top() + 52, f"Status: {status_web}")

        p.setFont(QFont("Segoe UI", 8))
        p.setPen(MUTED)
        p.drawText(r_web.left() + 18, r_web.top() + 70, f"Última busca: {cache.get('ultima_busca', 'Agora pouco')}")

        p.setPen(TEXT)
        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.drawText(r_web.left() + 18, r_web.top() + 94, "Última manchete em cache:")
        p.setFont(QFont("Segoe UI", 8))
        if itens:
            manch = itens[0].get("titulo", "")
            if len(manch) > 48:
                manch = manch[:46] + "..."
            p.drawText(QRectF(r_web.left() + 18, r_web.top() + 108, r_web.width() - 36, 40), Qt.AlignLeft | Qt.TextWordWrap, f"\"{manch}\"")
        else:
            p.drawText(r_web.left() + 18, r_web.top() + 112, "Pronto para buscar novas novidades.")

        # Linha 3: Barra de Ações Rápidas Clicáveis
        bar_btn_y = rect.bottom() - 56
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(TEXT)
        p.drawText(rect.left(), bar_btn_y - 6, "Ações Rápidas (Clique para interagir diretamente com o Pestinha):")

        botoes = [
            ("petisco", "🍪 Dar Petisco", "#ffb347"),
            ("carinho", "🥰 Fazer Carinho", "#ff70a6"),
            ("bolinha", "🎾 Jogar Bolinha", "#70d6ff"),
            ("notebook", "💻 Alternar Notebook", "#b388ff"),
            ("noticia", "🌐 Buscar Notícias", "#00f5d4"),
            ("dormir", "💤 Tirar Soneca", "#a0c4ff"),
        ]

        self.btn_rects = {}
        bw = (w - (len(botoes) - 1) * 8) / len(botoes)
        for idx, (btn_id, label, cor_btn) in enumerate(botoes):
            bx = rect.left() + idx * (bw + 8)
            rect_b = QRectF(bx, bar_btn_y, bw, 36)
            self.btn_rects[btn_id] = rect_b

            is_hov = (self.botao_hovered == btn_id)
            c = QColor(cor_btn)
            p.setBrush(c.darker(160) if is_hov else QColor("#142018"))
            p.setPen(QPen(c if is_hov else BORDER, 1.8 if is_hov else 1.0))
            p.drawRoundedRect(rect_b, 5, 5)

            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            p.setPen(QColor("#ffffff") if is_hov else c)
            p.drawText(rect_b, Qt.AlignCenter, label)

    def _desenhar_mini_raster(self, p: QPainter, box: QRectF):
        """Desenha uma versão compacta e dinâmica do raster cerebral."""
        brain = self.app.brain
        p.fillRect(box, QColor("#080c09"))
        p.setPen(BORDER)
        p.drawRect(box)

        bins = list(brain.raster)
        if bins:
            fired = np.stack(bins, axis=1)
            T = fired.shape[1]
            rgb = np.zeros((brain.N, T, 3), dtype=np.uint8)
            rgb[:] = (12, 18, 14)
            for kind, color in KIND_RGB.items():
                rows = brain.kind == kind
                rgb[rows] = np.where(fired[rows][..., None], np.array(color, dtype=np.uint8), rgb[rows])
            data = np.ascontiguousarray(rgb)
            img = QImage(data.data, T, brain.N, 3 * T, QImage.Format_RGB888)
            width = box.width() * min(1.0, T / max(1, brain.raster.maxlen))
            target = QRectF(box.right() - width, box.top(), width, box.height())
            p.drawImage(target, img)
        else:
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(MUTED)
            p.drawText(box, Qt.AlignCenter, "Integrando disparos sinápticos...")

    # ---------------- ABA 1: CÉREBRO & RASTER COMPLETO ----------------

    def _desenhar_aba_neural(self, p: QPainter, rect: QRectF):
        app = self.app
        brain = app.brain
        w, h = rect.width(), rect.height()

        split = int(w * 0.58)
        # Metade Esquerda: Raster Plot completo dos 470 neurônios
        r_esq = QRectF(rect.left(), rect.top(), split - 12, h)
        self._desenhar_card(p, r_esq, "⚡ Disparos dos 470 Neurônios (Raster · Últimos 3 segundos)")

        label_w = 90
        box = QRectF(r_esq.left() + label_w + 10, r_esq.top() + 42, r_esq.width() - label_w - 20, r_esq.height() - 54)
        p.fillRect(box, QColor("#080c09"))

        bins = list(brain.raster)
        if bins:
            fired = np.stack(bins, axis=1)
            T = fired.shape[1]
            rgb = np.zeros((brain.N, T, 3), dtype=np.uint8)
            rgb[:] = (14, 20, 16)
            for kind, color in KIND_RGB.items():
                rows = brain.kind == kind
                rgb[rows] = np.where(fired[rows][..., None], np.array(color, dtype=np.uint8), rgb[rows])
            data = np.ascontiguousarray(rgb)
            img = QImage(data.data, T, brain.N, 3 * T, QImage.Format_RGB888)
            width = box.width() * min(1.0, T / max(1, brain.raster.maxlen))
            target = QRectF(box.right() - width, box.top(), width, box.height())
            p.drawImage(target, img)

        # Nomes e faixas das populações neuronais
        p.setFont(QFont("Segoe UI", 7))
        row_h = box.height() / max(1, brain.N)
        for pool in brain.pools:
            y0 = box.top() + pool["start"] * row_h
            p.setPen(QColor(34, 48, 38))
            p.drawLine(int(box.left()), int(y0), int(box.right()), int(y0))
            if pool["n"] * row_h >= 6:
                color = {"sensory": BLUE, "motor": YELLOW}.get(pool["group"], TEXT)
                p.setPen(color)
                p.drawText(QRectF(r_esq.left() + 10, y0 - 1, label_w, max(12, pool["n"] * row_h)),
                           Qt.AlignRight | Qt.AlignVCenter, pool["name"])

        # Metade Direita: Motores, Sinapses e Canais
        r_dir = QRectF(rect.left() + split, rect.top(), w - split, h)
        self._desenhar_card(p, r_dir, "🎮 Motores & Eficácia Sináptica (Habituação)")

        my = r_dir.top() + 48
        motor_rates = brain.rates

        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.setPen(YELLOW)
        p.drawText(r_dir.left() + 16, my, "Atividade dos Motores (Hz):")
        my += 18

        for mot_nome, efeito in list(MOTOR_EFFECT.items())[:8]:
            taxa = motor_rates.get(mot_nome, 0.0)
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(TEXT)
            p.drawText(r_dir.left() + 16, my + 10, f"{mot_nome}")

            rect_mb = QRectF(r_dir.left() + 85, my, r_dir.width() - 170, 12)
            p.setBrush(QColor("#18231c"))
            p.setPen(BORDER)
            p.drawRoundedRect(rect_mb, 2, 2)

            fill_m = min(1.0, taxa / 40.0) * (rect_mb.width() - 2)
            p.setBrush(YELLOW)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(rect_mb.left() + 1, rect_mb.top() + 1, fill_m, rect_mb.height() - 2), 2, 2)

            p.setFont(QFont("Segoe UI", 7))
            p.setPen(MUTED)
            p.drawText(rect_mb.right() + 8, my + 10, f"{taxa:.1f} Hz")
            my += 26

        # Neurotransmissores
        my += 10
        p.setPen(BORDER)
        p.drawLine(r_dir.left() + 16, my, r_dir.right() - 16, my)
        my += 16

        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.setPen(ACCENT)
        p.drawText(r_dir.left() + 16, my, "Neurotransmissores & Balanço Biológico:")
        my += 18

        neuro = [
            ("Dopamina (Recompensa/Exploração)", app.drives.stimulation, "#4fe387"),
            ("Serotonina (Satisfação/Paz)", 1.0 - app.protest.grievance / MAX_GRIEVANCE, "#60b5ff"),
            ("Adrenalina (Susto/Alerta)", app.pet_state.shake / 6.0, "#ff595e"),
        ]
        for n_rot, n_val, n_cor in neuro:
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(TEXT)
            p.drawText(r_dir.left() + 16, my + 10, n_rot)
            my += 14

            br_n = QRectF(r_dir.left() + 16, my, r_dir.width() - 32, 10)
            p.setBrush(QColor("#18231c"))
            p.setPen(BORDER)
            p.drawRoundedRect(br_n, 2, 2)
            p.setBrush(QColor(n_cor))
            p.setPen(Qt.NoPen)
            val_cl = min(1.0, max(0.0, float(n_val)))
            p.drawRoundedRect(QRectF(br_n.left() + 1, br_n.top() + 1, (br_n.width() - 2) * val_cl, br_n.height() - 2), 2, 2)
            my += 22

    # ---------------- ABA 2: HUMOR & GREVE DETALHADA ----------------

    def _desenhar_aba_humor(self, p: QPainter, rect: QRectF):
        app = self.app
        col_w = (rect.width() - 16) / 2.0
        y = rect.top()

        # Coluna Esquerda: Termômetro e Greve
        r_esq = QRectF(rect.left(), y, col_w, rect.height())
        self._desenhar_card(p, r_esq, "🚨 Termômetro de Insatisfação & Greve Geral")

        pr = app.protest
        estagio = pr.stage
        nomes_estagio = ["0 - Calmo", "1 - Reclamação", "2 - Manifestação", "3 - Greve Geral", "4 - Revolução"]
        cor_estagio = ACCENT if estagio == 0 else (WARN if estagio < 3 else RED)

        p.setFont(QFont("Segoe UI", 9))
        p.setPen(TEXT)
        p.drawText(r_esq.left() + 18, r_esq.top() + 52, "Estágio Atual:")
        p.setPen(cor_estagio)
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(r_esq.left() + 115, r_esq.top() + 52, nomes_estagio[min(estagio, 4)])

        pct = min(1.0, max(0.0, pr.grievance / MAX_GRIEVANCE))
        bar_rect = QRectF(r_esq.left() + 18, r_esq.top() + 72, r_esq.width() - 36, 18)
        p.setBrush(QColor("#18231c"))
        p.setPen(BORDER)
        p.drawRoundedRect(bar_rect, 4, 4)

        fill_w = (bar_rect.width() - 2) * pct
        p.setBrush(cor_estagio)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(bar_rect.left() + 1, bar_rect.top() + 1, fill_w, bar_rect.height() - 2), 3, 3)

        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.setPen(QColor("#ffffff"))
        p.drawText(bar_rect, Qt.AlignCenter, f"{pct * 100:.1f}% insatisfação ({pr.grievance:.1f}/{MAX_GRIEVANCE})")

        p.setFont(QFont("Segoe UI", 8))
        p.setPen(MUTED)
        detalhes_greve = (
            f"• Revoluções já feitas: {pr.revolutions}\n"
            f"• Cartazes colados na tela: {len(getattr(app.protest_ctl, 'signs_active', []))}\n"
            f"• Quando o Pestinha fica muito tempo sozinho ou sem carinho, a insatisfação sobe.\n"
            f"• Ao atingir o estágio 3 ou 4, ele entra em greve e recusa comandos de trabalho!"
        )
        p.drawText(QRectF(r_esq.left() + 18, r_esq.top() + 104, r_esq.width() - 36, 90), Qt.AlignLeft | Qt.TextWordWrap, detalhes_greve)

        castigo_y = r_esq.top() + 210
        p.setPen(BORDER)
        p.drawLine(r_esq.left() + 18, castigo_y, r_esq.right() - 18, castigo_y)

        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(TEXT)
        p.drawText(r_esq.left() + 18, castigo_y + 24, "Cantinho do Castigo:")
        esta_preso = app.castigo.dentro
        p.setPen(RED if esta_preso else ACCENT)
        p.drawText(r_esq.left() + 155, castigo_y + 24, "DE CASTIGO" if esta_preso else "Livre pela tela")

        p.setFont(QFont("Segoe UI", 8))
        p.setPen(MUTED)
        p.drawText(QRectF(r_esq.left() + 18, castigo_y + 38, r_esq.width() - 36, 60),
                   Qt.AlignLeft | Qt.TextWordWrap,
                   f"Fugas bem-sucedidas: {app.castigo.vitorias.get('fugir', 0):.0f} | Rancor acumulado: {app.castigo.rancor:.2f}\n"
                   f"Quanto mais ele foge do cantinho, mais esperto e rápido ele fica para escapar.")

        # Coluna Direita: Sentimentos e Drives
        r_dir = QRectF(rect.left() + col_w + 16, y, col_w, rect.height())
        self._desenhar_card(p, r_dir, "❤️ Sentimentos, Emoções & Homeostase")

        emocao = app.pet_state.emotion
        nome_emo = EMOTION_NAMES.get(emocao, emocao).capitalize()
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.setPen(TEXT)
        p.drawText(r_dir.left() + 18, r_dir.top() + 52, f"Emoção Ativa no Momento: {nome_emo}")

        drives = app.drives
        necessidades = [
            ("Energia (Sono)", drives.energy, "#4fe387", "Recarrega dormindo ou descansando"),
            ("Estimulação (Novidades)", drives.stimulation, "#60b5ff", "Sobe com brincadeiras e trabalho"),
            ("Carência (Carinho & Petisco)", 1.0 - drives.affection, "#ffb347", "Satisfeito com cafuné e comidinha"),
        ]

        bar_y = r_dir.top() + 75
        for rotulo, val, cor_hex, dica in necessidades:
            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            p.setPen(TEXT)
            p.drawText(r_dir.left() + 18, bar_y + 12, rotulo)

            rect_b = QRectF(r_dir.left() + 18, bar_y + 18, r_dir.width() - 36, 14)
            p.setBrush(QColor("#18231c"))
            p.setPen(BORDER)
            p.drawRoundedRect(rect_b, 3, 3)

            p.setBrush(QColor(cor_hex))
            p.setPen(Qt.NoPen)
            val_clamp = min(1.0, max(0.0, float(val)))
            p.drawRoundedRect(QRectF(rect_b.left() + 1, rect_b.top() + 1, (rect_b.width() - 2) * val_clamp, rect_b.height() - 2), 2, 2)

            p.setFont(QFont("Segoe UI", 7))
            p.setPen(MUTED)
            p.drawText(QRectF(r_dir.left() + 18, bar_y + 35, r_dir.width() - 36, 16), Qt.AlignRight, f"{val_clamp * 100:.0f}% · {dica}")
            bar_y += 54

    # ---------------- ABA 3: MEMÓRIA, Q-LEARNING & WEB ----------------

    def _desenhar_aba_memoria(self, p: QPainter, rect: QRectF):
        app = self.app
        col_w = (rect.width() - 16) / 2.0

        # Coluna Esquerda: Q-Learning
        r_esq = QRectF(rect.left(), rect.top(), col_w, rect.height())
        self._desenhar_card(p, r_esq, "📊 Preferências Aprendidas (Q-Learning / Reforço)")

        p.setFont(QFont("Segoe UI", 8))
        prefs = app.memory.learned if hasattr(app, "memory") else {}
        geral = prefs.get("geral", {})

        py = r_esq.top() + 50
        p.setPen(MUTED)
        p.drawText(r_esq.left() + 18, py, "Ação")
        p.drawText(r_esq.left() + 130, py, "Vezes Feita")
        p.drawText(r_esq.left() + 230, py, "Valência Média (Seu Feedback)")
        py += 18

        for acao, dados in list(geral.items())[:6]:
            contagem, valencia = dados[0], dados[1]
            p.setPen(TEXT)
            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            p.drawText(r_esq.left() + 18, py, acao)

            p.setFont(QFont("Segoe UI", 8))
            p.drawText(r_esq.left() + 145, py, f"{contagem:.0f}")

            cor_val = ACCENT if valencia > 0.05 else (RED if valencia < -0.05 else MUTED)
            p.setPen(cor_val)
            sinal = "+" if valencia > 0 else ""
            p.drawText(r_esq.left() + 250, py, f"{sinal}{valencia:.2f}")

            py += 24

        py += 15
        p.setPen(BORDER)
        p.drawLine(r_esq.left() + 18, py, r_esq.right() - 18, py)
        py += 22

        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(TEXT)
        p.drawText(r_esq.left() + 18, py, "Estímulos Condicionados (Pavlov):")
        py += 20
        cond_v = app.conditioning.V if hasattr(app, "conditioning") else {}
        p.setFont(QFont("Segoe UI", 8))
        for k, v in cond_v.items():
            p.setPen(TEXT)
            p.drawText(r_esq.left() + 22, py, f"{k}: {v:.2f}")
            py += 18

        # Coluna Direita: Notícias Web & Cache
        r_dir = QRectF(rect.left() + col_w + 16, rect.top(), col_w, rect.height())
        self._desenhar_card(p, r_dir, "🌐 Conexão Web & Notícias em Cache")

        from ..sense.noticias_web import carregar_cache_noticias
        cache = carregar_cache_noticias(app.paths)
        status = cache.get("status", "ONLINE")
        itens = cache.get("itens", [])

        status_cor = ACCENT if "ONLINE" in status else (WARN if "CACHE" in status else RED)
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.setPen(status_cor)
        p.drawText(r_dir.left() + 18, r_dir.top() + 52, f"Status da Conexão: {status}")

        p.setFont(QFont("Segoe UI", 8))
        p.setPen(MUTED)
        p.drawText(r_dir.left() + 18, r_dir.top() + 72, f"Última busca: {cache.get('ultima_busca', 'Nenhuma')}")
        p.drawText(r_dir.left() + 18, r_dir.top() + 88, f"Provedor: {cache.get('provedor', 'Padrão')} ({len(itens)} notícias)")

        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.setPen(TEXT)
        p.drawText(r_dir.left() + 18, r_dir.top() + 120, "Manchetes & Fatos Salvos:")

        ny = r_dir.top() + 142
        for item in itens[:5]:
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(TEXT)
            tit = item.get("titulo", "")
            if len(tit) > 50:
                tit = tit[:48] + "..."
            p.drawText(r_dir.left() + 18, ny, f"• {tit}")
            p.setPen(MUTED)
            p.drawText(r_dir.left() + 30, ny + 14, f"Fonte: {item.get('fonte', 'Web')}")
            ny += 36

    # ---------------- UTILITÁRIOS ----------------

    def _desenhar_card(self, p: QPainter, rect: QRectF, titulo: str):
        """Desenha a moldura de um card de seção."""
        p.setBrush(PANEL)
        p.setPen(QPen(BORDER, 1.2))
        p.drawRoundedRect(rect, 6, 6)

        p.fillRect(QRectF(rect.left(), rect.top(), rect.width(), 32), PANEL_HEADER)
        p.setPen(BORDER)
        p.drawLine(rect.left(), rect.top() + 32, rect.right(), rect.top() + 32)

        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(TEXT)
        p.drawText(rect.left() + 14, rect.top() + 21, titulo)
