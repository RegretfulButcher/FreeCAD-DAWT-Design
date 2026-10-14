"""Five-term polynomial curves for the lower duct contour."""

import math


def coefficients(side: dict) -> list[float]:
    """Solve five curve coefficients from trailing-edge and crest constraints."""
    # Integer powers avoid the square-root nose and its singular curvature.
    p = [i + 1 for i in range(5)]
    x = side["crest_location"]
    z = side["crest_height"]
    curvature = side["crest_curvature"]
    slope = math.tan(math.radians(side["trailing_edge_slope_deg"]))
    matrix = [
        [1 for power in p],
        [power for power in p],
        [x**power for power in p],
        [power * x**(power - 1) for power in p],
        [power * (power - 1) * x**(power - 2) for power in p],
    ]
    rhs = [side["trailing_edge_height"], slope, z, 0.0, curvature]
    return solve_system(matrix, rhs)


def solve_system(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Solve a small dense system with pivoted Gaussian elimination."""
    rows = [row[:] + [value] for row, value in zip(matrix, rhs)]
    for pivot in range(len(rhs)):
        best = max(range(pivot, len(rows)), key=lambda i: abs(rows[i][pivot]))
        rows[pivot], rows[best] = rows[best], rows[pivot]
        scale = rows[pivot][pivot]
        if abs(scale) < 1e-14:
            raise ValueError("Five-term curve coefficient system is singular.")
        rows[pivot] = [value / scale for value in rows[pivot]]
        for row in range(len(rows)):
            if row != pivot:
                factor = rows[row][pivot]
                rows[row] = [a - factor * b for a, b in zip(rows[row], rows[pivot])]
    return [row[-1] for row in rows]


def surface(x: float, values: list[float]) -> float:
    """Evaluate the five-term polynomial at normalized position x."""
    return sum(value * x ** (index + 1) for index, value in enumerate(values))
