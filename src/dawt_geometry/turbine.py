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


def _spline_edge(points):
    """Interpolate one airfoil side as a single smooth CAD edge."""
    curve = Part.BSplineCurve()
    curve.interpolate(points)
    return curve.toShape()


def _section(parameters, radius, chord, twist_deg):
    """Make a closed radial section with chord along the azimuthal direction."""
    angle = math.radians(twist_deg)
    chord_x, chord_z = math.sin(angle), math.cos(angle)
    normal_x, normal_z = math.cos(angle), -math.sin(angle)
    contour = _airfoil_contour(parameters)
    points = []
    for x, y in contour:
        along = (x - 0.25) * chord
        thickness = y * chord
        points.append(Base.Vector(
            parameters.turbine_origin_x + along * chord_x + thickness * normal_x,
            parameters.hub_origin_r + radius,
            along * chord_z + thickness * normal_z,
        ))
    leading_edge = min(range(len(contour)), key=lambda index: contour[index][0])
    upper = _spline_edge(points[:leading_edge + 1])
    lower_points = [points[leading_edge], *points[leading_edge + 1:], points[0]]
    lower = _spline_edge(lower_points)
    return Part.Wire([upper, lower])


def _root_circle(parameters, radius, twist_deg):
    """Make a smooth circular wire with upper/lower edges matching sections."""
    angle = math.radians(twist_deg)
    chord_x, chord_z = math.sin(angle), math.cos(angle)
    normal_x, normal_z = math.cos(angle), -math.sin(angle)
    center_y = parameters.hub_origin_r + radius

    def circle_point(theta):
        along = parameters.turbine_root_shaft_radius * math.cos(theta)
        thickness = parameters.turbine_root_shaft_radius * math.sin(theta)
        return Base.Vector(
            parameters.turbine_origin_x + along * chord_x + thickness * normal_x,
            center_y,
            along * chord_z + thickness * normal_z,
        )

    samples_per_half = max(16, parameters.turbine_airfoil_points - 1)
    upper_points = [circle_point(math.pi * index / samples_per_half)
                    for index in range(samples_per_half + 1)]
    lower_points = [circle_point(math.pi + math.pi * index / samples_per_half)
                    for index in range(samples_per_half + 1)]
    return Part.Wire([_spline_edge(upper_points), _spline_edge(lower_points)])


def turbine_blade(parameters: DesignParameters, stations_path: Path = NTNU_GEOMETRY):
    """Build a turbine split at the configured NTNU root end station."""
    stations = _stations(stations_path)
    if stations[-1][0] > parameters.rotor_radius:
        raise ValueError("NTNU blade tip extends beyond the configured rotor radius.")
    first_spacing = stations[1][0] - stations[0][0]
    root_station = stations[0][0] - first_spacing
    if root_station >= parameters.hub_radius:
        raise ValueError("The circular blade shaft must extend into the hub radius.")
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
    raised_hub_station = parameters.hub_radius + parameters.turbine_hub_clearance
    if raised_hub_station >= stations[root_end_index][0]:
        raise ValueError("The turbine hub clearance reaches the selected blade section.")
    root_circle = _root_circle(parameters, root_station, stations[0][2])
    hub_circle = _root_circle(parameters, raised_hub_station, stations[0][2])
    expected_edges = len(blade_sections[0].Edges)
    if (len(root_circle.Edges) != expected_edges
            or len(hub_circle.Edges) != expected_edges):
        raise RuntimeError("Circular root sections do not match the airfoil edge count.")

    # Keep the shaft inserted into the hub, with its upper circular guide 1 mm
    # above the hub surface by default. Ruled faces preserve the linear form.
    root = Part.makeLoft(
        [root_circle, hub_circle, blade_sections[root_end_index]], True, True
    )
    checked(root, "NTNU turbine linear root transition")
    turbine = Part.makeCompound([blade, root])
    return checked(turbine, "NTNU turbine blade and root shaft")
