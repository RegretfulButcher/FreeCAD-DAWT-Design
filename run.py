"""Create the DAWT STEP profiles with FreeCAD's Python interpreter."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = (
    Path(__file__).resolve().parent
    if "__file__" in globals()
    else Path.cwd().resolve()
)
sys.path.insert(0, str(PROJECT_DIR / "src"))

from dawt_geometry.config import DesignParameters


def freecad_candidates() -> list[Path]:
    """Return FreeCAD command candidates for the current host platform."""
    configured = os.environ.get("FREECADCMD")
    candidates = [Path(configured)] if configured else []
    if sys.platform == "darwin":
        candidates.append(Path(
            "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"
        ))
    elif os.name == "nt":
        candidates.append(Path(r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe"))
    else:
        # Native Linux installs and WSL installations are both supported.
        candidates.extend([
            Path("/usr/bin/freecadcmd"),
            Path("/usr/local/bin/freecadcmd"),
            Path("/mnt/c/Program Files/FreeCAD 1.1/bin/freecadcmd.exe"),
        ])
    return candidates


def find_freecad() -> Path | None:
    """Find an executable FreeCAD command, if one is installed."""
    for candidate in freecad_candidates():
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def parse_arguments() -> argparse.Namespace:
    """Read the output-folder option."""
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
    command_path = find_freecad()
    if command_path is None:
        searched = ", ".join(str(path) for path in freecad_candidates())
        raise SystemExit(
            "FreeCAD was not found. Set FREECADCMD to the freecadcmd executable "
            f"or install it in one of: {searched}"
        )

    script_path = PROJECT_DIR / "run.py"
    script_text = script_path.as_posix()
    arguments = ["run.py", *sys.argv[1:]]
    freecad_code = (
        "import sys; "
        f"sys.argv = {arguments!r}; "
        f"exec(compile(open({script_text!r}, encoding='utf-8').read(), "
        f"{script_text!r}, 'exec'))"
    )
    command = [str(command_path), "-c", freecad_code]
    try:
        subprocess.run(command, cwd=PROJECT_DIR, check=True)
    except subprocess.CalledProcessError as error:
        raise SystemExit(
            f"FreeCAD exited unsuccessfully (return code {error.returncode}). "
            "Check that the installed FreeCAD build supports this Mac."
        ) from error


if __name__ == "__main__":
    main()
