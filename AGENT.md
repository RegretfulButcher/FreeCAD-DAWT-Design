# Maintenance guide

This project creates overlapping STEP geometry for a 120-degree periodic
three-dimensional DAWT CFD sector. The x-r axisymmetric profiles are revolved
around the x axis from -60 to +60 degrees. The turbine blade is a 3D loft from
the NTNU station table. Keep each component independent for subtraction in
SpaceClaim; the assembly is a compound, with no booleans.

## Coordinate and unit conventions

- `x` is the axial direction and `r` is radial distance from the x axis.
- The x-r profiles use FreeCAD's x-y plane; revolving about x creates the
  sector in y-z.
- All FreeCAD geometry uses millimetres.
- `resources/ntnu_geometry.csv` stores radius and chord in metres and twist
  in degrees, as in OpTurbo's CFD table.
- One blade is exported as the periodic representative of the three-blade
  turbine, centered on the sector bisector.

## Geometry and workflow

- `profiles.py` builds the outer domain, resolution region, and hub profiles.
- `duct.py` builds the lower duct profile.
- `turbine.py` reads the NTNU table and lofts the radial blade sections.
- `airfoil.py` provides the existing PARSEC section as an S826-like fallback.
- The turbine STEP contains the NTNU blade and a circular root transition.
  Its round section reaches the hub surface; its radius is configurable.
- `build_case.py` revolves each axisymmetric profile by 120 degrees and exports
  every overlapping shape plus a compound assembly.
- No actuator disk is built or exported.
- Use `config.py` for dimensions and `validation.py` for dimension checks.
- Run `python run.py` using FreeCAD's Python command to produce STEP exports.
  `output/` is generated and ignored by Git.

Keep generated files and local machine metadata out of version control.
