# 更新日志 · Changelog

## v0.1.6

### 简体中文

- 画板和复习批注现在可以复制选区或整张画布的可编辑笔迹。粘贴后保留压感数据、颜色和线宽，可以整体移动、逐笔编辑或撤销粘贴。
- 粘贴到 Anki 笔记字段会插入可重新打开的 SVG。也可以右键点击已有的 Plus 绘图，选择 **复制可编辑绘图**，再粘贴到其他笔记或画板。
- 剪贴板同时提供普通图片，方便粘贴到支持图片的应用。复习批注工具栏另有按钮，可将卡片和批注一起复制为图片。

### English

- Copy selected strokes or the whole drawing from a blackboard or review annotation. Pasted strokes retain pressure data, color, and width. Move them together, edit them individually, or undo the paste.
- Paste into an Anki note field to insert an SVG you can reopen and edit. Right-click an existing Plus drawing and choose **Copy editable drawing** to reuse it in another note or blackboard.
- The clipboard also includes an image for other apps. The review annotation toolbar has a separate button to copy the card and its annotations as an image.

## v0.1.5

### 简体中文

- 记住上次选择的笔尖粗细。编辑画板、复习黑板和批注层共用这个设置，重启 Anki 后仍会恢复。

### English

- Remember the last selected pen width across the editor blackboard, review blackboard, and annotation overlay, including after an Anki restart.

## v0.1.4

### 简体中文

- 从添加或编辑窗口打开画板时，原窗口保持可见。画板会优先在窗口旁展开，空间不足时覆盖一侧。

### English

- Keep the Add or Edit window visible when opening the blackboard. The blackboard opens beside it when space allows and overlaps one side on smaller screens.

## v0.1.3

### 简体中文

- 检查 GitHub 更新时，优先读取发行版附带的版本和 SHA-256 校验文件，降低 GitHub API 限流对更新检查的影响。

### English

- Check the version and SHA-256 checksum from the GitHub release asset first so update checks can continue when the GitHub API is rate-limited.

## v0.1.2

### 简体中文

- 修复设置窗口被画板挡住的问题，画板最大化时也能操作设置。
- 画板新增最小化、最大化和还原按钮。通过原入口即可恢复最小化的画板。
- 界面语言可选简体中文、英文或跟随 Anki。

### English

- Keep Settings above the blackboard, including when the blackboard is maximized.
- Add minimize, maximize, and restore controls. Reopen a minimized blackboard from its original toolbar button.
- Add Simplified Chinese and English interface options, with an option to follow Anki's language.

## v0.1.1

### 简体中文

- 原版和 Plus 同时启用时，默认隐藏重复的原版按钮。可在 Plus 的工具栏设置恢复显示，原版仍可通过 AnkiWeb 更新。
- 新增 **检查更新（GitHub）**，可从 Anki 菜单下载安装 Plus 的新版本。

### English

- Hide duplicate buttons by default when the original add-on and Plus are both enabled. The Plus toolbar settings can show the original buttons again, and the original add-on can still receive AnkiWeb updates.
- Add **Check for updates (GitHub)** to download and install new versions of Plus from Anki.
