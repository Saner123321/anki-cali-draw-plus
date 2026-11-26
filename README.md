# Anki-Cali Draw Plus

基于 Anki-Cali Draw 的桌面 Anki 手写插件。用触控笔在无限画布上写字，用手指移动和缩放画布。插入卡片的手写可以重新打开，继续逐笔编辑。

## 使用

1. 用 Anki 的 **工具 → 插件 → 从文件安装** 安装 `.ankiaddon`，然后重启 Anki。本地插件 ID 为 `anki_cali_draw_plus`。
2. 在添加、编辑或浏览窗口中，点鼠标悬停提示带 **Anki-Cali Draw Plus** 的画板图标，新建绘图。点击 **Insert into note** 保存到字段。添加窗口中的笔记仍需按 **Add** 入库。
3. 要修改已保存的绘图，点同一工具栏上带 **reopen a saved drawing** 提示的图标。笔记中有多张手写图时，按字段名和出现顺序选择。修改后点 **Update drawing**，卡片原位置会显示更新版。
4. 在 **工具 → Anki-Cali Draw Plus → Settings… → Drawing** 里可选十字、圆点、空心圆或隐藏笔尖光标，也可调整尺寸和压感强度。只有触屏的设备可以切换为手指写字。

复习时可用 `Ctrl+Alt+Shift+E` 打开 Plus 黑板，或用 `Ctrl+Alt+Shift+D` 打开贴在卡片上的批注层。批注层里手指负责滚动卡片，笔迹随卡片滚动。捏合缩放适用于黑板。`Alt+Shift+Z` 切换工具显隐。**Copy PNG** 可把当前选择或整张画布复制成普通图片。

## 文件格式和兼容性

字段通过普通 `<img>` 引用 Anki 媒体里的一个 SVG。SVG 路径由原 Canvas 绘制例程生成，内嵌的版本化 JSON 保存世界坐标、设备报告的原始压力、渲染使用的平滑压力、颜色、宽度和笔迹类型。桌面编辑器只读取 JSON 模型。卡片的 HTML 和 SVG 路径足以显示图片，手机无需安装绘图插件。

每个版本通过 Anki 的媒体接口写入以内容散列命名的文件。更新时保留原图片的宽度和其他属性，并替换所选 `<img>` 的 `src`。复制到其他卡片的引用可以继续使用旧版本。Anki 的 **检查媒体** 会把已无卡片引用的旧版本列为未使用。丢失媒体时，需要先同步或恢复对应 SVG。旧版已经只以 PNG 插入的绘图可以正常阅读，PNG 本身没有独立笔迹可供恢复。

当前编辑器支持 24 MiB 以内的 Plus SVG。保存选区可生成单独的绘图。重新打开的绘图始终保存整张画布，选中一笔时也一样。

默认触控模式把手指事件送到画布导航，笔接触时将其余触点移出当前手势，笔离开后有 120 毫秒的防误触间隔。手掌先接触、驱动把笔报告为鼠标、以及特定设备的多点触控上报都有待硬件验证。

## 构建和更新上游

运行 `python build.py` 生成安装包。`upstream/ankiweb` 保存原始发行版快照，基线标签为 `upstream-1205964508-1794405980`。未来 AnkiWeb 发布更新时，在这个分支用新版发行包替换对应的源文件并提交，排除本机 `meta.json`、用户配置和缓存。为新版本打标签，再在 `main` 合并 `upstream/ankiweb`，解决冲突后重新运行桌面和同步测试。

Anki-Cali Draw 原作来自 AnkiWeb `1205964508`，页面版本为 1.3.2。原包的 MIT 许可证原样保留，文件中的版权署名仍为 `<YOUR NAME>`，可取得的上游资料里未核实到作者姓名。 [Anki-Cali Draw 原版](https://ankiweb.net/shared/info/1205964508)

实现前阅读了 AnkiDraw 的压感采样、平滑和 `touch-action` 处理，以及 Image Editor Enhanced 的 SVG 重开桥接、`write_data()` 和图片引用更新。Plus 使用自己的输入路由和格式，第三方项目仅作为源码参考。 [AnkiDraw 源码](https://github.com/Rytisgit/Anki-StylusDraw/tree/858f5f4be1a5a9945ae87450460dfc1c75cfb83f/AnkiDraw) · [Image Editor Enhanced 源码](https://github.com/Ficello/Anki-Image-Editor-Enhanced-Edition-/tree/4675b50cc07e1defb3e8672870a572186aa8d68e)
