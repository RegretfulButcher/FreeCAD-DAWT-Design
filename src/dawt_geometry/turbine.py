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


def turbine_blade(parameters: DesignParameters, stations_path: Path = NTNU_GEOMETRY):
    """Loft one blade, the periodic representative of the three-blade rotor."""
    stations = _stations(stations_path)
    if stations[-1][0] > parameters.rotor_radius:
        raise ValueError("NTNU blade tip extends beyond the configured rotor radius.")
    if stations[0][0] >= parameters.hub_radius:
        radius, chord, twist = stations[0]
        stations.insert(0, (parameters.hub_radius - 5.0, chord, twist))
    sections = [_section(parameters, radius, chord, twist)
                for radius, chord, twist in stations]
    blade = Part.makeLoft(sections, True, False)
    return checked(blade, "NTNU turbine blade loft")
