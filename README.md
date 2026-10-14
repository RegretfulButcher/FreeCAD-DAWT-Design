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
5. `duct.step` — a planar lower-duct/flange path offset into a surface-filled
   face with configurable thickness and rounded end caps. Its contour uses a
   five-term polynomial in `x` through `x^5`, with finite slope and curvature
   at the leading edge.
6. `profile_assembly.step` — a compound containing all five profiles.

All dimensions are millimetres. The actuator disk and hub share `x = 0` and
the same axis, so they are coincident.

## Running

On macOS, the launcher uses:

```text
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd
```

Ordinary Python automatically relaunches the generator with the platform's
FreeCAD command and explicitly executes the script inside FreeCAD. Generated
STEP files are written to `output/`, which is intentionally ignored by Git:

```sh
cd /path/to/FreeCAD-DAWT-Design
python3 run.py
```

To create a separate case, choose another output folder:

```sh
python3 run.py --out output/case_01
```

Choose how FreeCAD joins the offset edges at corners with `-m` (`arc` is the
default and rounds the open ends; `intersection` extends neighboring offsets
to their sharp intersection):

```sh
python3 run.py -m arc
python3 run.py -m intersection --out output/sharp_case
```

If FreeCAD is installed elsewhere, set `FREECADCMD` to the full path of its
`freecadcmd` executable.

You can also call FreeCAD directly or select another output directory:

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd run.py
python3 run.py --out output/case_01
```

This project contains no downstream CAD automation or launchers.

The launcher supports macOS, Windows, WSL, and native Linux. Set the
`FREECADCMD` environment variable when FreeCAD is installed outside the
standard locations. Python bytecode, editor metadata, macOS `.DS_Store`
files, and generated STEP output are excluded by `.gitignore`.

On Apple Silicon macOS, verify the installation and generate the default
case with:

```sh
file /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd
python3 run.py
```

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
    ├── duct_curve.py              # five-term curve coefficient math
    ├── duct.py                    # lower duct contour and flange
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
- Set the `duct_lower_crest_*` and trailing-edge fields, `duct_flange_length`,
  `duct_flange_angle_deg`, `duct_chord`, and `duct_reverse` to modify the
  planar flange face. `duct_thickness` is the full XY strip width, centered on
  the path. Arc mode uses FreeCAD's default 2D offset join, including its arc
  joins and round caps at both open-path ends. The resulting boundary is merged
  into four curves and filled with Surface Filling. The five curve coefficients are solved
  from the crest height,
  crest location and curvature, plus the trailing-edge height and slope. The
  flange starts at the lower curve's trailing edge and its angle
  is measured from the positive x direction. Positive angles such as 70–90°
  are supported without restricting the user. The entire project is planar;
  no geometry is extruded along `z`.
