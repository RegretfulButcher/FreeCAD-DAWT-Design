# Maintenance guide

This folder generates the independent 2D profiles needed for the DAWT
axisymmetric CFD workflow. It is a replacement project beside the original
`dawt_freecad_step` folder. Keep the original available for reference, but do
not copy downstream CAD automation into this project.

## Coordinate system

- `x` is the axial direction.
- `r` is the radial direction and is represented by FreeCAD's `y` coordinate.
- All geometry is in millimetres.
- The axis is `r = 0`.
- The hub centre and actuator-disk centre are both `x = 0`.

## Geometry contract

`profiles.py` provides four independent profiles:

- a rectangular outer domain;
- a curved resolution-section face with no hub cutout;
- an annular actuator-disk face;
- an upper-half hub face with two rounded ends.
- one configurable PARSEC duct profile.

The individual STEP files and `profile_assembly.step` contain overlapping
profiles. Do not add boolean cuts or fusions unless explicitly requested.

## Editing workflow

1. Change dimensions in `config.py`.
2. Add or update checks in `validation.py`.
3. Keep shape construction in `profiles.py`.
4. Keep FreeCAD API details in `freecad_helpers.py`.
5. Keep file naming and orchestration in `build_case.py`.
6. Run `python3 run.py` and inspect the exported STEP files.

`run.py` discovers the FreeCAD command for the host platform. On macOS the
default is `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd`.
Set `FREECADCMD` to override this path. When started with ordinary Python, the
script relaunches itself with the discovered executable.

Do not put FreeCAD imports in configuration or validation modules. This lets
basic dimension checks run with ordinary Python.

## Generated files and version control

`output/` contains generated STEP exports and is intentionally ignored. Python
bytecode, local caches, editor settings, virtual environments, and macOS
`.DS_Store` files are also ignored. Do not commit generated exports or local
machine metadata; commit source, documentation, and configuration changes
only.

For macOS verification, the expected FreeCAD command is:

`/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd`

Run `python3 run.py --out output/macos_test` and confirm that all six STEP
files are created. If FreeCAD is installed elsewhere, set `FREECADCMD` before
running the script.

## Important constraints

- The resolution section is 1350 mm long. Its height is always derived from
  `resolution_inlet_radius`, so there is no separate height parameter. The
  inlet arc is tangent to the top edge and perpendicular to the bottom edge.
- The actuator radial span is 405 mm from the 45 mm hub radius to the
  450 mm outer radius.
- The actuator thickness is 5 mm.
- The hub length must be greater than twice its radius.
- The default actuator and hub axial origins are coincident at `x = 0`.
  The actuator radial position is always constrained to the hub's radial
  origin plus the hub radius; it has no independent radial origin.
- The duct uses the original single nozzle PARSEC definition and supports
  chord length, angle, radial reversal, and its own origin.
- Profile wires must be closed and valid before export.
- The assembly must be a compound of the four individual shapes.
