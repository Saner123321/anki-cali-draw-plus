"""Sync the smoke-test note through Anki's official local sync server."""
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import aqt  # Load Anki's Windows runtime before importing the collection modules.
from anki.collection import Collection

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / ".anki-test"
SOURCE = TEST / "desktop" / "Cali Plus Test" / "collection.anki2"
USER = "caliplus-test"


def full_sync(col, auth, upload):
    status = col.sync_collection(auth, sync_media=False)
    col.close_for_full_sync()
    col.full_upload_or_download(auth=auth, upload=upload, server_usn=status.server_media_usn)
    col.reopen(after_full_sync=True)
    sync_media(col, auth)


def sync_media(col, auth):
    col.sync_media(auth)
    deadline = time.monotonic() + 30
    while col.media_sync_status().active:
        if time.monotonic() > deadline:
            raise TimeoutError("Media sync did not complete")
        time.sleep(.1)


def main():
    fixture = json.loads((TEST / "fixture.json").read_text())
    before, after = fixture["saved"], fixture["updated"]
    source = Collection(str(SOURCE))
    try:
        fields = source.get_note(fixture["nid"]).fields
        media = {name: (Path(source.media.dir()) / name).read_bytes() for name in (before, after)}
    finally:
        source.close()
    with tempfile.TemporaryDirectory(dir=TEST, ignore_cleanup_errors=True) as run_dir:
        root = Path(run_dir)
        with socket.socket() as address:
            address.bind(("127.0.0.1", 0))
            port = address.getsockname()[1]
        password = secrets.token_urlsafe(16)
        environment = {**os.environ, "SYNC_HOST": "127.0.0.1", "SYNC_PORT": str(port),
                       "SYNC_BASE": str(root / "server"), "SYNC_USER1": f"{USER}:{password}"}
        (root / "server").mkdir()
        with (TEST / "sync.log").open("wb") as log:
            server = subprocess.Popen(
                [sys.executable, "-c", "from anki.syncserver import run_sync_server; run_sync_server()"],
                env=environment, stdout=log, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            try:
                wait_for_server(server, port)
                endpoint = f"http://127.0.0.1:{port}/"
                sender_dir = root / "sender"
                sender_dir.mkdir()
                sender = Collection(str(sender_dir / "collection.anki2"))
                try:
                    note = sender.new_note(sender.models.by_name("Basic"))
                    note["Front"], note["Back"] = fields[0], fields[1].replace(after, before)
                    assert sender.media.write_data(before, media[before]) == before
                    sender.add_note(note, sender.decks.id("Cali Plus Sync Test"))
                    sender_auth = sender.sync_login(USER, password, endpoint)
                    full_sync(sender, sender_auth, True)
                    receiver_dir = root / "receiver"
                    receiver_dir.mkdir()
                    receiver = Collection(str(receiver_dir / "collection.anki2"))
                    try:
                        receiver_auth = receiver.sync_login(USER, password, endpoint)
                        full_sync(receiver, receiver_auth, False)
                        assert receiver.get_note(note.id).fields == note.fields
                        assert (Path(receiver.media.dir()) / before).read_bytes() == media[before]
                        assert not (Path(receiver.media.dir()) / after).exists()
                        note = sender.get_note(note.id)
                        note["Back"] = fields[1]
                        assert sender.media.write_data(after, media[after]) == after
                        sender.update_note(note)
                        for client, auth in ((sender, sender_auth), (receiver, receiver_auth)):
                            client.sync_collection(auth, sync_media=False)
                            sync_media(client, auth)
                        assert receiver.get_note(note.id).fields == fields
                        for name in (before, after):
                            assert (Path(receiver.media.dir()) / name).read_bytes() == media[name]
                        assert not receiver.media.check().missing
                    finally:
                        receiver.close()
                finally:
                    sender.close()
                print("PASS: Full sync and incremental edit transferred the note and both SVGs byte for byte", flush=True)
                if "--android" in sys.argv:
                    status_file = TEST / "android" / "sync-endpoint.json"
                    status_file.write_text(json.dumps({"port": port, "user": USER, "password": password}))
                    try:
                        deadline = time.monotonic() + 360
                        while status_file.exists() and time.monotonic() < deadline:
                            time.sleep(1)
                    finally:
                        status_file.unlink(missing_ok=True)
            finally:
                server.terminate()
                server.wait(timeout=10)


def wait_for_server(server, port):
    for _ in range(100):
        if server.poll() is not None:
            raise RuntimeError("Sync server exited. See .anki-test/sync.log")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=.25):
                return
        except OSError:
            time.sleep(.1)
    raise TimeoutError("Sync server did not start")


if __name__ == "__main__":
    main()
