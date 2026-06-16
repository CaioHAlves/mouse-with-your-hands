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

Abrem duas janelas: o preview com a câmera e o esqueleto das mãos, e a
janela **Ajustes**, com os controles de sensibilidade. Com o preview em foco:

- **q** — sai (solta o botão do mouse se estiver arrastando)
- **p** — pausa/retoma o controle do mouse (o rastreamento continua visível)
- **r** — restaura os ajustes padrão

## Gerar executável

Há um workflow do GitHub Actions (`.github/workflows/build.yml`) que empacota
o app com o [PyInstaller](https://pyinstaller.org/) e gera os pacotes do
Windows e do Linux:

- **Manualmente**: aba **Actions** → **Build executables** → **Run workflow**.
  Ao terminar, baixe os artefatos (`MouseComAsMaos-windows` e
  `MouseComAsMaos-linux`) na própria execução.
- **Por release**: empurre uma tag `v*` (ex.: `git tag v1.0.0 && git push
  --tags`) e os pacotes são anexados automaticamente à Release.

O executável fica dentro da pasta `MouseComAsMaos/` — distribua a pasta
inteira (modo *onedir*). O modelo `hand_landmarker.task` já vai embutido,
então o app roda offline.

Para gerar localmente (na mesma plataforma do alvo: Windows gera `.exe`,
Linux gera o binário Linux):

```bash
pip install pyinstaller
python main.py            # uma vez, para baixar hand_landmarker.task
pyinstaller --noconfirm MouseComAsMaos.spec
```

O `MouseComAsMaos.spec` cuida das pegadinhas do empacotamento (coleta os
dados do MediaPipe e embute o modelo). O resultado fica em
`dist/MouseComAsMaos/`.

## Ajustes de sensibilidade

Use os sliders da janela **Ajustes** — valem na hora e ficam salvos em
`settings.json` ao sair (a tecla `r` volta ao padrão):

- **Suavizacao** — maior = cursor mais responsivo, menor = mais estável
- **Pinca (arrastar)** — quão juntos polegar e indicador precisam estar para
  engatar o arrasto. Diminua se o arrasto dispara sozinho; aumente se está
  difícil engatar.
- **Dobra (clique)** — quão dobrado o dedo precisa estar para contar como
  clique. Diminua se está clicando sem querer; aumente se os cliques não saem.
- **Cooldown clique** — tempo mínimo entre cliques (centésimos de segundo)
- **Margem da tela** — margem do quadro da câmera mapeada para fora da tela
  (permite alcançar os cantos sem esticar o braço)

Opções mais avançadas continuam em `config.py`:

- `click_anchor_delay_s` — o clique é aplicado onde o cursor estava há este
  tempo (antes de o dedo dobrar), para não errar alvos pequenos
- `camera_index` — troque se você tiver mais de uma câmera
- `target_fps`, `frame_width`, `frame_height` — captura da câmera
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
- **Cursor tremendo**: diminua o slider Suavizacao (ex.: 20).
- **FPS baixo**: ilumine bem o ambiente — webcams cortam o FPS pela metade
  no escuro por causa da auto-exposição. O app já pede 30 FPS e o codec
  MJPG à câmera; se ainda assim ficar lento, reduza `frame_width`/
  `frame_height` em `config.py`.
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
