"""Build the desktop add-on archive without machine-specific state."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
FILES = ("LICENSE", "README.md", "README.en.md", "__init__.py", "annotation.py", "blackboard.py", "drawing_media.py",
         "drawing_clipboard.py",
         "settings.py", "i18n.py", "updater.py", "manifest.json", "config.json", "config.md", "web/annotate.js",
         "web/board.html", "web/core.js", "web/scene.js")


def build() -> Path:
    version = json.loads((ROOT / "manifest.json").read_text())["human_version"]
    output = ROOT / "dist" / f"Anki-Cali-Draw-Plus-{version}.ankiaddon"
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name in FILES:
            archive.write(ROOT / name, name)
    descriptor = {"version": version, "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
    output.with_name("update.json").write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    print(build())
