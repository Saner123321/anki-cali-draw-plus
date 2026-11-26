"""Anki-Cali Draw Plus – add-on entry point.

Two drawing tools for the reviewer:
  * Blackboard  (blackboard.py)  – a frameless scratchpad window beside the card
  * Annotation  (annotation.py)  – transparent ink drawn directly on the card
  * Settings    (settings.py)    – the settings window
This file only wires them into Anki: shortcuts, menus, toolbar buttons, hooks.
"""
from __future__ import annotations

import json
from typing import Optional

from aqt import gui_hooks, mw
from aqt.qt import QAction, QInputDialog, QKeySequence, QShortcut
from aqt.utils import showInfo, tooltip

from .annotation import AnnotationOverlay
from .blackboard import BlackboardWindow, get_config
from .drawing_media import drawing_refs, read_scene
from .settings import SettingsDialog
from .updater import check_for_updates

NAME = "Anki-Cali Draw Plus"

_board: Optional[BlackboardWindow] = None
_editor_board: Optional[BlackboardWindow] = None
_board_action: Optional[QAction] = None
_annot_action: Optional[QAction] = None
_zen_action: Optional[QAction] = None
_shortcuts: dict = {}  # config key -> (QShortcut, default); kept apart from the menu items so no key text shows in names
_overlay = AnnotationOverlay()

# Toolbar icons: single-quoted attributes so they can sit inside a JSON/HTML string.
_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='16' height='16' fill='none' "
    "stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{}</svg>"
)
TOOLBAR_ICONS = {
    "caliplus_board": _SVG.format(  # easel with a scribble
        "<rect x='3' y='4' width='18' height='13' rx='2'/><path d='M8 21l2-4M16 21l-2-4'/>"
        "<path d='M7 12c2-4 3 2 5-1s3 1 5-2'/>"
    ),
    "caliplus_annotate": _SVG.format(  # card with a pen
        "<rect x='3' y='3' width='14' height='18' rx='2'/><path d='M7 8h6M7 12h3'/>"
        "<path d='M13 19l6.5-6.5a1.8 1.8 0 0 1 2.5 2.5L15.5 21.5 12 22z'/>"
    ),
}


def _key(name: str, default: str) -> str:
    return get_config().get(name, default)


# --------------------------------------------------------------------------
# Actions
# --------------------------------------------------------------------------
def open_settings() -> None:
    SettingsDialog(mw, on_saved=_on_settings_saved).exec()


def toggle_board() -> None:
    """Show/hide the blackboard window."""
    global _board
    if _board is not None and _board.isVisible():
        _board.hide_panel()
        return
    if mw.state != "review":
        tooltip(f"{NAME}: the blackboard is available while reviewing.")
        return
    if _board is None:
        _board = BlackboardWindow(on_toggle=toggle_board, on_settings=open_settings)
    _board.show_for_reviewer()


def open_from_editor(editor) -> None:
    note = getattr(editor, "note", None)
    if note is None:
        tooltip(f"{NAME}: select or open a note first.")
        return
    idx = editor.currentField
    if idx is None:
        idx = getattr(editor, "last_field_index", None)
    names = note.keys()
    field = names[idx] if idx is not None and 0 <= idx < len(names) else None
    _show_editor_board(editor, note, field)


def edit_from_editor(editor) -> None:
    note = getattr(editor, "note", None)
    col = mw.col
    if note is None or col is None:
        tooltip(f"{NAME}: select or open a note first.")
        return

    def open_drawing() -> None:
        if mw.col is not col or editor.note is not note or getattr(editor, "web", None) is None:
            return
        refs = [ref for field in note.keys() for ref in drawing_refs(field, note[field])]
        if not refs:
            tooltip("This note has no editable Cali Draw Plus drawings.", parent=editor.widget)
            return
        ref = refs[0]
        if len(refs) > 1:
            labels = [f"{i+1}. {ref.field} ({ref.filename[10:18]})" for i, ref in enumerate(refs)]
            chosen, ok = QInputDialog.getItem(editor.widget, NAME, "Open which drawing?", labels, 0, False)
            if not ok:
                return
            ref = refs[labels.index(chosen)]
        try:
            scene = read_scene(col, ref.filename)
        except ValueError as exc:
            tooltip(str(exc), parent=editor.widget)
            return
        if mw.col is col and editor.note is note:
            _show_editor_board(editor, note, ref.field, ref, scene)

    editor.call_after_note_saved(open_drawing)


def _show_editor_board(editor, note, field, drawing=None, scene="") -> None:
    global _editor_board
    if _editor_board is None:
        _editor_board = BlackboardWindow(on_toggle=lambda: _editor_board.hide_panel(), on_settings=open_settings)
    _editor_board.show_for_editor(editor, note, field, drawing, scene)


def toggle_zen() -> None:
    """Zen mode: hide / show every tool (blackboard and annotation mode)."""
    done = False
    if _overlay.enabled:
        _overlay.toggle_zen()
        done = True
    if _board is not None and _board.isVisible():
        _board.toggle_zen()
        done = True
    if _editor_board is not None and _editor_board.isVisible():
        _editor_board.toggle_zen()
        done = True
    if not done:
        tooltip(f"{NAME}: open the blackboard or annotation mode first.")


def toggle_annotation() -> None:
    """Show/hide ink drawn directly on the card."""
    _overlay.toggle()


# --------------------------------------------------------------------------
# Hooks
# --------------------------------------------------------------------------
def _on_show_question(card) -> None:
    _overlay.on_new_card(card.id)
    if _board is not None:
        _board.on_new_card(card.id)


def _on_answered(reviewer, card, ease) -> None:
    _overlay.on_answered(card.id)
    if _board is not None:
        _board.on_answered(card.id)


def _on_state_change(new_state: str, old_state: str) -> None:
    cfg = get_config()
    if new_state != "review":
        _overlay.disable()
        if _board is not None and _board.is_reviewer_target() and cfg.get("auto_hide_outside_review", True):
            _board.hide_panel()
    elif cfg.get("auto_open_on_review") and (_board is None or not _board.isVisible()):
        toggle_board()


def _on_theme_change(*_args) -> None:
    _overlay.apply_theme()
    for board in (_board, _editor_board):
        if board is not None:
            board.apply_theme()


def _on_profile_close() -> None:
    global _board, _editor_board
    _overlay.reset()
    for board in (_board, _editor_board):
        if board is not None:
            board.destroy_for_good()
    _board = _editor_board = None


def _add_editor_button(buttons: list, editor) -> None:
    """A 'draw' button in the editor toolbar of the Add, Edit Current and Browser windows."""
    if not get_config().get("show_editor_button", True):
        return
    buttons.append(
        editor.addButton(
            None,
            "caliplus_editor",
            open_from_editor,
            tip=f"{NAME}: draw and insert into this note",
            label=TOOLBAR_ICONS["caliplus_board"],
            id="caliplus_editor",
            rightside=False,
        )
    )
    buttons.append(
        editor.addButton(
            None,
            "caliplus_edit",
            edit_from_editor,
            tip=f"{NAME}: reopen a saved drawing in this note",
            label=TOOLBAR_ICONS["caliplus_annotate"],
            id="caliplus_edit",
            rightside=False,
        )
    )


def _add_context_menu(reviewer, menu) -> None:
    menu.addAction(f"{NAME}: Blackboard").triggered.connect(toggle_board)
    menu.addAction(f"{NAME}: Annotate on card").triggered.connect(toggle_annotation)


def _add_toolbar_links(links: list, toolbar) -> None:
    """Up to two small icon buttons in Anki's top toolbar (each can be hidden in Settings)."""
    cfg = get_config()
    if cfg.get("show_board_button", True):
        links.append(
            toolbar.create_link(
                "caliplus_board",
                "Blackboard",
                toggle_board,
                tip=f"{NAME}: blackboard",
                id="caliplus_board",
            )
        )
    if cfg.get("show_annotate_button", True):
        links.append(
            toolbar.create_link(
                "caliplus_annotate",
                "Annotate",
                toggle_annotation,
                tip=f"{NAME}: draw on the card",
                id="caliplus_annotate",
            )
        )


def _style_toolbar(web_content, context) -> None:
    """Style the Plus links and hide matching upstream actions within the toolbar views."""
    from aqt import toolbar
    from aqt.editor import Editor

    cfg = get_config()
    hide_original = cfg.get("hide_upstream_buttons", True)
    if isinstance(context, Editor):
        if hide_original and cfg.get("show_editor_button", True):
            web_content.head += "<style>#ankicali_editor{display:none!important}</style>"
        return
    # Modern Anki wraps the main toolbar in a TopToolbar context.
    if not isinstance(context, (toolbar.Toolbar, getattr(toolbar, "TopToolbar", toolbar.Toolbar))):
        return
    hidden = [f"#ankicali_{name}" for name in ("board", "annotate") if cfg.get(f"show_{name}_button", True)]
    if hide_original and hidden:
        web_content.head += "<style>" + ",".join(hidden) + "{display:none!important}</style>"
    web_content.head += (
        "<style>#caliplus_board,#caliplus_annotate{display:inline-flex!important;align-items:center;"
        "padding:2px 6px!important;margin:0 1px;border-radius:6px}"
        "#caliplus_board:hover,#caliplus_annotate:hover{background:rgba(127,127,127,.22)}</style>"
    )
    web_content.body += (
        "<script>(function(){var I=" + json.dumps(TOOLBAR_ICONS) + ";"
        "for(var id in I){var a=document.getElementById(id);if(a)a.innerHTML=I[id];}})();</script>"
    )


def _on_config_updated(_cfg: dict) -> None:
    for name, (shortcut, default) in _shortcuts.items():
        shortcut.setKey(QKeySequence(_key(name, default)))
    _overlay.apply_settings()  # theme, pressure, zen mode, favourite colours
    for board in (_board, _editor_board):
        if board is not None:
            board.apply_config()


def _refresh_toolbar() -> bool:
    """Redraw Anki's top toolbar so the show/hide switches apply immediately."""
    for name in ("draw", "redraw"):
        fn = getattr(mw.toolbar, name, None)
        if callable(fn):
            try:
                fn()
                return True
            except Exception:
                continue
    return False


_SETTING_LABELS = {
    "theme": "Theme",
    "persistence": "When the card changes",
    "shortcut": "Blackboard shortcut",
    "annotate_shortcut": "Annotate shortcut",
    "zen_shortcut": "Zen shortcut",
    "zen_style": "Zen mode",
    "pressure_enabled": "Pressure sensitivity",
    "pressure_strength": "Pressure strength",
    "touch_mode": "Finger input",
    "cursor_shape": "Pen cursor",
    "cursor_size": "Cursor size",
    "placement": "Blackboard position",
    "width": "Blackboard width",
    "board_opacity": "Blackboard opacity",
    "solid_background": "Solid blackboard",
    "auto_open_on_review": "Open blackboard on review",
    "auto_hide_outside_review": "Hide blackboard outside review",
    "show_board_button": "Blackboard toolbar button",
    "show_annotate_button": "Annotate toolbar button",
    "show_editor_button": "Editor draw button",
    "hide_upstream_buttons": "Hide duplicate original buttons",
    "save_to_card": "Save to card",
}


def _on_settings_saved(old: dict, new: dict) -> None:
    """Apply everything from the settings window right away, and always tell the user to
    restart Anki when something changed (a few settings only take effect after a restart)."""
    _on_config_updated({})
    _refresh_toolbar()
    changed = [
        _SETTING_LABELS.get(k, k)
        for k in sorted(set(old) | set(new))
        if k != "favorite_colors" and old.get(k) != new.get(k)
    ]
    if changed:
        showInfo(
            "Settings saved.\n\n"
            "Please restart Anki so that every change takes effect - some settings only apply "
            "after a restart.\n\nChanged: " + ", ".join(changed),
            parent=mw,
        )


# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------
def _setup() -> None:
    global _board_action, _annot_action, _zen_action

    menu = mw.form.menuTools.addMenu(NAME)
    _board_action = QAction("Blackboard", mw)
    _board_action.triggered.connect(toggle_board)
    menu.addAction(_board_action)
    _annot_action = QAction("Annotate on card", mw)
    _annot_action.triggered.connect(toggle_annotation)
    menu.addAction(_annot_action)
    _zen_action = QAction("Toggle zen mode (hide all tools)", mw)
    _zen_action.triggered.connect(toggle_zen)
    menu.addAction(_zen_action)
    menu.addSeparator()
    settings_action = QAction("Settings…", mw)
    settings_action.triggered.connect(open_settings)
    menu.addAction(settings_action)
    update_action = menu.addAction("Check for updates (GitHub)…")
    update_action.triggered.connect(lambda: check_for_updates(mw, update_action))

    # Keyboard shortcuts are plain QShortcuts, not menu-item shortcuts: they work the same
    # but Qt does not print the key combination next to the menu entries.
    for name, default, fn in (
        ("shortcut", "Ctrl+Alt+Shift+E", toggle_board),
        ("annotate_shortcut", "Ctrl+Alt+Shift+D", toggle_annotation),
        ("zen_shortcut", "Alt+Shift+Z", toggle_zen),
    ):
        sc = QShortcut(QKeySequence(_key(name, default)), mw)
        sc.activated.connect(fn)
        _shortcuts[name] = (sc, default)

    _overlay.open_settings = open_settings
    gui_hooks.reviewer_did_show_question.append(_on_show_question)
    gui_hooks.reviewer_did_answer_card.append(_on_answered)
    gui_hooks.reviewer_will_show_context_menu.append(_add_context_menu)
    gui_hooks.top_toolbar_did_init_links.append(_add_toolbar_links)
    gui_hooks.editor_did_init_buttons.append(_add_editor_button)
    gui_hooks.webview_will_set_content.append(_style_toolbar)
    gui_hooks.webview_did_receive_js_message.append(_overlay.on_js_message)
    gui_hooks.state_did_change.append(_on_state_change)
    gui_hooks.profile_will_close.append(_on_profile_close)
    if hasattr(gui_hooks, "theme_did_change"):  # newer Anki builds
        gui_hooks.theme_did_change.append(_on_theme_change)

    # The add-on's "Config" button opens our settings window instead of raw JSON.
    mw.addonManager.setConfigAction(__name__, open_settings)
    mw.addonManager.setConfigUpdatedAction(__name__, _on_config_updated)


_setup()
