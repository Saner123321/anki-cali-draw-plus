"""Transfer editable Plus drawings through the desktop clipboard."""
from __future__ import annotations

import base64
import json

from anki.errors import BackendError
from aqt import mw
from aqt.qt import QApplication, QBuffer, QByteArray, QImage, QImageReader, QIODevice, QMimeData, QSize, Qt
from aqt.utils import tooltip

from .drawing_media import (MAX_SVG_BYTES, MEDIA_NAME, clipboard_media_names, load_clipboard_svg,
                            media_name, read_scene, read_svg)
from .i18n import tr

DRAWING_MIME = "application/vnd.anki-cali-draw-plus.svg"
MAX_PREVIEW_BASE64 = 24 * 1024 * 1024


def _clipboard():
    return QApplication.clipboard()


def _drawing_bytes(mime: QMimeData) -> bytes:
    data = mime.data(DRAWING_MIME)
    if not data or data.size() > MAX_SVG_BYTES:
        raise ValueError("Invalid drawing on the clipboard.")
    return bytes(data)


def copy_drawing(payload: str, parent) -> None:
    """Expose the original strokes and the ordinary image clipboard format together."""
    try:
        if len(payload) > MAX_SVG_BYTES * 2 + MAX_PREVIEW_BASE64:
            raise ValueError("Invalid drawing on the clipboard.")
        data = json.loads(payload)
        svg = data["svg"].encode("utf-8")
        load_clipboard_svg(svg)
        preview = data.get("png", "")
        if not isinstance(preview, str) or len(preview) > MAX_PREVIEW_BASE64:
            raise ValueError("Invalid drawing on the clipboard.")
        image = QImage()
        if preview:
            image.loadFromData(base64.b64decode(preview, validate=True), "PNG")
    except (ValueError, AttributeError, KeyError, TypeError, RecursionError):
        tooltip(tr("Could not copy the drawing."), parent=parent)
        return

    _set_drawing(svg, image, parent)


def _set_drawing(svg: bytes, image: QImage, parent) -> None:
    mime = QMimeData()
    mime.setData(DRAWING_MIME, QByteArray(svg))
    if not image.isNull():
        mime.setImageData(image)
    _clipboard().setMimeData(mime)
    tooltip(tr("Editable drawing copied."), parent=parent)


def editor_copy_action(web, menu) -> None:
    col = mw.col
    if col is None or not hasattr(web, "lastContextMenuRequest"):
        return
    request = web.lastContextMenuRequest()
    if request is None:
        return
    url = request.mediaUrl().toString()
    prefix = mw.serverURL()
    if not url.startswith(prefix) or not MEDIA_NAME.fullmatch(filename := url[len(prefix):]):
        return

    def copy() -> None:
        if mw.col is not col:
            return
        try:
            svg = read_svg(col, filename)
            load_clipboard_svg(svg)
        except ValueError as exc:
            tooltip(tr(str(exc)), parent=web)
            return
        buffer = QBuffer()
        buffer.setData(svg)
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        reader = QImageReader(buffer, b"svg")
        size = reader.size()
        if max(size.width(), size.height()) > 4096:
            reader.setScaledSize(size.scaled(QSize(4096, 4096), Qt.AspectRatioMode.KeepAspectRatio))
        _set_drawing(svg, reader.read(), web)

    menu.addAction(tr("Copy editable drawing"), copy)


def paste_strokes(parent, insert) -> None:
    """Read editable ink or the Plus images selected in another Anki field."""
    mime = _clipboard().mimeData()
    groups = []
    try:
        if mime and mime.hasFormat(DRAWING_MIME):
            _width, scene = load_clipboard_svg(_drawing_bytes(mime))
            groups.append(scene)
        elif mime and mime.hasHtml() and mw.col is not None:
            html = mime.html()
            if len(html) > MAX_SVG_BYTES:
                raise ValueError("Invalid drawing on the clipboard.")
            total = 0
            for filename in clipboard_media_names(html, mw.serverURL()):
                scene = read_scene(mw.col, filename)
                total += len(scene)
                if total > MAX_SVG_BYTES:
                    raise ValueError("Invalid drawing on the clipboard.")
                groups.append(scene)
    except (ValueError, OSError) as exc:
        tooltip(tr(str(exc)), parent=parent)
        return

    groups = [scene for scene in groups if scene != "[]"]
    if groups:
        insert("[" + ",".join(groups) + "]")
    else:
        tooltip(tr("No editable Plus strokes on the clipboard."), parent=parent)


def editor_paste_mime(mime: QMimeData, web, _internal: bool, _extended: bool, drop_event: bool) -> QMimeData:
    """Let Anki insert the SVG at the caret and keep its normal paste/undo handling."""
    if drop_event or not mime.hasFormat(DRAWING_MIME) or mw.col is None or getattr(web.editor, "note", None) is None:
        return mime
    result = QMimeData()
    try:
        svg = _drawing_bytes(mime)
        width, _scene = load_clipboard_svg(svg)
        expected = media_name(svg)
        filename = mw.col.media.write_data(expected, svg)
        if filename != expected:
            raise ValueError("Anki could not keep the drawing media filename.")
        result.setHtml(f'<img src="{filename}" width="{width}">')
    except (ValueError, OSError, BackendError) as exc:
        tooltip(tr(str(exc)), parent=web)
    return result
