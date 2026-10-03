"""Builder for a lower-surface PARSEC duct with an angled flange."""

import math

import Part
from FreeCAD import Base

from .config import DesignParameters
from .freecad_helpers import checked
from .parsec import coefficients, surface


def _line_intersection(first, first_direction, second, second_direction):
    """Return the XY intersection of two non-parallel infinite lines."""
    cross = (first_direction.x * second_direction.y
             - first_direction.y * second_direction.x)
    if abs(cross) < 1e-12:
        raise ValueError("PARSEC and flange tangents must not be parallel.")
    delta_x = second.x - first.x
    delta_y = second.y - first.y
    distance = (delta_x * second_direction.y
                - delta_y * second_direction.x) / cross
    return first + first_direction * distance


def duct(parameters: DesignParameters):
    """Build a planar strip by offsetting the lower PARSEC/flange path in XY."""
    lower_parsec = {
        "leading_edge_radius": parameters.duct_lower_leading_edge_radius,
        "crest_location": parameters.duct_lower_crest_location,
        "crest_height": parameters.duct_lower_crest_height,
        "crest_curvature": parameters.duct_lower_crest_curvature,
        "trailing_edge_height": parameters.duct_lower_trailing_edge_height,
        "trailing_edge_slope_deg": parameters.duct_lower_trailing_edge_slope_deg,
    }
    x_values = [i / (parameters.duct_points - 1)
                for i in range(parameters.duct_points)]
    lower_coefficients = coefficients(lower_parsec, -1)
    lower = [surface(x, lower_coefficients) for x in x_values]
    if parameters.duct_reverse:
        lower = [-value for value in lower]
    bottom = []
    for x, y_lower in zip(x_values, lower):
        axial = parameters.duct_origin_x + parameters.duct_chord * x
        radial = parameters.duct_origin_r + parameters.duct_chord * y_lower
        bottom.append(Base.Vector(axial, radial, 0))

    tail = bottom[-1]
    flange_angle = math.radians(parameters.duct_flange_angle_deg)
    flange_end = Base.Vector(
        tail.x + parameters.duct_flange_length * math.cos(flange_angle),
        tail.y + parameters.duct_flange_length * math.sin(flange_angle),
        0,
    )
    half_width = parameters.duct_thickness / 2
    left, right = [], []
    for index, point in enumerate(bottom):
        previous = bottom[max(0, index - 1)]
        following = bottom[min(len(bottom) - 1, index + 1)]
        tangent = following.sub(previous)
        tangent.normalize()
        normal = Base.Vector(-tangent.y, tangent.x, 0)
        left.append(point + normal * half_width)
        right.append(point - normal * half_width)

    lower_tangent = bottom[-1].sub(bottom[-2])
    lower_tangent.normalize()
    flange_tangent = flange_end.sub(tail)
    flange_tangent.normalize()
    lower_normal = Base.Vector(-lower_tangent.y, lower_tangent.x, 0)
    flange_normal = Base.Vector(-flange_tangent.y, flange_tangent.x, 0)
    left_miter = _line_intersection(
        tail + lower_normal * half_width, lower_tangent,
        tail + flange_normal * half_width, flange_tangent,
    )
    right_miter = _line_intersection(
        tail - lower_normal * half_width, lower_tangent,
        tail - flange_normal * half_width, flange_tangent,
    )
    left[-1] = left_miter
    right[-1] = right_miter
    left_flange_end = flange_end + flange_normal * half_width
    right_flange_end = flange_end - flange_normal * half_width

    left_curve = Part.BSplineCurve()
    right_curve = Part.BSplineCurve()
    left_curve.interpolate(left)
    right_curve.interpolate(list(reversed(right)))
    wire = Part.Wire([
        left_curve.toShape(),
        Part.LineSegment(left_miter, left_flange_end).toShape(),
        Part.LineSegment(left_flange_end, right_flange_end).toShape(),
        Part.LineSegment(right_flange_end, right_miter).toShape(),
        right_curve.toShape(),
        Part.LineSegment(right[0], left[0]).toShape(),
    ])
    return checked(Part.Face(wire), "PARSEC flange strip")
