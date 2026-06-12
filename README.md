# Mouse com as mãos 🖐️🖱️

Controle o cursor do mouse com as mãos pela webcam, estilo Tony Stark. Usa
[MediaPipe](https://developers.google.com/mediapipe) para rastrear as mãos,
OpenCV para a câmera e pyautogui para mover e clicar o mouse de verdade.

## Gestos

| Gesto | Ação |
|---|---|
| Mover a mão (base do indicador) | Move o cursor |
| Dobrar rapidamente o **indicador** | Clique **esquerdo** |
| Dobrar rapidamente o **dedo médio** | Clique **direito** |
| **Pinça** (polegar + indicador juntos) | Segura o botão esquerdo (**arrastar** janelas/itens) |
| Soltar a pinça | Solta o que estava arrastando |

Funciona com qualquer uma das mãos (até duas no quadro). Quando as duas estão
visíveis, a mão que já estava controlando o cursor continua no controle; se
ela sair do quadro, a outra assume.

O cursor segue a **base** do indicador (não a ponta), então dobrar o dedo para
clicar quase não desloca o cursor.

## Requisitos

- Python **3.9 ou superior** (qualquer versão com wheel do MediaPipe disponível)
- Uma webcam
- **Windows** ou **Linux com sessão X11** (em Wayland o pyautogui não consegue
  mover o mouse — faça login em uma sessão "Xorg"/"X11" na tela de login)

## Instalação

```bash
git clone https://github.com/CaioHAlves/mouse-with-your-hands.git
cd mouse-with-your-hands

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

Na primeira execução, o modelo de mãos do MediaPipe (`hand_landmarker.task`,
~8 MB) é baixado automaticamente para a pasta do projeto — só nessa vez é
preciso estar conectado à internet.

Abre uma janela de preview com a câmera e o esqueleto das mãos. Com essa
janela em foco:

- **q** — sai (solta o botão do mouse se estiver arrastando)
- **p** — pausa/retoma o controle do mouse (o rastreamento continua visível)

## Ajustes de sensibilidade

Tudo fica em `config.py`. Os dois valores que mais provavelmente você vai
querer ajustar para a sua câmera e iluminação:

- `pinch_threshold` (padrão 0.40) — quão juntos polegar e indicador precisam
  estar para engatar a pinça. Diminua se o arrasto dispara sozinho; aumente
  se está difícil engatar.
- `fold_threshold` (padrão 0.9) — quão dobrado o dedo precisa estar para
  contar como clique. Diminua se está clicando sem querer; aumente se os
  cliques não saem.

Outros úteis:

- `smoothing_alpha` — suavização do cursor (maior = mais responsivo,
  menor = mais estável)
- `frame_margin` — margem do quadro da câmera mapeada para fora da tela
  (permite alcançar os cantos sem esticar o braço)
- `click_cooldown_s` — tempo mínimo entre cliques
- `click_anchor_delay_s` — o clique é aplicado onde o cursor estava há este
  tempo (antes de o dedo dobrar), para não errar alvos pequenos; aumente se
  os cliques estiverem caindo "atrasados" no caminho do cursor
- `camera_index` — troque se você tiver mais de uma câmera
- `failsafe` — se `True`, jogar o cursor num canto da tela aborta o pyautogui
  (proteção de emergência; desligado por padrão porque os cantos são
  alcançáveis de propósito)

## Solução de problemas

- **`AttributeError: module 'mediapipe' has no attribute 'solutions'`**: você
  está com uma versão antiga deste projeto. As wheels novas do MediaPipe não
  trazem mais a API legada `mp.solutions`; o projeto usa a Tasks API. Faça
  `git pull` e rode de novo.
- **Erro ao baixar `hand_landmarker.task`**: a primeira execução precisa de
  internet. Sem ela, baixe o arquivo manualmente (a URL aparece na mensagem
  de erro) e salve na pasta do projeto.
- **A câmera não abre**: confira `camera_index` em `config.py` (tente 1, 2...)
  e as permissões de câmera do sistema.
- **O cursor não se move no Linux**: você provavelmente está em Wayland.
  Na tela de login, escolha a sessão "Ubuntu on Xorg" (ou equivalente).
- **Cliques disparando sozinhos / não saindo**: ajuste `fold_threshold`.
  Boa iluminação e a mão de frente para a câmera ajudam muito o MediaPipe.
- **Arrasto travando ou soltando sozinho**: ajuste `pinch_threshold` /
  `pinch_release` (a diferença entre eles é a histerese que evita o
  "pisca-pisca").
- **Cursor tremendo**: diminua `smoothing_alpha` (ex.: 0.2).
- **Cliques erram botões pequenos (minimizar, fechar...)**: o clique usa a
  posição de `click_anchor_delay_s` atrás (padrão 0.25s), de antes de o dedo
  dobrar, e o cursor fica congelado enquanto o dedo está dobrado. Se ainda
  errar, aumente um pouco esse valor ou diminua `smoothing_alpha`.
- **Cliques não funcionam em janelas de administrador**: o Windows bloqueia
  cliques sintéticos em programas elevados; rode o `python main.py` num
  terminal como administrador se precisar controlá-los.

## Como testar

1. Cursor: confira que você alcança os 4 cantos da tela.
2. Cliques: uma dobra de indicador = um clique esquerdo; dedo médio = direito.
3. Arrasto: faça a pinça sobre a barra de título de uma janela, mova, solte.
4. Durante a pinça, nenhum clique deve disparar.
5. Entrar com a segunda mão no quadro não deve roubar o cursor.
