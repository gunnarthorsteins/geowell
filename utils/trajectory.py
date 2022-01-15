import json
import warnings

import numpy as np


class Trigonometrics:
    """Degree-based trigonometric functions b/c np doesn't have it for some reason??"""

    def cosd(deg: float):
        """Calculates the cosine of an angle in *degrees*.

        Args:
            deg (float): The desired angle (in degrees)

        Returns:
            float: The cosine of the angle
        """
        return np.cos(np.deg2rad(deg))

    def sind(deg):
        """Calculates the sine of an angle in *degrees*.

        Args:
            deg (float): The desired angle (in degrees)

        Returns:
            float: The sine of the angle
        """
        return np.sin(np.deg2rad(deg))

    def tand(deg):
        """Calculates the tangent of an angle in *degrees*.

        Args:
            deg (float): The desired angle (in degrees)

        Returns:
            float: The tangent of the angle
        """
        return np.tan(np.deg2rad(deg))


def get_index(a, b):
    """Helper function for _get_casing_split. 

    Args:
        a (np.array): Left of leq-sign
        b (np.array): Right of leq-sign

    Returns:
        (list): A list of boolean values
    """
    return sum(a < b)


class Trajectory2d:

    """Generates 2D-trajectory of proposed well.
    
    Made up of three legs:
    1) Down to KOP
    2) Build-up
    3) Last leg to well bottom (straight)
    """

    def __init__(self):

        with open("config.json") as json_file:
            default_values = json.load(json_file)

        self.Y = default_values["default_values"]["Y"]
        self.X = default_values["default_values"]["X"]
        self.MMD = default_values["default_values"]["mmd"]
        self.DIP = default_values["default_values"]["dip"]
        self.Z = default_values["default_values"]["Z"]
        self.AZ = default_values["default_values"]["az"]
        self.CD = default_values["default_values"]["cd"]
        self.KOP = default_values["default_values"]["kop"]
        self.BU = default_values["default_values"]["bu"]

    def _get_casing_split(self):
        """Finds the well trajectory index of the casing split.

        It's not very readable but does the job. TODO: Make actually readable.

        Returns:
            split_index (int): Index denoting where to split r & z
        """

        shifted_cd = self.CD - self.Z

        if self.CD <= self.KOP:  # Casing split on first leg
            split_index = get_index(self.z, shifted_cd)
        # The +50 is b/c the vertical segment always
        # has a len of 50 (default linspace length - here build-up)
        # which must be accounted for
        elif self.KOP < self.CD < self.len_buildup[-1]:  # Casing split on 2nd leg
            split_index = get_index(self.len_buildup, shifted_cd) + 50
        elif self.len_buildup[-1] < self.CD:  # Casing split on third leg
            split_index = (
                len(self.len_buildup) + get_index(self.len_slanted, shifted_cd) + 50
            )
        else:
            warnings.warn("Check casing block")

        return split_index

    def _vertical_leg(self):
        """First leg - vertical well segment

        Returns:
            r_vertical (np.array): Horizontal displacement (all zeros)
            z_vertical (np.array): Vertical displacement linspace
        """

        z_vertical = np.linspace(-self.Z, self.KOP - self.Z)
        r_vertical = np.zeros_like(z_vertical)

        return r_vertical, z_vertical

    def _buildup_leg(self, end_z_vertical):
        """Second leg - gradual incline buildup.

        The leg is approximated as a series of multiple straight
        segments with gradually increasing angle. It's much better to deal
        with than making it actually curved.

        Args:
            end_z_vertical (float): Last z val of previous leg (r val is 0)

        Returns:
            r_buildup (np.array): Horizontal displacement,
                perpendicular to azimuth
            z_vertical (np.array): Vertical displacement
        """

        r_buildup = np.zeros(self.DIP - 1)
        z_buildup = np.zeros(self.DIP - 1)
        self.len_buildup = np.zeros(self.DIP - 1)

        z_buildup[0] = end_z_vertical
        self.len_buildup[0] = end_z_vertical
        for i in range(1, self.DIP - 1):
            r_buildup[i] = r_buildup[i - 1] + Trigonometrics.sind(i) / self.BU
            z_buildup[i] = z_buildup[i - 1] + Trigonometrics.cosd(i) / self.BU
            self.len_buildup[i] = self.len_buildup[i - 1] + 1 / self.BU

        return r_buildup, z_buildup

    def _slanted_leg(self, end_r_buildup, end_z_buildup):
        """Third and last leg - straight slanted.

        Args:
            end_r_buildup (float): Last r val of previous leg
            end_z_buildup (float): Last z val of previous leg

        Returns:
            r_slanted (np.array): Horizontal displacement,
                                  perpendicular to azimuth
            z_slanted (np.array): Vertical displacement
        """

        L2 = self.MMD - self.KOP - self.DIP / self.BU
        r_slanted = np.linspace(end_r_buildup, L2 * Trigonometrics.sind(self.DIP))
        vert = end_z_buildup + np.linspace(0, L2 * Trigonometrics.cosd(self.DIP))
        p = np.polyfit(r_slanted, vert, 1)
        z_zlanted = np.polyval(p, r_slanted)
        self.len_slanted = z_zlanted / Trigonometrics.cosd(self.DIP)

        return r_slanted, z_zlanted

    def assemble(self):
        """Concatenates the three legs.

        Returns:
            r_total (np.array): The concatenated r-values
            z_total (np.array): The concatenated z-values 
            casing_split_index (int): The index where the casing ends
        """

        self.r, self.z = self._vertical_leg()
        if self.KOP:
            r2, z2 = self._buildup_leg(self.z[-1])
            r3, z3 = self._slanted_leg(r2[-1], z2[-1])

            r_total = np.concatenate((self.r, r2, r3))
            z_total = np.concatenate((self.z, z2, z3))
            casing_split_index = self._get_casing_split()

        return r_total, z_total, casing_split_index


class Trajectory3d(Trajectory2d):
    """Generates a 3D trajectory by extrapolating from 2D trajectory.

    What it does is splitting the r-values from the Trajectory2d class
    into x and y components by considering the azimuth.

    Args:
        Trajectory2d (class instance): 2D well trajectory
    """

    def __init__(self):
        super().__init__()
        self.r, self.z, self.casing_split_index = super().assemble()

    def _get_delta(self, r):
        """Forks horizontal displacement r into
        x and y components using the azimuth.

        Args:
            r (float): r component (inherited from super)

        Returns:
            delta_x (float): east/westbound increment
            delta_y (float): north/southbound increment
        """

        delta_y = r / np.sqrt(Trigonometrics.tand(self.AZ) ** 2 + 1)
        delta_x = delta_y * Trigonometrics.tand(self.AZ)

        # Only needed when working with WGS84 (lat/lon)
        # M_TO_DEG = 1.11e5  # m to deg on Earth's surface
        # delta_y /= M_TO_DEG
        # # m to deg is lat dependent for lon
        # delta_x *= cosd(self.X) / M_TO_DEG

        return delta_x, delta_y

    def fork_r(self):
        """Forks array r into x and y components.

        Returns:
            x (np.array): east/westbound component
            y (np.array): north/southbound component
            r (np.array): The horizontal displacement. Used for 2D plot
            z (np.array): Vertical component
            casing_split_index (int): casing split index,
                                      see Trajectory2d.get_casing_split()
        """

        x = self.X + np.zeros(len(self.r))
        y = self.Y + np.zeros(len(self.r))

        # Special cases -> tand(az) = inf
        if self.AZ == 90 or self.AZ == 270:
            x += self.r
            return x, y, self.r, self.z, self.casing_split_index

        for i, r in enumerate(self.r):
            delta_x, delta_y = self._get_delta(r)
            # Must consider which quadrant we're in
            if 90 < self.AZ <= 270:
                y[i] -= delta_y
                x[i] -= delta_x
            else:
                y[i] += delta_y
                x[i] += delta_x
                
        return x, y, self.r, self.z, self.casing_split_index
