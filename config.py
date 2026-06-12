"""Configurações do controle de mouse por gestos.

Todos os ajustes finos ficam aqui. Os dois valores que mais provavelmente
precisarão de ajuste conforme sua câmera/iluminação são `pinch_threshold`
e `fold_threshold`.
"""

from dataclasses import dataclass


@dataclass
class Config:
    # Câmera
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480

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

    # Se a mão ativa sumir por mais que isso durante um arrasto, solta o botão.
    lost_hand_release_frames: int = 10

    # pyautogui
    failsafe: bool = False

    # Janela de preview com a câmera e os landmarks.
    show_preview: bool = True


CONFIG = Config()
