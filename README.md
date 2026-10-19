# FreeCAD 3D periodic turbine domain

This project creates overlapping STEP components for a 120-degree periodic
turbine CFD domain. The axisymmetric x-r geometry is revolved around the x
axis from -60 to +60 degrees. A true 3D NTNU turbine blade is lofted through
the radius, chord, and twist stations in `resources/ntnu_geometry.csv`.

The assembly is a compound of independent components. It contains the outer
domain sector, resolution sector, hub sector, duct sector, and one turbine
blade representing the 120-degree periodic sector. No actuator disk is
included, and no boolean subtraction is performed; subtract the overlapping
components in SpaceClaim as before.

## Airfoil section

The `airfoil.py` module uses the project's existing PARSEC section as an
S826-like fallback. The airfoiltools coordinate file was not available during
this implementation. The blade loft is intended as a geometry-generation
test and uses the PARSEC contour at each NTNU span station.

The blade root uses a ruled, linear loft from the circular shaft through the
first NTNU airfoil station. The circular section reaches the hub surface, with
a 7.5 mm default shaft radius configurable in `DesignParameters`.

Airfoil samples use a symmetric tanh distribution with a default beta of 2.0,
clustering points near both the leading and trailing edges. Change
`turbine_airfoil_points` or `turbine_airfoil_tanh_beta` in `DesignParameters`
to adjust section resolution and clustering strength; beta zero gives uniform
spacing.

## Generate STEP files

Run `python run.py` from this directory. The launcher finds FreeCAD on Windows,
macOS, Linux, or WSL, or accepts an explicit path through `FREECADCMD`.
Generated files are written to ignored `output/`. To use another folder, run:

```sh
python run.py --out output/case_01
```

The exported shapes are:

- `outer_domain_sector.step`
- `resolution_sector.step`
- `hub_sector.step`
- `duct_sector.step`
- `ntnu_turbine_blade.step`
- `periodic_domain_assembly.step`
