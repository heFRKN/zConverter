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
datas += collect_data_files("curl_cffi")

a = Analysis(
    ["run.py"],
    pathex=[str(ROOT)],
    binaries=collect_dynamic_libs("imageio_ffmpeg") + collect_dynamic_libs("curl_cffi"),
    datas=datas,
    hiddenimports=["yt_dlp_ejs", "curl_cffi", "yt_dlp.networking._curlcffi", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineCore"],
    excludes=["tkinter", "unittest", "pydoc", "setuptools", "PySide6.QtPdf", "PySide6.Qt3DCore",
              "PySide6.QtMultimedia"],
    noarchive=False,
)

# Qt pulls in a lot this app never loads; leave it out of the release.
# The login browser needs QtWebEngine + its Quick/Qml/Network dependencies, but not QML modules,
# 3D, devtools or every UI translation.
_UNUSED = ("qt6pdf", "qpdf", "virtualkeyboard", "quick3d", "quickcontrols2", "shadertools", "physics",
           "qt6quicktimeline", "qt6quickparticles", "qt6charts", "qt6datavis", "qt6graphs", "qt6sensors",
           "qt6texttospeech", "qt6spatialaudio", "qt6bluetooth", "qt6nfc", "qt6serial", "qt6scxml",
           "qt6location", "qt6multimedia", "qt6labs", "qtwebengine_devtools_resources")
_KEEP_LOCALES = ("en-us.pak", "tr.pak")


def _wanted(dest: str) -> bool:
    d = dest.lower().replace("\\", "/")
    name = d.split("/")[-1]
    if "/qml/" in d or any(u in name for u in _UNUSED):
        return False
    if "/translations/" in d:
        return "qtwebengine_locales" in d and name in _KEEP_LOCALES
    return True


a.binaries = [b for b in a.binaries if _wanted(b[0])]
a.datas = [d for d in a.datas if _wanted(d[0])]
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
