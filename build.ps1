python -m pip install --upgrade pyinstaller pillow
python scripts\create_icon.py
pyinstaller --noconfirm --onefile --windowed --icon assets\photodock.ico --name PhotoDock photodock.py

Write-Host "便携版已生成：dist\PhotoDock.exe"
Write-Host "如已安装 Inno Setup，可运行：iscc installer\PhotoDock.iss"
