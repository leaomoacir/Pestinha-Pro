"""
RODA RADIAL DE OPÇÕES (MENU INTERATIVO COM SUBMENUS) - pestinha/ui/radial_menu.py

Menu circular de alto impacto visual que surge ao segurar o botão direito sobre o pet:
  - Fatias circulares com ícones, cores e iluminação direcional (atan2)
  - Suporte completo a submenus (Diálogo com o Pet, Tecnologia/Notebook, Notícias & Datas)
  - Núcleo central com prévia da ação, descrição detalhada e botão de retorno
  - Seleção fluida por gesto: ao soltar o botão, executa a ação sob a mira
  - Cancelamento intuitivo soltando no miolo central
"""

import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from ..body.pet import overlay_flags, set_no_activate

RAIO_EXTERNO = 175.0
RAIO_INTERNO = 58.0
RAIO_CANCELAR = 44.0


# Estrutura completa de Menus e Submenus
MENUS_DEF = {
    "principal": [
        {"id": "submenu_falar", "icone": "💬", "titulo": "Conversar", "desc": "Fale com o Pestinha: sim, não, piadas e opiniões", "submenu": True, "cor": "#60b5ff"},
        {"id": "petisco", "icone": "🍪", "titulo": "Dar Petisco", "desc": "Biscoitinho que dá energia e felicidade", "cor": "#ffb347"},
        {"id": "carinho", "icone": "🥰", "titulo": "Dar Carinho", "desc": "Afago imediato, aquece o coração e sinapses", "cor": "#ff70a6"},
        {"id": "bolinha", "icone": "🎾", "titulo": "Jogar Bolinha", "desc": "Põe a bolinha de tênis física para brincar", "cor": "#70d6ff"},
        {"id": "submenu_tech", "icone": "💻", "titulo": "Notebook / Tablet", "desc": "Girar a tela, modo tablet ou notebook", "submenu": True, "cor": "#b388ff"},
        {"id": "painel", "icone": "🧠", "titulo": "Central Neural", "desc": "Abre a central completa de humor e cérebro", "cor": "#4fe387"},
        {"id": "dormir", "icone": "💤", "titulo": "Dormir / Soneca", "desc": "Pede para tirar uma soneca ou despertar", "cor": "#a0c4ff"},
        {"id": "submenu_mundo", "icone": "🌐", "titulo": "Mundo & Datas", "desc": "Notícias web e curiosidades de hoje", "submenu": True, "cor": "#00f5d4"},
    ],
    "submenu_falar": [
        {"id": "falar_sim", "icone": "👍", "titulo": "\"Sim! / Isso aí!\"", "desc": "Apoie e concorde com o que ele acabou de fazer", "cor": "#4fe387"},
        {"id": "falar_nao", "icone": "✋", "titulo": "\"Não! / Para com isso!\"", "desc": "Dê uma bronca amigável para parar travessuras", "cor": "#ff595e"},
        {"id": "falar_elogio", "icone": "⭐", "titulo": "\"Muito bem! Bom garoto!\"", "desc": "Elogie com carinho e veja ele fazer festa", "cor": "#ffd166"},
        {"id": "falar_nadaver", "icone": "😂", "titulo": "\"Nada a ver, hein!\"", "desc": "Tire uma onda amigável com a cara dele", "cor": "#ff9e00"},
        {"id": "falar_piada", "icone": "🎭", "titulo": "\"Conta uma piada!\"", "desc": "Peça uma piadinha divertida do repertório dele", "cor": "#70d6ff"},
        {"id": "falar_status", "icone": "🤔", "titulo": "\"O que tá achando?\"", "desc": "Pergunte como ele está se sentindo agora", "cor": "#b388ff"},
        {"id": "falar_querpetisco", "icone": "🍪", "titulo": "\"Quer um petisco?\"", "desc": "Ofereça comida e veja os olhinhos brilharem", "cor": "#ffb347"},
        {"id": "voltar", "icone": "🔙", "titulo": "Voltar", "desc": "Retornar ao menu radial principal", "cor": "#8d99ae"},
    ],
    "submenu_tech": [
        {"id": "tech_virar", "icone": "🔄", "titulo": "Virar a Tela", "desc": "Gira a tela do notebook entre você e ele", "cor": "#60b5ff"},
        {"id": "tech_tablet", "icone": "📱", "titulo": "Modo Tablet", "desc": "Coloca o tablet para assistir vídeos e ouvir som", "cor": "#4fe387"},
        {"id": "tech_notebook", "icone": "💻", "titulo": "Modo Notebook", "desc": "Abre o notebook com teclado", "cor": "#b388ff"},
        {"id": "tech_guardar", "icone": "📦", "titulo": "Guardar Aparelho", "desc": "Guarda o notebook/tablet na mochila", "cor": "#ff70a6"},
        {"id": "voltar", "icone": "🔙", "titulo": "Voltar", "desc": "Retornar ao menu radial principal", "cor": "#8d99ae"},
    ],
    "submenu_mundo": [
        {"id": "noticia", "icone": "📰", "titulo": "Notícias Tech", "desc": "Pesquisa as últimas novidades online agora", "cor": "#00f5d4"},
        {"id": "fala_dia", "icone": "📅", "titulo": "Falar de Hoje", "desc": "Comenta sobre a data, dia da semana ou evento", "cor": "#ffd166"},
        {"id": "voltar", "icone": "🔙", "titulo": "Voltar", "desc": "Retornar ao menu radial principal", "cor": "#8d99ae"},
    ],
}


class RadialMenu(QWidget):
    """Menu radial interativo com submenus e seleção intuitiva por mira e mouse."""

    acao_selecionada = Signal(str)
    fechado = Signal()

    def __init__(self, app):
        super().__init__(None, overlay_flags())
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)

        self.app = app
        self.diametro = int(RAIO_EXTERNO * 2 + 70)
        self.resize(self.diametro, self.diametro)

        self.menu_atual = "principal"
        self.setor_selecionado = -1
        self.aberto_em = time.monotonic()
        self.escala_anim = 1.0

        # Timer de animação suave de transição (60 FPS)
        self.timer_anim = QTimer(self)
        self.timer_anim.timeout.connect(self._step_anim)

        # Timer para abrir submenu automaticamente ao repousar o cursor (500 a 1000 ms)
        self.timer_submenu_hover = QTimer(self)
        self.timer_submenu_hover.setSingleShot(True)
        self.timer_submenu_hover.timeout.connect(self._abrir_submenu_hover)
        self._hovered_submenu_id = None

    @property
    def items(self):
        return MENUS_DEF.get(self.menu_atual, MENUS_DEF["principal"])

    @property
    def num_setores(self):
        return len(self.items)

    def showEvent(self, event):
        super().showEvent(event)
        set_no_activate(self)
        self.aberto_em = time.monotonic()
        self.escala_anim = 0.85
        self.setor_selecionado = -1
        if not self.timer_anim.isActive():
            self.timer_anim.start(16)

    def _step_anim(self):
        elapsed = time.monotonic() - self.aberto_em
        if elapsed < 0.12:
            self.escala_anim = 0.85 + (elapsed / 0.12) * 0.15
        else:
            self.escala_anim = 1.0
            self.timer_anim.stop()
        self.update()

    def abrir_no_ponto(self, centro_global, menu="principal"):
        """Posiciona o centro da roda exatamente na coordenada global informada."""
        self.menu_atual = menu
        self.setor_selecionado = -1
        self.aberto_em = time.monotonic()
        self.escala_anim = 0.88
        if not self.timer_anim.isActive():
            self.timer_anim.start(16)

        gx = centro_global.x() if hasattr(centro_global, "x") else centro_global[0]
        gy = centro_global.y() if hasattr(centro_global, "y") else centro_global[1]

        # Garante que caiba confortavelmente na tela
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = max(screen.x() + 10, min(screen.right() - self.width() - 10, int(gx - self.width() / 2)))
        y = max(screen.y() + 10, min(screen.bottom() - self.height() - 10, int(gy - self.height() / 2)))

        self.move(x, y)
        self.show()
        self.raise_()

    def calcular_setor_mouse(self, pos_local):
        """Devolve o índice da fatia apontada pelo mouse ou -1 se estiver no centro."""
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        dx = pos_local.x() - cx
        dy = pos_local.y() - cy
        dist = math.hypot(dx, dy)

        if dist < RAIO_CANCELAR or dist > RAIO_EXTERNO + 40:
            return -1

        # Ângulo de -pi a +pi; queremos 0 no topo (-90 graus)
        ang = math.atan2(dy, dx) + math.pi / 2.0
        if ang < 0:
            ang += 2 * math.pi

        tamanho_fatia = 2 * math.pi / self.num_setores
        ang_ajustado = (ang + tamanho_fatia / 2.0) % (2 * math.pi)
        indice = int(ang_ajustado / tamanho_fatia) % self.num_setores
        return indice

    def processar_posicao_mira(self, pos_local):
        """Processa a mira do mouse, abre submenus com hover de 600ms e volta se arrastar para fora."""
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        dx = pos_local.x() - cx
        dy = pos_local.y() - cy
        dist = math.hypot(dx, dy)

        # Se já estiver dentro de um submenu e o usuário arrastar para fora (dist > RAIO_EXTERNO + 40)
        # ou puxar de volta para o miolo central (dist < RAIO_CANCELAR - 5):
        if self.menu_atual != "principal":
            if dist > RAIO_EXTERNO + 45 or dist < RAIO_CANCELAR - 5:
                # Volta para o menu principal de onde veio!
                self.menu_atual = "principal"
                self.setor_selecionado = -1
                self.timer_submenu_hover.stop()
                self._hovered_submenu_id = None
                self.escala_anim = 0.95
                self.timer_anim.start(16)
                self.update()
                return

        antigo = self.setor_selecionado
        idx = self.calcular_setor_mouse(pos_local)
        self.setor_selecionado = idx

        # Se o cursor estiver sobre uma opção que possui submenu, dispara timer de 600ms
        if self.menu_atual == "principal" and 0 <= idx < len(self.items):
            item = self.items[idx]
            if item.get("submenu"):
                if self._hovered_submenu_id != item["id"]:
                    self._hovered_submenu_id = item["id"]
                    # 600 ms sobrepondo sem precisar clicar!
                    self.timer_submenu_hover.start(600)
            else:
                self.timer_submenu_hover.stop()
                self._hovered_submenu_id = None
        else:
            self.timer_submenu_hover.stop()
            self._hovered_submenu_id = None

        if antigo != self.setor_selecionado:
            self.update()

    def _abrir_submenu_hover(self):
        """Ao repousar o cursor por 600ms sobre um setor com submenu, abre automaticamente sem precisar clicar!"""
        if self.menu_atual == "principal" and 0 <= self.setor_selecionado < len(self.items):
            item = self.items[self.setor_selecionado]
            if item.get("submenu") and item["id"] in MENUS_DEF:
                self.menu_atual = item["id"]
                self.setor_selecionado = -1
                self._hovered_submenu_id = None
                self.aberto_em = time.monotonic()
                self.escala_anim = 0.92
                self.timer_anim.start(16)
                self.update()

    def mouseMoveEvent(self, event):
        self.processar_posicao_mira(event.position())

    def mouseReleaseEvent(self, event):
        """Ao soltar o botão, executa a opção selecionada ou entra no submenu."""
        if event.button() in (Qt.RightButton, Qt.LeftButton):
            idx = self.calcular_setor_mouse(event.position())
            self.fechar_com_escolha(idx)

    def fechar_com_escolha(self, idx):
        """Executa a opção ou abre o submenu."""
        if idx == -1:
            # Soltou no miolo central
            if self.menu_atual != "principal":
                # No centro de um submenu, voltar é intuitivo
                self.menu_atual = "principal"
                self.setor_selecionado = -1
                self.aberto_em = time.monotonic()
                self.escala_anim = 0.9
                self.timer_anim.start(16)
                self.update()
                return
            self.timer_anim.stop()
            self.hide()
            self.fechado.emit()
            return

        if 0 <= idx < len(self.items):
            item = self.items[idx]
            acao_id = item["id"]

            if acao_id == "voltar":
                self.menu_atual = "principal"
                self.setor_selecionado = -1
                self.aberto_em = time.monotonic()
                self.escala_anim = 0.9
                self.timer_anim.start(16)
                self.update()
                return

            if item.get("submenu", False) or acao_id in MENUS_DEF:
                # Transição para submenu
                self.menu_atual = acao_id
                self.setor_selecionado = -1
                self.aberto_em = time.monotonic()
                self.escala_anim = 0.9
                self.timer_anim.start(16)
                self.update()
                return

            # Ação final selecionada!
            self.timer_anim.stop()
            self.hide()
            self.acao_selecionada.emit(acao_id)
            self.fechado.emit()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        cx = self.width() / 2.0
        cy = self.height() / 2.0

        p.save()
        p.translate(cx, cy)
        scale = max(0.4, min(1.05, self.escala_anim))
        p.scale(scale, scale)

        # 1. Halo / Brilho de fundo com degradê suave estilo HUD
        grad_halo = QRadialGradient(0, 0, RAIO_EXTERNO + 30)
        grad_halo.setColorAt(0.0, QColor(10, 16, 13, 235))
        grad_halo.setColorAt(0.75, QColor(12, 22, 17, 210))
        grad_halo.setColorAt(1.0, QColor(5, 10, 8, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(grad_halo)
        p.drawEllipse(QPointF(0, 0), RAIO_EXTERNO + 28, RAIO_EXTERNO + 28)

        # 2. Desenho das Fatias Circulares
        ang_fatia = 360.0 / self.num_setores
        ang_inicial = -90.0 - ang_fatia / 2.0

        for i, item in enumerate(self.items):
            selecionado = (i == self.setor_selecionado)
            ang_inicio_setor = ang_inicial + i * ang_fatia
            cor_tema = QColor(item.get("cor", "#4fe387"))

            r_ext = RAIO_EXTERNO + (10.0 if selecionado else 0.0)
            r_int = RAIO_INTERNO - (2.0 if selecionado else 0.0)

            path = QPainterPath()
            path.arcMoveTo(QRectF(-r_ext, -r_ext, r_ext * 2, r_ext * 2), -ang_inicio_setor)
            path.arcTo(QRectF(-r_ext, -r_ext, r_ext * 2, r_ext * 2), -ang_inicio_setor, -ang_fatia + 1.5)
            path.arcTo(QRectF(-r_int, -r_int, r_int * 2, r_int * 2), -ang_inicio_setor - ang_fatia + 1.5, ang_fatia - 1.5)
            path.closeSubpath()

            if selecionado:
                grad_fatia = QLinearGradient(0, -r_ext, 0, r_ext)
                grad_fatia.setColorAt(0.0, cor_tema.darker(170))
                grad_fatia.setColorAt(1.0, cor_tema.darker(280))
                p.setBrush(grad_fatia)
                p.setPen(QPen(cor_tema, 2.6))
            else:
                p.setBrush(QColor(18, 28, 22, 225))
                p.setPen(QPen(QColor(38, 58, 44, 200), 1.2))

            p.drawPath(path)

            # Diferenciação visual para fatias que possuem submenu
            if item.get("submenu"):
                # 1. Arco duplo na borda externa
                p.setPen(QPen(cor_tema if selecionado else QColor(cor_tema.red(), cor_tema.green(), cor_tema.blue(), 110), 1.8, Qt.DotLine if not selecionado else Qt.SolidLine))
                p_sub = QPainterPath()
                r_sub = r_ext + (3.0 if selecionado else 2.0)
                p_sub.arcMoveTo(QRectF(-r_sub, -r_sub, r_sub * 2, r_sub * 2), -ang_inicio_setor)
                p_sub.arcTo(QRectF(-r_sub, -r_sub, r_sub * 2, r_sub * 2), -ang_inicio_setor, -ang_fatia + 1.5)
                p.drawPath(p_sub)

                # 2. Marcador chevron ▶ na ponta externa da fatia
                ang_meio_rad = math.radians(ang_inicio_setor + ang_fatia / 2.0)
                r_chev = r_ext - 13.0
                cx_ch = r_chev * math.cos(ang_meio_rad)
                cy_ch = r_chev * math.sin(ang_meio_rad)
                p.setFont(QFont("Segoe UI", 7, QFont.Bold))
                p.setPen(cor_tema if selecionado else QColor("#9cbfa6"))
                p.drawText(QRectF(cx_ch - 8, cy_ch - 8, 16, 16), Qt.AlignCenter, "▶")

            # Posição do Ícone e Rótulo
            ang_meio_rad = math.radians(ang_inicio_setor + ang_fatia / 2.0)
            r_icone = (r_int + r_ext) / 2.0
            ix = r_icone * math.cos(ang_meio_rad)
            iy = r_icone * math.sin(ang_meio_rad)

            # Emoji do setor
            p.setFont(QFont("Segoe UI Emoji", 16 if selecionado else 13))
            p.setPen(QColor("#ffffff") if selecionado else QColor("#d6e6dc"))
            p.drawText(QRectF(ix - 18, iy - 20, 36, 26), Qt.AlignCenter, item["icone"])

            # Título curto sob o ícone na fatia
            p.setFont(QFont("Segoe UI", 7, QFont.Bold if selecionado else QFont.Normal))
            p.setPen(cor_tema if selecionado else QColor("#b0c8b8"))
            titulo_curto = item["titulo"].split("/")[0].replace('"', '').strip()
            if item.get("submenu") and "▶" not in titulo_curto:
                titulo_curto += " ▶"
            p.drawText(QRectF(ix - 36, iy + 6, 72, 16), Qt.AlignCenter, titulo_curto)

        # 3. Núcleo Central (Central Hub)
        cor_destaque = QColor("#4fe387")
        if 0 <= self.setor_selecionado < len(self.items):
            cor_destaque = QColor(self.items[self.setor_selecionado].get("cor", "#4fe387"))

        p.setPen(QPen(cor_destaque if self.setor_selecionado >= 0 else QColor("#36503e"), 2.2))
        grad_hub = QRadialGradient(0, 0, RAIO_INTERNO)
        grad_hub.setColorAt(0.0, QColor("#18241c"))
        grad_hub.setColorAt(1.0, QColor("#0c140f"))
        p.setBrush(grad_hub)
        p.drawEllipse(QPointF(0, 0), RAIO_INTERNO - 2, RAIO_INTERNO - 2)

        # Informações no centro
        if 0 <= self.setor_selecionado < len(self.items):
            sel = self.items[self.setor_selecionado]
            p.setFont(QFont("Segoe UI Emoji", 18))
            p.setPen(QColor("#ffffff"))
            p.drawText(QRectF(-35, -34, 70, 30), Qt.AlignCenter, sel["icone"])

            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            p.setPen(cor_destaque)
            p.drawText(QRectF(-48, -4, 96, 20), Qt.AlignCenter | Qt.TextWordWrap, sel["titulo"])

            if sel.get("submenu"):
                # Badge indicador de submenu
                p.setBrush(cor_destaque.darker(220))
                p.setPen(QPen(cor_destaque, 1.2))
                rect_badge = QRectF(-38, 16, 76, 14)
                p.drawRoundedRect(rect_badge, 3, 3)
                p.setFont(QFont("Segoe UI", 6, QFont.Bold))
                p.setPen(QColor("#ffffff"))
                p.drawText(rect_badge, Qt.AlignCenter, "SUBMENU ▶")

                p.setFont(QFont("Segoe UI", 6))
                p.setPen(QColor("#a8c2b0"))
                p.drawText(QRectF(-48, 32, 96, 15), Qt.AlignCenter, "Solte para abrir")
            else:
                p.setFont(QFont("Segoe UI", 7))
                p.setPen(QColor("#a8c2b0"))
                p.drawText(QRectF(-50, 18, 100, 26), Qt.AlignCenter | Qt.TextWordWrap, "Solte para selecionar")
        else:
            if self.menu_atual != "principal":
                p.setFont(QFont("Segoe UI Emoji", 14))
                p.setPen(QColor("#ffffff"))
                p.drawText(QRectF(-30, -28, 60, 24), Qt.AlignCenter, "🔙")
                p.setFont(QFont("Segoe UI", 7, QFont.Bold))
                p.setPen(QColor("#8d99ae"))
                p.drawText(QRectF(-40, -2, 80, 20), Qt.AlignCenter, "Voltar")
                p.setFont(QFont("Segoe UI", 6))
                p.setPen(QColor("#6b7a70"))
                p.drawText(QRectF(-40, 18, 80, 20), Qt.AlignCenter, "ao menu principal")
            else:
                p.setFont(QFont("Segoe UI Emoji", 14))
                p.setPen(QColor("#ffffff"))
                p.drawText(QRectF(-30, -28, 60, 24), Qt.AlignCenter, "🎯")
                p.setFont(QFont("Segoe UI", 7, QFont.Medium))
                p.setPen(QColor("#7f9c87"))
                p.drawText(QRectF(-45, -2, 90, 38), Qt.AlignCenter | Qt.TextWordWrap, "Aponte a opção\nou solte p/ fechar")

        p.restore()
        p.end()
