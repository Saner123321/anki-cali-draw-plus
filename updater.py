"""Download released Plus versions and install them through Anki's add-on manager."""
from __future__ import annotations

import hashlib
import json
import logging
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zipfile import ZipFile

from aqt.addons import InstallOk
from aqt.utils import askUser, openLink, showInfo, showWarning

from .i18n import tr

REPO = "Saner123321/anki-cali-draw-plus"
RELEASES = f"https://github.com/{REPO}/releases"
LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
PACKAGE = "anki_cali_draw_plus"
MAX_DOWNLOAD = 2 * 1024 * 1024
_VERSION = re.compile(r"(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})")
_ZIP_PATH = re.compile(r"(?:[a-zA-Z0-9_-]+/)*[a-zA-Z0-9_][a-zA-Z0-9_.-]*")
_LOG = logging.getLogger(__name__)


def _version(text):
    match = _VERSION.fullmatch(text)
    if not match:
        raise ValueError("Invalid release version")
    return tuple(map(int, match.groups()))


def _download(url, limit, allowed_hosts, accept):
    request = Request(url, headers={"User-Agent": "Anki-Cali-Draw-Plus", "Accept": accept})
    with urlopen(request, timeout=12) as response:
        destination = urlsplit(response.geturl())
        if destination.scheme != "https" or destination.hostname not in allowed_hosts:
            raise ValueError("Unexpected GitHub download redirect")
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("GitHub download exceeds the size limit")
    return data


def _validate_addon(data, version):
    with ZipFile(BytesIO(data)) as bundle:
        entries = bundle.infolist()
        names = {entry.filename.casefold() for entry in entries}
        if len(names) != len(entries) or sum(entry.file_size for entry in entries) > 8 * 1024 * 1024:
            raise ValueError("Unexpected contents in the add-on archive")
        if any(not _ZIP_PATH.fullmatch(entry.filename) or entry.filename.endswith(".") for entry in entries):
            raise ValueError("Invalid add-on archive path")
        if (not {"__init__.py", "config.json", "manifest.json"} <= names
                or any("meta.json" in name.split("/") or name.startswith("user_files/") for name in names)):
            raise ValueError("The archive is missing add-on files or contains local settings")
        manifest = json.loads(bundle.read("manifest.json"))
        if manifest.get("package") != PACKAGE or manifest.get("human_version") != version or manifest.get("conflicts"):
            raise ValueError("The update archive targets a different add-on or version")
        if bundle.testzip() is not None:
            raise ValueError("Corrupt add-on archive")


def find_update(current):
    raw = _download(LATEST, 256 * 1024, {"api.github.com"}, "application/vnd.github+json")
    release = json.loads(raw)
    tag = release["tag_name"]
    if not tag.startswith("v") or release["draft"] or release["prerelease"]:
        raise ValueError("GitHub did not return a stable release")
    version = tag[1:]
    if _version(version) <= _version(current):
        return None
    name = f"Anki-Cali-Draw-Plus-{version}.ankiaddon"
    expected_url = f"{RELEASES}/download/{tag}/{name}"
    asset = next((asset for asset in release["assets"] if asset.get("name") == name), None)
    if asset is None or asset.get("browser_download_url") != expected_url:
        raise ValueError("GitHub release is missing the Plus installation file")
    digest = asset.get("digest")
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("GitHub release is missing a valid SHA-256 checksum")
    data = _download(expected_url, MAX_DOWNLOAD, {"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"},
                     "application/octet-stream")
    if f"sha256:{hashlib.sha256(data).hexdigest()}" != digest:
        raise ValueError("The download did not match its GitHub checksum")
    _validate_addon(data, version)
    return version, data


def check_for_updates(mw, action):
    action.setEnabled(False)

    def check():
        manifest = Path(__file__).with_name("manifest.json")
        return find_update(json.loads(manifest.read_bytes())["human_version"])

    def checked(future):
        action.setEnabled(True)
        try:
            update = future.result()
        except Exception:
            _LOG.exception("Could not fetch the Plus release from GitHub")
            if askUser(tr("Could not check or download the update. Open GitHub Releases in your browser?"), parent=mw, defaultno=True):
                openLink(f"{RELEASES}/latest")
            return
        if update is None:
            showInfo(tr("Anki-Cali Draw Plus is up to date."), parent=mw)
            return
        version, package = update
        if not askUser(tr("Install Anki-Cali Draw Plus {version} from GitHub?", version=version), parent=mw, defaultno=True):
            return
        try:
            result = mw.addonManager.install(BytesIO(package))
            if not isinstance(result, InstallOk) or not result.compatible:
                raise ValueError("Anki rejected the update")
        except Exception:
            _LOG.exception("Could not install the Plus update")
            showWarning(tr("Could not install the update. You can install it from the GitHub Releases page."), parent=mw)
            return
        action.setEnabled(False)
        showInfo(tr("Anki-Cali Draw Plus {version} was installed. Restart Anki to use it.", version=version), parent=mw)

    mw.taskman.with_progress(check, on_done=checked, parent=mw, label=tr("Checking GitHub for updates…"), uses_collection=False)
