"""
FLOATS - os painéis flutuantes (monitor neural e painel de protesto).

Modo teste: ficam sempre na tela, arrastáveis. Fora dele, só aparecem quando você
abre pelo menu ou pela bandeja, e ficam até você fechar de novo (ou esconder o pet).
A bandeja pode esconder ou mostrar; o tamanho e a posição ficam salvos (paths.panels).
"""

from PySide6.QtGui import QGuiApplication

from .central_painel import CentralPainel
from .monitor import NeuralMonitor
from .panel import StrikePanel

KEYS = ("neural", "greve")


class FloatManager:
    """Guarda os painéis abertos (monitor neural autêntico e painel de protesto)."""
    def __init__(self, app):
        """Começa sem painéis abertos."""
        self.app = app
        self.windows = {}
        self.opened = set()             # painéis que você abriu à mão (menu ou bandeja)
        self.hidden_by_tray = False

    def window(self, key):
        """Devolve o painel `key`, instanciando o monitor neural autêntico ou o painel de protesto."""
        chave = "neural" if key in ("central", "neural") else key
        if chave not in self.windows:
            screen = QGuiApplication.primaryScreen().availableGeometry()
            if chave == "neural":
                self.windows["neural"] = NeuralMonitor(self.app, (screen.x() + 40, screen.y() + 40))
            elif chave == "greve":
                self.windows["greve"] = StrikePanel(self.app, (screen.x() + 60, screen.y() + 60))
        return self.windows.get(chave, self.windows.get("neural"))

    def sync(self, automatic, base):
        """
        automatic: modo teste ligado (os painéis ficam sempre na tela).
        base: o pet está ativo, não escondido e a tela cheia não atrapalha.
        """
        for key in KEYS:
            # abertos à mão aparecem sempre; os automáticos (modo teste) obedecem à bandeja
            aberto = (key in self.opened) or (key == "neural" and "central" in self.opened)
            shown = base and (aberto or (automatic and not self.hidden_by_tray))
            if shown:
                self.window(key).show()
            elif key in self.windows:
                self.windows[key].hide()

    def open(self, key):
        """Abre um painel, se o pet estiver ativo, visível e a tela não estiver cheia."""
        if not self.app.floats_base():          # desligado, escondido ou tela cheia: não abre
            return
        chave = "neural" if key in ("central", "neural") else key
        self.opened.add(chave)
        if key == "central":
            self.opened.add("central")
        w = self.window(chave)
        w.show()
        w.raise_()

    def close(self, key):
        """Fecha um painel e o esquece da lista de abertos."""
        chave = "neural" if key in ("central", "neural") else key
        self.opened.discard(key)
        self.opened.discard(chave)
        if chave in self.windows:
            self.windows[chave].hide()

    def toggle(self, key):
        """Abre o painel se estiver fechado; fecha se estiver aberto."""
        chave = "neural" if key in ("central", "neural") else key
        if chave in self.opened or key in self.opened:
            self.close(chave)
        else:
            self.open(chave)

    def toggle_tray(self, automatic, base):
        """Esconde ou mostra todos os painéis de uma vez (pelo ícone da bandeja)."""
        self.hidden_by_tray = not self.hidden_by_tray
        if self.hidden_by_tray:
            self.opened.clear()                  # "esconder painéis" fecha também os abertos à mão
        self.sync(automatic, base)

    def visible_handles(self):
        """Identificadores das janelas dos painéis visíveis (o pet não deve contá-los como janelas de outros programas)."""
        return {int(w.winId()) for w in self.windows.values() if w.isVisible()}
