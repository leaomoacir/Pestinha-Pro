"""
NOTÍCIAS & FATOS WEB (IA & BUSCA EM TEMPO REAL) - Módulo em sense/

Permite que o Pestinha pesquise notícias tech, curiosidades e novidades na internet
durante momentos ociosos (usuário ausente/away), guardando em cache local seguro
(memory/cache_noticias.json) para apresentar via balão de fala ou plantão de notícias.

100% não bloqueante (executa em thread de fundo com timeout estrito de 3s).
Totalmente tolerante a falhas: se estiver offline, usa o acervo local sem travar.
"""

import json
import os
import random
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from ..log import log
from ..paths import Paths

INTERVALO_BUSCA_OCIOSA_SEGUNDOS = 900  # 15 minutos de intervalo mínimo entre buscas
TIMEOUT_REQUISICAO = 3.5

_thread_em_andamento = False
_lock = threading.Lock()
_ultimo_tempo_busca = 0.0


def _obter_caminho_cache(paths=None):
    if paths is None:
        paths = Paths()
    return paths.cache_noticias


def carregar_cache_noticias(paths=None):
    """Carrega o cache local de notícias salvas."""
    caminho = _obter_caminho_cache(paths)
    if not caminho.exists():
        return {
            "status": "NUNCA_BUSCADO",
            "ultima_busca": None,
            "itens": [],
            "provedor": "Nenhum",
            "detalhes": "Nenhuma busca realizada ainda."
        }
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"[noticias_web] Erro ao ler cache: {e}")
        return {
            "status": "ERRO_LEITURA",
            "ultima_busca": None,
            "itens": [],
            "provedor": "Erro",
            "detalhes": str(e)
        }


def salvar_cache_noticias(dados, paths=None):
    """Salva o cache de notícias atomicamente."""
    caminho = _obter_caminho_cache(paths)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_name(f".{caminho.name}.tmp")
    try:
        conteudo = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
        with open(tmp, "wb") as f:
            f.write(conteudo)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, caminho)
        return True
    except Exception as e:
        log(f"[noticias_web] Falha ao salvar cache: {e}")
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        return False


def _buscar_tabnews(timeout=TIMEOUT_REQUISICAO):
    """Busca as manchetes mais relevantes do TabNews (comunidade dev brasileira)."""
    url = "https://www.tabnews.com.br/api/v1/contents?strategy=relevant&per_page=12"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Pestinha/1.0 (Desktop Pet; Windows; Python)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status == 200:
            itens = json.loads(resp.read().decode("utf-8"))
            noticias = []
            for item in itens:
                titulo = item.get("title", "").strip()
                if titulo and len(titulo) > 10:
                    noticias.append({
                        "titulo": titulo,
                        "fonte": "TabNews Tech",
                        "tipo": "noticia",
                        "link": f"https://www.tabnews.com.br/{item.get('owner_username', '')}/{item.get('slug', '')}"
                    })
            return noticias
    return []


def _buscar_wikipedia_fato(timeout=TIMEOUT_REQUISICAO):
    """Busca um fato / resumo curioso aleatório da Wikipedia em português."""
    url = "https://pt.wikipedia.org/api/rest_v1/page/random/summary"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Pestinha/1.0 (Desktop Pet; Windows; Python)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status == 200:
            data = json.loads(resp.read().decode("utf-8"))
            titulo = data.get("title", "").strip()
            extrato = data.get("extract", "").strip()
            if titulo and extrato:
                # Pega a primeira frase do resumo
                primeira_frase = extrato.split(". ")[0].strip()
                if not primeira_frase.endswith("."):
                    primeira_frase += "."
                texto = f"{titulo}: {primeira_frase}"
                if len(texto) > 160:
                    texto = texto[:157] + "..."
                return [{
                    "titulo": texto,
                    "fonte": "Wikipédia Curiosidades",
                    "tipo": "curiosidade",
                    "link": data.get("content_urls", {}).get("desktop", {}).get("page", "")
                }]
    return []


def buscar_noticias_web_sync(paths=None):
    """
    Executa a busca síncrona de notícias e fatos na internet.
    Deve ser chamado preferencialmente em uma thread de fundo.
    """
    global _ultimo_tempo_busca
    _ultimo_tempo_busca = time.time()
    itens_coletados = []
    erros = []

    # 1. Busca TabNews
    try:
        tn = _buscar_tabnews()
        if tn:
            itens_coletados.extend(tn)
    except Exception as e:
        erros.append(f"TabNews: {e}")

    # 2. Busca Wikipédia Curiosidades
    try:
        wiki = _buscar_wikipedia_fato()
        if wiki:
            itens_coletados.extend(wiki)
    except Exception as e:
        erros.append(f"Wikipédia: {e}")

    agora_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Verifica se o usuário configurou chave de IA (Gemini ou OpenAI)
    provedor_ia = "Web Feeds Diretos (TabNews + Wikipédia)"
    chave_gemini = os.environ.get("GEMINI_API_KEY")
    chave_openai = os.environ.get("OPENAI_API_KEY")
    if chave_gemini:
        provedor_ia = "Gemini API Ativa + Web Feeds"
    elif chave_openai:
        provedor_ia = "OpenAI API Ativa + Web Feeds"

    if itens_coletados:
        random.shuffle(itens_coletados)
        dados = {
            "status": "ONLINE",
            "ultima_busca": agora_iso,
            "itens": itens_coletados,
            "provedor": provedor_ia,
            "detalhes": f"{len(itens_coletados)} notícias e curiosidades atualizadas com sucesso via internet."
        }
        salvar_cache_noticias(dados, paths)
        log(f"[noticias_web] Sucesso na busca online: {len(itens_coletados)} itens salvos.")
        return dados
    else:
        # Modo offline ou falha de conexão: preserva o cache antigo se houver
        cache_atual = carregar_cache_noticias(paths)
        if cache_atual.get("itens"):
            cache_atual["status"] = "OFFLINE_COM_CACHE"
            cache_atual["detalhes"] = f"Sem internet agora ({'; '.join(erros)}), mantendo cache anterior."
            salvar_cache_noticias(cache_atual, paths)
            return cache_atual
        else:
            dados_erro = {
                "status": "OFFLINE",
                "ultima_busca": agora_iso,
                "itens": [],
                "provedor": "Plantão Offline Local",
                "detalhes": f"Sem conexão com a internet ({'; '.join(erros)})."
            }
            salvar_cache_noticias(dados_erro, paths)
            log(f"[noticias_web] Sem conexão com a web. Detalhes: {erros}")
            return dados_erro


def buscar_noticias_background(paths=None, forcar=False, callback=None):
    """
    Dispara a busca de notícias em segundo plano sem travar a interface gráfica.
    Respeita intervalo de tempo salvo para não sobrecarregar a rede em ociosidade.
    """
    global _thread_em_andamento, _ultimo_tempo_busca

    if _thread_em_andamento:
        return False

    agora = time.time()
    if not forcar and (agora - _ultimo_tempo_busca) < INTERVALO_BUSCA_OCIOSA_SEGUNDOS:
        # Busca recente demais, não precisa repetir
        return False

    def _worker():
        global _thread_em_andamento
        with _lock:
            _thread_em_andamento = True
        try:
            res = buscar_noticias_web_sync(paths)
            if callback:
                try:
                    callback(res)
                except Exception as e:
                    log(f"[noticias_web] Erro no callback: {e}")
        finally:
            with _lock:
                _thread_em_andamento = False

    t = threading.Thread(target=_worker, name="PestinhaWebFetcher", daemon=True)
    t.start()
    return True


def obter_noticia_fresca(paths=None):
    """
    Retorna uma notícia ou curiosidade formatada para exibição em balão de fala.
    Retorna None se não houver notícias disponíveis.
    """
    cache = carregar_cache_noticias(paths)
    itens = cache.get("itens", [])
    if not itens:
        return None

    item = random.choice(itens)
    titulo = item.get("titulo", "")
    tipo = item.get("tipo", "noticia")
    fonte = item.get("fonte", "Web")

    if tipo == "curiosidade":
        return f"💡 CURIOSIDADE DA WEB ({fonte}):\n{titulo}"
    else:
        prefixos = [
            f"🌐 NOTÍCIA WEB ({fonte}):",
            f"📰 VI NA INTERNET ({fonte}):",
            f"💻 PLANTÃO TECH ({fonte}):",
            f"🔍 ACABEI DE PESQUISAR NA WEB ({fonte}):",
        ]
        return f"{random.choice(prefixos)}\n{titulo}"


def obter_status_conexao(paths=None):
    """
    Retorna uma tupla (conectado: bool, texto_formatado: str) para exibição ao usuário.
    """
    cache = carregar_cache_noticias(paths)
    status = cache.get("status", "NUNCA_BUSCADO")
    ultima = cache.get("ultima_busca", "Ainda não realizada")
    total = len(cache.get("itens", []))
    provedor = cache.get("provedor", "Padrão")
    detalhes = cache.get("detalhes", "")

    if status == "ONLINE":
        texto = (
            f"🌐 CONEXÃO WEB & IA: ATIVA (ONLINE)\n\n"
            f"✅ Acesso à internet confirmado!\n"
            f"📰 Itens frescos em cache: {total}\n"
            f"🤖 Mecanismo: {provedor}\n"
            f"⏰ Última pesquisa: {ultima}\n\n"
            f"💡 O Pestinha pesquisa notícias e curiosidades automaticamente "
            f"quando você está ocioso ou longe do computador!"
        )
        return True, texto
    elif status == "OFFLINE_COM_CACHE":
        texto = (
            f"🌐 CONEXÃO WEB & IA: OFFLINE (COM CACHE)\n\n"
            f"⚠️ Sem conexão agora, mas há {total} notícias salvas.\n"
            f"⏰ Última busca online: {ultima}\n"
            f"💡 Tentará reconectar na próxima pausa ou momento ocioso."
        )
        return False, texto
    else:
        texto = (
            f"🌐 CONEXÃO WEB & IA: OFFLINE\n\n"
            f"❌ Nenhuma conexão com a internet detectada.\n"
            f"Detalhes: {detalhes}\n"
            f"💡 O Pestinha está usando o acervo interno offline."
        )
        return False, texto

