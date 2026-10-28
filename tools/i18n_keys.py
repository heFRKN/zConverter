"""List translation keys used with t("...") that have no English entry yet.

    python tools/i18n_keys.py
"""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zconverter.i18n import EN, EXTRA_KEYS  # noqa: E402


def keys() -> list[str]:
    found = []
    for path in sorted((ROOT / "zconverter").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "t"
                    and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                if node.args[0].value not in found:
                    found.append(node.args[0].value)
    return found + [k for k in EXTRA_KEYS if k not in found]


if __name__ == "__main__":
    missing = [k for k in keys() if k not in EN]
    for k in missing:
        print(repr(k))
    print(f"{len(missing)} missing", file=sys.stderr)
    sys.exit(1 if missing else 0)
