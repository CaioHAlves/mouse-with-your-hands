"""Wrapper do MediaPipe Hands: frame BGR -> landmarks normalizados por mão."""

from dataclasses import dataclass

import cv2
import mediapipe as mp

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


@dataclass
class Hand:
    # 21 pontos (x, y, z) normalizados em [0, 1] relativos ao quadro.
    landmarks: list
    # "Left" ou "Right" (já corresponde à mão real, pois o quadro é espelhado
    # antes do processamento).
    handedness: str
    # Resultado bruto do MediaPipe, usado só para desenhar.
    raw: object


class HandTracker:
    def __init__(self, cfg: Config):
        self._hands = mp.solutions.hands.Hands(
            max_num_hands=cfg.max_hands,
            min_detection_confidence=cfg.detection_confidence,
            min_tracking_confidence=cfg.tracking_confidence,
        )

    def process(self, frame_bgr) -> list[Hand]:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = self._hands.process(rgb)

        hands = []
        if result.multi_hand_landmarks:
            for lm_list, handedness in zip(
                result.multi_hand_landmarks, result.multi_handedness
            ):
                landmarks = [(p.x, p.y, p.z) for p in lm_list.landmark]
                label = handedness.classification[0].label
                hands.append(Hand(landmarks=landmarks, handedness=label, raw=lm_list))
        return hands

    def draw(self, frame_bgr, hands: list[Hand]):
        for hand in hands:
            mp.solutions.drawing_utils.draw_landmarks(
                frame_bgr, hand.raw, mp.solutions.hands.HAND_CONNECTIONS
            )

    def close(self):
        self._hands.close()
