# Academic Figure Studio

用于 Codex 的本地学术组图插件。交互画布支持显微镜及普通 图像处理、论文图版及演示文稿图片制作。

当前版本：v0.4.4。直接下载插件包：<https://github.com/KevinZhangYY/academic-figure-studio/releases/latest/download/academic-figure-studio.zip>

v0.4.4 修复非正方形图版底边吸附偏移：使用裁剪后或局部放大区域的实际显示高度计算底边，对齐辅助线按吸附后的最终位置绘制。

## AI Harness 快速部署

AI Harness 可按以下顺序执行。所有命令都应在克隆后的插件根目录运行。

```sh
git clone https://github.com/KevinZhangYY/academic-figure-studio.git
cd academic-figure-studio
npm ci
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
FIGURE_PYTHON="$PWD/.venv/bin/python" sh scripts/launch.sh --port 8765
```

在另一个终端检查服务：

```sh
curl -fsS http://127.0.0.1:8765/api/health
```

预期返回包含 `"ok":true`、`"name":"Academic Figure Studio"` 和 `"version":"0.4.4"`。若 8765 被占用，可在启动命令中改为其他端口，并检查对应的 `http://127.0.0.1:<port>/api/health`。

将服务注册为 Codex 插件：

```sh
python3 scripts/package_plugin.py
codex plugin marketplace add ./dist/academic-figure-marketplace
codex plugin add academic-figure-studio@academic-figure-local --json
```

安装成功后，AI Harness 可调用 `$academic-figure-studio`，并请求在内嵌浏览器面板打开工作台。若宿主不支持内嵌面板，则向用户提供服务返回的 localhost URL。

环境变量：

- `FIGURE_PYTHON`：指定具备 Pillow 与 NumPy 的 Python 可执行文件。
- `FIGURE_FONT_PATH`：指定思源黑体 OTF；默认读取 `~/Library/Fonts/SourceHanSansCN-Regular.otf`。
- `FIGURE_TESSERACT`：可选，指定 Tesseract 路径；未提供时仍可手动校准。

## 从发布包快速安装

发布包已包含 JavaScript 导出依赖，适合复制到受控环境：

```sh
curl -fL -o academic-figure-studio.zip https://github.com/KevinZhangYY/academic-figure-studio/releases/latest/download/academic-figure-studio.zip
unzip academic-figure-studio.zip
codex plugin marketplace add ./academic-figure-marketplace
codex plugin add academic-figure-studio@academic-figure-local --json
```

Python 图像依赖仍需满足 `requirements.txt`；发布包不会自动安装系统字体或 Tesseract。

## 本地开发启动

```sh
npm ci
sh scripts/launch.sh
```

打开 `http://127.0.0.1:8765`。编辑器仅监听本机，图像不上传云端。可以通过 `--port 8766` 更改端口。

当前机器可直接运行启动脚本，使用 Codex 已提供的 Python 图像处理环境。其他机器需要 Python 3.10+、Node.js 18+，并通过 `python3 -m pip install -r requirements.txt` 安装 Python 依赖。建议使用虚拟环境。环境变量 `FIGURE_PYTHON` 可指定 Python 可执行文件。

字体默认读取 `~/Library/Fonts/SourceHanSansCN-Regular.otf`。其他系统请将 `FIGURE_FONT_PATH` 指向思源黑体 OTF 文件。可选的 Tesseract 用于识别原始比例尺文字，未安装时仍可手动校准。

## 操作流程

1. 导入多张 PNG、JPEG、TIFF、BMP 或 WebP 图像。程序识别明显的底部黑色或白色信息栏，自动设置裁切线。
2. 读取到可识别的 TIFF 物理像素尺寸时，自动完成校准并显示比例尺，右侧显示校准来源。选中图像，在右侧检查原图预览；通过滑块或像素输入调整保留高度。裁切不改变原文件。
3. 无可用元数据时，点击“在原图上校准”。窗口默认完整显示未裁剪原图，包含底部机器标尺；支持 100% / 200% 放大及定位底部标尺。在机器标尺两端点击，再输入实际长度及单位。OCR 候选必须核对后确认，也可以直接输入已知的 nm/px。手动校准可覆盖元数据值，之后可恢复元数据校准。
4. 在“画布排版”中选择论文双栏、单栏、16:9 或自定义尺寸，应用一至三列排版。图像可拖动，右下角手柄可等比缩放。拖动时，移动图版的四条边缘会与其他图版边缘比较；进入吸附阈值后显示对齐线并贴合，水平与垂直方向独立计算。对齐线仅用于交互，不进入导出结果。
5. 点击“局部放大”，在母图上拖出矩形选区。放大图直接读取原始像素，自动生成选区边框、两条连接线和独立比例尺。支持多个选区、移动放大图、修改连线颜色或隐藏连线。
6. 比例尺和文字默认带自动反色衬边：白色标尺使用深色衬边，黑色标尺使用白色衬边。可在比例尺属性中关闭。
7. 导出 PNG、TIFF、PDF、SVG 或 PowerPoint。未校准或长度不适合图版的比例尺必须校准、调整或关闭后才能导出。

快捷键：`V` 选择、`R` 局部放大、`Delete` 删除、`⌘/Ctrl+Z` 撤销、`⌘/Ctrl+Shift+Z` 重做。

## 保存与导出

- 自动保存到浏览器本地 IndexedDB。通过“保存项目”下载的 `.figstudio` 文件包含原始图片、校准值、ROI 及排版，可跨浏览器重新打开。
- 原始上传字节保存在 `.sem-data/<id>/original`，显示图像保存在同目录。原始文件始终不被覆盖。不同来源的已知校准值分别保存。
- PNG/TIFF 使用选择的 300 或 600 DPI，包含对应分辨率元数据。
- PDF 保留矢量文字、比例尺与连线，并完整嵌入思源黑体；完整字体使文件比子集字体更大。
- SVG 内嵌图像与思源黑体，文字、框线可编辑。部分第三方编辑器对内嵌字体的支持不同。
- PowerPoint 的各图像、文字、比例尺和连线均为独立对象。字体名称为 Source Han Sans CN，接收方需要安装该字体。导出后在 PowerPoint 中单独改变某个图像尺寸不会联动重新计算标尺，修改比例尺或放大选区应返回插件再导出。

## TIFF 自动校准

当前支持以下物理像素尺寸元数据：

- FEI / Thermo Fisher 的 SFEG、HELIOS TIFF 私有标签中的 Scan.PixelWidth / PixelHeight（米 / 像素）。
- Hitachi TIFF 的 UTF-16LE 私有标签 SemImageFile.PixelSize（nm / 像素）。
- ZEISS TIFF 的 AP_PIXEL_SIZE / AP_IMAGE_PIXEL_SIZE 明确单位字段。
- OME-TIFF 的 PhysicalSizeX / PhysicalSizeY。
- ImageJ TIFF 的样品长度单位与像素分辨率组合。
- 带明确物理单位的 PixelSizeX、PixelWidth 或 PixelSize 文本字段。

普通 TIFF 打印 DPI 不作为样品尺寸。元数据缺失、单位未知、数值无效、字段冲突或 OME 尺寸与图片不一致时，要求手动标定。旋转图像按旋转后的对应轴读取校准值。其他设备的二进制私有格式未保证覆盖，需要设备样例才能继续扩展。

解析逻辑参考 tifffile 的 FEI / ZEISS 标签实现、RosettaSciIO 的 TIFF 轴标定实现和 OME 物理尺寸约定；单独存放于 `scripts/tiff_calibration.py`，不依赖这些库运行。

## 识别范围

底栏检测使用图像行的高对比度统计变化，适用于连续黑底/白底信息栏；它不是通用设备版式识别模型。混合底色、叠加在有效图像中的文字、低对比度底栏或大片纯色样品区域需要手动检查。没有清晰边界时保持原图。原始标尺 OCR 是辅助候选，不等同于可靠的物理校准。

高位深 TIFF 使用全局线性映射生成 8 位显示图，并显示映射范围，原始文件仍保留。当前读取多页 TIFF 的第一页。演示图像为标明来源的合成纹理，不是实验数据。当前版本没有旋转、任意多边形 ROI、自动识别科学特征或多页幻灯片功能。

## Codex 插件

插件清单：`.codex-plugin/plugin.json`。技能入口：`skills/academic-figure-studio/SKILL.md`。

打包本地插件市场（包含导出依赖，不包含原始图像或项目数据）：

```sh
python3 scripts/package_plugin.py
codex plugin marketplace add ./dist/academic-figure-marketplace
codex plugin add academic-figure-studio@academic-figure-local
```

安装后，可在支持刷新插件的 Codex 会话中调用 `$academic-figure-studio`，或请求在内嵌画布中打开工作台。若当前会话未重新发现插件，使用新会话。插件通过本地服务渲染画布，并优先显示在 Codex 内嵌浏览器面板中；若宿主不支持面板控制，再提供本地地址。

## 验证

```sh
npm test
# 使用具备 Pillow 与 NumPy 的 Python
python3 -m unittest discover -s tests -p 'test_*.py'
# 需要启动编辑器、Playwright 及 Chrome
PLAYWRIGHT_PATH=/path/to/playwright npm run test:browser
python3 tests/verify_exports.py
```

新增测试覆盖 TIFF 自动校准、元数据缺失时完整原图两点标定、衬边反色以及 PDF 输出。浏览器测试覆盖演示导入、ROI 手势、关联连线、拖动、撤销/重做、校准、五种格式导出及项目恢复。图像算法另有黑白底栏、无底栏、空白图和高位深 TIFF 测试。尚未用用户实际图像校验设备版式适配性。

## 比例尺定位与字号

默认标尺字号和粗细采用统一画布尺寸，不随小图宽度、ROI 或标尺线长缩小；各图版仍可单独设置字号和粗细。文字与标尺作为整体按所选角落定位，底部及侧边留出 15 个画布像素。标注放不下时提示调整尺寸，不自动缩小文字。固定物理长度的标尺线随图像比例变化；固定显示长度模式则自动换算物理长度。
