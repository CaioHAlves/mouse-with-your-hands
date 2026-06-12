"""Wrapper do MediaPipe Hands (Tasks API): frame BGR -> landmarks por mão.

Usa a Tasks API (`mediapipe.tasks`), que é a API mantida pelo MediaPipe — as
wheels mais novas (ex.: Python 3.13+) não trazem mais a antiga `mp.solutions`.
O modelo `hand_landmarker.task` (~8 MB) é baixado automaticamente na primeira
execução.
"""

import urllib.request
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)

from config import Config

# Índices dos landmarks do MediaPipe Hands usados pelo projeto.
WRIST = 0
THUMB_TIP = 4
INDEX_MCP = 5
INDEX_PIP = 6
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_TIP = 12

# Pares de landmarks ligados no desenho do esqueleto da mão.
HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),          # polegar
    (0, 5), (5, 6), (6, 7), (7, 8),          # indicador
    (5, 9), (9, 10), (10, 11), (11, 12),     # médio
    (9, 13), (13, 14), (14, 15), (15, 16),   # anelar
    (13, 17), (17, 18), (18, 19), (19, 20),  # mínimo
    (0, 17),                                 # palma
)

MODEL_FILENAME = "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)


@dataclass
class Hand:
    # 21 pontos (x, y, z) normalizados em [0, 1] relativos ao quadro.
    landmarks: list
    # "Left" ou "Right" (já corresponde à mão real, pois o quadro é espelhado
    # antes do processamento).
    handedness: str


def _model_path() -> Path:
    path = Path(__file__).resolve().parent / MODEL_FILENAME
    if not path.exists():
        print(f"Baixando o modelo de mãos do MediaPipe (~8 MB) para {path}...")
        try:
            urllib.request.urlretrieve(MODEL_URL, path)
        except Exception as exc:
            path.unlink(missing_ok=True)
            raise RuntimeError(
                "Não foi possível baixar o modelo hand_landmarker.task. "
                "Verifique sua conexão com a internet (só é necessária na "
                f"primeira execução) ou baixe manualmente de {MODEL_URL} "
                f"e salve como {path}."
            ) from exc
        print("Download concluído.")
    return path


class HandTracker:
    def __init__(self, cfg: Config):
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(_model_path())),
            running_mode=RunningMode.VIDEO,
            num_hands=cfg.max_hands,
            min_hand_detection_confidence=cfg.detection_confidence,
            min_tracking_confidence=cfg.tracking_confidence,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        # detect_for_video exige timestamps estritamente crescentes.
        self._timestamp_ms = 0

    def process(self, frame_bgr) -> list[Hand]:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._timestamp_ms += 33  # ~30 FPS nominais; só precisa ser crescente
        result = self._landmarker.detect_for_video(image, self._timestamp_ms)

        hands = []
        for lm_list, handedness in zip(result.hand_landmarks, result.handedness):
            landmarks = [(p.x, p.y, p.z) for p in lm_list]
            hands.append(Hand(landmarks=landmarks, handedness=handedness[0].category_name))
        return hands

    def draw(self, frame_bgr, hands: list[Hand]):
        h, w = frame_bgr.shape[:2]
        for hand in hands:
            pts = [(int(x * w), int(y * h)) for x, y, _ in hand.landmarks]
            for a, b in HAND_CONNECTIONS:
                cv2.line(frame_bgr, pts[a], pts[b], (0, 255, 0), 2)
            for p in pts:
                cv2.circle(frame_bgr, p, 4, (0, 0, 255), -1)

    def close(self):
        self._landmarker.close()
