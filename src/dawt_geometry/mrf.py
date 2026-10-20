"""Build an axis-to-duct-clearance profile for the rotating MRF zone."""

import math

import Part
from FreeCAD import Base

from .config import DesignParameters
from .freecad_helpers import checked


def _interpolate_radius(points, x_value):
    """Linearly interpolate or extend a monotonic x-r boundary."""
    if x_value <= points[0][0]:
        first, second = points[0], points[1]
    elif x_value >= points[-1][0]:
        first, second = points[-2], points[-1]
    else:
        for first, second in zip(points, points[1:]):
            if first[0] <= x_value <= second[0]:
                break
    fraction = (x_value - first[0]) / (second[0] - first[0])
    return first[1] + fraction * (second[1] - first[1])


def _lower_duct_boundary(duct_profile):
    """Select and sample the long duct edge nearest the axis."""
    candidates = sorted(duct_profile.Edges, key=lambda edge: edge.Length,
                       reverse=True)[:2]
    if len(candidates) != 2:
        raise RuntimeError("Could not identify both long duct surface edges.")
    edge = min(
        candidates,
        key=lambda item: sum(point.y for point in item.discretize(Number=300))
        / 300,
    )
    count = max(300, min(4000, int(edge.Length / 0.25) + 2))
    points = sorted((point.x, point.y)
                    for point in edge.discretize(Number=count))
    unique = []
    for point in points:
        if not unique or point[0] - unique[-1][0] > 1e-8:
            unique.append(point)
    if len(unique) < 2:
        raise RuntimeError("The lower duct surface has insufficient samples.")
    return unique


def _spline_edge(points):
    """Interpolate one offset boundary as a single smooth CAD edge."""
    curve = Part.BSplineCurve()
    curve.interpolate(points)
    return curve.toShape()


def mrf_zone(parameters: DesignParameters, duct_profile):
    """Make an x-r MRF profile reaching the axis with duct clearance above it."""
    lower_surface = _lower_duct_boundary(duct_profile)
    offset_distance = parameters.mrf_clearance
    offset_surface = []
    for index, (x_value, radius) in enumerate(lower_surface):
        previous = lower_surface[max(0, index - 1)]
        following = lower_surface[min(len(lower_surface) - 1, index + 1)]
        dx = following[0] - previous[0]
        dr = following[1] - previous[1]
        length = math.hypot(dx, dr)
        if length <= 1e-12:
            continue
        # Samples are ordered in increasing x; this normal points toward r=0.
        nx, nr = dr / length, -dx / length
        offset_surface.append((x_value + offset_distance * nx,
                               radius + offset_distance * nr))

    offset_surface.sort()
    # The base bounds span the duct's lower airfoil section, stopping at its
    # flange-root junction. Optional lengths extend either end at fixed radius.
    airfoil_x_start = parameters.duct_origin_x
    airfoil_x_end = airfoil_x_start + parameters.duct_chord
    x_start = airfoil_x_start - parameters.mrf_min_extension
    x_end = airfoil_x_end + parameters.mrf_max_extension
    if x_end <= x_start or len(offset_surface) < 2:
        raise RuntimeError("Could not determine the duct's axial extent for MRF.")

    airfoil_start_radius = _interpolate_radius(offset_surface, airfoil_x_start)
    airfoil_end_radius = _interpolate_radius(offset_surface, airfoil_x_end)
    upper = [(x_start, airfoil_start_radius)]
    upper.append((airfoil_x_start, airfoil_start_radius))
    upper.extend((x_value, radius)
                 for x_value, radius in offset_surface
                 if airfoil_x_start < x_value < airfoil_x_end)
    upper.append((airfoil_x_end, airfoil_end_radius))
    upper.append((x_end, airfoil_end_radius))
    if min(radius for _, radius in upper) <= 0:
        raise ValueError("The MRF clearance offset crosses the rotation axis.")

    upper_points = [Base.Vector(x_value, radius, 0)
                    for x_value, radius in upper]
    unique_upper = []
    for point in upper_points:
        if not unique_upper or point.sub(unique_upper[-1]).Length > 1e-7:
            unique_upper.append(point)
    if len(unique_upper) < 2:
        raise RuntimeError("The MRF duct-clearance boundary has insufficient points.")

    axis_start = Base.Vector(x_start, 0, 0)
    axis_end = Base.Vector(x_end, 0, 0)
    upper_edge = _spline_edge(list(reversed(unique_upper)))
    wire = Part.Wire([
        Part.makeLine(axis_start, axis_end),
        Part.makeLine(axis_end, unique_upper[-1]),
        upper_edge,
        Part.makeLine(unique_upper[0], axis_start),
    ])
    return checked(Part.Face(wire), "MRF zone profile")
