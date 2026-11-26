"""Settings window for Anki-Cali Draw Plus (Tools -> Anki-Cali Draw Plus -> Settings...)."""
from __future__ import annotations

import json
from typing import Callable, Optional

from aqt import mw
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QKeySequence,
    QKeySequenceEdit,
    QLabel,
    QRadioButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import showWarning

from .blackboard import ADDON, DEFAULT_SAVE, get_config

LAST_FIELD_LABEL = "(Last field of the note)"


def _combo(items: list) -> QComboBox:
    box = QComboBox()
    for label, value in items:
        box.addItem(label, value)
    return box


def _select(box: QComboBox, value) -> None:
    idx = box.findData(value)
    box.setCurrentIndex(idx if idx >= 0 else 0)


def _hint(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("color: gray;")
    return label


def _all_field_names() -> list:
    names: list = []
    try:
        for model in mw.col.models.all():
            for fld in model["flds"]:
                if fld["name"] not in names:
                    names.append(fld["name"])
    except Exception:
        pass
    return sorted(names, key=str.lower)


def _key_text(edit: QKeySequenceEdit) -> str:
    seq = edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
    return seq.split(",")[0].strip()  # one chord only


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget, on_saved: Optional[Callable[[dict, dict], None]] = None) -> None:
        super().__init__(parent)
        self._on_saved = on_saved
        self.setWindowTitle("Anki-Cali Draw Plus - Settings")
        self.setMinimumWidth(470)

        tabs = QTabWidget()
        tabs.addTab(self._tab_general(), "General")
        tabs.addTab(self._tab_blackboard(), "Blackboard")
        tabs.addTab(self._tab_drawing(), "Drawing")
        tabs.addTab(self._tab_save(), "Save to card")
        tabs.addTab(self._tab_toolbar(), "Toolbar")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self._restore)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)
        self._load(get_config())

    # ------------------------------------------------------------------ tabs
    def _tab_general(self) -> QWidget:
        w, form = QWidget(), QFormLayout()
        w.setLayout(form)
        self.theme = _combo([("Follow Anki (automatic)", "auto"), ("Light", "light"), ("Dark", "dark")])
        self.persist = _combo(
            [
                ("Clear after I rate the card (scratchpad)", "clear_on_next"),
                ("Remember a drawing for each card", "per_card"),
                ("Keep one drawing for the whole session", "keep"),
            ]
        )
        self.k_board = QKeySequenceEdit()
        self.k_annot = QKeySequenceEdit()
        form.addRow("Theme:", self.theme)
        form.addRow("When the card changes:", self.persist)
        form.addRow("Blackboard shortcut:", self.k_board)
        form.addRow("Annotate shortcut:", self.k_annot)
        form.addRow(_hint("Click a shortcut box and press the keys you want. Ctrl is Cmd on macOS."))
        return w

    def _tab_blackboard(self) -> QWidget:
        w, form = QWidget(), QFormLayout()
        w.setLayout(form)
        self.placement = _combo(
            [
                ("Beside the Anki window", "beside"),
                ("Over the card (overlay)", "overlay"),
                ("Where I left it last time", "remember"),
            ]
        )
        self.width_px = QSpinBox()
        self.width_px.setRange(300, 2000)
        self.width_px.setSingleStep(20)
        self.width_px.setSuffix(" px")
        self.opacity = QSpinBox()
        self.opacity.setRange(0, 100)
        self.opacity.setSuffix(" %")
        self.opacity.setToolTip("0 % = fully transparent background, 100 % = solid. Default: 40 %")
        self.solid = QCheckBox("Solid blackboard (100 % opacity, no see-through)")
        self.solid.toggled.connect(lambda on: self.opacity.setEnabled(not on))
        self.auto_open = QCheckBox("Open the blackboard automatically when a review starts")
        self.auto_hide = QCheckBox("Hide it when I leave the reviewer")
        form.addRow("Opens:", self.placement)
        form.addRow("Width:", self.width_px)
        form.addRow(self.solid)
        form.addRow("Opacity:", self.opacity)
        form.addRow(self.auto_open)
        form.addRow(self.auto_hide)
        form.addRow(_hint("Opacity range: 0 % (fully transparent - only your ink and the tools are visible) to 100 % (solid). The default is 40 %; tick \"Solid blackboard\" if you prefer 100 %. Lower values fade the blackboard's background so you can see the card behind it - best with the \"Over the card\" position. Your ink always stays solid. On Linux this needs a compositing window manager."))
        return w

    def _tab_drawing(self) -> QWidget:
        w, form = QWidget(), QFormLayout()
        w.setLayout(form)
        self.pressure_on = QCheckBox("Pressure sensitivity: lines get thicker the harder you press")
        self.pressure_strength = QSpinBox()
        self.pressure_strength.setRange(0, 100)
        self.pressure_strength.setSuffix(" %")
        self.pressure_on.toggled.connect(self.pressure_strength.setEnabled)
        self.touch_mode = _combo([("Pan / pinch", "pan"), ("Draw with a finger", "ink")])
        self.cursor_shape = _combo([("Crosshair", "cross"), ("Dot", "dot"), ("Hollow circle", "ring"), ("Hidden", "hidden")])
        self.cursor_size = QSpinBox()
        self.cursor_size.setRange(6, 48)
        self.cursor_size.setSuffix(" px")
        self.zen_mode = _combo(
            [
                ("Hide the tools while I'm writing (default)", "writing"),
                ("Hide the tools until I press the zen shortcut", "toggle"),
                ("Off - never hide the tools automatically", "off"),
            ]
        )
        self.k_zen = QKeySequenceEdit()
        form.addRow(self.pressure_on)
        form.addRow("Strength:", self.pressure_strength)
        form.addRow(_hint("Needs a pressure-sensitive pen. Mouse and finger strokes have a constant width."))
        form.addRow("Finger input:", self.touch_mode)
        form.addRow("Pen cursor:", self.cursor_shape)
        form.addRow("Cursor size:", self.cursor_size)
        form.addRow("Zen mode:", self.zen_mode)
        form.addRow("Zen shortcut:", self.k_zen)
        form.addRow(
            _hint(
                "Zen mode hides every tool and the title bar so only your drawing is left. "
                "\"While I'm writing\": the tools fade out whenever you draw and return when you stop. "
                "\"Until I press the shortcut\": they stay hidden until you press the zen shortcut. "
                "You can also click the eye button in the toolbar at any time; a faint eye stays in the corner to bring the tools back."
            )
        )
        return w

    def _tab_save(self) -> QWidget:
        w, outer = QWidget(), QVBoxLayout()
        w.setLayout(outer)

        where = QGroupBox("Where should the drawing be pasted?")
        wl = QVBoxLayout(where)
        self.radio_ask = QRadioButton("Ask me every time")
        self.radio_field = QRadioButton("Always use this field:")
        self.field = QComboBox()
        self.field.addItem(LAST_FIELD_LABEL, "")
        for name in _all_field_names():
            self.field.addItem(name, name)
        self.radio_field.toggled.connect(self.field.setEnabled)
        wl.addWidget(self.radio_ask)
        wl.addWidget(self.radio_field)
        wl.addWidget(self.field)
        wl.addWidget(_hint("If the current note does not have that field, you will be asked instead. "
                           "When you draw from the card editor, the field you were editing is used first."))
        outer.addWidget(where)

        fmt, form = QGroupBox("Picture"), QFormLayout()
        fmt.setLayout(form)
        self.insert_pos = _combo(
            [
                ("Add at the end of the field", "end"),
                ("Add at the start of the field", "start"),
                ("Replace the field's content", "replace"),
            ]
        )
        self.scale = QDoubleSpinBox()
        self.scale.setRange(0.25, 8.0)
        self.scale.setSingleStep(0.25)
        self.scale.setDecimals(2)
        self.scale.setSuffix("x")
        self.scale.setToolTip("1x = as drawn on the blackboard, 2x = twice as large on the card ...")
        self.bg = QCheckBox("Include a background (otherwise transparent)")
        self.dark_export = QCheckBox("Dark background and light ink")
        form.addRow("Insert:", self.insert_pos)
        form.addRow("Size on card:", self.scale)
        form.addRow(_hint("1x = the size you drew it, 2x = twice as large, up to 8x. Pictures are always saved sharp; very wide ones may still be limited by your card template's own width rules."))
        form.addRow(self.bg)
        form.addRow(self.dark_export)
        outer.addWidget(fmt)
        outer.addStretch(1)
        return w

    def _tab_toolbar(self) -> QWidget:
        w, lay = QWidget(), QVBoxLayout()
        w.setLayout(lay)
        self.show_board = QCheckBox("Show the Blackboard button in Anki's top toolbar")
        self.show_annot = QCheckBox("Show the Annotate button in Anki's top toolbar")
        self.show_editor = QCheckBox("Show drawing buttons in the card editor (Add / Edit / Browser)")
        self.hide_upstream = QCheckBox("Hide duplicate buttons from the original Anki-Cali Draw")
        lay.addWidget(self.show_board)
        lay.addWidget(self.show_annot)
        lay.addWidget(self.show_editor)
        lay.addWidget(self.hide_upstream)
        lay.addWidget(_hint("The original add-on stays enabled and still receives AnkiWeb updates. Reopen the editor to see changes to its buttons."))
        lay.addStretch(1)
        return w

    # ----------------------------------------------------------- load/collect
    def _load(self, cfg: dict) -> None:
        save = {**DEFAULT_SAVE, **(cfg.get("save_to_card") or {})}
        _select(self.theme, cfg.get("theme", "auto"))
        _select(self.persist, cfg.get("persistence", "clear_on_next"))
        self.k_board.setKeySequence(QKeySequence(cfg.get("shortcut", "Ctrl+Alt+Shift+E")))
        self.k_annot.setKeySequence(QKeySequence(cfg.get("annotate_shortcut", "Ctrl+Alt+Shift+D")))
        _select(self.placement, cfg.get("placement", "beside"))
        self.width_px.setValue(int(cfg.get("width", 620)))
        self.opacity.setValue(int(round(float(cfg.get("board_opacity", 0.4)) * 100)))
        solid = bool(cfg.get("solid_background", False))
        self.solid.setChecked(solid)
        self.opacity.setEnabled(not solid)
        self.auto_open.setChecked(bool(cfg.get("auto_open_on_review", False)))
        self.auto_hide.setChecked(bool(cfg.get("auto_hide_outside_review", True)))
        on = bool(cfg.get("pressure_enabled", True))
        self.pressure_on.setChecked(on)
        self.pressure_strength.setValue(int(cfg.get("pressure_strength", 70)))
        self.pressure_strength.setEnabled(on)
        _select(self.touch_mode, cfg.get("touch_mode", "pan"))
        _select(self.cursor_shape, cfg.get("cursor_shape", "cross"))
        try:
            self.cursor_size.setValue(int(cfg.get("cursor_size", 24)))
        except (TypeError, ValueError):
            self.cursor_size.setValue(24)
        _select(self.zen_mode, cfg.get("zen_style", "writing"))
        self.k_zen.setKeySequence(QKeySequence(cfg.get("zen_shortcut", "Alt+Shift+Z")))
        self.show_board.setChecked(bool(cfg.get("show_board_button", True)))
        self.show_annot.setChecked(bool(cfg.get("show_annotate_button", True)))
        self.show_editor.setChecked(bool(cfg.get("show_editor_button", True)))
        self.hide_upstream.setChecked(bool(cfg.get("hide_upstream_buttons", True)))

        use_field = save["paste_mode"] == "field"
        self.radio_field.setChecked(use_field)
        self.radio_ask.setChecked(not use_field)
        self.field.setEnabled(use_field)
        target = save["target_field"]
        if target and self.field.findData(target) < 0:  # field from another note type
            self.field.addItem(target, target)
        _select(self.field, target)
        _select(self.insert_pos, save["insert_position"])
        self.scale.setValue(float(save["export_scale"]))
        self.bg.setChecked(bool(save["export_background"]))
        self.dark_export.setChecked(bool(save["export_dark_mode"]))

    def _collect(self) -> dict:
        cfg = dict(get_config())
        cfg.pop("show_toolbar_button", None)  # old key
        cfg.pop("opacity", None)  # old key
        cfg.pop("zen_mode", None)  # old key (replaced by zen_style)
        save = {**DEFAULT_SAVE, **(cfg.get("save_to_card") or {})}
        save.update(
            paste_mode="field" if self.radio_field.isChecked() else "ask",
            target_field=self.field.currentData() or "",
            insert_position=self.insert_pos.currentData(),
            export_scale=self.scale.value(),
            export_background=self.bg.isChecked(),
            export_dark_mode=self.dark_export.isChecked(),
        )
        cfg.update(
            theme=self.theme.currentData(),
            persistence=self.persist.currentData(),
            shortcut=_key_text(self.k_board),
            annotate_shortcut=_key_text(self.k_annot),
            zen_shortcut=_key_text(self.k_zen),
            zen_style=self.zen_mode.currentData(),
            pressure_enabled=self.pressure_on.isChecked(),
            pressure_strength=self.pressure_strength.value(),
            touch_mode=self.touch_mode.currentData(),
            cursor_shape=self.cursor_shape.currentData(),
            cursor_size=self.cursor_size.value(),
            placement=self.placement.currentData(),
            width=self.width_px.value(),
            board_opacity=round(self.opacity.value() / 100, 2),
            solid_background=self.solid.isChecked(),
            auto_open_on_review=self.auto_open.isChecked(),
            auto_hide_outside_review=self.auto_hide.isChecked(),
            show_board_button=self.show_board.isChecked(),
            show_annotate_button=self.show_annot.isChecked(),
            show_editor_button=self.show_editor.isChecked(),
            hide_upstream_buttons=self.hide_upstream.isChecked(),
            save_to_card=save,
        )
        return cfg

    # --------------------------------------------------------------- actions
    def _restore(self) -> None:
        self._load(mw.addonManager.addonConfigDefaults(ADDON) or {})

    def _save(self) -> None:
        cfg = self._collect()
        keys = [k for k in (cfg["shortcut"], cfg["annotate_shortcut"], cfg["zen_shortcut"]) if k]
        if len(keys) != len(set(keys)):
            showWarning("The Blackboard, Annotate and Zen shortcuts must all be different.", parent=self)
            return
        old = json.loads(json.dumps(get_config()))
        mw.addonManager.writeConfig(ADDON, cfg)
        if self._on_saved:
            self._on_saved(old, cfg)
        self.accept()
