"""Public toolbox checks, including the shared synthetic RE suite."""
from pathlib import Path
import runpy
import shutil

import cryptography  # noqa: F401
import pyboy  # noqa: F401
import serial  # noqa: F401

for tool in "clang llvm-objdump llvm-nm cmake meson ninja pkg-config dtc adb fastboot file strings xxd readelf nm java".split():
    assert shutil.which(tool), f"Missing tool: {tool}"
runpy.run_path(str(Path(__file__).resolve().parents[1] / "re_tools/smoke.py"), run_name="__main__")
