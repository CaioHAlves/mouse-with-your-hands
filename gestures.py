"""Detecção de gestos por geometria pura dos landmarks (sem I/O)."""

import math
from dataclasses import dataclass

from config import Config
from hand_tracker import (
    Hand,
    INDEX_MCP,
    INDEX_PIP,
    INDEX_TIP,
    MIDDLE_MCP,
    MIDDLE_PIP,
    MIDDLE_TIP,
    THUMB_TIP,
    WRIST,
)


@dataclass
class FrameGesture:
    pinch: bool
    pinch_ratio: float
    index_folded: bool
    middle_folded: bool
    # Ponto normalizado (x, y) que o cursor segue.
    anchor: tuple


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def hand_size(lm) -> float:
    """Distância pulso -> base do dedo médio.

    Serve de normalizador para que os limiares de gesto não dependam da
    distância da mão até a câmera.
    """
    return _dist(lm[WRIST], lm[MIDDLE_MCP]) or 1e-6


def pinch_ratio(lm) -> float:
    return _dist(lm[THUMB_TIP], lm[INDEX_TIP]) / hand_size(lm)


def is_pinching(lm, cfg: Config, was_pinching: bool) -> bool:
    """Pinça polegar+indicador, com histerese para não piscar no limiar."""
    ratio = pinch_ratio(lm)
    if was_pinching:
        return ratio < cfg.pinch_release
    return ratio < cfg.pinch_threshold


def is_finger_folded(lm, tip: int, pip: int, cfg: Config) -> bool:
    """Dedo dobrado, de forma invariante à rotação da mão.

    Compara distâncias até o pulso em vez de comparar coordenadas y, que
    quebraria com a mão inclinada.
    """
    return _dist(lm[tip], lm[WRIST]) < _dist(lm[pip], lm[WRIST]) * cfg.fold_threshold


def cursor_anchor(lm) -> tuple:
    """O cursor segue a base do indicador (MCP), não a ponta: assim dobrar o
    dedo para clicar quase não desloca o cursor."""
    x, y, _ = lm[INDEX_MCP]
    return (x, y)


class GestureDetector:
    def __init__(self, cfg: Config):
        self._cfg = cfg
        self._was_pinching = False

    def read(self, hand: Hand) -> FrameGesture:
        lm = hand.landmarks
        cfg = self._cfg
        pinch = is_pinching(lm, cfg, self._was_pinching)
        self._was_pinching = pinch
        return FrameGesture(
            pinch=pinch,
            pinch_ratio=pinch_ratio(lm),
            index_folded=is_finger_folded(lm, INDEX_TIP, INDEX_PIP, cfg),
            middle_folded=is_finger_folded(lm, MIDDLE_TIP, MIDDLE_PIP, cfg),
            anchor=cursor_anchor(lm),
        )

    def reset(self):
        self._was_pinching = False
