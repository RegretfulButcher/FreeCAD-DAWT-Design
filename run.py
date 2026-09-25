"""Create the DAWT STEP profiles with FreeCAD's Python interpreter."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

FREECAD_COMMAND = Path(r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe")
WSL_FREECAD_COMMAND = Path("/mnt/c/Program Files/FreeCAD 1.1/bin/freecadcmd.exe")
PROJECT_DIR = (
    Path(__file__).resolve().parent
    if "__file__" in globals()
    else Path.cwd().resolve()
)
sys.path.insert(0, str(PROJECT_DIR / "src"))

from dawt_geometry.config import DesignParameters


def parse_arguments() -> argparse.Namespace:
    """Read command-line options for the output folder."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="output", help="STEP output folder")
    return parser.parse_args()


def main() -> None:
    """Validate dimensions, build the profiles, and print output paths."""
    try:
        from dawt_geometry.build_case import build_case
    except ModuleNotFoundError as error:
        if error.name in {"FreeCAD", "Part"}:
            run_with_freecad()
            return
        raise
    args = parse_arguments()
    paths = build_case(DesignParameters(), PROJECT_DIR / args.out)
    for path in paths:
        print(f"Created: {path}")


def run_with_freecad() -> None:
    """Relaunch this script and explicitly execute it inside FreeCAD."""
    command_path = WSL_FREECAD_COMMAND if os.name != "nt" else FREECAD_COMMAND
    if not command_path.exists():
        raise SystemExit(f"FreeCAD was not found at: {FREECAD_COMMAND}")

    script_path = PROJECT_DIR / "run.py"
    script_text = str(script_path)
    if os.name != "nt" and script_text.startswith("/mnt/c/"):
        script_text = "C:/" + script_text[len("/mnt/c/"):]
    script_text = script_text.replace("\\", "/")
    arguments = ["run.py", *sys.argv[1:]]
    freecad_code = (
        "import sys; "
        f"sys.argv = {arguments!r}; "
        f"exec(compile(open({script_text!r}, encoding='utf-8').read(), "
        f"{script_text!r}, 'exec'))"
    )
    command = [str(command_path), "-c", freecad_code]
    subprocess.run(command, cwd=PROJECT_DIR, check=True)


if __name__ == "__main__":
    main()
