"""Carinho: olhinhos fechados de felicidade enquanto ele recebe carinho, e voltam ao normal depois."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pestinha.body.pet_state import PetState  # noqa: E402


def test_feliz_fechado_aparece_depois_do_carinho_e_some():
    st = PetState()
    st.mark_caress(now=100.0)
    assert st.feliz_fechado(now=100.5) is True
    assert st.feliz_fechado(now=200.0) is False


def test_feliz_dura_mais_que_o_carinho():
    st = PetState()
    st.mark_caress(now=100.0)
    assert st.caressing(now=101.0) is False
    assert st.feliz_fechado(now=101.0) is True


def test_reacao_liked_e_petisco(tmp_path):
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from pestinha.core.episodic import EpisodicMemory
    from pestinha.world.objetos import NoteThing, PetiscoThing
    note = NoteThing("teste")
    p = PetiscoThing()
    assert note.liked is not None
    assert p.width() == 40
    # Valida resolução de memória como curtido com ❤️
    mem = EpisodicMemory(tmp_path / "episodes.jsonl", tmp_path / "prefs.json")
    ep = mem.start("WORK|curioso", "bilhete", thing=note)
    mem.on_liked(note, 2.5)
    assert len(mem.open) == 0
    assert len(mem.recent) == 1
    assert mem.recent[0]["valencia"] == 0.8
    assert "curtido com ❤️" in mem.recent[0]["resultado"]
    note.close()
    p.close()
