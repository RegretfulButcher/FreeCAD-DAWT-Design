# DAWT FreeCAD STEP profiles

This is a clean, beginner-friendly rewrite of `dawt_freecad_step`. The
original folder is not modified.

The program creates independent 2D profiles in the FreeCAD x-r plane. The
profiles are exported without boolean subtraction so they can be edited and
subtracted later in a separate CAD workflow:

1. `outer_domain.step` — a 6750 mm by 9000 mm rectangle.
2. `resolution_section.step` — a 1350 mm long section with a 900 mm
   quarter-circle inlet and therefore a 900 mm height.
3. `actuator_disk.step` — a 405 mm radial annulus and 5 mm axial thickness.
4. `hub.step` — an 800 mm long hub with 45 mm radius and rounded ends.
5. `duct.step` — one configurable PARSEC duct profile.
6. `profile_assembly.step` — a compound containing all five profiles.

All dimensions are millimetres. The actuator disk and hub share `x = 0` and
the same axis, so they are coincident.

## Running

The configured FreeCAD installation is:

```text
C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe
```

Ordinary Python automatically relaunches the generator with that executable
and explicitly executes the script inside FreeCAD:

```powershell
cd "C:\Project Saves\Python Codes\Design Algorithm\dawt_freecad_step_modular"
python .\run.py
```

When launched from WSL, the same installation is addressed through
`/mnt/c/Program Files/FreeCAD 1.1/bin/freecadcmd.exe` automatically.

You can also call FreeCAD directly or select another output directory:

```powershell
& "C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" .\run.py
python .\run.py --out output\case_01
```

This project contains no downstream CAD automation or launchers.

## Structure

```text
dawt_freecad_step_modular/
├── run.py                         # command-line entry point
├── README.md                      # project guide
├── AGENT.md                       # maintenance guide for future agents
└── src/dawt_geometry/
    ├── config.py                  # dimensions and output names
    ├── validation.py              # simple design checks
    ├── profiles.py                # domain, resolution, disk, and hub
    ├── parsec.py                  # PARSEC coefficient math
    ├── duct.py                    # one PARSEC duct profile
    ├── freecad_helpers.py         # document and STEP helpers
    └── build_case.py              # orchestration
```

To change dimensions, edit `DesignParameters` in `config.py`. The validation
module rejects impossible dimensions before FreeCAD starts building geometry.

## Design decisions

- Every function has a short docstring explaining its purpose.
- Geometry builders return one checked FreeCAD shape.
- The assembly is a `Part.Compound`, not a fused or cut solid.
- No subtraction is performed in Python.
- The resolution section has no hub subtraction. Its inlet arc is tangent to
  the top line and perpendicular to the bottom line.
- Set each shape's origin fields independently to move it. The actuator disk
  uses the hub's radial origin and hub radius as its inner radial constraint.
- Set `duct_chord`, `duct_angle_deg`, and `duct_reverse` to modify the duct.
