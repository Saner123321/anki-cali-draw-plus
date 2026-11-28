# Anki-Cali Draw Plus

**简体中文** · [English](README.en.md) · [下载最新版](https://github.com/Saner123321/anki-cali-draw-plus/releases/latest) · [更新日志](https://github.com/Saner123321/anki-cali-draw-plus/blob/main/CHANGELOG.md)

Anki-Cali Draw Plus 是基于 Anki-Cali Draw 的桌面 Anki 手写插件。用触控笔在无限画布上写下笔记，把笔迹存入卡片后，随时可以重新打开编辑，也可以复制到其他画板或笔记继续修改。

感谢 Anki-Cali Draw 原作者开发并分享了这个插件。 [AnkiWeb 上的原版（1205964508）](https://ankiweb.net/shared/info/1205964508)

## Plus 功能

- **手笔分离**。用触控笔在无限画布上书写，用手指平移画布，无需切换工具。
- **双指缩放**。在画板上用双指捏合缩放，也可以用双指平移。
- **可重新编辑的 SVG 笔迹**。插入卡片后仍可重新打开，逐笔选择、移动、擦除或继续绘制。
- **复制可编辑笔迹**。可复制选中的几笔或整张画板，粘贴到另一张画板或 Anki 笔记后继续编辑。
- **笔尖光标与粗细记忆**。可调整光标形状和大小，也可隐藏光标。画板会记住上次选择的笔尖粗细。

## 使用

1. 从 [GitHub 最新发行版](https://github.com/Saner123321/anki-cali-draw-plus/releases/latest) 下载 `.ankiaddon`。用 Anki 的 **工具 → 插件 → 从文件安装** 安装，然后重启 Anki。本地插件 ID 为 `anki_cali_draw_plus`。同一安装包可用于 x64 和 ARM64 Anki。Windows ARM 平板可安装官方 [Anki Windows 11 (ARM)](https://apps.ankiweb.net/) 版。
2. 在添加、编辑或浏览窗口中，点鼠标悬停提示带 **Anki-Cali Draw Plus** 的画板图标，新建绘图。点击 **Insert into note** 保存到字段。添加窗口中的笔记仍需按 **Add** 入库。
3. 要修改已保存的绘图，点同一工具栏上带 **reopen a saved drawing** 提示的图标。笔记中有多张手写图时，按字段名和出现顺序选择。修改后点 **Update drawing**，卡片原位置会显示更新版。
4. 在 **工具 → Anki-Cali Draw Plus → Settings… → Drawing** 里可选十字、圆点、空心圆或隐藏笔尖光标，也可调整尺寸和压感强度。只有触屏的设备可以切换为手指写字。

画板标题栏右侧可以打开设置、最小化、最大化／还原和关闭画板。从原入口可以恢复最小化的画板，继续原来的绘图。画板的齿轮打开的设置窗口显示在画板前方。默认画板跟随打开它的添加或编辑窗口，有空间时在窗口旁展开，屏幕空间不足时只覆盖一侧。

在 **设置 → 常规 → 界面语言** 可选 **跟随 Anki**、**English** 或 **简体中文**。默认跟随 Anki，Anki 的中文界面使用简体中文，其余语言使用英文。点击保存后切换语言，已打开的画板和笔迹会保留。

### 复制和粘贴笔迹

- 在画板中，按 `Ctrl+C` 或点 **复制**，复制选中的笔迹。没有选区时复制整张画板。在另一张 Plus 画板按 `Ctrl+V` 或点 **粘贴可编辑笔迹**。粘贴的笔迹会出现在视图中央并自动选中，可以一起移动，也可以取消选区后逐笔编辑。
- 粘贴到 Anki 笔记字段时，绘图以可重新打开的 SVG 插入光标所在位置。要从已有笔记取出笔迹，在其 Plus 绘图上右键选 **复制可编辑绘图**，然后粘贴到目标画板或字段。
- 其他支持图片粘贴的应用可以读取剪贴板中的图片版本。复习时，批注工具栏也支持复制和粘贴可编辑笔迹，并提供单独的 **将卡片和批注复制到剪贴板** 按钮。

## 两个插件一起用和更新

Plus 默认会在顶部工具栏和卡片编辑器隐藏重复的原版按钮。原版 `1205964508` 可以保持启用，仍在 **工具 → 插件 → 检查更新** 里接收 AnkiWeb 更新。要同时显示两套按钮，在 Plus 的 **Settings… → Toolbar** 取消勾选 **Hide duplicate buttons from the original Anki-Cali Draw**。

Plus 有自己的 **工具 → Anki-Cali Draw Plus → Check for updates (GitHub)…** 入口。发现新版后确认安装，再重启 Anki。更新优先读取最新 Release 附带的版本和校验文件，校验安装包的 SHA-256，并沿用 Anki 安装器保留插件设置。平板和电脑都可以独立检查和更新。已经安装 0.1.0 的设备需要先从 GitHub 安装一次最新版。

复习时可用 `Ctrl+Alt+Shift+E` 打开 Plus 黑板，或用 `Ctrl+Alt+Shift+D` 打开贴在卡片上的批注层。批注层里手指负责滚动卡片，笔迹随卡片滚动。捏合缩放适用于黑板。`Alt+Shift+Z` 切换工具显隐。

## 文件格式和兼容性

字段通过普通 `<img>` 引用 Anki 媒体里的一个 SVG。SVG 路径由原 Canvas 绘制例程生成，内嵌的版本化 JSON 保存世界坐标、设备报告的原始压力、渲染使用的平滑压力、颜色、宽度和笔迹类型。桌面编辑器只读取 JSON 模型。卡片的 HTML 和 SVG 路径足以显示图片，手机无需安装绘图插件。

每个版本通过 Anki 的媒体接口写入以内容散列命名的文件。更新时保留原图片的宽度和其他属性，并替换所选 `<img>` 的 `src`。复制到其他卡片的引用可以继续使用旧版本。Anki 的 **检查媒体** 会把已无卡片引用的旧版本列为未使用。丢失媒体时，需要先同步或恢复对应 SVG。旧版已经只以 PNG 插入的绘图可以正常阅读，PNG 本身没有独立笔迹可供恢复。

当前编辑器支持 24 MiB 以内的 Plus SVG。保存选区可生成单独的绘图。重新打开的绘图始终保存整张画布，选中一笔时也一样。

默认触控模式把手指事件送到画布导航，笔接触时将其余触点移出当前手势，笔离开后有 120 毫秒的防误触间隔。手掌先接触、驱动把笔报告为鼠标、以及特定设备的多点触控上报都有待硬件验证。

## 构建和更新上游

运行 `python build.py` 生成安装包。`upstream/ankiweb` 保存原版 1.3.2 的发行包快照，基线标签为 `upstream-1205964508-1794405980`。未来 AnkiWeb 发布更新时，在这个分支用新版发行包替换对应的源文件并提交，排除本机 `meta.json`、用户配置和缓存。为新版本打标签，再在 `main` 合并 `upstream/ankiweb`，解决冲突后重新运行桌面和同步测试。

发布 Plus 时更新 `manifest.json` 的 `human_version`，在 `CHANGELOG.md` 中添加同版本的更新说明，再提交并推送对应的 `vX.Y.Z` 标签。GitHub Actions 会构建安装包并把该版本的说明发布到 GitHub Releases。原版的 AnkiWeb 更新可以独立安装，合并进 Plus 需要走上游导入流程。

## 许可证

仓库和 `.ankiaddon` 安装包原样保留上游的 MIT 许可证与版权声明。上游版权行中的 `<YOUR NAME>` 占位符也按原样保留。 [LICENSE](LICENSE)

## 源码参考

实现前阅读了 AnkiDraw 的压感采样、平滑和 `touch-action` 处理，以及 Image Editor Enhanced 的 SVG 重开桥接、`write_data()` 和图片引用更新。Plus 使用自己的输入路由和格式，第三方项目仅作为源码参考。 [AnkiDraw 源码](https://github.com/Rytisgit/Anki-StylusDraw/tree/858f5f4be1a5a9945ae87450460dfc1c75cfb83f/AnkiDraw) · [Image Editor Enhanced 源码](https://github.com/Ficello/Anki-Image-Editor-Enhanced-Edition-/tree/4675b50cc07e1defb3e8672870a572186aa8d68e)
