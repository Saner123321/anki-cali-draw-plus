### Anki-Cali Draw Plus – settings

Open settings from **Tools → Anki-Cali Draw Plus → Settings…**, the ⚙ button on the blackboard / annotation toolbar, or the add-on's *Config* button.

Advanced keys (for hand-editing `config.json`):

- `save_to_card.paste_mode` – `ask` (choose the field every time) or `field` (always use `target_field`; empty = last field of the note).
- `save_to_card.insert_position` – `end`, `start` or `replace`.
- `save_to_card.export_scale` – size of the picture on the card: `1` = as drawn, `2` = twice as large ... (0.25 – 8).
- `save_to_card.image_html` – HTML for a new drawing. Include one `<img src="{filename}">`. `{width}` is the display width in pixels. Updating an existing drawing preserves its image attributes and surrounding HTML.
- `persistence` – `clear_on_next`, `per_card` or `keep`.
- `placement` – `beside`, `overlay` or `remember`.
- `board_opacity` – blackboard opacity from `0.0` (fully transparent) to `1.0` (solid); default `0.4`.
- `solid_background` – `true` = always solid (100 %), ignoring `board_opacity`.
- `pressure_enabled`, `pressure_strength` – stylus pressure sensitivity (0-100).
- `touch_mode` – `pan` enables finger pan and pinch on the blackboard. `ink` allows drawing with a finger. In annotation mode, `pan` scrolls the current card.
- `cursor_shape` – `cross`, `dot`, `ring`, or `hidden` for the drawing tools. The eraser and selection tools keep their own cursors.
- `cursor_size` – drawing cursor size in CSS pixels, from 6 to 48.
- `zen_style` – `writing` (default: tools hide while you draw), `toggle` (tools stay hidden until `zen_shortcut` is pressed) or `off`. The eye button in the toolbar hides/shows the tools manually in any style.
- `favorite_colors` – the five favourite colours (edited from the colour picker in the toolbar).
- `show_board_button`, `show_annotate_button` – the two icon buttons in Anki's top toolbar.
- `show_editor_button` – show the new-drawing and reopen-drawing buttons in the card editor (Add / Edit / Browser).
