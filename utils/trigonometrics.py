import numpy as np

"""Degree-based trigonometric functions b/c np doesn't have it for some reason??"""


def cosd(deg: float):
    """Calculates the cosine of an angle in degrees, not radians.

    Args:
        deg (float): The desired angle (in degrees)

    Returns:
        float: The cosine of the angle
    """
    return np.cos(np.deg2rad(deg))


def sind(deg):
    """Calculates the sine of an angle in degrees, not radians.

    Args:
        deg (float): The desired angle (in degrees)

    Returns:
        float: The sine of the angle
    """
    return np.sin(np.deg2rad(deg))


def tand(deg):
    """Calculates the tangent of an angle in degrees, not radians.

    Args:
        deg (float): The desired angle (in degrees)

    Returns:
        float: The tangent of the angle
    """
    return np.tan(np.deg2rad(deg))
