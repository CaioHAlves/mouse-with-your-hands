"""Controle o mouse com as mãos pela webcam, estilo Tony Stark.

Uso: python main.py
Teclas (com a janela de preview em foco): q sai, p pausa/retoma,
r restaura os ajustes padrão.
"""

import sys
import threading
import time

import cv2

from config import CONFIG, load_settings, reset_settings, save_settings
from controller import DRAGGING, MouseController
from gestures import GestureDetector
from hand_tracker import HandTracker

PREVIEW_WINDOW = "Mouse com as maos"
SETTINGS_WINDOW = "Ajustes"

# (nome do slider, campo do Config, mínimo) — valores em centésimos; o máximo
# é o teto do trackbar. O OpenCV só aceita mínimo 0, então o piso é aplicado
# na leitura.
SLIDERS = (
    ("Suavizacao", "smoothing_alpha", 5, 90),
    ("Pinca (arrastar)", "pinch_threshold", 20, 80),
    ("Dobra (clique)", "fold_threshold", 70, 100),
    ("Cooldown clique", "click_cooldown_s", 10, 150),
    ("Margem da tela", "frame_margin", 5, 30),
)


class ThreadedCamera:
    """Lê a câmera numa thread própria, guardando só o frame mais recente.

    A captura segue em paralelo com o processamento (MediaPipe + mouse), em
    vez de o loop principal parar esperando cada frame chegar.
    """

    def __init__(self, cap):
        self._cap = cap
        self._lock = threading.Lock()
        self._new_frame = threading.Event()
        self._frame = None
        self._ok = True
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self):
        while self._ok:
            ok, frame = self._cap.read()
            if not ok:
                self._ok = False
                self._new_frame.set()
                return
            with self._lock:
                self._frame = frame
            self._new_frame.set()

    def read(self, timeout: float = 1.0):
        """Espera um frame ainda não consumido e o devolve (ok, frame)."""
        if not self._new_frame.wait(timeout):
            return self._ok, None
        self._new_frame.clear()
        with self._lock:
            return self._ok, self._frame

    def release(self):
        self._ok = False
        self._thread.join(timeout=1.0)
        self._cap.release()


def open_camera(cfg):
    if sys.platform == "win32":
        cap = cv2.VideoCapture(cfg.camera_index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(cfg.camera_index)
    # MJPG destrava o FPS no Windows: o codec padrão (YUY2) costuma limitar
    # a captura a 5-15 FPS dependendo da resolução.
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.frame_height)
    cap.set(cv2.CAP_PROP_FPS, cfg.target_fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def create_settings_window(cfg):
    cv2.namedWindow(SETTINGS_WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(SETTINGS_WINDOW, 420, 200)
    for name, field, _lo, hi in SLIDERS:
        value = int(round(getattr(cfg, field) * 100))
        cv2.createTrackbar(name, SETTINGS_WINDOW, value, hi, lambda _v: None)


def apply_settings(cfg):
    """Copia os sliders para o CONFIG; vale na hora, pois os outros módulos
    leem o mesmo objeto a cada frame."""
    for name, field, lo, _hi in SLIDERS:
        value = max(lo, cv2.getTrackbarPos(name, SETTINGS_WINDOW))
        setattr(cfg, field, value / 100)
    cfg.pinch_release = cfg.pinch_threshold + 0.15


def sync_sliders(cfg):
    for name, field, _lo, _hi in SLIDERS:
        cv2.setTrackbarPos(name, SETTINGS_WINDOW, int(round(getattr(cfg, field) * 100)))


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


def main():
    cfg = CONFIG
    load_settings(cfg)

    cap = open_camera(cfg)
    if not cap.isOpened():
        print(f"Erro: não foi possível abrir a câmera {cfg.camera_index}.")
        print("Ajuste camera_index em config.py ou verifique as permissões.")
        return 1

    tracker = HandTracker(cfg)
    detector = GestureDetector(cfg)
    controller = MouseController(cfg)
    camera = ThreadedCamera(cap)

    if cfg.show_preview:
        create_settings_window(cfg)

    active_label = None
    paused = False
    prev_t = time.monotonic()
    fps = 0.0

    print("Controlando o mouse com as mãos.")
    print("Teclas: q = sair, p = pausar, r = restaurar ajustes padrão.")

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Erro: falha ao ler frame da câmera.")
                break
            if frame is None:
                continue

            if cfg.show_preview:
                apply_settings(cfg)

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
                    f"{status} | {fps:.0f} FPS | q sai, p pausa, r padrao",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow(PREVIEW_WINDOW, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("p"):
                paused = not paused
                if paused:
                    controller.release()
                    detector.reset()
            if key == ord("r") and cfg.show_preview:
                reset_settings(cfg)
                sync_sliders(cfg)
                print("Ajustes restaurados para o padrão.")
    finally:
        if cfg.show_preview:
            save_settings(cfg)
        controller.release()
        camera.release()
        cv2.destroyAllWindows()
        tracker.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
