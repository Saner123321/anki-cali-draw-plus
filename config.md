### Anki-Cali Draw – settings

Open the friendly settings window with **Tools → Anki-Cali Draw → Settings…**, the ⚙ button on the blackboard / annotation toolbar, or the *Config* button of this add-on.

Advanced keys (for hand-editing `config.json`):

- `save_to_card.paste_mode` – `ask` (choose the field every time) or `field` (always use `target_field`; empty = last field of the note).
- `save_to_card.insert_position` – `end`, `start` or `replace`.
- `save_to_card.export_scale` – size of the picture on the card: `1` = as drawn, `2` = twice as large ... (0.25 – 8).
- `save_to_card.image_html` – HTML inserted; `{filename}` is the stored media file and `{width}` the display width in px.
- `persistence` – `clear_on_next`, `per_card` or `keep`.
- `placement` – `beside`, `overlay` or `remember`.
- `board_opacity` – blackboard opacity from `0.0` (fully transparent) to `1.0` (solid); default `0.4`.
- `solid_background` – `true` = always solid (100 %), ignoring `board_opacity`.
- `pressure_enabled`, `pressure_strength` – stylus pressure sensitivity (0-100).
- `zen_style` – `writing` (default: tools hide while you draw), `toggle` (tools stay hidden until `zen_shortcut` is pressed) or `off`. The eye button in the toolbar hides/shows the tools manually in any style.
- `favorite_colors` – the five favourite colours (edited from the colour picker in the toolbar).
- `show_board_button`, `show_annotate_button` – the two icon buttons in Anki's top toolbar.
- `show_editor_button` – the draw button in the card editor (Add / Edit / Browser). It inserts the drawing into the field you were editing.
