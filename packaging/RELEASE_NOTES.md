Windows x64 独立便携版。下载 Academic-Figure-Studio-Windows-x64.exe，双击启动，浏览器将打开工作台。无需安装 Python、Node.js 或 Codex。首次启动解压内置组件可能需要等待数秒。

- 内置 Python、Node.js、思源黑体和图像/导出依赖。
- 启动时检查 GitHub 稳定版本，也可点击“检查更新”；仅提示和提供下载，不自动安装。
- 更新前保存 .figstudio 项目，关闭旧启动器，然后运行新 EXE。请继续使用同一个浏览器以恢复其本地项目。
- Windows 数据目录：%LOCALAPPDATA%\AcademicFigureStudio\data。
- 包含批量框选、整体拖动、底边吸附和局部放大标尺修复。

本版本通过 Microsoft Azure Trusted Signing 完成代码签名，带时间戳与受信任发布者签名。构建前已通过完整功能测试（启动、字体、TIFF 标定及全部导出格式），签名后发布。SHA256SUMS.txt 可用于核对下载完整性。首次运行仍可能因新程序信誉积累短暂提示，选择「仍要运行」即可；随下载量增加，Windows 会自动减少提示。

构建在 Windows GitHub Actions 中完成，发布前自动测试实际 EXE 的启动、字体、TIFF 元数据标定和 PNG/TIFF/PDF/PPTX 导出。实验图片不会随安装包发布。

academic-figure-studio.zip 是供 Codex 使用的插件包；EXE 为独立 Windows 应用。Windows ARM64 原生版和 32 位系统不在此构建范围内。
