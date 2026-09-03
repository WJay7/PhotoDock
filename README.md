# PhotoDock

Windows 照片自动导入工具。选择相机/存储卡来源目录和保存目录后，程序会轮询来源目录，发现新照片时自动导入。

## 当前版本

- Tkinter 桌面界面，无第三方运行时依赖
- 支持 JPG、PNG、HEIC 及常见 RAW 扩展名
- 使用 SHA-256 内容指纹进行增量去重
- 按文件时间归档到 `年/月/日` 目录
- 可选关闭日期归档，直接保存到目标文件夹根目录
- 复制到临时 `.part` 文件并校验后原子改名，避免产生损坏文件
- `build.ps1` 可使用 PyInstaller 打包为单文件 exe

## 运行

```powershell
python photodock.py
```

首次运行会选择来源和保存位置，配置和索引保存在 `%APPDATA%\PhotoDock`。

## 构建安装程序

GitHub Actions 会在手动运行或推送 `v*.*.*` 标签时自动构建 Windows 安装包。手动运行后，可在运行记录的 Artifacts 下载 `PhotoDock-Windows`；推送版本标签后，构建完成会自动创建 GitHub Release，并把 `PhotoDock-Setup.exe` 附在发行版下载区。

如果本机安装了 [Inno Setup](https://jrsoftware.org/isinfo.php)，也可以执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
iscc installer\PhotoDock.iss
```

安装包会创建开始菜单快捷方式、可选桌面快捷方式，并提供标准卸载程序。用户配置和照片索引保存在 `%APPDATA%\PhotoDock`，卸载不会删除它们。
