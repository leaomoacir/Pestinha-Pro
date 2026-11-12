"""
SINCRONIZAÇÃO - backup, exportação, restauração e sincronização com nuvem/Git.

100% sob seu controle:
    - Exportar/Importar a memória do pet em arquivo .zip
    - Sincronização automática com repositório Git privado (se a pasta memory for um repo Git)
    - Suporte a pasta de dados local sincronizada (OneDrive, Google Drive, Dropbox, Syncthing)
"""

import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

from .log import log
from .paths import pet_id_valido


def exportar_cerebro(origem_pasta, destino_zip):
    """
    Compacta os arquivos de um pet (ou a pasta inteira de memória) em um arquivo zip.
    Devolve True se deu certo, False se falhou.
    """
    origem = Path(origem_pasta)
    destino = Path(destino_zip)
    if not origem.exists():
        return False
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
            if origem.is_file():
                zf.write(origem, origem.name)
            else:
                for raiz, _dirs, arquivos in os.walk(origem):
                    for arq in arquivos:
                        # Ignora arquivos temporários e logs antigos
                        if arq.endswith((".tmp", ".log")):
                            continue
                        caminho_completo = Path(raiz) / arq
                        relativo = caminho_completo.relative_to(origem)
                        zf.write(caminho_completo, relativo)
        return True
    except (OSError, zipfile.BadZipFile) as err:
        log(f"[sincronizacao] erro ao exportar: {err}")
        return False


def importar_cerebro(origem_zip, destino_pasta):
    """
    Restaura arquivos de memória de um zip para a pasta de destino de forma segura.
    Valida contra path-traversal e arquivos corrompidos.
    """
    origem = Path(origem_zip)
    destino = Path(destino_pasta)
    if not origem.exists() or not zipfile.is_zipfile(origem):
        return False
    destino.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(origem, "r") as zf:
            for membro in zf.infolist():
                # Proteção contra path traversal (ex.: ../../arquivo)
                alvo = (destino / membro.filename).resolve()
                if not str(alvo).startswith(str(destino.resolve())):
                    log(f"[sincronizacao] arquivo inseguro no zip ignorado: {membro.filename}")
                    continue
                if membro.is_dir():
                    alvo.mkdir(parents=True, exist_ok=True)
                else:
                    alvo.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(membro) as fonte, open(alvo, "wb") as saida:
                        shutil.copyfileobj(fonte, saida)
        return True
    except (OSError, zipfile.BadZipFile) as err:
        log(f"[sincronizacao] erro ao importar: {err}")
        return False


def git_pull_seguro(pasta_repo, timeout_s=5):
    """
    Roda 'git pull --rebase' se a pasta for um repositório git configurado.
    Não trava o app e não dá erro se estiver offline.
    """
    repo = Path(pasta_repo)
    if not (repo / ".git").exists():
        return False
    try:
        resultado = subprocess.run(
            ["git", "-C", str(repo), "pull", "--rebase"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        if resultado.returncode == 0:
            log("[sincronizacao] git pull concluído com sucesso")
            return True
        log(f"[sincronizacao] git pull não sincronizou: {resultado.stderr.strip()[:100]}")
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def git_push_seguro(pasta_repo, pet_nome="Pestinha", timeout_s=8):
    """
    Adiciona alterações, faz commit silencioso, rebase e push para o repositório remoto.
    """
    repo = Path(pasta_repo)
    if not (repo / ".git").exists():
        return False
    try:
        subprocess.run(["git", "-C", str(repo), "add", "."], capture_output=True, timeout=timeout_s)
        msg = f"Sincronização do pet: {pet_nome}"
        subprocess.run(["git", "-C", str(repo), "commit", "-m", msg], capture_output=True, timeout=timeout_s)
        # Garante que puxa novidades de outro PC antes de empurrar para evitar conflito
        subprocess.run(["git", "-C", str(repo), "pull", "--rebase", "--autostash"], capture_output=True, timeout=timeout_s)
        resultado = subprocess.run(
            ["git", "-C", str(repo), "push"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return resultado.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False

