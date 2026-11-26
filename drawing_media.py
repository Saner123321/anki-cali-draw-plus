"""The standalone SVG media format and field references used by Cali Draw Plus."""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

MEDIA_NAME = re.compile(r"cali-plus-[a-f0-9]{32}\.svg")
MAX_SVG_BYTES = 24 * 1024 * 1024
SVG_NS = "{http://www.w3.org/2000/svg}"
_COLOR = re.compile(r"#[0-9a-fA-F]{6}")
_ATTR = re.compile(r"""\s+([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?""")


def _number(value, limit: float) -> bool:
    return type(value) in (int, float) and -limit <= value <= limit and math.isfinite(value)


def load_scene(svg: bytes) -> str:
    """Read just the versioned stroke model. The editor never injects the SVG DOM."""
    if len(svg) > MAX_SVG_BYTES or b"<!" in svg:
        raise ValueError("Drawing file is too large or invalid.")
    try:
        root = ElementTree.fromstring(svg.decode("utf-8"))
        metadata = root.find(f"{SVG_NS}metadata[@id='cali-draw-plus']")
        if root.tag != SVG_NS + "svg" or metadata is None:
            raise ValueError("Missing drawing data.")
        document = json.loads(metadata.text or "")
    except (ElementTree.ParseError, UnicodeError, ValueError, RecursionError) as exc:
        raise ValueError("Could not read the embedded drawing data.") from exc
    if not isinstance(document, dict) or document.get("version") != 1:
        raise ValueError("Unsupported drawing format version.")
    strokes = document.get("strokes")
    if not isinstance(strokes, list):
        raise ValueError("Invalid drawing stroke list.")
    for stroke in strokes:
        if not isinstance(stroke, dict) or stroke.get("t") not in ("pen", "poly", "line", "arrow", "rect", "ellipse"):
            raise ValueError("Invalid stroke type.")
        kind, color, width, points = (stroke.get(k) for k in ("t", "c", "w", "p"))
        if not isinstance(color, str) or (color != "auto" and not _COLOR.fullmatch(color)):
            raise ValueError("Invalid stroke colour.")
        if not _number(width, 1e8) or width <= 0:
            raise ValueError("Invalid stroke width.")
        if any(k in stroke and type(stroke[k]) is not bool for k in ("pen", "hl", "closed")):
            raise ValueError("Invalid stroke flags.")
        if "ps" in stroke and (not _number(stroke["ps"], 1) or stroke["ps"] < 0):
            raise ValueError("Invalid pressure strength.")
        if not isinstance(points, list) or not points or (kind not in ("pen", "poly") and len(points) != 2):
            raise ValueError("Invalid stroke point count.")
        for point in points:
            if (not isinstance(point, list) or not 2 <= len(point) <= (4 if kind == "pen" else 2)
                    or not all(_number(v, 1e9) for v in point[:2])
                    or not all(_number(v, 1) and v >= 0 for v in point[2:])):
                raise ValueError("Invalid stroke coordinates or pressure.")
    # Keep the drawing model independent of any SVG or unknown JSON properties.
    keys = ("t", "c", "w", "p", "pen", "hl", "closed", "ps")
    return json.dumps([{key: s[key] for key in keys if key in s} for s in strokes], separators=(",", ":"))


def read_scene(col, filename: str) -> str:
    if not MEDIA_NAME.fullmatch(filename):
        raise ValueError("This image is not an editable Cali Draw Plus file.")
    try:
        with (Path(col.media.dir()) / filename).open("rb") as media:
            return load_scene(media.read(MAX_SVG_BYTES + 1))
    except OSError as exc:
        raise ValueError("Drawing media is missing. Sync media and try again.") from exc


def media_name(data: bytes) -> str:
    return f"cali-plus-{hashlib.sha256(data).hexdigest()[:32]}.svg"


class _Images(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=False)
        self.files: list[tuple[str, int, int]] = []
        self.offsets = [0, *(m.end() for m in re.finditer("\n", html))]
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs) -> None:
        if tag != "img":
            return
        sources = [value for name, value in attrs if name == "src"]
        if len(sources) != 1 or not sources[0] or not MEDIA_NAME.fullmatch(sources[0]):
            return
        line, column = self.getpos()
        start = self.offsets[line - 1] + column
        for attr in _ATTR.finditer(self.get_starttag_text(), 4):
            if attr[1].lower() == "src" and attr.lastindex > 1:
                lo, hi = attr.span(attr.lastindex)
                self.files.append((sources[0], start + lo, start + hi))
                return


@dataclass(frozen=True)
class DrawingRef:
    field: str
    filename: str
    occurrence: int
    repeated_field: str | None = None

    def replace(self, html: str, filename: str) -> str:
        matches = [(start, end) for name, start, end in _Images(html).files if name == self.filename]
        if self.repeated_field is None:
            valid = len(matches) == 1
        else:
            valid = html == self.repeated_field and self.occurrence < len(matches)
        if not valid:
            raise ValueError("The drawing reference changed. Reopen it from the note before saving.")
        start, end = matches[self.occurrence]
        return html[:start] + filename + html[end:]


def drawing_refs(field: str, html: str) -> list[DrawingRef]:
    files = [name for name, _, _ in _Images(html).files]
    totals, seen = {}, {}
    for name in files:
        totals[name] = totals.get(name, 0) + 1
    refs = []
    for name in files:
        occurrence = seen.get(name, 0)
        refs.append(DrawingRef(field, name, occurrence, html if totals[name] > 1 else None))
        seen[name] = occurrence + 1
    return refs
