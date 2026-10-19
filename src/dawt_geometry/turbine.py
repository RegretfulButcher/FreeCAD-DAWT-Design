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


def _airfoil_contour(parameters):
    """Return unique contour samples, omitting the repeated trailing edge."""
    points = profile(
        parameters.turbine_airfoil_points,
        parameters.turbine_airfoil_tanh_beta,
    )
    if math.dist(points[0], points[-1]) <= 1e-9:
        points = points[:-1]
    return points


def _section(parameters, radius, chord, twist_deg):
    """Make a closed radial section with chord along the azimuthal direction."""
    angle = math.radians(twist_deg)
    chord_x, chord_z = math.sin(angle), math.cos(angle)
    normal_x, normal_z = math.cos(angle), -math.sin(angle)
    points = []
    for x, y in _airfoil_contour(parameters):
        along = (x - 0.25) * chord
        thickness = y * chord
        points.append(Base.Vector(
            parameters.turbine_origin_x + along * chord_x + thickness * normal_x,
            parameters.hub_origin_r + radius,
            along * chord_z + thickness * normal_z,
        ))
    return Part.Wire(Part.makePolygon(points + [points[0]]).Edges)


def _root_circle(parameters, radius, twist_deg):
    """Make a circle with the airfoil contour's normalized point progression."""
    contour = _airfoil_contour(parameters)
    segment_lengths = [math.dist(contour[index], contour[index + 1])
                       for index in range(len(contour) - 1)]
    perimeter = sum(segment_lengths) + math.dist(contour[-1], contour[0])
    if perimeter <= 0:
        raise ValueError("The turbine airfoil contour has zero perimeter.")

    fractions = [0.0]
    cumulative = 0.0
    for length in segment_lengths:
        cumulative += length
        fractions.append(cumulative / perimeter)

    angle = math.radians(twist_deg)
    chord_x, chord_z = math.sin(angle), math.cos(angle)
    normal_x, normal_z = math.cos(angle), -math.sin(angle)
    center_y = parameters.hub_origin_r + radius
    points = []
    for fraction in fractions:
        theta = 2 * math.pi * fraction
        along = parameters.turbine_root_shaft_radius * math.cos(theta)
        thickness = parameters.turbine_root_shaft_radius * math.sin(theta)
        points.append(Base.Vector(
            parameters.turbine_origin_x + along * chord_x + thickness * normal_x,
            center_y,
            along * chord_z + thickness * normal_z,
        ))
    return Part.Wire(Part.makePolygon(points + [points[0]]).Edges)


def turbine_blade(parameters: DesignParameters, stations_path: Path = NTNU_GEOMETRY):
    """Build a turbine split at the configured NTNU root end station."""
    stations = _stations(stations_path)
    if stations[-1][0] > parameters.rotor_radius:
        raise ValueError("NTNU blade tip extends beyond the configured rotor radius.")
    first_spacing = stations[1][0] - stations[0][0]
    root_station = stations[0][0] - first_spacing
    if root_station >= parameters.hub_radius:
        raise ValueError("The circular blade root must lie inside the hub radius.")
    blade_sections = [_section(parameters, radius, chord, twist)
                      for radius, chord, twist in stations]
    section_edge_counts = {len(section.Edges) for section in blade_sections}
    if len(section_edge_counts) != 1:
        raise RuntimeError("NTNU airfoil sections do not have matching edge counts.")
    root_end_index = parameters.turbine_root_end_section - 1
    # Both solids share the selected section. With section two, section one is
    # skipped and the root loft runs directly from the shaft to section two.
    blade = Part.makeLoft(blade_sections[root_end_index:], True, False)

    # Keep the root transition as a separate solid in the turbine STEP.
    root_circle = _root_circle(parameters, root_station, stations[0][2])
    hub_circle = _root_circle(parameters, parameters.hub_radius, stations[0][2])
    expected_edges = len(blade_sections[0].Edges)
    if len(root_circle.Edges) != expected_edges or len(hub_circle.Edges) != expected_edges:
        raise RuntimeError("Circular root sections do not match the airfoil edge count.")

    # Ruled faces keep the shaft-to-selected-section root part linear.
    root = Part.makeLoft(
        [root_circle, hub_circle, blade_sections[root_end_index]], True, True
    )
    checked(root, "NTNU turbine linear root transition")
    turbine = Part.makeCompound([blade, root])
    return checked(turbine, "NTNU turbine blade and root shaft")
