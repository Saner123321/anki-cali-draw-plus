"""Build the desktop add-on archive without machine-specific state."""
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
FILES = ("LICENSE", "README.md", "__init__.py", "annotation.py", "blackboard.py", "drawing_media.py",
         "settings.py", "i18n.py", "updater.py", "manifest.json", "config.json", "config.md", "web/annotate.js",
         "web/board.html", "web/core.js", "web/scene.js")


def build() -> Path:
    version = json.loads((ROOT / "manifest.json").read_text())["human_version"]
    output = ROOT / "dist" / f"Anki-Cali-Draw-Plus-{version}.ankiaddon"
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name in FILES:
            archive.write(ROOT / name, name)
    return output


if __name__ == "__main__":
    print(build())
