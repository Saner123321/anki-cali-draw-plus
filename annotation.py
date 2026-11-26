"""Annotation mode: draw directly on top of the card.

The drawing surface is injected into Anki's own reviewer page (web/annotate.js),
so it is transparent by construction, scrolls with the card and needs no extra
window. This module injects it, keeps it in sync with the review flow and
handles the messages it sends back.
"""
from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional

from aqt import mw
from aqt.qt import QApplication, QTimer
from aqt.theme import theme_manager
from aqt.utils import tooltip

from .blackboard import FAVORITE_LISTENERS, get_config, get_favorites, pressure_value, save_favorites, zen_mode

_WEB = os.path.join(os.path.dirname(__file__), "web")


class AnnotationOverlay:
    def __init__(self) -> None:
        self.enabled = False
        self._scenes: dict[int, str] = {}
        self._cid: Optional[int] = None
        self._js_source: Optional[str] = None
        self.open_settings: Optional[Callable[[], None]] = None
        FAVORITE_LISTENERS.append(self.apply_settings)

    # -- helpers ----------------------------------------------------------
    @property
    def _web(self):
        return mw.reviewer.web

    def _dark(self) -> bool:
        theme = get_config().get("theme", "auto")
        return theme == "dark" or (theme == "auto" and theme_manager.night_mode)

    def _inject_and_show(self) -> None:
        if self._js_source is None:
            parts = []
            for name in ("core.js", "annotate.js"):  # engine first, then the overlay UI
                with open(os.path.join(_WEB, name), encoding="utf-8") as f:
                    parts.append(f.read())
            self._js_source = "\n".join(parts)
        self._web.eval(self._js_source)  # idempotent: no-op if already injected
        self._web.eval(f"__ankidraw.show({json.dumps(self._settings())})")

    def _settings(self) -> dict:
        return {
            "dark": self._dark(),
            "pressure": pressure_value(),
            "zen": zen_mode(),
            "zenKey": get_config().get("zen_shortcut", "Alt+Z"),
            "favs": get_favorites(),
        }

    def apply_settings(self) -> None:
        """Settings (or favourite colours) changed: update the overlay right now."""
        self._call(f"__ankidraw.configure({json.dumps(self._settings())})")

    def toggle_zen(self) -> None:
        self._call("__ankidraw.toggleZen()")

    def _call(self, js: str, cb=None) -> None:
        guarded = f"window.__ankidraw ? {js} : ''"
        if cb:
            self._web.evalWithCallback(guarded, cb)
        else:
            self._web.eval(guarded)

    def apply_theme(self) -> None:
        self._call(f"__ankidraw.setTheme({json.dumps(self._dark())})")

    def reset(self) -> None:
        """Forget everything (profile closing)."""
        self.enabled = False
        self._scenes.clear()
        self._cid = None

    # -- toggling ---------------------------------------------------------
    def toggle(self) -> None:
        if self.enabled:
            self.disable()
        elif mw.state != "review":
            tooltip("Annotation mode is available while reviewing.")
        else:
            self.enabled = True
            self._inject_and_show()

    def disable(self) -> None:
        if self.enabled:
            self.enabled = False
            self._call("__ankidraw.hide()")

    # -- review flow (same persistence modes as the blackboard) -----------
    def on_new_card(self, card_id: int) -> None:
        if card_id == self._cid:
            return  # same card redrawn (e.g. after an edit): keep the ink
        self._cid = card_id
        if self.enabled:
            self._inject_and_show()  # the reviewer page may have been reloaded
            if get_config().get("persistence") == "per_card":
                scene = self._scenes.get(card_id, "")
                self._call(f"__ankidraw.load({json.dumps(scene)})")

    def on_answered(self, card_id: int) -> None:
        mode = get_config().get("persistence", "clear_on_next")
        if mode == "per_card":
            def store(s: Any) -> None:
                if s:
                    self._scenes[card_id] = s
                else:
                    self._scenes.pop(card_id, None)
            self._call("__ankidraw.dump()", store)
            self._call("__ankidraw.clear()")
        elif mode == "clear_on_next":
            self._call("__ankidraw.clear()")
        self._cid = None

    # -- messages from the page -------------------------------------------
    def on_js_message(self, handled: tuple, message: str, context: Any) -> tuple:
        if not message.startswith("ankidraw:"):
            return handled
        if message == "ankidraw:closed":
            self.enabled = False
        elif message == "ankidraw:settings":
            if self.open_settings:
                self.open_settings()
        elif message.startswith("ankidraw:favs:"):
            try:
                save_favorites(json.loads(message[len("ankidraw:favs:"):]))
            except ValueError:
                pass
        elif message == "ankidraw:copy":
            self._copy_screenshot()
        return (True, None)

    def _copy_screenshot(self) -> None:
        """Copy the card + ink as an image (toolbar hidden for the shot)."""
        web = self._web

        def grab() -> None:
            QApplication.clipboard().setPixmap(web.grab())
            self._call("__ankidraw.unprep()")
            tooltip("Card with annotations copied to clipboard.")

        web.evalWithCallback("__ankidraw.prep()", lambda _r: QTimer.singleShot(80, grab))
