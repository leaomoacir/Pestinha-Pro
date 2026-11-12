"""
CONTEXTO & SAZONAL - Análise sensorial de datas comemorativas, estilos musicais e notícias.

Camada `sense`:
- Detecta datas sazonais: São João / Festa Junina, Natal, Ano Novo, Carnaval, Páscoa, Halloween, Dia do Dev.
- Analisa o contexto da janela ativa: estilo musical (Rock, Lo-Fi, Pop/Funk/Eletrônica, Sertanejo), streaming de vídeo e desenvolvimento.
- Catálogo de notícias tech dinâmicas e curiosidades ("Plantão do Pestinha").
"""

from datetime import datetime
import os
import random

# ============================================================
# DATAS COMEMORATIVAS & EVENTOS SAZONAIS
# ============================================================

def obter_evento_sazonal(dt=None):
    """
    Retorna o evento comemorativo ativo na data atual (ou dt fornecido).
    Permite também forçar via variável de ambiente PESTINHA_EVENTO (para testes/degustação).
    """
    forcado = os.environ.get("PESTINHA_EVENTO")
    if forcado:
        return forcado.lower()

    if dt is None:
        dt = datetime.now()

    m, d = dt.month, dt.day

    # Ano Novo / Réveillon (30/dez a 03/jan)
    if (m == 12 and d >= 30) or (m == 1 and d <= 3):
        return "ano_novo"

    # Carnaval (fevereiro ou início de março)
    if (m == 2 and 10 <= d <= 28) or (m == 3 and d <= 5):
        return "carnaval"

    # Páscoa (meados de março até abril)
    if (m == 3 and d >= 22) or (m == 4 and d <= 25):
        return "pascoa"

    # São João / Festa Junina (todo o mês de junho)
    if m == 6:
        return "sao_joao"

    # Dia do Programador (dia 256 do ano: 12 ou 13 de setembro)
    dia_ano = dt.timetuple().tm_yday
    if dia_ano == 256 or (m == 9 and d in (12, 13)):
        return "programador"

    # Halloween / Dia das Bruxas (25 a 31 de outubro)
    if m == 10 and d >= 25:
        return "halloween"

    # Natal (10 a 26 de dezembro)
    if m == 12 and 10 <= d <= 26:
        return "natal"

    return None


FALAS_SAZONAIS = {
    "sao_joao": [
        "Olha a chuva! É mentira, é commit na main! 🔥",
        "Pula a fogueira, iaiá! Cuidado pra não queimar a produção! 🌽",
        "Arraiá do Pestinha: hoje tem quentão, milho e zero bugs! 🪗",
        "Quem não dança quadrilha vira estagiário de suporte! 🌽✨",
        "Anarriê! Todo mundo pro deploy de sexta! 🔥",
    ],
    "natal": [
        "Ho ho ho! O Papai Noel trouxe 0 warnings no build! 🎅🎄",
        "Pisca-pisca ligado e servidor no ar! 🎁✨",
        "Quem passar o Natal debogando ganha carvão! 🎅",
        "Troco panetone por code review aprovado sem comentários! 🎄",
    ],
    "ano_novo": [
        "Feliz Ano Novo! Novas metas, velhos repositórios! 🥂✨",
        "Esse ano o refactor finalmente sai da promessa! 🍾",
        "Adeus 2026, a meta de 2027 é dormir 8 horas por dia! 🎉",
        "3... 2... 1... Deploy comemorativo de réveillon! 🎆",
    ],
    "carnaval": [
        "Não me chame de bug, me chame de bloquinho! 🎭🎉",
        "Atrás do trio elétrico só não vai quem já deployou! 🥁",
        "Fantasia de dev sênior: olheiras e xícara de café! 🎊",
        "Só volto a codar na quarta-feira de cinzas! 🎭",
    ],
    "pascoa": [
        "Troco ovo de páscoa por PR aprovada sem conflito! 🐰🍫",
        "Coelhinho da Páscoa, o que trazes pra mim? Um merge limpo! 🥚",
        "Caça aos ovos? Aqui a gente caça é memory leak! 🐰",
    ],
    "halloween": [
        "Doces ou travessuras? Se não der petisco eu fecho a IDE! 🎃👻",
        "Cuidado com o código zumbi que roda sem ninguém saber por quê! 🦇",
        "O monstro debaixo da cama se chama dívida técnica! 🎃⚡",
    ],
    "programador": [
        "0x100! Feliz Dia do Programador! 256 dias de código puro! 💻⚡",
        "Café, bugs e cafeína: o ciclo termodinâmico da vida! ☕🚀",
        "Hoje é dia oficial de ignorar avisos do linter! 👾",
    ],
}


# ============================================================
# RECONHECIMENTO DE CONTEXTO: MÚSICA, STREAMING E TRABALHO
# ============================================================

PALAVRAS_CHAVE_MUSICA = {
    "rock": [
        "rock", "metal", "metallica", "iron maiden", "ac/dc", "slipknot", "linkin park",
        "nirvana", "punk", "guitar", "led zeppelin", "black sabbath", "queen", "ramones",
        "system of a down", "audioslave", "guns n' roses", "foo fighters", "avenged sevenfold"
    ],
    "lofi": [
        "lofi", "lo-fi", "chill", "jazz", "bossa", "relax", "study", "beats", "piano",
        "coffee", "synthwave", "ambient", "sleep", "calm", "meditation", "chilledcow"
    ],
    "pop_funk": [
        "pop", "funk", "dance", "edm", "remix", "sertanejo", "pagode", "eletrônica",
        "hits", "anitta", "dua lipa", "alok", "vintage culture", "david guetta", "taylor",
        "beyonce", "trap", "rap", "hip hop", "matue", "marilia mendonca", "jorge & mateus"
    ],
}

PALAVRAS_CHAVE_VIDEO = [
    "youtube", "netflix", "twitch", "prime video", "crunchyroll", "disney+", "max",
    "filme", "serie", "anime", "episodio", "trailer", "gameplay", "ao vivo", "live"
]

PALAVRAS_CHAVE_DEV = [
    "python", "rust", "typescript", "javascript", "react", "docker", "git", "linux",
    "vscode", "visual studio", "terminal", "powershell", "bash", "sql", "postgres"
]


def analisar_contexto_ativo(processo_nome: str, titulo_janela: str):
    """
    Analisa o programa e o título da janela ativa para inferir o que o usuário está fazendo/ouvindo/assistindo.
    Retorna uma tupla: (categoria, subcategoria, reacao_sugerida, fala_sugerida).
    """
    p = (processo_nome or "").lower()
    t = (titulo_janela or "").lower()
    conteudo = f"{p} {t}"

    # 1. Detecção de Música
    e_app_musica = any(app in p for app in ("spotify", "deezer", "music", "itunes")) or "music" in t
    for subcat, palavras in PALAVRAS_CHAVE_MUSICA.items():
        if any(palavra in conteudo for palavra in palavras):
            if subcat == "rock":
                fala = random.choice([
                    "Esse som é pedrada! Bate cabeça aí! 🤘🎸",
                    "Solo de guitarra aprovado no code review! ⚡🎸",
                    "Rock pesado = código compilando na força bruta! 🤘",
                ])
                return ("musica", "rock", "headbanging", fala)
            elif subcat == "lofi":
                fala = random.choice([
                    "Foco supremo com esse lo-fi... ☕🎧",
                    "Café quentinho, batida suave e mente sã. 🎵",
                    "Lo-fi ligado: modo monge ativado! 🧘✨",
                ])
                return ("musica", "lofi", "lofi_chill", fala)
            elif subcat == "pop_funk":
                fala = random.choice([
                    "Solta o som que o ritmo tá bom! 🎶🕺",
                    "Quem programa dançando coda sem bugs! 🎶💃",
                    "Batida animada detectada! 🎵✨",
                ])
                return ("musica", "pop_funk", "dancar", fala)

    if e_app_musica:
        return ("musica", "geral", "dancar", "Música boa tocando! Solta o play! 🎵🎧")

    # 2. Detecção de Vídeo / Streaming
    if any(palavra in conteudo for palavra in PALAVRAS_CHAVE_VIDEO):
        fala = random.choice([
            "Cena de cinema! Pega a pipoca e não dá spoiler! 🍿🎬",
            "Pausa aí rapidinho pra pegar água! 🥤✨",
            "Só mais um episódio e vou dormir (mentira)! 🍿👀",
            "Esse plot twist nem a inteligência artificial previu! 🎬🍿",
        ])
        return ("video", "streaming", "pipoca", fala)

    # 3. Detecção de Código / Desenvolvimento
    if any(palavra in conteudo for palavra in PALAVRAS_CHAVE_DEV):
        fala = random.choice([
            "Focado no código! Se precisar de café, tô aqui! 💻☕",
            "Commitou na branch certa, né? Confere aí! 👀",
            "Docker subiu ou é o ventilador do PC que ligou? 🐳⚡",
            "Refatorar é arte, testar em produção faz parte! 🚀",
        ])
        return ("trabalho", "dev", "digitando", fala)

    return ("geral", "padrao", "idle", None)


# ============================================================
# PLANTÃO DO PESTINHA: NOTÍCIAS & CURIOSIDADES TECH DINÂMICAS
# ============================================================

NOTICIAS_PLANTAO = [
    "PLANTÃO: Cientistas descobrem que 90% dos bugs somem quando você vai explicar pro colega! 🐞",
    "URGENTE: Nova IA promete resolver todos os problemas do mundo, exceto centralizar uma div! 🤖",
    "FATO HISTÓRICO: O primeiro bug de computador em 1947 foi literalmente uma mariposa presa num relé! 🦋",
    "NOTÍCIA: Desenvolvedor diz que era 'só um commit rápido' e quebra ambiente de homologação. 💥",
    "BOLETIM DO CLIMA: Frente fria de prazos se aproxima. Chance de 100% de café na sua mesa! ☕🌧️",
    "CURIOSIDADE: O Python recebeu esse nome por causa do grupo de comédia Monty Python, não da cobra! 🐍🎬",
    "PLANTÃO DE SEGURANÇA: Senha '123456' continua sendo a mais usada e a que mais dá dor de cabeça. 🔐",
    "ESTUDO CIENTÍFICO: Conversar com um patinho de borracha (ou seu pet) aumenta o QI em 40%! 🦆💻",
    "NOTÍCIA: Git add . seguido de git commit -m 'ajustes' atinge marca de 1 bilhão de ocorrências. 📦",
    "BOLETIM ECONÔMICO: Ações da indústria cafeeira sobem toda vez que um dev abre o terminal. 📈☕",
    "PLANTÃO: Código comentado 'depois eu arrumo' completa 10 anos sem alterações no repositório. ⏳",
    "CURIOSIDADE TECH: O código que levou o homem à Lua tinha menos linhas que uma página moderna em React! 🚀",
    "AVISO IMPORTANTE: Beba água e estique as costas. Sua coluna não tem backup na nuvem! 💧🧘",
]


def obter_noticia_dinamica(paths=None):
    """Retorna uma notícia ou curiosidade do Plantão do Pestinha (web recente ou plantão interno)."""
    try:
        from .noticias_web import obter_noticia_fresca
        fresca = obter_noticia_fresca(paths)
        if fresca and random.random() < 0.8:
            return fresca
    except Exception:
        pass
    return random.choice(NOTICIAS_PLANTAO)


def obter_fala_do_dia(dt=None):
    """Retorna uma fala humorística sobre o dia atual (datas comemorativas, dia da semana ou curiosidades)."""
    if dt is None:
        dt = datetime.now()

    # 1. Checa evento sazonal ativo
    evento = obter_evento_sazonal(dt)
    if evento and evento in FALAS_SAZONAIS:
        return random.choice(FALAS_SAZONAIS[evento])

    # 2. Checa datas especiais do calendário
    m, d = dt.month, dt.day
    if m == 4 and d == 1:
        return "Primeiro de abril! Todos os testes unitários passaram... mentira! 🤡"
    elif m == 5 and d == 25:
        return "Dia da Toalha e do Orgulho Nerd! Não entre em pânico! 42 🚀🪐"
    elif m == 6 and d == 12:
        return "Feliz Dia dos Namorados! Meu único amor é código sem warnings! ❤️"
    elif m == 5 and d == 1:
        return "Dia do Trabalho! Hoje o código compila sozinho por decreto! 🛠️"

    # 3. Dia da semana
    weekday = dt.weekday()  # 0 = seg, 4 = sex, 5 = sab, 6 = dom
    if weekday == 4:
        return random.choice([
            "Sextou! Deploy na sexta-feira é viver perigosamente! 🍻",
            "Sexta-feira chegou! Só mais 4 horas fingindo que tô compilando! 🚀",
            "Hoje é sexta! Ninguém mexe em banco de dados! 🍕",
        ])
    elif weekday == 0:
        return random.choice([
            "Segunda-feira... meu cérebro ainda tá carregando os módulos! ☕😴",
            "Bom dia! Café primeiro, refactoring depois! ☕⚡",
            "Segunda-feira: semana nova, bugs novos! 🐞",
        ])
    elif weekday in (5, 6):
        return random.choice([
            "Fim de semana! Se alguém me chamar no Slack eu finjo demência! 🏖️",
            "Fim de semana chegou! Modo soneca ativado com sucesso! 😴✨",
        ])
    elif weekday == 2:
        return "Quarta-feira! Meio da semana, metade dos bugs resolvidos! 🐪"

    # 4. Notícia do plantão
    return obter_noticia_dinamica()

