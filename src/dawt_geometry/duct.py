"""Builder for a lower-surface PARSEC duct with an angled flange."""

import math

import Part
from FreeCAD import Base

from .config import DesignParameters
from .freecad_helpers import checked
from .parsec import coefficients, surface


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
    leading_edge = bottom[0]
    centerline = bottom + [flange_end]
    half_width = parameters.duct_thickness / 2
    left, right = [], []
    for index, point in enumerate(centerline):
        previous = centerline[max(0, index - 1)]
        following = centerline[min(len(centerline) - 1, index + 1)]
        tangent = following.sub(previous)
        tangent.normalize()
        normal = Base.Vector(-tangent.y, tangent.x, 0)
        left.append(point + normal * half_width)
        right.append(point - normal * half_width)

    outline = left + list(reversed(right)) + [left[0]]
    wire = Part.makePolygon(outline)
    return checked(Part.Face(wire), "PARSEC flange strip")
