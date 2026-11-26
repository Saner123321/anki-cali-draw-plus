"""Exercise the desktop add-on and its hosted update in a profile with no account."""
import base64
import json
import shutil
import sys
import time
import traceback
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / ".anki-test"
BASE = TEST / "desktop"
STAGE = sys.argv[1]
assert STAGE in ("write", "reopen", "update")
sys.path.insert(0, str(ROOT))
sys.argv = [sys.argv[0], "-b", str(BASE)]

import aqt
from aqt.profiles import ProfileManager
from aqt.qt import QEventLoop, QTimer
from aqt.webview import AnkiWebView

from build import build

BASE.mkdir(parents=True, exist_ok=True)
pm = ProfileManager(BASE)
pm.setupMeta()
pm.meta.update(defaultLang="en_US", firstRun=False)
pm.set_update_check(False)
if STAGE == "write":
    pm.create("Cali Plus Test")
pm.load("Cali Plus Test")
pm.profile.update(syncKey=None, autoSync=False)
pm.save()
pm.db.close()

target = BASE / "addons21" / "anki_cali_draw_plus"
target.mkdir(parents=True, exist_ok=True)
with ZipFile(build()) as archive:
    archive.extractall(target)
original = Path.home() / "AppData/Roaming/Anki2/addons21/1205964508"
if original.is_dir():
    shutil.copytree(original, BASE / "addons21/1205964508", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("meta.json", "__pycache__", "user_files"))
    (BASE / "addons21/1205964508/meta.json").write_text('{"mod": 1794405980}')

aqt.AnkiApp.KEY = "Anki-Cali-Draw-Plus-Dev-20261126"


def pause(ms=30):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def until(get, label, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if result := get():
            return result
        pause()
    raise AssertionError(f"Timed out: {label}")


def js(web, source):
    out = []
    web.evalWithCallback(source, out.append)
    until(lambda: out, source[:90])
    return out[0]


def whole(button):
    return f"[...document.querySelectorAll('button')].find(b=>b.textContent==={json.dumps(button)}).click()"


def editor_image(web, filename):
    return js(web, """(() => {
      const name=""" + json.dumps(filename) + """;
      const find=root=>[...root.querySelectorAll('img')].some(i=>i.src.endsWith('/'+name)) ||
        [...root.querySelectorAll('*')].some(e=>e.shadowRoot && find(e.shadowRoot));
      return find(document);
    })()""")


def real_editor(col, note):
    browser = aqt.dialogs.open("Browser", aqt.mw)
    browser.search_for(f"nid:{note.id}")
    until(lambda: browser.editor.note and browser.editor.note.id == note.id, "Browser showing the note")
    until(lambda: js(browser.editor.web, "!!document.getElementById('caliplus_editor')"), "editor buttons render")
    assert js(browser.editor.web, """(() => {
      const old=document.getElementById('ankicali_editor');
      const reopen=document.getElementById('caliplus_edit');
      return old && getComputedStyle(old).display==='none' && reopen && getComputedStyle(reopen).display!=='none';
    })()"""), "only Plus drawing buttons should be visible in the editor"
    return browser


def review_tools(mw, addon, note):
    mw.col.decks.select(note.cards()[0].did)
    mw.moveToState("review")
    until(lambda: mw.reviewer.card, "reviewer launched")
    addon.toggle_annotation()
    web = mw.reviewer.web
    until(lambda: js(web, "!!window.__caliplus"), "review annotation loaded")
    result = js(web, """(() => {
      const before=__caliplus.dump();
      const root=[...document.querySelectorAll('div')].map(e=>e.shadowRoot).find(r=>r&&r.querySelector('.ad-wl'));
      if(!root || root.querySelector('.ad-wl').textContent!=='2')return false;
      const canvas=root.getElementById('top');
      const pen={pointerId:101,pointerType:'pen',button:0,clientX:100,clientY:100};
      canvas.dispatchEvent(new PointerEvent('pointerdown',pen));
      canvas.dispatchEvent(new PointerEvent('pointerup',pen));
      const width=JSON.parse(__caliplus.dump()).at(-1).w;
      __caliplus.setTheme(true);
      __caliplus.load('[{"t":"pen","hl":true,"c":"auto","w":15,"p":[[5,6],[9,10]]}]');
      const stroke=JSON.parse(__caliplus.dump())[0];
      __caliplus.setTheme(false);
      __caliplus.load(before);
      return width===2 && stroke.hl && stroke.w===15;
    })()""")
    assert result, "annotation highlighter or theme change failed"
    addon.toggle_annotation()
    addon.toggle_board()
    board = until(lambda: addon._board and addon._board._ready and addon._board, "review blackboard ready")
    assert js(board.web, "ankiBridge.dump()") == "", "editor ink leaked into review blackboard"
    assert js(board.web, "document.querySelector('.ad-wl').textContent") == "2"
    js(board.web, "ankiBridge.load('[{\"t\":\"pen\",\"c\":\"auto\",\"w\":3,\"p\":[[25,30]]}]')")
    copied = []
    board._copy_png = copied.append
    js(board.web, whole("Copy PNG"))
    png = until(lambda: copied, "review blackboard clipboard image")[0]
    assert base64.b64decode(png).startswith(b"\x89PNG\r\n\x1a\n")
    addon.toggle_board()


def editor_window_controls(board, editor):
    from anki import lang
    from aqt.qt import QApplication, QDialogButtonBox, QTabWidget, Qt
    from anki_cali_draw_plus.i18n import interface_language
    from anki_cali_draw_plus.settings import SettingsDialog

    board.resize(850, 710)
    normal_size = board.size()
    board.bar.maximize_button.click()
    until(board.isMaximized, "canvas maximized from its title bar")
    assert board.bar.maximize_button.accessibleName() == "Restore"
    assert board.size().width() >= normal_size.width()
    original = js(board.web, "ankiBridge.dump()")

    def change_language(value, tab):
        result = []

        def inspect_and_save():
            dialog = QApplication.activeModalWidget()
            try:
                assert isinstance(dialog, SettingsDialog), "settings did not become the active modal window"
                assert dialog.parentWidget() is board
                assert dialog.windowHandle().transientParent() is board.windowHandle()
                assert dialog.windowModality() == Qt.WindowModality.WindowModal
                if sys.platform == "win32":
                    import win32gui
                    hwnd = int(dialog.winId())
                    canvas_hwnd = int(board.winId())
                    while hwnd and hwnd != canvas_hwnd:
                        hwnd = win32gui.GetWindow(hwnd, 2)  # GW_HWNDNEXT, next lower in the native Z order
                    assert hwnd == canvas_hwnd, "native settings window is behind the canvas"
                assert dialog.findChild(QTabWidget).tabText(0) == tab
                dialog.language.setCurrentIndex(dialog.language.findData(value))
                dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save).click()
                result.append(True)
            except Exception:
                result.append(traceback.format_exc())
                if isinstance(dialog, SettingsDialog):
                    dialog.reject()

        QTimer.singleShot(120, inspect_and_save)
        board.bar.settings_button.click()
        assert result == [True], result
        assert board.isMaximized(), "settings save should leave the canvas maximized"

    change_language("zh_CN", "General")
    assert board.bar.maximize_button.toolTip() == "还原"
    assert js(board.web, "document.querySelector('[data-cali-tip=Pen]').getAttribute('data-tip')") == "画笔"
    change_language("en", "常规")
    assert board.bar.maximize_button.toolTip() == "Restore"
    change_language("auto", "General")
    actual = lang.current_lang
    try:
        lang.current_lang = "zh-CN"
        assert interface_language() == "zh_CN"
        lang.current_lang = "en_US"
        assert interface_language() == "en"
    finally:
        lang.current_lang = actual

    board.bar.minimize_button.click()
    until(board.isMinimized, "canvas minimized from the title bar")
    session = board._session
    js(editor.web, "document.getElementById('caliplus_editor').click()")
    until(lambda: board.isVisible() and not board.isMinimized(), "editor button restores minimized canvas")
    assert board.isMaximized() and board._session == session, "restore should keep the editor session and window mode"
    board.bar.maximize_button.click()
    until(lambda: not board.isMaximized(), "canvas restored to normal size")
    assert board.size() == normal_size
    assert js(board.web, "ankiBridge.dump()") == original


def add_mode(mw, addon):
    from anki_cali_draw_plus.drawing_media import drawing_refs

    dialog = aqt.dialogs.open("AddCards", mw)
    editor = dialog.editor
    area = dialog.screen().availableGeometry()
    width = min(650, area.width() // 2)
    dialog.setGeometry(area.right() - width - 30, area.top() + 65, width, min(550, area.height() - 100))
    front = f"Cali Plus Add workflow {time.time_ns()}"
    editor.note["Front"] = front
    editor.loadNote(focusTo=1)
    until(lambda: js(editor.web, "!!document.getElementById('caliplus_editor')"), "Add toolbar ready")
    editor.currentField = 1
    main_state = mw.windowState()
    mw.showMinimized()
    try:
        js(editor.web, "document.getElementById('caliplus_editor').click()")
        board = until(lambda: addon._editor_board._target.editor is editor and addon._editor_board.isVisible() and addon._editor_board,
                      "Add mode opens a separate drawing even when the main window is minimized")
        assert dialog.isVisible() and not dialog.isMinimized() and mw.isMinimized()
        assert board.windowHandle().transientParent() is dialog.windowHandle()
        if sys.platform == "win32":
            import win32gui
            assert win32gui.GetWindow(int(board.winId()), 4) == int(dialog.winId())  # GW_OWNER
            assert win32gui.IsWindowVisible(int(dialog.winId())) and not win32gui.IsIconic(int(dialog.winId()))
        if dialog.frameGeometry().left() - area.left() >= 350:
            assert not board.frameGeometry().intersects(dialog.frameGeometry())
    finally:
        mw.setWindowState(main_state)
    js(board.web, "ankiBridge.load('[{\"t\":\"pen\",\"c\":\"auto\",\"w\":3,\"p\":[[25,30]]}]')")
    editor_window_controls(board, editor)
    board.hide_panel()
    dialog.move(area.left() + 30, dialog.y())
    editor.currentField = 1
    js(editor.web, "document.getElementById('caliplus_editor').click()")
    until(board.isVisible, "canvas reopens beside the moved editor")
    assert dialog.isVisible() and not dialog.isMinimized()
    if area.right() - dialog.frameGeometry().right() >= 350:
        assert board.frameGeometry().left() > dialog.frameGeometry().right()
    js(board.web, whole("Insert into note"))
    ref = until(lambda: drawing_refs("Back", editor.note["Back"]), "image inserted in Add mode")[0]
    until(lambda: editor_image(editor.web, ref.filename), "Add editor image")
    dialog.addCards()
    until(lambda: any(ref.filename in mw.col.get_note(nid)["Back"]
                      for nid in mw.col.find_notes(f'"{front}"')), "Add saved the note")
    board.hide_panel()
    dialog.close()


def github_update(mw, addon):
    from anki_cali_draw_plus import updater

    manifest = target / "manifest.json"
    current = json.loads(manifest.read_bytes())
    # Exercise the menu with an artificially older version in the isolated copy.
    manifest.write_text(json.dumps({**current, "human_version": "0.1.4"}))
    manager = mw.addonManager
    saved = {**manager.getConfig("anki_cali_draw_plus"), "cursor_size": 31}
    manager.writeConfig("anki_cali_draw_plus", saved)
    original_meta = manager.addonMeta("1205964508")
    user_file = target / "user_files" / "test-update-data.txt"
    user_file.parent.mkdir(exist_ok=True)
    user_file.write_text("retain me")
    menu = next(action.menu() for action in mw.form.menuTools.actions() if action.text() == addon.NAME)
    action = next(action for action in menu.actions() if "GitHub" in action.text())
    messages = []
    ask, info, warning, open_link = updater.askUser, updater.showInfo, updater.showWarning, updater.openLink
    api_descriptor = updater._api_release_descriptor

    def reject_api():
        raise AssertionError("The published update should work without the GitHub REST API")

    def approve(message, **kwargs):
        if message.startswith("Install Anki-Cali Draw Plus "):
            return True
        messages.append(message)
        return False

    updater.askUser = approve
    updater.showInfo = updater.showWarning = lambda message, **kwargs: messages.append(message)
    updater.openLink = lambda url: messages.append(url)
    updater._api_release_descriptor = reject_api
    try:
        action.trigger()
        until(lambda: messages, "GitHub update menu completed", seconds=50)
        assert "was installed" in messages[0], messages
        assert manager.getConfig("anki_cali_draw_plus") == saved
        assert user_file.read_text() == "retain me"
        assert manager.addonMeta("1205964508") == original_meta and manager.isEnabled("1205964508")
        version = json.loads(manifest.read_bytes())["human_version"]
        assert version == current["human_version"]
        assert updater.find_update(version) is None
    finally:
        updater.askUser, updater.showInfo, updater.showWarning, updater.openLink = ask, info, warning, open_link
        updater._api_release_descriptor = api_descriptor


def run():
    browser = preview = None
    try:
        mw = aqt.mw
        col = until(lambda: mw.col, "isolated Anki collection")
        import anki_cali_draw_plus as add_on
        from anki_cali_draw_plus.drawing_media import drawing_refs, read_scene

        assert "1205964508" in sys.modules, "upstream did not load alongside Plus"
        toolbar = mw.toolbar.web
        ready = "document.querySelectorAll('#caliplus_board svg, #caliplus_annotate svg').length===2"
        until(lambda: js(toolbar, ready), "Plus toolbar icon rendering")
        original_visibility = "['ankicali_board','ankicali_annotate'].map(id=>getComputedStyle(document.getElementById(id)).display)"
        assert js(toolbar, original_visibility) == ["none", "none"]
        pm = mw.addonManager
        config = pm.getConfig("anki_cali_draw_plus")
        original = pm.addonMeta("1205964508")
        pm.writeConfig("anki_cali_draw_plus", {**config, "hide_upstream_buttons": False})
        mw.toolbar.draw()
        until(lambda: js(toolbar, ready), "toolbar refresh without deduplication")
        assert all(style != "none" for style in js(toolbar, original_visibility))
        pm.writeConfig("anki_cali_draw_plus", config)
        mw.toolbar.draw()
        assert pm.addonMeta("1205964508") == original and pm.isEnabled("1205964508")
        fixture = TEST / "fixture.json"
        if STAGE == "write":
            cfg = pm.getConfig("anki_cali_draw_plus")
            pm.writeConfig("anki_cali_draw_plus", {k: v for k, v in cfg.items() if k != "pen_width"})
            deck = col.decks.id("Cali Plus Test")
            model = col.models.by_name("Basic")
            note = col.new_note(model)
            note["Front"] = "Cali Plus SVG test"
            note["Back"] = "Preserve <b>this text</b>."
            col.add_note(note, deck)
            browser = real_editor(col, note)
            browser.editor.currentField = 1
            js(browser.editor.web, "document.getElementById('caliplus_editor').click()")
            board = until(lambda: add_on._editor_board and add_on._editor_board._ready and add_on._editor_board,
                          "Plus editor toolbar opens the board")
            result = js(board.web, (ROOT / "tests/input.js").read_text())
            assert result == "ok", result
            pause(220)
            result = js(board.web, (ROOT / "tests/touch.js").read_text())
            assert result == "ok", result
            saved = until(lambda: drawing_refs("Back", col.get_note(note.id)["Back"]), "initial SVG save")[0]
            until(lambda: board._target.drawing is not None, "save acknowledgement")
            until(lambda: saved.filename in browser.editor.note["Back"] and editor_image(browser.editor.web, saved.filename),
                  "inserted image appears in the live editor")
            strokes = json.loads(read_scene(col, saved.filename))
            assert len(strokes) == 5 and abs(strokes[0]["p"][1][3] - .8) < .01, strokes
            assert col.get_note(note.id)["Back"].startswith("Preserve <b>this text</b>.")
            assert js(board.web, "document.querySelector('.ad-wl').textContent") == "3"
            js(board.web, """(() => {
              const slider=document.querySelector('.ad-slider.v'), rect=slider.getBoundingClientRect();
              const p={pointerId:111,pointerType:'pen',button:0,clientX:rect.left+2,clientY:rect.bottom-rect.height/39};
              slider.dispatchEvent(new PointerEvent('pointerdown',p));
              slider.dispatchEvent(new PointerEvent('pointerup',p));
            })()""")
            until(lambda: pm.getConfig("anki_cali_draw_plus")["pen_width"] == 2, "slider stores width 2")
            # Close the editor first so its final flush cannot overwrite fixture setup.
            browser.close()
            browser = None
            pause(200)
            other = col.get_note(note.id)
            other["Front"] += f'<br><img src="{saved.filename}">'
            col.update_note(other)
            fixture.write_text(json.dumps({"nid": note.id, "saved": saved.filename, "strokes": strokes}))
        elif STAGE == "reopen":
            original = json.loads(fixture.read_text())
            note = col.get_note(original["nid"])
            assert drawing_refs("Front", note["Front"])[0].filename == original["saved"]
            browser = real_editor(col, note)
            # Open the second reference via the same picker used by the toolbar.
            from aqt.qt import QInputDialog
            original_picker = QInputDialog.getItem
            QInputDialog.getItem = lambda _parent, _title, _label, choices, *_: (choices[1], True)
            try:
                js(browser.editor.web, "document.getElementById('caliplus_edit').click()")
                board = until(lambda: add_on._editor_board and add_on._editor_board._ready and add_on._editor_board,
                              "Plus reopen toolbar opens the board")
            finally:
                QInputDialog.getItem = original_picker
            assert js(board.web, "document.querySelector('.ad-wl').textContent") == "2", "pen width survived restart"
            loaded = json.loads(js(board.web, "ankiBridge.dump()"))
            assert [{k: v for k, v in s.items() if k != "id"} for s in loaded] == original["strokes"]
            # Delete the isolated first stroke, leaving the other four.
            js(board.web, """(() => {
                const c=document.getElementById('top');
                const e=(type,opts)=>c.dispatchEvent(new PointerEvent(type,{pointerId:1,pointerType:'mouse',button:0,buttons:1,...opts}));
                const strokes=JSON.parse(ankiBridge.dump());
                const xmin=Math.min(...strokes.flatMap(s=>s.p.map(p=>p[0]-s.w)));
                const xmax=Math.max(...strokes.flatMap(s=>s.p.map(p=>p[0]+s.w)));
                const ymin=Math.min(...strokes.flatMap(s=>s.p.map(p=>p[1]-s.w)));
                const ymax=Math.max(...strokes.flatMap(s=>s.p.map(p=>p[1]+s.w)));
                const z=Math.min(1,Math.min(innerWidth/(xmax-xmin),innerHeight/(ymax-ymin))*.85);
                const at={clientX:innerWidth/2+(225-(xmin+xmax)/2)*z,clientY:innerHeight/2+(160-(ymin+ymax)/2)*z};
                window.dispatchEvent(new KeyboardEvent('keydown',{key:'v'}));
                e('pointerdown',at);e('pointerup',{...at,buttons:0});
                window.dispatchEvent(new KeyboardEvent('keydown',{key:'Delete'}));
            })()""")
            after = json.loads(js(board.web, "ankiBridge.dump()"))
            assert [{k: v for k, v in s.items() if k != "id"} for s in after] == original["strokes"][1:]
            js(board.web, whole("Update drawing"))
            changed = until(lambda: next((r for r in drawing_refs("Back", col.get_note(note.id)["Back"])
                                         if r.filename != original["saved"]), None), "replacement saved")
            until(lambda: board._target.drawing.filename == changed.filename, "update acknowledgement")
            until(lambda: changed.filename in browser.editor.note["Back"] and editor_image(browser.editor.web, changed.filename),
                  "updated image appears in the live editor")
            actual = col.get_note(note.id)
            assert len(drawing_refs("Back", actual["Back"])) == 1
            assert actual["Back"].startswith("Preserve <b>this text</b>.")
            assert drawing_refs("Front", actual["Front"])[0].filename == original["saved"]
            assert len(json.loads(read_scene(col, changed.filename))) == 4
            assert not col.media.check().missing
            preview = AnkiWebView(parent=mw, title="Cali Plus media test")
            preview.stdHtml(actual["Back"], context=mw.reviewer)
            until(lambda: js(preview, "document.images[0]?.naturalWidth || 0"), "SVG rendered as img")
            browser.close()
            browser = None
            board.hide_panel()
            add_mode(mw, add_on)
            review_tools(mw, add_on, actual)
            fixture.write_text(json.dumps({**original, "updated": changed.filename}))
        else:
            github_update(mw, add_on)
        (TEST / f"{STAGE}.result").write_text("PASS", encoding="utf-8")
    except Exception:
        (TEST / f"{STAGE}.result").write_text(traceback.format_exc(), encoding="utf-8")
    finally:
        if preview:
            preview.cleanup()
        if browser:
            browser.close()
        QTimer.singleShot(50, aqt.mw.close)


aqt.gui_hooks.profile_did_open.append(lambda: QTimer.singleShot(750, run))
aqt.run()
