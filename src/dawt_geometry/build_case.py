"""Build and export all DAWT profiles."""

from pathlib import Path

import Part
from FreeCAD import Base

from .config import DesignParameters, OUTPUT_NAMES
from .freecad_helpers import add_shape, export_shape, make_document
from .duct import duct
from .mrf import mrf_zone
from .profiles import hub, rectangle, resolution_section
from .turbine import turbine_blade
from .validation import validate_parameters


def _periodic_sector(shape, parameters: DesignParameters, name: str):
    """Revolve an x-r profile through the sector centered on the +y ray."""
    start = shape.copy()
    start.rotate(Base.Vector(0, 0, 0), Base.Vector(1, 0, 0),
                 -parameters.sector_angle_deg / 2)
    result = start.revolve(
        Base.Vector(0, 0, 0), Base.Vector(1, 0, 0), parameters.sector_angle_deg
    )
    if result.isNull() or not result.isValid():
        raise RuntimeError(f"Could not create the {name} periodic sector.")
    return result


def build_case(
    parameters: DesignParameters,
    output_dir: Path,
) -> list[Path]:
    """Create revolved 3D sectors, one NTNU blade, and their compound assembly."""
    validate_parameters(parameters)
    profiles = {
        "domain": rectangle(parameters),
        "resolution": resolution_section(parameters),
        "hub": hub(parameters),
        "duct": duct(parameters),
    }
    profiles["mrf"] = mrf_zone(parameters, profiles["duct"])
    shapes = {name: _periodic_sector(shape, parameters, name)
              for name, shape in profiles.items()}
    shapes["turbine"] = turbine_blade(parameters)
    document = make_document()
    for name, shape in shapes.items():
        add_shape(document, name, shape)
    assembly = Part.makeCompound(list(shapes.values()))
    add_shape(document, "profile_assembly", assembly)
    document.recompute()
    names = ("domain", "resolution", "hub", "duct", "mrf", "turbine")
    paths = [export_shape(shapes[name], output_dir / OUTPUT_NAMES[name])
             for name in names]
    paths.append(export_shape(assembly, output_dir / OUTPUT_NAMES["assembly"]))
    return paths
