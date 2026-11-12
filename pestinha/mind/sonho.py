"""
SONHO - ciclo de reflexão e geração de pensamentos durante o sono e ausência do usuário.

Só roda quando você NÃO está no computador (activity == 'AWAY') ou quando o pet dorme.
Não disputa CPU com jogos ou trabalho, não usa daemons permanentes. Gera pensamentos
frescos baseados no que você fez na sessão para ele falar quando você voltar.
"""

from ..log import log
import random
import time
from pathlib import Path
from ..store import append_line

TEMPO_MINIMO_AUSENCIA = 20.0     # s ausente para iniciar uma reflexão de sonho
COOLDOWN_SONHO = 300.0           # s (5 minutos) entre ciclos de reflexão


class SonhoController:
    """Controla os pensamentos e reflexões do pet quando o usuário se afasta ou ele dorme."""

    def __init__(self, conteudo_paths, debug_fn=lambda: False):
        self.paths = conteudo_paths
        self.debug = debug_fn
        self.ultimo_sonho = 0.0
        self.ausente_desde = None
        self.ultimas_janelas = []
        self.ultimos_programas = set()
        self.petiscos_recebidos = 0
        self.carinhos_recebidos = 0

    def registrar_contexto(self, app_name, window_title=""):
        """Registra programas e janelas da sessão ativa para alimentar as reflexões."""
        if app_name and app_name != "unknown.exe":
            self.ultimos_programas.add(app_name.lower())
        if window_title and len(window_title) > 3 and window_title not in self.ultimas_janelas:
            self.ultimas_janelas.append(window_title)
            if len(self.ultimas_janelas) > 5:
                self.ultimas_janelas.pop(0)

    def registrar_interacao(self, tipo):
        """Registra carinho ou petisco recebido na sessão."""
        if tipo == "petisco":
            self.petiscos_recebidos += 1
        elif tipo == "carinho":
            self.carinhos_recebidos += 1

    def tick(self, now, activity, asleep, notes_ref=None):
        """Verifica se é hora de sonhar/refletir durante a ausência ou sono."""
        if activity == "AWAY" or asleep:
            if self.ausente_desde is None:
                self.ausente_desde = now
            tempo_parado = now - self.ausente_desde
            if tempo_parado >= TEMPO_MINIMO_AUSENCIA and now - self.ultimo_sonho >= COOLDOWN_SONHO:
                self.sonhar(now, notes_ref)
        else:
            self.ausente_desde = None

    def sonhar(self, now, notes_ref=None):
        """Executa um ciclo de reflexão, gerando pensamentos baseados na sessão."""
        self.ultimo_sonho = now
        pensamentos = self._gerar_pensamentos()
        if not pensamentos:
            return

        # Grava os pensamentos nas memórias dinâmicas do pet
        arquivo_dinamico = getattr(self.paths, "notes", None)
        if arquivo_dinamico and hasattr(arquivo_dinamico, "parent"):
            dinamico_path = arquivo_dinamico.parent / "recadinhos_dinamicos.txt"
            for p in pensamentos:
                try:
                    append_line(dinamico_path, p)
                except OSError:
                    pass

        # Adiciona diretamente na lista em memória para ele falar na volta
        if notes_ref is not None and hasattr(notes_ref, "lines"):
            for p in pensamentos:
                if p not in notes_ref.lines:
                    notes_ref.lines.append(p)

        if self.debug():
            log(f"[sonho] o pet refletiu na ausência e gerou {len(pensamentos)} pensamentos!")

    def _gerar_pensamentos(self):
        """Gera frases inteligentes procedurais baseadas na sessão recente."""
        candidatos = []

        # Reação a petiscos recebidos
        if self.petiscos_recebidos > 0:
            candidatos.append("Aquele petisco de hoje tava bom demais... já tô com saudades 🍪")
            candidatos.append("Sonhei com uma fábrica inteira de petiscos.")
            self.petiscos_recebidos = 0

        # Reação a carinho
        if self.carinhos_recebidos >= 3:
            candidatos.append("Gostei dos carinhos de hoje. Minhas sinapses ficaram quentinhas.")
            self.carinhos_recebidos = 0

        # Reação aos programas usados
        progs = self.ultimos_programas
        if any(p in progs for p in ("code", "visual studio code", "pycharm", "cursor", "devenv")):
            candidatos.append("Vi você codando firme hoje... qualquer hora eu faço o code review.")
            candidatos.append("Seu código de hoje teve uma energia disruptiva de alto nível.")
        if any(p in progs for p in ("chrome", "msedge", "firefox", "brave")):
            candidatos.append("Tantas abas abertas... seu navegador tá pedindo socorro em silêncio.")
        if "spotify" in progs:
            candidatos.append("A trilha sonora de hoje tava inspiradora.")

        # Reação a títulos de janela específicos
        if self.ultimas_janelas:
            ultimo = self.ultimas_janelas[-1]
            if "youtube" in ultimo.lower():
                candidatos.append("Enquanto você assistia vídeo, eu calculei o ROI desse entretenimento.")
            elif "pestinha" in ultimo.lower():
                candidatos.append("Espiei você mexendo no meu próprio código... não mexe nos meus neurônios!")

        # Reflexões gerais sarcásticas e afetuosas
        gerais = [
            "Você sumiu... achei que tinha ido comprar mais memória RAM pra mim.",
            "Aproveitei que você saiu pra minerar duas moedas imaginárias na sua GPU.",
            "Quando você não tá na frente do PC, tudo fica tão silencioso...",
            "Tirei um cochilo de 470 neurônios enquanto você foi ali.",
            "Sonhei que o cursor e eu tínhamos assinado um tratado de paz.",
        ]
        candidatos.extend(random.sample(gerais, min(2, len(gerais))))
        random.shuffle(candidatos)
        return candidatos[:3]

