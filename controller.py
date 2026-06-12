"""Máquina de estados dos gestos + suavização + ações de mouse (pyautogui)."""

import time

from config import Config
from gestures import FrameGesture

IDLE = "IDLE"
DRAGGING = "DRAGGING"


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def map_to_screen(nx: float, ny: float, cfg: Config, screen_w: int, screen_h: int):
    """Mapeia coordenadas normalizadas da câmera para pixels da tela.

    A caixa interna do quadro (descontada a margem) vira a tela inteira,
    então os cantos da tela são alcançáveis sem sair do campo da câmera.
    """
    m = cfg.frame_margin
    u = clamp((nx - m) / (1 - 2 * m), 0.0, 1.0)
    v = clamp((ny - m) / (1 - 2 * m), 0.0, 1.0)
    return (u * screen_w, v * screen_h)


class Smoother:
    """Média móvel exponencial para suavizar o cursor."""

    def __init__(self, alpha: float):
        self._alpha = alpha
        self._pos = None

    def update(self, target):
        if self._pos is None:
            self._pos = target
        else:
            a = self._alpha
            self._pos = (
                a * target[0] + (1 - a) * self._pos[0],
                a * target[1] + (1 - a) * self._pos[1],
            )
        return self._pos

    def reset(self):
        self._pos = None


class MouseController:
    def __init__(self, cfg: Config):
        self._cfg = cfg
        # Import preguiçoso: pyautogui exige um display, e assim os demais
        # módulos continuam importáveis em ambiente headless (testes).
        import pyautogui

        pyautogui.FAILSAFE = cfg.failsafe
        pyautogui.PAUSE = 0
        self._gui = pyautogui

        self._screen_w, self._screen_h = pyautogui.size()
        self._smoother = Smoother(cfg.smoothing_alpha)
        self.mode = IDLE
        self._pinch_frames = 0
        self._release_frames = 0
        self._lost_frames = 0
        self._last_left_click_t = 0.0
        self._last_right_click_t = 0.0
        self._prev_index_folded = False
        self._prev_middle_folded = False

    def update(self, gesture: FrameGesture | None):
        """Chamado uma vez por frame com o gesto da mão ativa (ou None)."""
        cfg = self._cfg

        if gesture is None:
            self._lost_frames += 1
            if self.mode == DRAGGING and self._lost_frames > cfg.lost_hand_release_frames:
                self._gui.mouseUp()
                self.mode = IDLE
            if self._lost_frames > cfg.lost_hand_release_frames:
                self._smoother.reset()
                self._pinch_frames = 0
                self._release_frames = 0
                self._prev_index_folded = False
                self._prev_middle_folded = False
            return

        self._lost_frames = 0

        target = map_to_screen(
            gesture.anchor[0], gesture.anchor[1], cfg, self._screen_w, self._screen_h
        )
        x, y = self._smoother.update(target)
        self._gui.moveTo(x, y)

        if self.mode == IDLE:
            self._update_idle(gesture)
        else:
            self._update_dragging(gesture)

        self._prev_index_folded = gesture.index_folded
        self._prev_middle_folded = gesture.middle_folded

    def _update_idle(self, gesture: FrameGesture):
        cfg = self._cfg
        if gesture.pinch:
            self._pinch_frames += 1
            if self._pinch_frames >= cfg.pinch_grace_frames:
                self._gui.mouseDown()
                self.mode = DRAGGING
                self._release_frames = 0
            return

        self._pinch_frames = 0

        # Uma pinça em formação curva o indicador e parece um clique: se o
        # polegar e o indicador já estão próximos, a pinça vence o clique.
        if gesture.pinch_ratio < cfg.pinch_release:
            return

        now = time.monotonic()
        if (
            gesture.index_folded
            and not self._prev_index_folded
            and now - self._last_left_click_t > cfg.click_cooldown_s
        ):
            self._gui.click(button="left")
            self._last_left_click_t = now
        elif (
            gesture.middle_folded
            and not self._prev_middle_folded
            and now - self._last_right_click_t > cfg.click_cooldown_s
        ):
            self._gui.click(button="right")
            self._last_right_click_t = now

    def _update_dragging(self, gesture: FrameGesture):
        if gesture.pinch:
            self._release_frames = 0
            return
        self._release_frames += 1
        if self._release_frames >= self._cfg.pinch_grace_frames:
            self._gui.mouseUp()
            self.mode = IDLE
            self._pinch_frames = 0

    def release(self):
        """Solta o botão se estiver arrastando (usado ao pausar/sair)."""
        if self.mode == DRAGGING:
            self._gui.mouseUp()
            self.mode = IDLE
        self._pinch_frames = 0
        self._release_frames = 0
