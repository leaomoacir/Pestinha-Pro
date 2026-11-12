"""
Testes para o módulo de sincronização e backup do pet.
"""

from pathlib import Path
from pestinha.sincronizacao import exportar_cerebro, importar_cerebro, git_pull_seguro, git_push_seguro


def test_exportar_e_importar_cerebro(tmp_path):
    origem = tmp_path / "memory" / "pets" / "pestinha"
    origem.mkdir(parents=True)
    (origem / "nervous.json").write_text('{"pesos": [1, 2, 3]}', encoding="utf-8")
    (origem / "episodes.jsonl").write_text('{"acao": "meme", "valencia": 0.8}\n', encoding="utf-8")

    destino_zip = tmp_path / "backup.zip"
    sucesso = exportar_cerebro(origem, destino_zip)
    assert sucesso is True
    assert destino_zip.exists()

    restaurado = tmp_path / "restaurado"
    sucesso_import = importar_cerebro(destino_zip, restaurado)
    assert sucesso_import is True
    assert (restaurado / "nervous.json").exists()
    assert (restaurado / "episodes.jsonl").exists()
    assert (restaurado / "nervous.json").read_text(encoding="utf-8") == '{"pesos": [1, 2, 3]}'


def test_git_sync_quando_nao_e_repo(tmp_path):
    pasta_vazia = tmp_path / "sem_git"
    pasta_vazia.mkdir()
    # Não deve dar exceção nem crashar
    assert git_pull_seguro(pasta_vazia) is False
    assert git_push_seguro(pasta_vazia) is False

