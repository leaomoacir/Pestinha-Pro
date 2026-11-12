import json
from unittest.mock import Mock, patch
from pestinha.paths import Paths
from pestinha.sense.noticias_web import (
    carregar_cache_noticias,
    salvar_cache_noticias,
    obter_status_conexao,
    obter_noticia_fresca,
    buscar_noticias_web_sync,
    buscar_noticias_background,
)


def test_cache_salvar_e_carregar(tmp_path):
    paths = Paths(root=tmp_path)
    dados = {
        "status": "ONLINE",
        "ultima_busca": "2026-11-12 12:00:00",
        "itens": [{"titulo": "Python 3.15 lançado!", "fonte": "TabNews", "tipo": "noticia"}],
        "provedor": "Web",
        "detalhes": "Ok"
    }
    assert salvar_cache_noticias(dados, paths) is True

    carregado = carregar_cache_noticias(paths)
    assert carregado["status"] == "ONLINE"
    assert len(carregado["itens"]) == 1
    assert carregado["itens"][0]["titulo"] == "Python 3.15 lançado!"


def test_obter_status_conexao_online(tmp_path):
    paths = Paths(root=tmp_path)
    dados = {
        "status": "ONLINE",
        "ultima_busca": "2026-11-12 12:00:00",
        "itens": [{"titulo": "Notícia 1", "fonte": "Web", "tipo": "noticia"}],
        "provedor": "TabNews",
        "detalhes": "Tudo ok"
    }
    salvar_cache_noticias(dados, paths)

    online, msg = obter_status_conexao(paths)
    assert online is True
    assert "ONLINE" in msg
    assert "Itens frescos em cache: 1" in msg


def test_obter_status_conexao_offline(tmp_path):
    paths = Paths(root=tmp_path)
    dados = {
        "status": "OFFLINE",
        "ultima_busca": "2026-11-12 12:00:00",
        "itens": [],
        "provedor": "Plantão",
        "detalhes": "Sem rede"
    }
    salvar_cache_noticias(dados, paths)

    online, msg = obter_status_conexao(paths)
    assert online is False
    assert "OFFLINE" in msg


def test_obter_noticia_fresca_retorna_formatado(tmp_path):
    paths = Paths(root=tmp_path)
    dados = {
        "status": "ONLINE",
        "itens": [
            {"titulo": "Super novidade quântica!", "fonte": "TechLab", "tipo": "noticia"},
            {"titulo": "Gatos dormem 16h por dia.", "fonte": "Wiki", "tipo": "curiosidade"}
        ]
    }
    salvar_cache_noticias(dados, paths)

    fresca = obter_noticia_fresca(paths)
    assert fresca is not None
    assert any(term in fresca for term in ("Super novidade", "Gatos dormem"))


def test_busca_offline_com_erro_nao_trava(tmp_path, monkeypatch):
    paths = Paths(root=tmp_path)

    # Simula erro de conexão de rede
    def erro_url(*args, **kwargs):
        raise OSError("Sem rede")

    monkeypatch.setattr("urllib.request.urlopen", erro_url)

    res = buscar_noticias_web_sync(paths)
    assert res["status"] in ("OFFLINE", "OFFLINE_COM_CACHE")
    assert "Sem conexão" in res["detalhes"] or "Sem rede" in res["detalhes"]


def test_buscar_background_com_mock(tmp_path, monkeypatch):
    paths = Paths(root=tmp_path)
    chamou = []

    def mock_sync(p):
        chamou.append(p)
        return {"status": "ONLINE", "itens": []}

    monkeypatch.setattr("pestinha.sense.noticias_web.buscar_noticias_web_sync", mock_sync)

    callback = Mock()
    disparou = buscar_noticias_background(paths, forcar=True, callback=callback)
    assert disparou is True

