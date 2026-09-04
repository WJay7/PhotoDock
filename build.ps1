python -m pip install --upgrade pyinstaller pillow pystray
if (Get-Command inkscape -ErrorAction SilentlyContinue) { inkscape assets\photodock-camera.svg --export-type=png --export-filename=assets\photodock-camera.png --export-width=256 --export-height=256 }
python scripts\create_icon.py
pyinstaller --noconfirm --onefile --windowed --icon assets\photodock.ico --name PhotoDock photodock.py

Write-Host "便携版已生成：dist\PhotoDock.exe"
Write-Host "如已安装 Inno Setup，可运行：iscc installer\PhotoDock.iss"
