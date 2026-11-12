# Histórico de versões

## 2.0.0 — Pestinha Pro (Edição Aprimorada)

Baseado no projeto de código aberto [Pestinha](https://github.com/mille-okws/pestinha) criado por [mille-okws](https://github.com/mille-okws), sob a licença GNU GPL v3.

### Novas Funcionalidades
- **Roda Radial de Ações (Menu Circular de Interação Rápida):**
  - Segurar o botão direito (≥300ms) abre o menu radial translúcido sobre a tela.
  - Submenu de diálogo e interações avançadas com abertura automática por **hover de 600ms**, sem precisar clicar.
  - Retorno suave para o menu principal ao arrastar a mira para fora da roda.
  - Toque rápido no botão direito (<300ms) preserva o menu clássico de contexto.
- **Notebook Pro Grafite & Modo Tablet Digital:**
  - Posição realista com a tampa e emblema tech voltados para o usuário e reflexo da tela no rosto do pet.
  - Totalmente arrastável com botão esquerdo para reposicionar livremente na tela (persistido em `panels.json`).
  - Função de virar a tela para o usuário e alternância dinâmica para o modo Tablet Digital.
- **Leitura Confortável de Balões (Hover-Pause):**
  - Ao passar o cursor do mouse sobre qualquer balão de fala ou notícia, o tempo de expiração é pausado indefinidamente.
  - O pet interrompe sua caminhada e aguarda pacientemente enquanto o usuário lê o balão.
  - Tolerância de 3 segundos ao retirar o mouse e botão `✕` para fechamento instantâneo.
- **Busca de Notícias Web & Fatos Curiosos:**
  - Sistema inteligente de busca em momentos ociosos (`AWAY`) trazendo novidades do TabNews, fatos da Wikipédia e suporte a IAs modernas.
- **Datas Comemorativas Sazonais:**
  - Adornos visuais gerados proceduralmente: chapéu de palha no São João/Festa Junina, gorro de Natal, orelhas de Páscoa, máscara de Carnaval, cartola de Ano Novo, chapéu de bruxinha no Halloween e óculos Matrix no Dia do Programador.
- **Reconhecimento Musical & Streaming:**
  - Animação de *headbanging* rítmico no Rock/Metal, dança animada no Pop/Funk e modo relax no Lo-Fi, com notas musicais flutuantes (`🎵`, `🎸`, `🎶`, `✨`).
- **Membros Fisiológicos Animados:**
  - Perninhas bípedes com passos cadenciados apoiados na barra de tarefas.
  - Bracinhos com gestos expressivos (comemorar pulando, coçar a cabeça, cruzar os braços, digitar).
- **Galeria de Capturas de Alta Resolução (`docs/prints/`):**
  - Gerador aprimorado com DirectWrite nativo do Windows, sem artefatos ou caracteres ilegíveis.

### Correções e Estabilidade
- Correção no `paintEvent` com encapsulamento seguro `try ... finally` impedindo artefatos no canal alfa transparente do Desktop Window Manager (DWM).
- Suíte completa de 402 testes automatizados aprovada sem regressões.


## 0.8.0 — melhorias para o Windows

### Correções
- Janela maximizada em monitor sem barra de tarefas (ou com a barra oculta) não conta mais como tela cheia.
- O pet pousa em janelas de todos os monitores, cada um com a própria escala.
- Falha ao apagar os dados pela bandeja agora avisa quais arquivos ficaram, também no executável sem terminal.
- Só uma cópia abre por vez, para duas não gravarem na mesma memória.
- Sem permissão de escrita na pasta de dados, a bandeja avisa em vez de perder o aprendizado em silêncio.
- Erros não tratados vão para o log, e um erro ao salvar não impede as outras gravações nem o fechamento.
- Religar depois do pânico desloca os prazos pelo tempo parado, como já acontecia com a pausa.

### Melhorias
- O registro da rotina vem desligado e passa a se chamar "Registrar minha rotina", porque nada usa esses dados
  ainda. Quem já tinha a opção salva continua como estava.
- A tela de permissões só aparece na primeira vez, após o pânico ou com `--configurar`.
- Opção de abrir ao entrar no Windows, em Configurações.
- O executável do Windows grava em `%LOCALAPPDATA%\Pestinha`. Uma `memory/` já existente ao lado dele continua valendo.
- Instalador para Windows com Inno Setup (`instalador/pestinha.iss`).
- Mais programas reconhecidos (Cursor, Windsurf, Zed, Windows Terminal, IDEs JetBrains, Sublime, Notepad++), e
  `assets/comum/programas.json` para acrescentar outros.
- Design, vídeo e 3D passam a contar como trabalho: Blender, Figma, Photoshop, Illustrator, After Effects,
  Premiere, DaVinci Resolve, CapCut, Krita, Inkscape e os fatiadores Bambu Studio, OrcaSlicer, PrusaSlicer
  e Cura. Também Antigravity, Kiro, Trae e Android Studio como programação, e jogos populares (LoL,
  Roblox, Minecraft, Fortnite, Apex, Dota 2, Rocket League, Overwatch, GTA V, Elden Ring) como jogo.

## Suporte a macOS e Linux

- Toda a leitura do sistema (programa em primeiro plano, tempo ocioso, janelas, tela cheia, foco e o atalho
  de pânico) passa para `pestinha/plataforma/`, com um módulo por sistema. O resto do código não sabe
  qual sistema está rodando.
- O Windows continua com o mesmo comportamento: o código foi movido, não reescrito.
- macOS: Quartz e AppKit (pyobjc), tempo ocioso pelo `ioreg` se não houver pyobjc. Atalho via pynput.
- Linux (X11): xdotool, wmctrl e xprintidle; atalho via pynput. Em Wayland, o pet não enxerga janelas
  nem o tempo ocioso, e o atalho não funciona.
- A checagem de atividade reconhece os nomes de programa dos três sistemas (com ou sem `.exe`).

## Renomeação para Pestinha

- O programa e o pacote Python passam a se chamar `pestinha/` (antes `bryan/`); a classe principal é
  `PestinhaApp`; o executável, o log e a documentação usam Pestinha.
- Bryan continua sendo o nome do primeiro personagem: `pets/bryan.json`, `pets/bryan/`, a memória
  `memory/pets/bryan/` e os arquivos de conteúdo dele não mudaram.
- Os comentários e textos que falavam do pet em geral passam a dizer "o pet".

## 0.7.0 — primeira versão pública (em preparação)

### O que ele faz
- Pet de tela com corpo físico: gravidade, quique, giro, pouso nas barras de título, arraste e arremesso.
- Rede neural pulsada de 470 neurônios LIF, com 30 canais sensoriais, 10 populações de interneurônios
  e 15 motores (8 de expressão e 7 de decisão).
- Emoções vindas dos motores; carinho com olhinhos fechados de felicidade.
- Bolinha de tênis, notebook de trabalho (VS Code, Visual Studio, PyCharm, Claude, Codex) e pedido de
  trabalho que ele pode recusar.
- Travessuras com memes, fotos, post-its e bilhetes tristes, com frequência decidida pela rede.
- Protesto em estágios até a revolução contra o cursor, com cartazes e bolinhas de papel.
- Cantinho do castigo: placa arrastável, perdão por carinho, fuga por vontade acumulada, rancor, receio,
  medo condicionado da placa e cartazes de xingamento.
- Aprendizado: habituação, regra de três fatores, condicionamento Rescorla–Wagner, memória episódica.
- Pânico (`Ctrl + Alt + Shift + B`), pausa, modo teste, monitor neural e painel de protesto.

### Memória por personagem
- Cada personagem tem a sua memória em `memory/pets/<pet>/` (rede e os sete arquivos de memória); o que
  é do app (permissões, rotina, painéis, log) continua em `memory/`.
- Migração automática da versão antiga: copia, confere, guarda os originais em `memory/legado/<pet>/` e
  só então marca como migrado. Conflito ou falta de permissão não sobrescrevem nada: ele segue com os
  arquivos antigos e avisa na bandeja.

### Conteúdo por personagem
- Frases, cartazes e memes de cada personagem ficam em `pets/<pet>/`; imagens neutras (bolinhas, notebook)
  e suas fotos em `assets/comum/`. Um personagem nunca usa o conteúdo de outro: sem conteúdo próprio, usa
  frases neutras ou não faz aquela travessura.
- Os cartazes do cantinho do castigo saíram do código para as seções `[castigo]` e `[xingamento]` do
  `cartazes.txt` do pet.

### Escolha do personagem
- O programa passa a se chamar **Pestinha**; o Bryan é o primeiro personagem.
- O personagem é escolhido em Configurações (vale ao reabrir). Só `pets/<pet>.json` vira opção.
- Os textos usam o nome do personagem onde é ele que fala (apresentação, "Estou aqui", notebook, monitor
  neural, painel de protesto) e o nome do programa no resto (configurações, bandeja, pânico).
- O log passa a ser `memory/logs/pestinha.log`; o executável, `Pestinha.exe`.

### Jorge
- Segundo personagem: coach de finanças e IA, trambiqueiro. Mesma rede e mesmos estágios do Bryan, com
  outra semente, outro temperamento e conteúdo próprio (recadinhos, bilhetes tristes, cartazes de todos os
  estágios e do cantinho, e um panfleto de mentoria no lugar da bolinha de papel). Cinco memes para cada uma de felizes, contentes, curiosos e bravos, em `pets/jorge/memes/`.
- `ferramentas/medir_cartazes.py` confere, com as fontes de verdade, se cada cartaz cabe na placa.
- `ferramentas/gerar_panfleto.py` desenha o panfleto do Jorge.

### Cores e acessórios
- Cada pet pode ter as próprias cores (moldura, tela, olhos) e acessórios (óculos, gravata) no campo
  `aparencia` do `.json`. Os acessórios são uma camada por cima do rosto; olhos e expressões não mudam.
- O Jorge tem moldura e olhos dourados e gravata vermelha. O Bryan continua igual.

### Licença
- Código sob GPL-3.0-or-later (`LICENSE`).

### Qualidade
- Arquitetura em camadas verificada por teste; `app.py` dividido em composição e mixins de sessão e
  interação.
- Persistência validada: escrita atômica, recusa de `NaN`, carga tudo-ou-nada.
- Cinco rodadas de auditoria, com cada bug corrigido coberto por teste, registradas em `docs/auditorias/`.
- Suíte de testes, bateria de 100 cenários do cantinho e fuzzer com invariantes.
