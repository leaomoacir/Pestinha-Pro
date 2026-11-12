"""
MIGRAÇÃO - leva a memória da versão antiga (tudo solto em memory/) para memory/pets/<pet>/.

Os sete arquivos de memória soltos são do pet que estava escolhido (o dono); cada
`<id>_nervous.json` é da rede do pet `<id>`. Para cada pet, a migração:

    1. copia cada arquivo para a pasta do pet (temporário + troca atômica) e confere que a
       cópia é idêntica byte a byte e se lê do mesmo jeito no formato real (JSON ou JSONL);
    2. se houver qualquer conflito (destino já existe com outro conteúdo) ou erro, para:
       não move nenhum original e não marca o pet como migrado;
    3. com tudo validado, move os originais para memory/legado/<pet>/ (nunca apaga nada);
    4. por último, escreve o marcador `.migrado` com o hash de cada arquivo.

Interrompida em qualquer ponto, a próxima execução retoma sem perder nada: cópias iguais
são reaproveitadas e os originais só saem do lugar depois da validação. `restaurar` desfaz.
Pastas de memória não criam personagens: os pets selecionáveis vêm só de pets/*.json.
"""

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field

from .log import log
from .paths import pet_id_valido

ARQUIVOS_DE_MEMORIA = ["episodes.jsonl", "preferences.json", "drives.json", "protest.json",
                       "sad_protest.json", "conditioning.json", "castigo.json"]
SUFIXO_REDE = "_nervous.json"


@dataclass
class Resultado:
    """Resultado da migração: o que foi migrado, o que deu conflito e o que deu erro."""
    ok: bool = True
    migrados: list = field(default_factory=list)      # (pet, arquivo) copiados e validados
    conflitos: list = field(default_factory=list)     # (pet, arquivo, motivo)
    erros: list = field(default_factory=list)         # (pet, arquivo, motivo)
    avisos: list = field(default_factory=list)        # origem ilegível já antes (copiada igual)
    pets_concluidos: list = field(default_factory=list)

    def pet_ok(self, pet_id):
        """Este pet pode usar a pasta nova (nada pendente para ele)."""
        return not any(p == pet_id for p, _a, _m in self.conflitos + self.erros)

    def resumo(self):
        """Uma linha por motivo (o mesmo erro em dez arquivos vira uma linha só)."""
        por_motivo = {}
        for p, a, m in self.conflitos + self.erros:
            por_motivo.setdefault(m, []).append(f"{p}/{a}")
        return "; ".join(f"{', '.join(arquivos)}: {m}" if len(arquivos) <= 2
                         else f"{len(arquivos)} arquivos ({arquivos[0]}...): {m}"
                         for m, arquivos in por_motivo.items())


# ---------------- leitura no formato real ----------------

def _sem_nan(valor):
    """Recusa NaN e infinito ao ler ou gravar (estragariam o JSON)."""
    raise ValueError(f"constante não permitida: {valor}")


def _ler_formato(nome, dados):
    """O que a aplicação enxerga no arquivo: um documento JSON, ou a lista de registros JSONL."""
    texto = dados.decode("utf-8", errors="replace")
    if nome.endswith(".jsonl"):
        registros = []
        for linha in texto.splitlines():
            if not linha.strip():
                continue
            try:
                registros.append(json.loads(linha, parse_constant=_sem_nan))
            except ValueError:
                registros.append(("ilegível", linha))
        return registros
    try:
        return json.loads(texto, parse_constant=_sem_nan)
    except ValueError:
        return ("ilegível", texto)


def _ilegivel(nome, conteudo):
    """Diz se um arquivo antigo não pôde ser lido (JSON ou JSONL com erro)."""
    if nome.endswith(".jsonl"):
        return any(isinstance(r, tuple) and r[0] == "ilegível" for r in conteudo)
    return isinstance(conteudo, tuple) and conteudo[0] == "ilegível"


# ---------------- escrita segura ----------------

def _gravar_atomico(destino, dados):
    """Grava num arquivo temporário e troca pelo definitivo: se cair no meio, o original não é corrompido."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(f".{destino.name}.tmp")
    with open(tmp, "wb") as f:
        f.write(dados)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, destino)


def _mover_para_legado(origem, pasta_legado):
    """Move sem sobrescrever: se já houver um arquivo com o nome, usa um sufixo numerado."""
    pasta_legado.mkdir(parents=True, exist_ok=True)
    alvo = pasta_legado / origem.name
    n = 2
    while alvo.exists():
        alvo = pasta_legado / f"{origem.stem}.{n}{origem.suffix}"
        n += 1
    os.replace(origem, alvo)
    return alvo


# ---------------- migração ----------------

def fontes_antigas(paths, dono):
    """{pet: [(origem, nome no destino)]} do que ainda está no formato antigo."""
    fontes = {}
    if not paths.memory.exists():
        return fontes
    for nome in ARQUIVOS_DE_MEMORIA:
        origem = paths.memory / nome
        if origem.is_file():
            fontes.setdefault(dono, []).append((origem, nome))
    for origem in sorted(paths.memory.glob(f"*{SUFIXO_REDE}")):
        pet_id = origem.name[: -len(SUFIXO_REDE)]
        if origem.is_file() and pet_id_valido(pet_id):
            fontes.setdefault(pet_id, []).append((origem, "nervous.json"))
    return fontes


def migrar(paths, dono):
    """Migra a memória antiga. `dono` é o pet escolhido (dono dos sete arquivos soltos)."""
    resultado = Resultado()
    for pet_id, lista in fontes_antigas(paths, dono).items():
        _migrar_pet(paths, pet_id, lista, resultado)
    resultado.ok = not (resultado.conflitos or resultado.erros)
    if resultado.migrados or not resultado.ok:
        log(f"[migração] {len(resultado.migrados)} arquivo(s) validados; pets concluídos: "
            f"{resultado.pets_concluidos or 'nenhum'}" + ("" if resultado.ok else f"; PENDENTE: {resultado.resumo()}"))
    return resultado


def _migrar_pet(paths, pet_id, lista, resultado):
    """Migra os arquivos de um pet: copia, confere cada um e só então move o original para legado/ e marca como migrado."""
    destino = paths.pet(pet_id)
    hashes = {}
    falhou = False
    # 1) copia e valida tudo antes de mexer em qualquer original
    for origem, nome in lista:
        alvo = destino.base / nome
        try:
            dados = origem.read_bytes()
            if alvo.exists():
                if alvo.read_bytes() != dados:
                    resultado.conflitos.append((pet_id, nome, "o destino já existe com outro conteúdo"))
                    falhou = True
                    continue
            else:
                _gravar_atomico(alvo, dados)
            copia = alvo.read_bytes()
            lido_origem, lido_copia = _ler_formato(nome, dados), _ler_formato(nome, copia)
            if copia != dados or lido_origem != lido_copia:
                resultado.erros.append((pet_id, nome, "a cópia não confere com a origem"))
                falhou = True
                continue
            if _ilegivel(nome, lido_origem):
                resultado.avisos.append((pet_id, nome, "já estava ilegível na origem (copiado igual)"))
            hashes[nome] = hashlib.sha256(dados).hexdigest()
            resultado.migrados.append((pet_id, nome))
        except OSError as erro:
            resultado.erros.append((pet_id, nome, f"{type(erro).__name__}: {erro}"))
            falhou = True
    if falhou:
        return
    # 2) com tudo validado, os originais vão para o legado (move, não apaga)
    try:
        for origem, _nome in lista:
            if origem.exists():
                _mover_para_legado(origem, paths.legado / pet_id)
        # 3) por último, o marcador: sem ele, a próxima execução retoma
        conteudo = {"versao": 1, "quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "arquivos": hashes}
        _gravar_atomico(destino.marcador, json.dumps(conteudo, ensure_ascii=False, indent=1).encode("utf-8"))
        resultado.pets_concluidos.append(pet_id)
    except OSError as erro:
        resultado.erros.append((pet_id, "(legado/marcador)", f"{type(erro).__name__}: {erro}"))


def restaurar(paths, pet_id):
    """Desfaz a migração: restaura a geração mais recente e preserva backups anteriores no legado."""
    pasta = paths.legado / pet_id
    devolvidos = []
    if pasta.exists():
        recentes = {}
        for arquivo in pasta.iterdir():
            if not arquivo.is_file():
                continue
            match = re.match(r"^(.*)\.(\d+)(\.[^.]+)$", arquivo.name)
            nome = f"{match.group(1)}{match.group(3)}" if match else arquivo.name
            geracao = int(match.group(2)) if match else 1
            if nome not in recentes or geracao > recentes[nome][0]:
                recentes[nome] = (geracao, arquivo)
        for nome, (_geracao, arquivo) in sorted(recentes.items()):
            alvo = paths.memory / nome
            if not alvo.exists():
                os.replace(arquivo, alvo)
                devolvidos.append(alvo.name)
    marcador = paths.pet(pet_id).marcador
    if marcador.exists():
        os.replace(marcador, marcador.with_name(".migrado.desfeito"))
    return devolvidos


# ---------------- unificação profunda de memórias ----------------

def mesclar_memorias_pets(paths, pets_origem=("bryan", "jorge"), pet_destino="pestinha"):
    """
    Unifica o histórico completo de aprendizado e episódios dos pets de origem para o pet destino.
    Combina:
      - episodes.jsonl: todos os episódios únicos ordenados cronologicamente
      - preferences.json: tabela ponderada de contexto-ação e valências médias aprendidas
      - conditioning.json: respostas a estímulos condicionados aprendidos
    Mantém intactas as pastas originais em memory/pets/<origem>/.
    """
    destino_paths = paths.pet(pet_destino)
    destino_paths.base.mkdir(parents=True, exist_ok=True)

    todas_fontes = list(pets_origem)
    if pet_destino not in todas_fontes:
        todas_fontes.append(pet_destino)

    # 1. Mesclagem de episódios
    episodes = {}
    for nome in todas_fontes:
        p_ep = paths.pet(nome).episodes
        if p_ep.exists():
            try:
                with open(p_ep, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            eid = data.get("id", line)
                            episodes[eid] = data
                        except Exception:
                            pass
            except OSError:
                pass

    if episodes:
        sorted_eps = sorted(episodes.values(), key=lambda x: x.get("quando", ""))
        conteudo_eps = "\n".join(json.dumps(ep, ensure_ascii=False) for ep in sorted_eps) + "\n"
        _gravar_atomico(destino_paths.episodes, conteudo_eps.encode("utf-8"))

    # 2. Mesclagem de preferências aprendidas
    def _combinar_contagens(dict_list):
        res = {}
        for d in dict_list:
            for k, v in d.items():
                if not isinstance(v, (list, tuple)) or len(v) < 2:
                    continue
                if k not in res:
                    res[k] = [0.0, 0.0]
                count, val = float(v[0]), float(v[1])
                res[k][0] += count
                res[k][1] += count * val
        return {k: [c, (w / c) if c > 0 else 0.0] for k, (c, w) in res.items()}

    prefs_list = []
    for nome in todas_fontes:
        p_pref = paths.pet(nome).preferences
        if p_pref.exists():
            try:
                with open(p_pref, "r", encoding="utf-8") as f:
                    prefs_list.append(json.load(f))
            except Exception:
                pass

    if prefs_list:
        todos_contextos = set()
        for p in prefs_list:
            todos_contextos.update(p.get("tabela", {}).keys())

        merged_tabela = {}
        for ctx in todos_contextos:
            dicts = [p["tabela"][ctx] for p in prefs_list if "tabela" in p and ctx in p["tabela"]]
            merged_tabela[ctx] = _combinar_contagens(dicts)

        merged_geral = _combinar_contagens([p.get("geral", {}) for p in prefs_list])
        merged_prefs = {
            "tabela": merged_tabela,
            "geral": merged_geral,
            "saved_at": time.time(),
        }
        _gravar_atomico(destino_paths.preferences, json.dumps(merged_prefs, ensure_ascii=False, indent=1).encode("utf-8"))

    # 3. Mesclagem de condicionamento
    cond_stimuli = {}
    for nome in todas_fontes:
        p_cond = paths.pet(nome).conditioning
        if p_cond.exists():
            try:
                with open(p_cond, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                    v = cdata.get("V", {})
                    for stim, val in v.items():
                        cond_stimuli[stim] = max(cond_stimuli.get(stim, 0.0), float(val))
            except Exception:
                pass

    if cond_stimuli:
        _gravar_atomico(destino_paths.conditioning, json.dumps({"V": cond_stimuli}, ensure_ascii=False).encode("utf-8"))

    log(f"[migração] Memórias unificadas em {pet_destino}: {len(episodes)} episódios, "
        f"{len(merged_tabela) if prefs_list else 0} contextos aprendidos.")
    return len(episodes)

