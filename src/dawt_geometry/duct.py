"""Builder for a five-term lower duct contour with an angled flange."""

import math

import Part
import FreeCAD as App
from FreeCAD import Base

from .config import DesignParameters
from .freecad_helpers import checked
from .duct_curve import coefficients, surface


def _edge_samples(edge):
    """Discretize one boundary edge finely while keeping its endpoints."""
    count = max(3, min(4000, int(edge.Length / 0.25) + 3))
    return list(edge.discretize(Number=count))


def _join_edge_route(edges, indices, start_cap, end_cap):
    """Combine consecutive wire edges into one curve for Surface Filling."""
    route = [edges[index] for index in indices]
    if not route:
        raise RuntimeError("Offset boundary has an empty side between end caps.")

    samples = _edge_samples(route[0])
    cap_vertices = [vertex.Point for vertex in start_cap.Vertexes]
    current = min(
        (samples[0], samples[-1]),
        key=lambda point: min((point.sub(v).Length for v in cap_vertices), default=0),
    )
    joined = [current]
    for edge in route:
        points = _edge_samples(edge)
        if points[-1].sub(current).Length < points[0].sub(current).Length:
            points.reverse()
        if points[0].sub(current).Length > 1e-5:
            raise RuntimeError("Offset boundary edges are not connected in order.")
        joined.extend(point for point in points[1:]
                      if point.sub(joined[-1]).Length > 1e-7)
        current = joined[-1]

    end_vertices = [vertex.Point for vertex in end_cap.Vertexes]
    if min((current.sub(point).Length for point in end_vertices), default=1) > 1e-5:
        raise RuntimeError("Offset boundary does not meet its end cap.")
    curve = Part.BSplineCurve()
    curve.interpolate(joined)
    return curve.toShape()


def _surface_filled_face(document, wire, start_center, end_center, half_width):
    """Fill a closed offset wire from its four complete boundary curves."""
    edges = list(wire.Edges)
    cap_indices = {}
    for label, center in (("start", start_center), ("end", end_center)):
        candidates = []
        for index, edge in enumerate(edges):
            curve = edge.Curve
            if not hasattr(curve, "Center") or not hasattr(curve, "Radius"):
                continue
            distance = curve.Center.sub(center).Length
            if distance < max(1e-5, half_width * 1e-4):
                candidates.append((distance, index, edge))
        if not candidates:
            raise RuntimeError(f"Offset wire is missing its rounded {label} cap.")
        _, cap_indices[label], _ = min(candidates, key=lambda item: item[0])

    start_index, end_index = cap_indices["start"], cap_indices["end"]

    def between(first, last):
        result = []
        index = (first + 1) % len(edges)
        while index != last:
            result.append(index)
            index = (index + 1) % len(edges)
        return result

    side_a = _join_edge_route(
        edges, between(end_index, start_index), edges[end_index], edges[start_index]
    )
    side_b = _join_edge_route(
        edges, between(start_index, end_index), edges[start_index], edges[end_index]
    )
    boundary = document.addObject("Part::Feature", "DuctBoundary")
    boundary.Shape = Part.Compound([
        side_a, edges[start_index].copy(), side_b, edges[end_index].copy(),
    ])
    document.recompute()

    filling = document.addObject("Surface::Filling", "DuctSurface")
    filling.BoundaryEdges = [
        (boundary, f"Edge{index}") for index in range(1, 5)
    ]
    document.recompute()
    return checked(filling.Shape.copy(), "Surface Filling duct face")


def duct(parameters: DesignParameters):
    """Build a filled duct face using FreeCAD's default arc offset joins."""
    lower_curve = {
        "crest_location": parameters.duct_lower_crest_location,
        "crest_height": parameters.duct_lower_crest_height,
        "crest_curvature": parameters.duct_lower_crest_curvature,
        "trailing_edge_height": parameters.duct_lower_trailing_edge_height,
        "trailing_edge_slope_deg": parameters.duct_lower_trailing_edge_slope_deg,
    }
    x_values = [i / (parameters.duct_points - 1)
                for i in range(parameters.duct_points)]
    lower_coefficients = coefficients(lower_curve)
    lower = [surface(x, lower_coefficients) for x in x_values]
    if parameters.duct_reverse:
        lower = [-value for value in lower]

    points = [Base.Vector(
        parameters.duct_origin_x + parameters.duct_chord * x,
        parameters.duct_origin_r + parameters.duct_chord * y,
        0,
    ) for x, y in zip(x_values, lower)]
    tail = points[-1]
    flange_angle = math.radians(parameters.duct_flange_angle_deg)
    flange_end = Base.Vector(
        tail.x + parameters.duct_flange_length * math.cos(flange_angle),
        tail.y + parameters.duct_flange_length * math.sin(flange_angle),
        0,
    )

    center_curve = Part.BSplineCurve()
    center_curve.interpolate(points)
    path = Part.Wire([
        center_curve.toShape(),
        Part.LineSegment(tail, flange_end).toShape(),
    ])

    document = App.newDocument("temporary_duct_offset")
    try:
        source = document.addObject("Part::Feature", "DuctCenterPath")
        source.Shape = path
        offset = document.addObject("Part::Offset2D", "DuctOffset")
        offset.Source = source
        offset.Value = parameters.duct_thickness / 2
        offset.Mode = 1  # Pipe mode adds round caps to the open path.
        offset.Join = 0  # Arc joins.
        offset.Fill = False
        document.recompute()
        if offset.Shape.isNull() or not offset.Shape.isValid():
            raise RuntimeError("FreeCAD could not create the arc offset wire.")
        outline = offset.Shape.Wires[0].copy()
        document.removeObject(offset.Name)
        # Delete the original center path before filling the copied outline.
        document.removeObject(source.Name)
        result = _surface_filled_face(
            document, outline, points[0], flange_end, parameters.duct_thickness / 2
        )
    finally:
        # The copied result is the deliverable; discard the original path and
        # temporary Offset2D feature, as with the UI's delete-original option.
        App.closeDocument(document.Name)
    return result
