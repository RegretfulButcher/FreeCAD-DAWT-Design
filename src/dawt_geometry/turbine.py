"""Build the NTNU turbine blade as a loft through its radial airfoil sections."""

import csv
import math
from pathlib import Path

import Part
from FreeCAD import Base

from .airfoil import profile
from .config import DesignParameters, NTNU_GEOMETRY
from .freecad_helpers import checked


def _stations(path: Path):
    """Read NTNU radius, chord, and twist rows in metres and degrees."""
    with path.open(newline="", encoding="utf-8") as stream:
        values = [[float(value) for value in row]
                  for row in csv.reader(stream) if row]
    if len(values) < 2 or any(len(row) != 3 for row in values):
        raise ValueError(f"Expected radius,chord,twist rows in {path}.")
    if any(row[0] <= 0 or row[1] <= 0 for row in values):
        raise ValueError("NTNU radial stations and chords must be positive.")
    if any(b[0] <= a[0] for a, b in zip(values, values[1:])):
        raise ValueError("NTNU radial stations must be strictly increasing.")
    return [(radius * 1000, chord * 1000, twist)
            for radius, chord, twist in values]


def _section(parameters, radius, chord, twist_deg):
    """Make a closed radial section with chord along the azimuthal direction."""
    angle = math.radians(twist_deg)
    chord_x, chord_z = math.sin(angle), math.cos(angle)
    normal_x, normal_z = math.cos(angle), -math.sin(angle)
    points = []
    for x, y in profile(parameters.turbine_airfoil_points):
        along = (x - 0.25) * chord
        thickness = y * chord
        points.append(Base.Vector(
            parameters.turbine_origin_x + along * chord_x + thickness * normal_x,
            parameters.hub_origin_r + radius,
            along * chord_z + thickness * normal_z,
        ))
    return Part.Wire(Part.makePolygon(points + [points[0]]).Edges)


def _root_circle(parameters, radius):
    """Make the circular radial section at the inboard end of the loft."""
    count = 2 * parameters.turbine_airfoil_points - 1
    center_y = parameters.hub_origin_r + radius
    points = [Base.Vector(
        parameters.turbine_origin_x + parameters.turbine_root_shaft_radius * math.cos(
            2 * math.pi * index / count
        ),
        center_y,
        parameters.turbine_root_shaft_radius * math.sin(2 * math.pi * index / count),
    ) for index in range(count)]
    return Part.Wire(Part.makePolygon(points + [points[0]]).Edges)


def turbine_blade(parameters: DesignParameters, stations_path: Path = NTNU_GEOMETRY):
    """Loft one blade into a round root and extend its shaft to the hub."""
    stations = _stations(stations_path)
    if stations[-1][0] > parameters.rotor_radius:
        raise ValueError("NTNU blade tip extends beyond the configured rotor radius.")
    first_spacing = stations[1][0] - stations[0][0]
    root_station = stations[0][0] - first_spacing
    if root_station >= parameters.hub_radius:
        raise ValueError("The circular blade root must lie inside the hub radius.")
    blade_sections = [_section(parameters, radius, chord, twist)
                      for radius, chord, twist in stations]
    blade = Part.makeLoft(blade_sections, True, False)

    # Keep the short root transition as a separate solid in the turbine STEP.
    # Its two equal circular sections make a straight shaft reaching the hub;
    # its outer section lofts into the first NTNU airfoil station.
    root_sections = [
        _root_circle(parameters, root_station),
        _root_circle(parameters, parameters.hub_radius),
        blade_sections[0],
    ]
    root = Part.makeLoft(root_sections, True, False)
    turbine = Part.makeCompound([blade, root])
    return checked(turbine, "NTNU turbine blade and root shaft")
