# Anki-Cali Draw Plus

[简体中文](README.md) · **English**

Anki-Cali Draw Plus is a desktop Anki handwriting add-on based on Anki-Cali Draw. Thanks to the original author for developing and sharing the add-on. [Original add-on on AnkiWeb (1205964508)](https://ankiweb.net/shared/info/1205964508)

## What's new in Plus

- **Separate pen and touch controls.** Write with a stylus on the infinite canvas and pan with a finger without switching tools.
- **Two-finger gestures.** Pinch to zoom or pan with two fingers on the blackboard.
- **Editable SVG strokes.** Reopen a drawing after inserting it into a card to select, move, or erase individual strokes and keep drawing.
- **Pen cursor and remembered thickness.** Change the cursor shape and size, or hide it. The canvas remembers the last pen thickness you selected.

## Install and use

1. Download the `.ankiaddon` file, choose **Tools → Add-ons → Install from file**, then restart Anki. The local add-on ID is `anki_cali_draw_plus`. The same package works with x64 and ARM64 builds of Anki. On a Windows ARM tablet, use the official **Windows 11 (ARM)** build. [Latest Plus release](https://github.com/Saner123321/anki-cali-draw-plus/releases/latest) · [Official Anki downloads](https://apps.ankiweb.net/)
2. In the Add, Edit, or Browse window, click the blackboard icon with an **Anki-Cali Draw Plus** tooltip. Choose **Insert into note** to save the drawing to a field. In the Add window, press **Add** to save the note itself.
3. To edit a saved drawing, click the toolbar icon labeled **Reopen a saved drawing**. If the note has multiple drawings, choose one by its field and position. Click **Update drawing** to save it in place.
4. Under **Tools → Anki-Cali Draw Plus → Settings… → Drawing**, choose a crosshair, dot, hollow circle, or hidden cursor. You can also adjust cursor size and pressure sensitivity. On a touchscreen without a stylus, choose **Draw with a finger**.

The blackboard title bar has controls for settings, minimize, maximize or restore, and close. Use the same toolbar button to restore a minimized blackboard and keep drawing. Settings opens above the blackboard. By default, the blackboard opens beside the Add or Edit window that launched it. When space is limited, it overlaps one side.

Under **Settings → General → Interface language**, choose **Follow Anki**, **English**, or **简体中文**. By default, Plus uses Simplified Chinese when Anki is set to Chinese and English otherwise. Saving applies the language to open blackboards and preserves their drawings.

## Using both add-ons and updating Plus

Plus hides duplicate buttons from the original add-on in the top toolbar and editor by default. The original `1205964508` can stay enabled and receive AnkiWeb updates through **Tools → Add-ons → Check for Updates**. To show both sets of buttons, clear **Hide duplicate buttons from the original Anki-Cali Draw** under **Settings… → Toolbar**.

For Plus updates, choose **Tools → Anki-Cali Draw Plus → Check for updates (GitHub)…**, confirm the installation, and restart Anki. Plus reads the version and checksum from the latest GitHub Release, verifies the package with SHA-256, and uses the Anki installer to preserve local settings. Each device can check for updates independently. If you have version 0.1.0, install the latest GitHub release from file once.

While reviewing, use `Ctrl+Alt+Shift+E` to open the blackboard or `Ctrl+Alt+Shift+D` to open the on-card annotation overlay. In the overlay, dragging with a finger scrolls the card and its ink together. Pinch-to-zoom is available on the blackboard. `Alt+Shift+Z` toggles the drawing tools. **Copy PNG** copies the selection or the whole blackboard as a standard image.

## Drawing format and compatibility

A note field references an SVG in Anki media through a standard `<img>` tag. The original Canvas drawing routines generate the SVG paths. Versioned JSON inside the file stores world coordinates, raw and smoothed stylus pressure, color, width, and stroke type. The desktop editor reads this JSON to restore editable strokes. Other clients can display the SVG as an ordinary image without the drawing add-on.

Each revision is written through Anki's media API under a content-based filename. Saving an edit replaces the selected image's `src` and preserves its width and other attributes. Copies elsewhere can continue to reference the previous revision. Anki's **Check Media** lists old files when no notes reference them. To open a drawing whose media is missing, sync or restore its SVG first. PNG drawings from older versions remain viewable as images.

The editor supports Plus SVGs up to 24 MiB. Saving a selection can create a separate drawing. When editing an existing drawing, **Update drawing** saves the whole canvas.

In the default touch mode, fingers navigate the canvas. When the stylus touches down, other touch points leave the current gesture. A 120 ms delay after pen-up helps avoid accidental input. Palm-first contact, drivers that report stylus input as a mouse, and device-specific multitouch behavior still need hardware verification.

## Build and maintain the upstream snapshot

Run `python build.py` to create an installable package. The `upstream/ankiweb` branch holds the original 1.3.2 release snapshot, tagged `upstream-1205964508-1794405980`. If a new upstream release appears, import it on that branch, leaving out local `meta.json`, user settings, and caches. Tag the imported version, merge the branch into `main`, resolve any conflicts, and rerun the desktop and sync tests.

To release Plus, update `human_version` in `manifest.json`, commit the change, and push the matching `vX.Y.Z` tag. GitHub Actions builds the package and publishes the release. Original AnkiWeb updates can be installed separately. Bringing their changes into Plus uses the upstream import process.

## License

The repository and `.ankiaddon` package retain the upstream MIT license and copyright notice verbatim, including the `<YOUR NAME>` placeholder in the original notice. [LICENSE](LICENSE)

## Source references

We consulted AnkiDraw for pressure sampling, smoothing, and `touch-action` handling, and Image Editor Enhanced for reopening SVGs, using `write_data()`, and updating image references. Plus uses its own input routing and drawing format. [AnkiDraw source](https://github.com/Rytisgit/Anki-StylusDraw/tree/858f5f4be1a5a9945ae87450460dfc1c75cfb83f/AnkiDraw) · [Image Editor Enhanced source](https://github.com/Ficello/Anki-Image-Editor-Enhanced-Edition-/tree/4675b50cc07e1defb3e8672870a572186aa8d68e)
