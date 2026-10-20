"""User-editable dimensions and output names."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DesignParameters:
    """Store profile dimensions and the independent origin of each shape."""

    domain_length: float = 9000.0
    domain_height: float = 6750.0
    domain_origin_x: float = -2250.0
    domain_origin_r: float = 0.0
    resolution_length: float = 2700.0
    resolution_inlet_radius: float = 900.0
    resolution_origin_x: float = -900.0
    resolution_origin_r: float = 0.0
    sector_angle_deg: float = 120.0
    rotor_radius: float = 450.0
    turbine_origin_x: float = -2.5
    turbine_blade_count: int = 3
    turbine_airfoil_points: int = 61
    turbine_airfoil_tanh_beta: float = 2.0
    turbine_root_end_section: int = 1
    turbine_root_shaft_radius: float = 7.5
    hub_length: float = 800.0
    hub_radius: float = 45.0
    hub_origin_x: float = 335.0
    hub_origin_r: float = 0.0
    duct_origin_x: float = -72.0
    duct_origin_r: float = 475.0
    duct_chord: float = 90.0
    duct_thickness: float = 2.0
    duct_flange_length: float = 73.22
    duct_flange_angle_deg: float = 83.83
    duct_lower_crest_location: float = 0.27530
    duct_lower_crest_height: float = -0.0847
    duct_lower_crest_curvature: float = 2.5944
    duct_lower_trailing_edge_height: float = 0.002
    duct_lower_trailing_edge_slope_deg: float = -5.335
    duct_reverse: bool = False
    duct_points: int = 180
    mrf_clearance: float = 5.0
    mrf_min_extension: float = 10.0
    mrf_max_extension: float = 20.0


OUTPUT_NAMES = {
    "domain": "outer_domain_sector.step",
    "resolution": "resolution_sector.step",
    "hub": "hub_sector.step",
    "duct": "duct_sector.step",
    "mrf": "mrf_zone_sector.step",
    "turbine": "ntnu_turbine_blade.step",
    "assembly": "periodic_domain_assembly.step",
}

RESOURCE_DIR = Path(__file__).resolve().parents[2] / "resources"
NTNU_GEOMETRY = RESOURCE_DIR / "ntnu_geometry.csv"
