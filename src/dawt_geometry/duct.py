"""Builder for a lower-surface PARSEC duct with an angled flange."""

import math

import Part
from FreeCAD import Base

from .config import DesignParameters
from .freecad_helpers import checked
from .parsec import coefficients, surface


def duct(parameters: DesignParameters):
    """Build a planar face from the lower PARSEC surface and angled flange."""
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

    lower_curve = Part.BSplineCurve()
    lower_curve.interpolate(bottom)
    tail = bottom[-1]
    flange_angle = math.radians(parameters.duct_flange_angle_deg)
    flange_end = Base.Vector(
        tail.x + parameters.duct_flange_length * math.cos(flange_angle),
        tail.y + parameters.duct_flange_length * math.sin(flange_angle),
        0,
    )
    leading_edge = bottom[0]
    flange = Part.LineSegment(tail, flange_end).toShape()
    closure = Part.LineSegment(flange_end, leading_edge).toShape()
    wire = Part.Wire([lower_curve.toShape(), flange, closure])
    face = Part.Face(wire)
    return checked(face, "PARSEC flange face")
