"""Configurações do controle de mouse por gestos.

Os ajustes de sensibilidade podem ser mudados ao vivo pela janela "Ajustes"
do app (ficam salvos em settings.json). Este arquivo guarda os padrões e o
restante das opções.
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    # Câmera
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    target_fps: int = 30

    # MediaPipe
    max_hands: int = 2
    detection_confidence: float = 0.7
    tracking_confidence: float = 0.6

    # Mapeamento câmera -> tela
    # Fração da borda do quadro ignorada: a caixa interna (1 - 2*margem) é
    # mapeada para a tela inteira, então dá para alcançar os cantos sem
    # tirar a mão do campo de visão da câmera.
    frame_margin: float = 0.15

    # Suavização do cursor (EMA). Maior = mais responsivo, menor = mais suave.
    smoothing_alpha: float = 0.35

    # Pinça (arrastar): razão dist(polegar, indicador) / tamanho da mão.
    # Histerese: engata abaixo de pinch_threshold, só solta acima de
    # pinch_release — evita o drag "piscar" no limiar.
    pinch_threshold: float = 0.40
    pinch_release: float = 0.55
    # Frames consecutivos de pinça antes de iniciar/encerrar o arrasto.
    pinch_grace_frames: int = 3

    # Dedo dobrado (cliques): dobrado quando
    # dist(ponta, pulso) < dist(PIP, pulso) * fold_threshold.
    fold_threshold: float = 0.9
    click_cooldown_s: float = 0.5
    # O clique é aplicado na posição em que o cursor estava há este tempo,
    # antes de o dedo começar a dobrar — senão o movimento da dobra desloca
    # o cursor e o clique erra alvos pequenos (ex.: botão de minimizar).
    click_anchor_delay_s: float = 0.25

    # Se a mão ativa sumir por mais que isso durante um arrasto, solta o botão.
    lost_hand_release_frames: int = 10

    # pyautogui
    failsafe: bool = False

    # Janela de preview com a câmera e os landmarks.
    show_preview: bool = True


CONFIG = Config()

# Campos ajustáveis pelos sliders da janela "Ajustes", persistidos em
# settings.json. pinch_release não entra: é derivado (pinch_threshold + 0.15).
TUNABLE_FIELDS = (
    "smoothing_alpha",
    "pinch_threshold",
    "fold_threshold",
    "click_cooldown_s",
    "frame_margin",
)

SETTINGS_PATH = Path(__file__).resolve().parent / "settings.json"


def load_settings(cfg: Config):
    if not SETTINGS_PATH.exists():
        return
    try:
        data = json.loads(SETTINGS_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return
    for name in TUNABLE_FIELDS:
        value = data.get(name)
        if isinstance(value, (int, float)):
            setattr(cfg, name, float(value))
    cfg.pinch_release = cfg.pinch_threshold + 0.15


def save_settings(cfg: Config):
    data = {name: getattr(cfg, name) for name in TUNABLE_FIELDS}
    try:
        SETTINGS_PATH.write_text(json.dumps(data, indent=2))
    except OSError:
        pass


def reset_settings(cfg: Config):
    defaults = Config()
    for name in TUNABLE_FIELDS:
        setattr(cfg, name, getattr(defaults, name))
    cfg.pinch_release = defaults.pinch_release
    SETTINGS_PATH.unlink(missing_ok=True)
