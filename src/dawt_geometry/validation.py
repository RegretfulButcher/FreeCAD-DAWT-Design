"""Dimension checks that do not require FreeCAD."""

from .config import DesignParameters


def validate_parameters(parameters: DesignParameters) -> None:
    """Reject dimensions that would produce an invalid profile."""
    positive = (
        parameters.domain_length, parameters.domain_height,
        parameters.resolution_length,
        parameters.resolution_inlet_radius, parameters.rotor_radius,
        parameters.hub_length,
        parameters.hub_radius, parameters.turbine_root_shaft_radius,
        parameters.duct_chord, parameters.duct_thickness,
        parameters.duct_flange_length,
        parameters.duct_points,
    )
    if any(value <= 0 for value in positive):
        raise ValueError("All dimensions must be positive.")
    if parameters.hub_length <= 2 * parameters.hub_radius:
        raise ValueError("hub_length must be greater than two hub radii.")
    if not 0 < parameters.duct_lower_crest_location < 1:
        raise ValueError("duct_lower_crest_location must be between 0 and 1.")
    if not 0 < parameters.sector_angle_deg < 360:
        raise ValueError("sector_angle_deg must be between 0 and 360 degrees.")
    if parameters.turbine_blade_count < 1:
        raise ValueError("turbine_blade_count must be positive.")
    if parameters.turbine_airfoil_points < 3:
        raise ValueError("turbine_airfoil_points must be at least three.")
    if parameters.turbine_airfoil_tanh_beta < 0:
        raise ValueError("turbine_airfoil_tanh_beta must be nonnegative.")
    if abs(parameters.sector_angle_deg * parameters.turbine_blade_count - 360) > 1e-8:
        raise ValueError("The periodic sector angle must match the turbine blade count.")
