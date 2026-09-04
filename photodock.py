import hashlib
import json
import os
import shutil
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import ctypes
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None

APP_DIR = Path(os.environ.get("APPDATA", Path.home())) / "PhotoDock"
CONFIG_FILE = APP_DIR / "config.json"
DB_FILE = APP_DIR / "photodock.db"
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff", ".dng", ".cr2", ".cr3", ".nef", ".arw", ".rw2", ".orf"}


def sha256_file(path: Path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


class PhotoDock(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PhotoDock")
        self.geometry("900x600")
        self.minsize(760, 520)
        self.configure(bg="#F2F4F7")
        self._set_pixel_icon()
        self._tray = None
        self._tray_thread = None
        self._single_instance = ctypes.windll.kernel32.CreateMutexW(None, True, "PhotoDock.SingleInstance") if os.name == "nt" else None
        if os.name == "nt" and ctypes.windll.kernel32.GetLastError() == 183:
            # A previous PhotoDock instance is already running. Do not touch
            # tray resources here: the current instance has not initialized them.
            self.quit()
            raise SystemExit
        APP_DIR.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS photos (hash TEXT PRIMARY KEY, path TEXT NOT NULL, imported_at TEXT NOT NULL)")
        self.db.commit()
        self.running = False
        self.auto_scan = tk.BooleanVar(value=True)
        self.organize_by_date = tk.BooleanVar(value=True)
        self.source_var = tk.StringVar()
        self.destination_var = tk.StringVar()
        self.status_var = tk.StringVar(value="请选择照片来源和保存位置")
        self.progress_var = tk.DoubleVar(value=0)
        self._load_config()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        if pystray is not None:
            self._start_tray()
        self.after(1000, self._poll_source)
        if not self.source_var.get() or not self.destination_var.get():
            self.after(300, self._first_run_setup)

    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                self.source_var.set(data.get("source", ""))
                self.destination_var.set(data.get("destination", ""))
                self.organize_by_date.set(data.get("organize_by_date", True))
            except (OSError, json.JSONDecodeError):
                pass

    def _save_config(self):
        CONFIG_FILE.write_text(json.dumps({"source": self.source_var.get(), "destination": self.destination_var.get(), "organize_by_date": self.organize_by_date.get()}, ensure_ascii=False, indent=2), encoding="utf-8")

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#F2F4F7")
        style.configure("TLabelframe", background="#FFFFFF", bordercolor="#D8E4FF", relief="solid")
        style.configure("TLabelframe.Label", background="#FFFFFF", foreground="#173B78", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background="#F2F4F7", foreground="#374151")
        style.configure("Header.TLabel", background="#F2F4F7", foreground="#1769E8", font=("Segoe UI", 22, "bold"))
        style.configure("Subheader.TLabel", background="#F2F4F7", foreground="#6B7280", font=("Segoe UI", 10))
        style.configure("TButton", padding=(14, 8), foreground="#FFFFFF", background="#1464F4", borderwidth=0, font=("Segoe UI", 10, "bold"))
        style.map("TButton", background=[("active", "#0B54D6"), ("disabled", "#A9BFEF")])
        style.configure("TCheckbutton", background="#F2F4F7", foreground="#4B5563", font=("Segoe UI", 9))
        style.configure("Horizontal.TProgressbar", troughcolor="#DCE8FF", background="#1464F4", bordercolor="#DCE8FF", lightcolor="#1464F4", darkcolor="#1464F4")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(3, weight=1)
        sidebar = tk.Frame(self, bg="#1769E8", width=190)
        sidebar.grid(row=0, column=0, rowspan=5, sticky="nsew")
        sidebar.grid_propagate(False)
        tk.Label(sidebar, text="▣  PhotoDock", bg="#1769E8", fg="white", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=20, pady=(28, 6))
        tk.Label(sidebar, text="照片自动导入", bg="#1769E8", fg="#DDEAFF", font=("Segoe UI", 10)).pack(anchor="w", padx=22)
        tk.Frame(sidebar, bg="#4B91F5", height=1).pack(fill="x", padx=20, pady=24)
        tk.Label(sidebar, text="工作区", bg="#1769E8", fg="#BFD7FF", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=22, pady=(0, 10))
        tk.Label(sidebar, text="●  导入照片", bg="#3A83F0", fg="white", font=("Segoe UI", 10), padx=12, pady=9).pack(fill="x", padx=12)
        tk.Label(sidebar, text="⚙  设置", bg="#1769E8", fg="#DDEAFF", font=("Segoe UI", 10), padx=12, pady=9).pack(fill="x", padx=12)
        content = tk.Frame(self, bg="#F2F4F7")
        content.grid(row=0, column=1, rowspan=5, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(3, weight=1)
        heading = tk.Frame(content, bg="#F2F4F7")
        heading.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 12))
        ttk.Label(heading, text="导入照片", style="Header.TLabel").pack(anchor="w")
        ttk.Label(heading, text="连接设备后，PhotoDock 会自动整理新照片", style="Subheader.TLabel").pack(anchor="w", pady=(3, 0))
        paths = ttk.LabelFrame(content, text=" 1  文件夹设置 ")
        paths.grid(row=1, column=0, sticky="ew", padx=28, pady=8)
        paths.columnconfigure(1, weight=1)
        ttk.Label(paths, text="照片来源").grid(row=0, column=0, padx=10, pady=8)
        ttk.Entry(paths, textvariable=self.source_var).grid(row=0, column=1, sticky="ew", padx=5, pady=8)
        ttk.Button(paths, text="选择…", command=self._choose_source).grid(row=0, column=2, padx=10, pady=8)
        ttk.Label(paths, text="保存位置").grid(row=1, column=0, padx=10, pady=8)
        ttk.Entry(paths, textvariable=self.destination_var).grid(row=1, column=1, sticky="ew", padx=5, pady=8)
        ttk.Button(paths, text="选择…", command=self._choose_destination).grid(row=1, column=2, padx=10, pady=8)
        controls = ttk.Frame(content)
        controls.grid(row=2, column=0, sticky="ew", padx=28, pady=8)
        ttk.Button(controls, text="立即扫描并导入", command=self.start_import).pack(side="left")
        ttk.Checkbutton(controls, text="设备连接后自动导入", variable=self.auto_scan).pack(side="left", padx=18)
        ttk.Checkbutton(controls, text="按日期归档", variable=self.organize_by_date, command=self._save_config).pack(side="left", padx=4)
        ttk.Label(controls, textvariable=self.status_var).pack(side="right")
        task = ttk.LabelFrame(content, text=" 2  导入任务 ")
        task.grid(row=3, column=0, sticky="nsew", padx=28, pady=8)
        task.columnconfigure(0, weight=1)
        task.rowconfigure(1, weight=1)
        ttk.Progressbar(task, variable=self.progress_var, maximum=100).grid(row=0, column=0, sticky="ew", padx=14, pady=12)
        self.log = tk.Text(task, height=12, state="disabled", wrap="word")
        self.log.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        ttk.Label(content, text="PhotoDock 会记住你的设置。重复照片按内容指纹跳过。", foreground="#6B7280").grid(row=4, column=0, sticky="w", padx=28, pady=(0, 18))

    def _tray_image(self):
        image = Image.new("RGBA", (64, 64), "#1769E8")
        draw = ImageDraw.Draw(image)
        draw.rectangle((12, 22, 52, 52), fill="white")
        draw.rectangle((23, 15, 41, 23), fill="white")
        draw.rectangle((21, 28, 43, 46), fill="#1769E8")
        draw.rectangle((25, 32, 39, 42), fill="#75B5FF")
        return image

    def _start_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("打开 PhotoDock", lambda icon, item: self._restore_from_tray()),
            pystray.MenuItem("立即扫描并导入", lambda icon, item: self._tray_import()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出程序", lambda icon, item: self._quit_from_tray()),
        )
        self._tray = pystray.Icon("PhotoDock", self._tray_image(), "PhotoDock - 照片自动导入", menu)
        self._tray_thread = threading.Thread(target=self._tray.run, daemon=True)
        self._tray_thread.start()

    def _tray_import(self):
        self.after(0, self.start_import)

    def _hide_to_tray(self):
        if pystray is None:
            self.destroy()
            return
        self.withdraw()

    def _restore_from_tray(self):
        self.after(0, lambda: (self.deiconify(), self.lift(), self.focus_force()))

    def _quit_from_tray(self):
        if self._tray is not None:
            self._tray.stop()
        self.after(0, self.destroy)

    def _set_pixel_icon(self):
        """Create a small pixel-art camera icon without an external image dependency."""
        icon = tk.PhotoImage(width=32, height=32)
        rows = [
            "                                ", "                                ", "            ##      ##          ",
            "          ####    ####         ", "        ################        ", "      ####################      ",
            "    ######            ######    ", "   ####                  ####   ", "  ####      ######        ####  ",
            " ####      ##########        ####", "####      ####      ####        ####", "####     ###  ####  ###         ####",
            "####     ###   ##   ###         ####", "####     ###        ###         ####", "####      ####    ####          ####",
            " ####       ########           #### ", "  ####                      ####  ", "   ####                  ####    ",
            "    ######            ######    ", "      ####################      ", "        ################        ",
            "          ############          ", "            ########            ", "                                ",
        ]
        # Scale the 24x32 pattern vertically to fill the icon; transparent pixels stay empty.
        colors = {"#": "#1769E8", " ": "#F2F4F7"}
        for y, row in enumerate(rows):
            row = row[:32].ljust(32)
            icon.put("{" + " ".join(colors.get(c, "#F5F8FF") for c in row) + "}", to=(0, y + 4))
        self.iconphoto(True, icon)
        self._icon = icon

    def _first_run_setup(self):
        self._choose_source()
        self._choose_destination()

    def _choose_source(self):
        folder = filedialog.askdirectory(title="选择照片来源文件夹（相机或存储卡）")
        if folder:
            self.source_var.set(folder)
            self._save_config()
            self._write_log(f"来源已设置：{folder}")

    def _choose_destination(self):
        folder = filedialog.askdirectory(title="选择照片保存文件夹")
        if folder:
            self.destination_var.set(folder)
            self._save_config()
            self._write_log(f"保存位置已设置：{folder}")

    def _poll_source(self):
        if self.auto_scan.get() and not self.running and self.source_var.get() and Path(self.source_var.get()).exists():
            marker = sum((p.stat().st_size for p in Path(self.source_var.get()).rglob("*") if p.is_file() and p.suffix.lower() in PHOTO_EXTENSIONS), 0)
            if getattr(self, "_source_marker", None) is None:
                self._source_marker = marker
            elif marker != self._source_marker:
                self._source_marker = marker
                self.start_import()
        self.after(3000, self._poll_source)

    def _write_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", f"[{datetime.now():%H:%M:%S}] {text}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def start_import(self):
        if self.running:
            return
        source, destination = Path(self.source_var.get()), Path(self.destination_var.get())
        if not source.is_dir() or not destination:
            messagebox.showwarning("需要设置文件夹", "请先选择有效的照片来源和保存位置。")
            return
        destination.mkdir(parents=True, exist_ok=True)
        self._index_destination(destination)
        self._save_config()
        self.running = True
        self.progress_var.set(0)
        threading.Thread(target=self._import_worker, args=(source, destination, self.organize_by_date.get()), daemon=True).start()

    def _index_destination(self, destination):
        """Index existing photos so a first import also detects duplicates."""
        for path in destination.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in PHOTO_EXTENSIONS:
                continue
            try:
                digest = sha256_file(path)
                self.db.execute("INSERT OR REPLACE INTO photos(hash,path,imported_at) VALUES(?,?,?)", (digest, str(path), datetime.now().isoformat(timespec="seconds")))
            except OSError:
                continue
        self.db.commit()

    def _import_worker(self, source, destination, organize_by_date):
        files = [p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in PHOTO_EXTENSIONS]
        self._ui(lambda: self.status_var.set(f"扫描到 {len(files)} 张照片"))
        imported = skipped = failed = 0
        for index, source_file in enumerate(files, 1):
            try:
                if source_file.stat().st_size == 0:
                    continue
                digest = sha256_file(source_file)
                record = self.db.execute("SELECT path FROM photos WHERE hash=?", (digest,)).fetchone()
                destination_file_exists = record and Path(record[0]).is_file()
                if destination_file_exists:
                    skipped += 1
                else:
                    if organize_by_date:
                        day = datetime.fromtimestamp(source_file.stat().st_mtime)
                        folder = destination / f"{day:%Y}" / f"{day:%m}" / f"{day:%d}"
                    else:
                        folder = destination
                    folder.mkdir(parents=True, exist_ok=True)
                    target = folder / source_file.name
                    if target.exists():
                        target = folder / f"{source_file.stem}_{digest[:8]}{source_file.suffix.lower()}"
                    temp = target.with_suffix(target.suffix + ".part")
                    shutil.copy2(source_file, temp)
                    if sha256_file(temp) != digest:
                        temp.unlink(missing_ok=True)
                        raise IOError("复制校验失败")
                    temp.replace(target)
                    self.db.execute("INSERT OR REPLACE INTO photos(hash,path,imported_at) VALUES(?,?,?)", (digest, str(target), datetime.now().isoformat(timespec="seconds")))
                    self.db.commit()
                    imported += 1
                    if record:
                        self._ui(lambda p=str(source_file): self._write_log(f"已恢复缺失照片：{p}"))
            except Exception as exc:
                failed += 1
                self._ui(lambda e=str(exc), p=str(source_file): self._write_log(f"失败：{p}（{e}）"))
            self._ui(lambda n=index, total=max(1, len(files)): self.progress_var.set(n / total * 100))
        self.running = False
        self._ui(lambda: self.status_var.set(f"完成：导入 {imported}，跳过 {skipped}，失败 {failed}"))
        self._ui(lambda: self._write_log(f"导入完成：导入 {imported}，跳过 {skipped}，失败 {failed}"))

    def _ui(self, callback):
        self.after(0, callback)

    def destroy(self):
        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                pass
        self.db.close()
        super().destroy()


if __name__ == "__main__":
    PhotoDock().mainloop()
