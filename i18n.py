"""Interface translations. English source strings are also the fallback keys."""
from anki import lang

_NATIVE = {
    "Anki-Cali Draw Plus - Settings": "Anki-Cali Draw Plus 设置",
    "Settings": "设置", "Settings…": "设置…", "Settings saved.": "设置已保存。",
    "Minimize": "最小化", "Maximize": "最大化", "Restore": "还原",
    "Hide (your drawing is kept)": "关闭画板（保留笔迹）",
    "General": "常规", "Blackboard": "画板", "Drawing": "书写", "Toolbar": "工具栏",
    "Save": "保存", "Cancel": "取消", "Restore Defaults": "恢复默认",
    "Interface language:": "界面语言：", "Follow Anki": "跟随 Anki",
    "Follow Anki (automatic)": "自动跟随 Anki", "Light": "浅色", "Dark": "深色",
    "Theme:": "主题：", "When the card changes:": "切换卡片时：",
    "Clear after I rate the card (scratchpad)": "评分后清空画板",
    "Remember a drawing for each card": "为每张卡片保留一张画板",
    "Keep one drawing for the whole session": "本次复习共用一张画板",
    "Blackboard shortcut:": "画板快捷键：", "Annotate shortcut:": "批注快捷键：",
    "Click a shortcut box and press the keys you want. Ctrl is Cmd on macOS.": "点选快捷键输入框后，按下所需组合键。macOS 上的 Ctrl 对应 Cmd。",
    "Beside the Anki window": "Anki 窗口旁", "Over the card (overlay)": "覆盖卡片", "Where I left it last time": "记住上次的位置",
    "Opens:": "打开位置：", "Width:": "宽度：", "Opacity:": "不透明度：",
    "0 % = fully transparent background, 100 % = solid. Default: 40 %": "0% 为完全透明，100% 为不透明。默认 40%。",
    "Solid blackboard (100 % opacity, no see-through)": "使用不透明背景（100%）",
    "Open the blackboard automatically when a review starts": "开始复习时自动打开画板",
    "Hide it when I leave the reviewer": "离开复习时隐藏画板",
    'Opacity range: 0 % (fully transparent - only your ink and the tools are visible) to 100 % (solid). The default is 40 %; tick "Solid blackboard" if you prefer 100 %. Lower values fade the blackboard\'s background so you can see the card behind it - best with the "Over the card" position. Your ink always stays solid. On Linux this needs a compositing window manager.':
        "不透明度范围为 0% 至 100%，默认 40%。调低后可以看到画板后方的卡片，笔迹保持清晰。Linux 需要支持合成的窗口管理器。",
    "Pressure sensitivity: lines get thicker the harder you press": "启用压感（越用力，笔迹越粗）",
    "Strength:": "压感强度：", "Needs a pressure-sensitive pen. Mouse and finger strokes have a constant width.": "需要支持压感的笔。鼠标和手指书写时线宽固定。",
    "Pan / pinch": "拖动／双指缩放", "Draw with a finger": "手指书写", "Finger input:": "手指操作：",
    "Crosshair": "十字", "Dot": "圆点", "Hollow circle": "空心圆", "Hidden": "隐藏",
    "Pen cursor:": "笔尖光标：", "Cursor size:": "光标大小：",
    "Zen mode:": "专注模式：", "Zen shortcut:": "专注模式快捷键：",
    "Hide the tools while I'm writing (default)": "书写期间隐藏工具（默认）",
    "Hide the tools until I press the zen shortcut": "隐藏工具，直到按下快捷键",
    "Off - never hide the tools automatically": "关闭自动隐藏",
    'Zen mode hides every tool and the title bar so only your drawing is left. "While I\'m writing": the tools fade out whenever you draw and return when you stop. "Until I press the shortcut": they stay hidden until you press the zen shortcut. You can also click the eye button in the toolbar at any time; a faint eye stays in the corner to bring the tools back.':
        "专注模式会收起工具和标题栏。可用快捷键或工具栏中的眼睛按钮切换，也可点角落里的淡色眼睛恢复工具。",
    "Where should the drawing be pasted?": "将绘图插入哪个字段？", "Ask me every time": "每次询问", "Always use this field:": "始终使用此字段：",
    "(Last field of the note)": "（笔记的最后一个字段）",
    "If the current note does not have that field, you will be asked instead. When you draw from the card editor, the field you were editing is used first.": "如果当前笔记没有这个字段，保存时会询问。从编辑器打开画板时，优先使用正在编辑的字段。",
    "Picture": "图片", "Insert:": "插入位置：", "Size on card:": "卡片中的大小：",
    "Add at the end of the field": "添加到字段末尾", "Add at the start of the field": "添加到字段开头", "Replace the field's content": "替换整个字段",
    "1x = as drawn on the blackboard, 2x = twice as large on the card ...": "1× 为绘制大小，2× 为两倍大小。",
    "1x = the size you drew it, 2x = twice as large, up to 8x. Pictures are always saved sharp; very wide ones may still be limited by your card template's own width rules.": "1× 为绘制大小，最高可设为 8×。过宽的图片在卡片中可能会受到模板样式限制。",
    "Include a background (otherwise transparent)": "保留背景（取消勾选则透明）", "Dark background and light ink": "深色背景、浅色笔迹",
    "Show the Blackboard button in Anki's top toolbar": "在 Anki 顶部工具栏显示画板按钮",
    "Show the Annotate button in Anki's top toolbar": "在 Anki 顶部工具栏显示批注按钮",
    "Show drawing buttons in the card editor (Add / Edit / Browser)": "在添加、编辑及浏览器中显示绘图按钮",
    "Hide duplicate buttons from the original Anki-Cali Draw": "隐藏原版 Anki-Cali Draw 的重复按钮",
    "The original add-on stays enabled and still receives AnkiWeb updates. Reopen the editor to see changes to its buttons.": "原版仍可接收 AnkiWeb 更新。重新打开编辑窗口即可刷新其中的按钮。",
    "The Blackboard, Annotate and Zen shortcuts must all be different.": "画板、批注和专注模式的快捷键不能重复。",
    "Annotate": "批注", "Annotate on card": "在卡片上批注", "Toggle zen mode (hide all tools)": "切换专注模式（隐藏工具）",
    "Draw and insert into this note": "新建绘图并插入笔记", "Reopen a saved drawing in this note": "重新编辑笔记中的绘图",
    "The blackboard is available while reviewing.": "画板可在复习时打开。", "Select or open a note first.": "请先选择或打开笔记。",
    "Open the blackboard or annotation mode first.": "请先打开画板或批注模式。",
    "This note has no editable Cali Draw Plus drawings.": "这条笔记没有可编辑的 Cali Draw Plus 绘图。", "Open which drawing?": "打开哪张绘图？",
    "Annotation mode is available while reviewing.": "复习时可以打开批注模式。",
    "Card with annotations copied to clipboard.": "已将卡片和批注复制到剪贴板。",
    "Wait for the current drawing operation to finish.": "请等待当前绘图操作完成。",
    "Discard the unsaved changes to the drawing on the blackboard?": "要放弃画板中尚未保存的修改吗？",
    "Drawing saved to \"{field}\".": "已将绘图保存到「{field}」。", "Drawing inserted into \"{field}\".": "已将绘图插入「{field}」。",
    "Could not save the drawing: {error}": "无法保存绘图：{error}", "Could not reach the editor: {error}": "无法连接编辑器：{error}",
    "No card is being reviewed.": "当前没有正在复习的卡片。", "The review card changed.": "当前复习卡片已更换。",
    "The editor was closed or changed notes. Reopen the original note to save.": "编辑器已关闭或切换笔记。请重新打开原笔记再保存。",
    "The note or target field changed.": "笔记或目标字段已更改。", "The editor did not respond. Try saving again.": "编辑器未响应，请重试保存。",
    "Could not copy the drawing.": "无法复制绘图。", "Drawing copied to clipboard.": "已将绘图复制到剪贴板。",
    'This note has no "{wanted}" field - please choose one.': "当前笔记没有「{wanted}」字段，请选择一个字段。",
    "Add the drawing to which field?": "将绘图添加到哪个字段？",
    "Drawing file is too large or invalid.": "绘图文件过大或无效。",
    "Could not read the embedded drawing data.": "无法读取嵌入的笔迹数据。",
    "Unsupported drawing format version.": "这个版本的绘图格式尚不受支持。",
    "Invalid drawing stroke list.": "笔迹列表无效。", "Invalid stroke type.": "笔迹类型无效。",
    "Invalid stroke colour.": "笔迹颜色无效。", "Invalid stroke width.": "笔迹宽度无效。",
    "Invalid stroke flags.": "笔迹标记无效。", "Invalid pressure strength.": "压感强度无效。",
    "Invalid stroke point count.": "笔迹采样点数量无效。", "Invalid stroke coordinates or pressure.": "笔迹坐标或压力值无效。",
    "This image is not an editable Cali Draw Plus file.": "这张图片没有可编辑的 Cali Draw Plus 笔迹。",
    "Drawing media is missing. Sync media and try again.": "缺少绘图媒体文件。请同步媒体后重试。",
    "The drawing reference changed. Reopen it from the note before saving.": "笔记中的绘图引用已更改。请从笔记重新打开绘图再保存。",
    "The drawing exceeds the maximum SVG size.": "绘图超过 SVG 文件大小上限。",
    "The drawing target changed. Open the note again before saving.": "绘图目标已更改。请重新打开笔记再保存。",
    "Invalid drawing size.": "绘图尺寸无效。", "The collection changed before the drawing was saved.": "保存前牌库已切换。",
    "The note field changed while saving. Reopen the drawing and try again.": "保存期间笔记字段已更改。请重新打开绘图后再试。",
    'The image HTML template must insert one <img src="{filename}">.': '图片 HTML 模板必须插入一个 <img src="{filename}">。',
    "Anki could not keep the drawing media filename.": "Anki 无法保留绘图媒体的文件名。",
    "Check for updates (GitHub)…": "检查更新（GitHub）…", "Checking GitHub for updates…": "正在检查 GitHub 更新…",
    "Could not check or download the update. Open GitHub Releases in your browser?": "无法检查或下载更新。要在浏览器打开 GitHub 发行页吗？",
    "Anki-Cali Draw Plus is up to date.": "Anki-Cali Draw Plus 已是最新版。",
    "Install Anki-Cali Draw Plus {version} from GitHub?": "要从 GitHub 安装 Anki-Cali Draw Plus {version} 吗？",
    "Could not install the update. You can install it from the GitHub Releases page.": "更新安装失败。可以从 GitHub 发行页下载安装包。",
    "Anki-Cali Draw Plus {version} was installed. Restart Anki to use it.": "已安装 Anki-Cali Draw Plus {version}，重启 Anki 后生效。",
}

_WEB = {
    "Select / move / resize / rotate": "选取／移动／缩放／旋转",
    "Pen": "画笔", "Highlighter": "荧光笔", "Line": "直线", "Arrow": "箭头", "Rectangle": "矩形", "Ellipse": "椭圆",
    "Eraser": "橡皮擦", "Pan": "拖动画布", "Undo": "撤销", "Redo": "重做",
    "Delete selection": "删除选区", "Clear canvas": "清空画板", "Clear annotations": "清除批注",
    "Default ink (follows the theme)": "默认墨色（跟随主题）", "Default (yellow for highlighter)": "默认墨色（荧光笔用黄色）",
    "Favourite {number} (right-click: replace with the current colour)": "收藏颜色 {number}（右键替换为当前颜色）",
    "Colour spectrum - pick any colour, save 5 favourites": "自定义颜色，可保存 5 个常用颜色",
    "Favourites: click a slot to save this colour there": "点选色位，收藏当前颜色", "Save this colour in slot {number}": "将当前颜色保存到色位 {number}",
    "Pen thickness (slide up = thicker)": "线宽（上滑加粗）", "Pen thickness (slide right = thicker)": "线宽（右滑加粗）",
    "Copy PNG": "复制 PNG", "Copy selection": "复制选区", "Copy to clipboard as PNG": "以 PNG 图片复制到剪贴板",
    "Save to card": "保存到卡片", "Insert into note": "插入笔记", "Update drawing": "更新绘图", "{action} (selection)": "{action}（选区）",
    "Save an editable drawing to the note": "将可编辑的绘图保存到笔记",
    "Zoom out": "缩小", "Zoom in": "放大", "Reset zoom to 1×": "重置缩放为 1×", "Fit drawing (or selection) in view": "缩放以显示全部绘图或选区",
    "Show the tools again": "重新显示工具", "Zen mode: hide all tools. Bring them back with the faint eye in the corner": "专注模式：隐藏工具，点击角落的眼睛恢复",
    "Canvas is empty": "画板为空", "Drag to move this toolbar": "拖动此处可移动工具栏",
    "Interact with the card (click a tool to draw again)": "操作卡片（点击工具后可继续批注）",
    "Drawing. Click to interact with the card": "批注中，点击后可操作卡片", "Interacting. Click to draw again": "卡片操作中，点击后可继续批注",
    "Copy": "复制", "Copy the card with your annotations to the clipboard": "将卡片和批注复制到剪贴板",
    "Anki-Cali Draw Plus settings": "Anki-Cali Draw Plus 设置", "Close annotation mode": "关闭批注模式",
}


def interface_language():
    from .blackboard import get_config

    chosen = get_config().get("interface_language", "auto")
    if chosen in ("en", "zh_CN"):
        return chosen
    base = (lang.current_lang or "en").replace("_", "-").split("-", 1)[0].lower()
    return "zh_CN" if base == "zh" else "en"


def tr(source, **values):
    if interface_language() == "zh_CN":
        source = _NATIVE.get(source, _WEB.get(source, source))
    return source.format(**values) if values else source


def web_strings():
    return _WEB if interface_language() == "zh_CN" else {}
