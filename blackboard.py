"""Anki-Cali Draw blackboard window.

A small top-level tool window that hosts the bundled drawing page (web/board.html) inside
an ``AnkiWebView`` (QtWebEngine). Using AnkiWebView gives us, for free:

* ``pycmd(...)`` in JavaScript  -> ``_on_bridge_cmd`` in Python
* ``web.eval`` / ``web.evalWithCallback`` for Python -> JavaScript calls

Why a separate window and not a dock/child widget?
Anki's reviewer shortcuts (Space, 1-4, ...) are window-level QShortcuts on the
main window. Anything embedded in that window would trigger them while you
type or pick tools while drawing. A top-level tool window is a separate
shortcut context, so drawing never answers your cards by accident.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
from typing import Any, Callable, Optional

from aqt import mw
from aqt.operations.note import update_note
from aqt.qt import (
    QApplication,
    QHBoxLayout,
    QColor,
    QImage,
    QInputDialog,
    QLabel,
    QToolButton,
    QGuiApplication,
    QKeySequence,
    QPoint,
    QRect,
    QShortcut,
    Qt,
    QVBoxLayout,
    QWidget,
)
from aqt.theme import theme_manager
from aqt.utils import restoreGeom, saveGeom, tooltip
from aqt.webview import AnkiWebView

ADDON = mw.addonManager.addonFromModule(__name__)
GEOM_KEY = "caliDrawBoard"
EDGE = 5  # px of frame around the web view that acts as the resize border

PALETTE = {
    "light": {"bar": "#f4f4f8", "fg": "#1e1e1e", "bd": "#e1e1ea"},
    "dark": {"bar": "#232329", "fg": "#e6e6e6", "bd": "#3a3a45"},
}
MAX_STASHED_SCENES = 300

DEFAULT_SAVE = {
    "paste_mode": "ask",  # "ask" every time, or "field" = always target_field
    "target_field": "",  # "" = last field of the note
    "insert_position": "end",  # "end" | "start" | "replace"
    "image_html": '<img src="{filename}" width="{width}">',  # {width} = size on the card in px
    "export_scale": 2,
    "export_dark_mode": False,
    "export_background": True,
}


def get_config() -> dict:
    return mw.addonManager.getConfig(ADDON) or {}


_LEGACY_IMAGE_HTML = '<img src="{filename}">'


def save_config() -> dict:
    """The ``save_to_card`` section merged over defaults (user may omit keys)."""
    cfg = {**DEFAULT_SAVE, **(get_config().get("save_to_card") or {})}
    if cfg["image_html"].strip() == _LEGACY_IMAGE_HTML:  # old default saved by earlier versions
        cfg["image_html"] = DEFAULT_SAVE["image_html"]
    return cfg


def _img_html(template: str, filename: str, width: Optional[int]) -> str:
    html = template.format(filename=filename, width=width or "")
    return html.replace(' width=""', "")  # no usable width: let the card decide


DEFAULT_FAVORITES = ["#e03131", "#1971c2", "#2f9e44", "#f08c00", "#9c36b5"]
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
FAVORITE_LISTENERS: list = []  # callables run after the favourite colours change (blackboard + overlay)


def get_favorites() -> list:
    """Always exactly five valid #rrggbb colours."""
    out = list(DEFAULT_FAVORITES)
    raw = get_config().get("favorite_colors") or []
    for i, c in enumerate(raw[:5]):
        if isinstance(c, str) and _HEX.match(c):
            out[i] = c.lower()
    return out


def save_favorites(colors) -> list:
    out = list(DEFAULT_FAVORITES)
    for i, c in enumerate(list(colors)[:5]):
        if isinstance(c, str) and _HEX.match(c):
            out[i] = c.lower()
    cfg = dict(get_config())
    cfg["favorite_colors"] = out
    mw.addonManager.writeConfig(ADDON, cfg)
    for listener in list(FAVORITE_LISTENERS):
        try:
            listener()
        except Exception:  # a closed window must not break the others
            pass
    return out


def pressure_value() -> float:
    """0.0 = pressure sensitivity off, otherwise strength 0..1."""
    cfg = get_config()
    if not cfg.get("pressure_enabled", True):
        return 0.0
    try:
        return max(0.0, min(1.0, float(cfg.get("pressure_strength", 70)) / 100))
    except (TypeError, ValueError):
        return 0.7


def input_settings() -> dict:
    cfg = get_config()
    return {
        "touchMode": cfg.get("touch_mode", "pan"),
        "cursorShape": cfg.get("cursor_shape", "cross"),
        "cursorSize": cfg.get("cursor_size", 24),
    }


def zen_mode() -> str:
    # key is "zen_style" (not the old "zen_mode") so that everyone gets the new default: hide while writing
    mode = get_config().get("zen_style", "writing")
    return mode if mode in ("off", "toggle", "writing") else "writing"


def _event_pos(ev):
    """QMouseEvent position as a QPoint on both Qt5 and Qt6."""
    return ev.position().toPoint() if hasattr(ev, "position") else ev.pos()


class DragBar(QWidget):
    """Slim custom title bar for the frameless window: drag to move, X to hide."""

    def __init__(
        self, on_close: Callable[[], None], on_settings: Optional[Callable[[], None]] = None
    ) -> None:
        super().__init__()
        self.setObjectName("ankidrawBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(28)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 4, 0)
        lay.addWidget(QLabel("Anki-Cali Draw"))  # QLabel ignores clicks -> they reach the bar
        lay.addStretch(1)
        if on_settings:
            gear = QToolButton()
            gear.setText("\u2699")
            gear.setAccessibleName("Anki-Cali Draw settings")
            gear.setCursor(Qt.CursorShape.PointingHandCursor)
            gear.clicked.connect(on_settings)
            lay.addWidget(gear)
        btn = QToolButton()
        btn.setText("\u2715")
        btn.setAccessibleName("Hide (your drawing is kept)")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(on_close)
        lay.addWidget(btn)

    def restyle(self, c: dict) -> None:
        self.setStyleSheet(
            f"#ankidrawBar{{background:{c['bar']};}}"
            f"QLabel{{color:{c['fg']};font-weight:600;font-size:12px;}}"
            f"QToolButton{{color:{c['fg']};border:none;padding:3px 9px;border-radius:6px;}}"
            "QToolButton:hover{background:rgba(127,127,127,.25);}"
        )

    def mousePressEvent(self, ev) -> None:  # noqa: N802
        if ev.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle:
                handle.startSystemMove()  # native drag, works on Win/macOS/Linux


class BlackboardWindow(QWidget):
    def __init__(
        self,
        on_toggle: Callable[[], None],
        on_settings: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(mw, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self._on_toggle = on_toggle
        self._ready = False  # becomes True when the JS side says "calidraw:ready"
        self._queue: list[tuple[str, Optional[Callable]]] = []
        self._scenes: dict[int, str] = {}  # card id -> serialized elements (per_card mode)
        self._current_cid: Optional[int] = None
        self._placed = False
        self._destroying = False
        self._target = None  # (editor, field index) when opened from the card editor
        self._ontop = False
        self._translucent = False  # real see-through window (only when opacity < 100%)
        self._zen_hidden = False  # title bar hidden because the page is in zen mode

        self.setObjectName(GEOM_KEY)
        self.setWindowTitle("Anki-Cali Draw")
        self.resize(int(get_config().get("width", 620)), 640)

        self.web = AnkiWebView(parent=self, title="calidraw")
        if hasattr(self.web, "disable_zoom"):  # keep Ctrl+wheel for the canvas zoom
            self.web.disable_zoom()
        self.web.set_bridge_command(self._on_bridge_cmd, self)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMouseTracking(True)  # for resize cursors on the frame
        self.bar = DragBar(self.hide_panel, on_settings)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(EDGE, EDGE, EDGE, EDGE)
        layout.setSpacing(0)
        layout.addWidget(self.bar)
        layout.addWidget(self.web)

        # Window-local copy of the toggle shortcut (main-window shortcuts do not
        # fire while this separate window has focus).
        self._shortcut = QShortcut(QKeySequence(), self)
        self._shortcut.activated.connect(self._on_toggle)
        self._zen_shortcut = QShortcut(QKeySequence(), self)
        self._zen_shortcut.activated.connect(self.toggle_zen)
        FAVORITE_LISTENERS.append(self._push_settings)

        self.apply_config()
        self.web.setHtml(self._page_html())

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------
    def _resolve_theme(self) -> str:
        theme = get_config().get("theme", "auto")
        if theme in ("light", "dark"):
            return theme
        return "dark" if theme_manager.night_mode else "light"

    def _js_settings(self) -> dict:
        s = save_config()
        try:
            scale = max(0.25, min(8.0, float(s["export_scale"])))
        except (TypeError, ValueError):
            scale = 1.0
        return {
            "opacity": self._opacity(),
            "pressure": pressure_value(),
            **input_settings(),
            "zen": zen_mode(),
            "zenKey": get_config().get("zen_shortcut", "Alt+Z"),
            "favs": get_favorites(),
            "scale": scale,
            "exportDark": bool(s["export_dark_mode"]),
            "exportBackground": bool(s["export_background"]),
        }

    def _push_settings(self) -> None:
        """Settings changed: the page is loaded once, so tell it the new values."""
        self._run(f"ankiBridge.configure({json.dumps(self._js_settings())})")

    def _page_html(self) -> str:
        """Inline the settings and load the page with setHtml (no web server,
        no URL paths: nothing that can go 'Invalid path')."""
        settings = {"theme": self._resolve_theme(), **self._js_settings()}
        web = os.path.join(os.path.dirname(__file__), "web")
        with open(os.path.join(web, "board.html"), encoding="utf-8") as f:
            html = f.read()
        with open(os.path.join(web, "core.js"), encoding="utf-8") as f:
            core = f.read()
        html = html.replace("/*SETTINGS*/", f"window.ANKI_SETTINGS = {json.dumps(settings)};")
        return html.replace("/*CORE*/", core)

    def apply_config(self) -> None:
        cfg = get_config()
        self._shortcut.setKey(QKeySequence(cfg.get("shortcut", "Ctrl+Shift+E")))
        self._zen_shortcut.setKey(QKeySequence(cfg.get("zen_shortcut", "Alt+Z")))
        self.setWindowOpacity(1.0)  # QtWebEngine ignores window opacity; fade the page instead
        was_visible = self.isVisible()
        if self._sync_translucency() and was_visible:
            self.show()  # the native window was recreated
        self._push_settings()
        self._placed = False  # placement/width may have changed: re-place on next show
        if self.isVisible() and cfg.get("placement") != "remember":
            self._place()  # ...and apply it right now if the window is open
            self._placed = True
        self.apply_theme()

    def _opacity(self) -> float:
        try:
            cfg = get_config()
            if cfg.get("solid_background", False):
                return 1.0
            return min(1.0, max(0.0, float(cfg.get("board_opacity", 0.4))))  # default 40 %
        except (TypeError, ValueError):
            return 1.0

    def _sync_translucency(self) -> bool:
        """Make the window see-through only when needed. Returns True if it changed.

        QtWebEngine paints its own surface, so QWidget.setWindowOpacity does nothing
        to the page. Instead the window + web view become transparent and the page
        fades just its background (CSS), which also keeps your ink fully solid.
        """
        want = self._opacity() < 0.999
        if want == self._translucent:
            return False
        self._translucent = want
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, want)
        self.web.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, want)
        self._apply_web_background()
        # Toggling a window flag twice forces Qt to recreate the native window, which
        # is required for the translucency attribute to take effect.
        self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, False)
        return True

    def _apply_web_background(self) -> None:
        """AnkiWebView repaints its page background on theme changes; keep ours right."""
        if self._translucent:
            self.web.page().setBackgroundColor(QColor(0, 0, 0, 0))
            self.web.setStyleSheet("background: transparent;")
        else:
            dark = self._resolve_theme() == "dark"
            self.web.page().setBackgroundColor(QColor("#121212" if dark else "#ffffff"))
            self.web.setStyleSheet("")

    def apply_theme(self) -> None:
        c = PALETTE[self._resolve_theme()]
        self.setStyleSheet(f"#{GEOM_KEY}{{background:{c['bd']};}}")
        self.bar.restyle(c)
        self._apply_web_background()
        self._run(f"ankiBridge.setTheme({json.dumps(self._resolve_theme())})")

    # ------------------------------------------------------------------
    # Python -> JS (queued until the page has finished booting)
    # ------------------------------------------------------------------
    def _run(self, js: str, callback: Optional[Callable[[Any], None]] = None) -> None:
        if not self._ready:
            self._queue.append((js, callback))
            return
        if callback:
            self.web.evalWithCallback(js, callback)
        else:
            self.web.eval(js)

    def _flush_queue(self) -> None:
        queued, self._queue = self._queue, []
        for js, callback in queued:
            self._run(js, callback)

    def clear(self) -> None:
        self._run("ankiBridge.clear()")

    # ------------------------------------------------------------------
    # JS -> Python
    # ------------------------------------------------------------------
    def _on_bridge_cmd(self, cmd: str) -> Any:
        if cmd == "calidraw:ready":
            self._ready = True
            self._flush_queue()
        elif cmd == "calidraw:hide":
            self.hide_panel()
        elif cmd.startswith("calidraw:toast:"):
            tooltip(cmd[len("calidraw:toast:"):], parent=self)
        elif cmd.startswith("calidraw:zen:"):
            self._set_zen(cmd.endswith(":1"))
        elif cmd.startswith("calidraw:favs:"):
            try:
                save_favorites(json.loads(cmd[len("calidraw:favs:"):]))
            except ValueError:
                pass
        elif cmd.startswith("calidraw:copy:"):
            self._copy_png(cmd[len("calidraw:copy:"):].partition(":")[2])
        elif cmd.startswith("calidraw:save:"):
            width, _, data = cmd[len("calidraw:save:"):].partition(":")
            self._save_png_to_card(data, int(width) if width.isdigit() else None)
        return None

    # ------------------------------------------------------------------
    # Frameless-window resizing (the EDGE-px frame around the web view)
    # ------------------------------------------------------------------
    def _edges_at(self, pos) -> list:
        edges = []
        if pos.x() < EDGE:
            edges.append(Qt.Edge.LeftEdge)
        elif pos.x() > self.width() - EDGE:
            edges.append(Qt.Edge.RightEdge)
        if pos.y() < EDGE:
            edges.append(Qt.Edge.TopEdge)
        elif pos.y() > self.height() - EDGE:
            edges.append(Qt.Edge.BottomEdge)
        return edges

    def mouseMoveEvent(self, ev) -> None:  # noqa: N802
        e = self._edges_at(_event_pos(ev))
        if len(e) == 2:
            diag = (Qt.Edge.LeftEdge in e and Qt.Edge.TopEdge in e) or (
                Qt.Edge.RightEdge in e and Qt.Edge.BottomEdge in e
            )
            cur = Qt.CursorShape.SizeFDiagCursor if diag else Qt.CursorShape.SizeBDiagCursor
        elif e:
            horiz = e[0] in (Qt.Edge.LeftEdge, Qt.Edge.RightEdge)
            cur = Qt.CursorShape.SizeHorCursor if horiz else Qt.CursorShape.SizeVerCursor
        else:
            cur = Qt.CursorShape.ArrowCursor
        self.setCursor(cur)

    def mousePressEvent(self, ev) -> None:  # noqa: N802
        edges = self._edges_at(_event_pos(ev))
        handle = self.windowHandle()
        if edges and handle and ev.button() == Qt.MouseButton.LeftButton:
            combined = edges[0]
            for extra in edges[1:]:
                combined |= extra
            handle.startSystemResize(combined)

    # ------------------------------------------------------------------
    # Show / hide / placement
    # ------------------------------------------------------------------
    def show_panel(self) -> None:
        if not self._placed:
            self._place()
            self._placed = True
        if self._target is None and self._current_cid is None and mw.reviewer.card:
            # Opened mid-card: don't let the redraw hooks treat it as a "new" card.
            self._current_cid = mw.reviewer.card.id
        self.show()
        self.raise_()
        self.activateWindow()
        self.web.setFocus()

    def hide_panel(self) -> None:
        if self.isVisible() and get_config().get("placement") == "remember":
            saveGeom(self, GEOM_KEY)
        self.hide()
        self._return_focus()

    # -- which card is the drawing for? ---------------------------------
    def show_for_reviewer(self) -> None:
        self._target = None
        self._set_on_top(False)
        self._run(f"ankiBridge.setSaveLabel({json.dumps('Save to card')})")
        self.show_panel()

    def show_for_editor(self, editor) -> None:
        """Open for the Add / Edit / Browser editor: Save inserts into that note."""
        self._target = (editor, getattr(editor, "currentField", None))
        self._current_cid = None
        self._set_on_top(True)  # the editor is another top-level window
        self._run(f"ankiBridge.setSaveLabel({json.dumps('Insert into note')})")
        self.show_panel()

    def is_reviewer_target(self) -> bool:
        return self._target is None

    def _set_on_top(self, on: bool) -> None:
        if on != self._ontop:
            self._ontop = on
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, on)  # hides; show_panel re-shows

    def _return_focus(self) -> None:
        win = getattr(self._target[0], "parentWindow", None) if self._target else None
        try:
            (win or mw).activateWindow()
        except RuntimeError:  # editor window already destroyed
            mw.activateWindow()

    def _place(self) -> None:
        cfg = get_config()
        placement = cfg.get("placement", "beside")
        width = int(cfg.get("width", 620))

        if placement == "remember" and mw.pm.profile.get(f"{GEOM_KEY}Geom"):
            restoreGeom(self, GEOM_KEY)
            return

        if placement == "overlay":
            self.setGeometry(QRect(mw.web.mapToGlobal(QPoint(0, 0)), mw.web.size()))
            return

        # "beside" (also the first-run fallback for "remember")
        frame = mw.frameGeometry()
        screen = mw.screen() or QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        if avail.right() - frame.right() >= width:
            x = frame.right() + 1
        else:  # not enough room: cover the right edge of Anki instead
            x = max(avail.left(), frame.right() - width + 1)
        self.setGeometry(x, frame.top(), width, frame.height())

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        if not self._destroying:
            self.hide_panel()  # hide, don't destroy: the drawing survives
        event.accept()  # never block Anki from quitting

    # -- zen mode -----------------------------------------------------
    def toggle_zen(self) -> None:
        self._run("ankiBridge.toggleZen()")

    def _set_zen(self, hidden: bool) -> None:
        """The page entered/left 'tools hidden': hide the title bar too, and shift the
        drawing by its height so nothing jumps on screen."""
        if hidden == self._zen_hidden:
            return
        self._zen_hidden = hidden
        height = self.bar.height() or 28
        self.bar.setVisible(not hidden)
        self._run(f"ankiBridge.nudge({height if hidden else -height})")

    def destroy_for_good(self) -> None:
        if self._push_settings in FAVORITE_LISTENERS:
            FAVORITE_LISTENERS.remove(self._push_settings)
        self._destroying = True
        self.web.cleanup()
        self.close()
        self.deleteLater()

    # ------------------------------------------------------------------
    # Persistence modes (called from the reviewer hooks in __init__.py)
    # ------------------------------------------------------------------
    def on_new_card(self, card_id: int) -> None:
        """A question was shown. Same id => redraw of the same card; ignore."""
        if self._target is not None:  # drawing for the card editor: leave it alone
            return
        if card_id == self._current_cid:
            return
        previous, self._current_cid = self._current_cid, card_id
        mode = get_config().get("persistence", "clear_on_next")

        if mode == "clear_on_next":
            self.clear()
        elif mode == "per_card":
            if previous is not None:
                self._stash(previous)
            scene = self._scenes.get(card_id, "")
            self._run(f"ankiBridge.load({json.dumps(scene)})")
        # mode == "keep": do nothing

    def on_answered(self, card_id: int) -> None:
        """The user rated a card; the next one is about to be shown."""
        if self._target is not None:
            return
        mode = get_config().get("persistence", "clear_on_next")
        if mode == "per_card":
            self._stash(card_id)
            self.clear()
        elif mode == "clear_on_next":
            self.clear()
        self._current_cid = None

    def _stash(self, card_id: int) -> None:
        """Remember the canvas for ``card_id`` (JS calls run in order, so the
        dump always happens before any following clear/load)."""

        def store(serialized: Any) -> None:
            if serialized:
                self._scenes[card_id] = serialized
                while len(self._scenes) > MAX_STASHED_SCENES:
                    self._scenes.pop(next(iter(self._scenes)))
            else:
                self._scenes.pop(card_id, None)

        self._run("ankiBridge.dump()", store)

    # ------------------------------------------------------------------
    # Clipboard / card actions (thin wrappers around the module functions)
    # ------------------------------------------------------------------
    def _copy_png(self, b64: str) -> None:
        copy_png(b64, self)

    def _save_png_to_card(self, b64: str, width: Optional[int] = None) -> None:
        if self._target is not None:
            save_png_to_editor(b64, self._target[0], self._target[1], self, width)
        else:
            save_png_to_card(b64, self, width)


def copy_png(b64: str, parent: Optional[QWidget] = None) -> None:
    """Put a base64 PNG on the system clipboard as an image."""
    image = QImage()
    if not image.loadFromData(base64.b64decode(b64), "PNG"):
        tooltip("Could not copy the drawing.", parent=parent or mw)
        return
    QApplication.clipboard().setImage(image)
    tooltip("Drawing copied to clipboard.", parent=parent or mw)


def choose_field(note, parent: Optional[QWidget] = None) -> Optional[str]:
    """Pick the field that receives the picture. Returns None if the user cancels."""
    names = note.keys()
    cfg = save_config()
    wanted = cfg["target_field"]
    if cfg["paste_mode"] == "field":
        if not wanted:
            return names[-1]
        if wanted in names:
            return wanted
        tooltip(f'This note has no "{wanted}" field - please choose one.', parent=parent or mw)
    default = names.index(wanted) if wanted in names else len(names) - 1
    field, ok = QInputDialog.getItem(
        parent or mw, "Anki-Cali Draw", "Add the drawing to which field?", names, default, False
    )
    return field if ok else None


def _merge(old: str, html: str, position: str) -> str:
    if position == "replace" or not old.strip():
        return html
    return f"{html}<br>{old}" if position == "start" else f"{old}<br>{html}"


def save_png_to_card(b64: str, parent: Optional[QWidget] = None, width: Optional[int] = None) -> None:
    """Store a base64 PNG in the media folder and put it in a field of the current note."""
    parent = parent or mw
    card = mw.reviewer.card if mw.state == "review" else None
    if card is None:
        tooltip("No card is being reviewed.", parent=parent)
        return
    try:
        data = base64.b64decode(b64)
    except Exception:
        tooltip("Could not decode the exported image.", parent=parent)
        return
    note = card.note()
    field = choose_field(note, parent)
    if field is None:  # cancelled: nothing has been written yet
        return
    cfg = save_config()
    filename = mw.col.media.write_data(f"cali-draw-{card.id}-{int(time.time())}.png", data)
    html = _img_html(cfg["image_html"], filename, width)
    note[field] = _merge(note[field], html, cfg["insert_position"])
    update_note(parent=mw, note=note).success(
        lambda _changes: tooltip(f'Drawing added to "{field}".', parent=parent)
    ).run_in_background()


def save_png_to_editor(
    b64: str, editor, field_idx: Optional[int], parent: Optional[QWidget] = None, width: Optional[int] = None
) -> None:
    """Insert a base64 PNG into the note shown in a card editor (Add / Edit / Browser).

    Uses the field that was being edited when the blackboard was opened; if none was,
    the usual "ask / chosen field" setting decides.
    """
    parent = parent or mw
    if getattr(editor, "web", None) is None or getattr(editor, "note", None) is None:
        tooltip("The card editor was closed or has no note selected.", parent=parent)
        return
    try:
        data = base64.b64decode(b64)
    except Exception:
        tooltip("Could not decode the exported image.", parent=parent)
        return
    cfg = save_config()

    def insert() -> None:  # runs once the editor has flushed what you typed
        note = editor.note
        if note is None:
            return
        names = note.keys()
        if field_idx is not None and 0 <= field_idx < len(names):
            idx = field_idx
        else:
            chosen = choose_field(note, parent)
            if chosen is None:
                return
            idx = names.index(chosen)
        field = names[idx]
        filename = mw.col.media.write_data(f"cali-draw-{int(time.time())}.png", data)
        html = _img_html(cfg["image_html"], filename, width)
        note[field] = _merge(note[field], html, cfg["insert_position"])
        editor.loadNote(focusTo=idx)  # show it in the editor
        if note.id:  # existing note (Edit / Browser): persist; Add dialog saves on "Add"
            update_note(parent=editor.widget, note=note).run_in_background()
        tooltip(f'Drawing added to "{field}".', parent=parent)

    editor.call_after_note_saved(insert)
