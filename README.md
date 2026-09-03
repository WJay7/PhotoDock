# PhotoDock

Windows 照片自动导入工具。选择相机/存储卡来源目录和保存目录后，程序会轮询来源目录，发现新照片时自动导入。

## 当前版本

- Tkinter 桌面界面，无第三方运行时依赖
- 支持 JPG、PNG、HEIC 及常见 RAW 扩展名
- 使用 SHA-256 内容指纹进行增量去重
- 按文件时间归档到 `年/月/日` 目录
- 复制到临时 `.part` 文件并校验后原子改名，避免产生损坏文件
- `build.ps1` 可使用 PyInstaller 打包为单文件 exe

## 运行

```powershell
python photodock.py
```

首次运行会选择来源和保存位置，配置和索引保存在 `%APPDATA%\PhotoDock`。
