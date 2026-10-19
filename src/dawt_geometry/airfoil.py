"""PARSEC S826-like fallback section used when coordinate data is unavailable."""

import math


# These are the project's existing PARSEC section values, reused for the
# S826-like fallback geometry described in the design notes.
PARSEC = {
    "upper": {
        "leading_edge_radius": 0.0162187, "crest_location": 0.376723,
        "crest_height": 0.101977, "crest_curvature": -1.11136,
        "trailing_edge_height": 0.0, "trailing_edge_slope_deg": -12.9184,
    },
    "lower": {
        "leading_edge_radius": 0.00748922, "crest_location": 0.360,
        "crest_height": -0.11, "crest_curvature": 1.64354,
        "trailing_edge_height": 0.0, "trailing_edge_slope_deg": 0.148211,
    },
}


def _solve(matrix, rhs):
    """Solve the small dense system used by the PARSEC constraints."""
    rows = [row[:] + [value] for row, value in zip(matrix, rhs)]
    for pivot in range(len(rhs)):
        best = max(range(pivot, len(rows)), key=lambda index: abs(rows[index][pivot]))
        rows[pivot], rows[best] = rows[best], rows[pivot]
        scale = rows[pivot][pivot]
        if abs(scale) < 1e-14:
            raise ValueError("PARSEC airfoil coefficient system is singular.")
        rows[pivot] = [value / scale for value in rows[pivot]]
        for index in range(len(rows)):
            if index == pivot:
                continue
            factor = rows[index][pivot]
            rows[index] = [a - factor * b for a, b in zip(rows[index], rows[pivot])]
    return [row[-1] for row in rows]


def _coefficients(side, sign):
    """Calculate one six-term PARSEC surface."""
    powers = [index + 0.5 for index in range(6)]
    a1 = sign * math.sqrt(2 * side["leading_edge_radius"])
    x = side["crest_location"]
    z = side["crest_height"]
    curvature = side["crest_curvature"]
    slope = math.tan(math.radians(side["trailing_edge_slope_deg"]))
    matrix = [
        [1 for power in powers[1:]],
        [power for power in powers[1:]],
        [x**power for power in powers[1:]],
        [power * x ** (power - 1) for power in powers[1:]],
        [power * (power - 1) * x ** (power - 2) for power in powers[1:]],
    ]
    rhs = [
        side["trailing_edge_height"] - a1,
        slope - a1 * powers[0],
        z - a1 * x**powers[0],
        -a1 * powers[0] * x ** (powers[0] - 1),
        curvature - a1 * powers[0] * (powers[0] - 1) * x ** (powers[0] - 2),
    ]
    return [a1, *_solve(matrix, rhs)]


def _surface(x, coefficients):
    """Evaluate a PARSEC surface at normalized chord position x."""
    return sum(value * x ** (index + 0.5)
               for index, value in enumerate(coefficients))


def profile(points, tanh_beta=2.0):
    """Return a tanh-spaced Selig contour clustered at both chord ends."""
    if points < 3:
        raise ValueError("An airfoil profile requires at least three points per side.")
    if tanh_beta < 0:
        raise ValueError("tanh_beta must be nonnegative.")

    if tanh_beta == 0:
        x_values = [index / (points - 1) for index in range(points)]
    else:
        scale = math.tanh(tanh_beta)
        x_values = [
            0.5 * (1 + math.tanh(
                tanh_beta * (2 * index / (points - 1) - 1)
            ) / scale)
            for index in range(points)
        ]
        x_values[0], x_values[-1] = 0.0, 1.0

    upper = _coefficients(PARSEC["upper"], 1)
    lower = _coefficients(PARSEC["lower"], -1)
    contour = [(x, _surface(x, upper)) for x in reversed(x_values)]
    contour.extend((x, _surface(x, lower)) for x in x_values[1:])
    return contour
