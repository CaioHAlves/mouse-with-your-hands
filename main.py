"""Controle o mouse com as mãos pela webcam, estilo Tony Stark.

Uso: python main.py
Teclas (com a janela de preview em foco): q sai, p pausa/retoma.
"""

import sys
import time

import cv2

from config import CONFIG
from controller import DRAGGING, MouseController
from gestures import GestureDetector
from hand_tracker import HandTracker


def pick_active_hand(hands, current_label):
    """Política "sticky": a mão que já controla o cursor continua controlando
    enquanto estiver visível; se sumir, troca; sem histórico, prefere a direita.
    Evita o cursor pular quando a segunda mão entra no quadro."""
    if not hands:
        return None
    if current_label is not None:
        for hand in hands:
            if hand.handedness == current_label:
                return hand
    for hand in hands:
        if hand.handedness == "Right":
            return hand
    return hands[0]


def open_camera(cfg):
    if sys.platform == "win32":
        cap = cv2.VideoCapture(cfg.camera_index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(cfg.camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.frame_height)
    return cap


def main():
    cfg = CONFIG
    cap = open_camera(cfg)
    if not cap.isOpened():
        print(f"Erro: não foi possível abrir a câmera {cfg.camera_index}.")
        print("Ajuste camera_index em config.py ou verifique as permissões.")
        return 1

    tracker = HandTracker(cfg)
    detector = GestureDetector(cfg)
    controller = MouseController(cfg)

    active_label = None
    paused = False
    prev_t = time.monotonic()
    fps = 0.0

    print("Controlando o mouse com as mãos. Teclas: q = sair, p = pausar.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Erro: falha ao ler frame da câmera.")
                break

            # Espelha para o movimento da mão corresponder ao do cursor.
            frame = cv2.flip(frame, 1)
            hands = tracker.process(frame)

            active = pick_active_hand(hands, active_label)
            active_label = active.handedness if active else active_label

            if paused:
                gesture = None
            else:
                gesture = detector.read(active) if active else None
                controller.update(gesture)

            now = time.monotonic()
            dt = now - prev_t
            prev_t = now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1 / dt)

            if cfg.show_preview:
                tracker.draw(frame, hands)
                if paused:
                    status = "PAUSADO (p retoma)"
                elif controller.mode == DRAGGING:
                    status = "ARRASTANDO"
                elif active:
                    status = f"mao ativa: {active.handedness}"
                else:
                    status = "nenhuma mao detectada"
                cv2.putText(
                    frame,
                    f"{status} | {fps:.0f} FPS | q sai, p pausa",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow("Mouse com as maos", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("p"):
                paused = not paused
                if paused:
                    controller.release()
                    detector.reset()
    finally:
        controller.release()
        cap.release()
        cv2.destroyAllWindows()
        tracker.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
