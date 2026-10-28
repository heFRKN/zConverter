# PyInstaller build: pyinstaller zConverter.spec  (or run build.ps1)
# One-folder build on purpose: Qt (LGPL) stays as replaceable DLLs next to the exe.
import re
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
from PyInstaller.utils.win32.versioninfo import (FixedFileInfo, StringFileInfo, StringStruct,
                                                 StringTable, VarFileInfo, VarStruct, VSVersionInfo)

ROOT = Path(SPECPATH)
version = re.search(r'__version__ = "([^"]+)"', (ROOT / "zconverter" / "__init__.py").read_text()).group(1)
vtuple = tuple(int(x) for x in version.split(".")) + (0,)

datas = [
    ("assets/icon.ico", "assets"),
    ("LICENSE", "."),
    ("TERMS.md", "."),
    ("PRIVACY.md", "."),
    ("THIRD_PARTY_NOTICES.md", "."),
    ("licenses", "licenses"),
]
datas += collect_data_files("imageio_ffmpeg", includes=["binaries/*"])
datas += collect_data_files("yt_dlp_ejs")

a = Analysis(
    ["run.py"],
    pathex=[str(ROOT)],
    binaries=collect_dynamic_libs("imageio_ffmpeg"),
    datas=datas,
    hiddenimports=["yt_dlp_ejs"],
    excludes=["tkinter", "unittest", "pydoc", "setuptools", "PySide6.QtWebEngineCore",
              "PySide6.QtWebEngineWidgets", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtPdf",
              "PySide6.Qt3DCore", "PySide6.QtMultimedia"],
    noarchive=False,
)

# Qt pulls in libraries a widgets-only app never loads; leave them out of the release.
_UNUSED = ("opengl32sw", "qt6pdf", "qt6qml", "qt6quick", "qt6virtualkeyboard", "qpdf", "qtvirtualkeyboard",
           "qt6opengl.dll", "qt6network")
a.binaries = [b for b in a.binaries if not any(u in b[0].lower().replace("\\", "/").split("/")[-1] for u in _UNUSED)]
a.datas = [d for d in a.datas if "/translations/" not in d[0].replace("\\", "/").lower()]
pyz = PYZ(a.pure)

version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=vtuple, prodvers=vtuple),
    kids=[
        StringFileInfo([StringTable("041F04B0", [
            StringStruct("CompanyName", "heFRKN"),
            StringStruct("FileDescription", "zConverter"),
            StringStruct("FileVersion", version),
            StringStruct("InternalName", "zConverter"),
            StringStruct("LegalCopyright", "Copyright (c) 2026 heFRKN. MIT License."),
            StringStruct("OriginalFilename", "zConverter.exe"),
            StringStruct("ProductName", "zConverter"),
            StringStruct("ProductVersion", version),
        ])]),
        VarFileInfo([VarStruct("Translation", [0x041F, 1200])]),
    ],
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="zConverter",
    icon="assets/icon.ico",
    console=False,
    version=version_info,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="zConverter", upx=False)
