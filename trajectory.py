import json
import numpy as np
import warnings

from tests import TestPlots
from utils.trigonometrics import *

M_TO_DEG = 1.11e5  # m to deg on Earth's surface


class Trajectory2d:

    '''Three legs:
    1) Down to KOP
    2) Build-up
    3) Last leg to well bottom (straight)

    (Leading underscore for class methods not intended for external calls)
    '''

    def __init__(self):

        with open('config.json') as json_file:
            default_values = json.load(json_file)

        self.LON = default_values["default_values"]["lon"]
        self.LAT = default_values["default_values"]["lat"]
        self.MMD = default_values["default_values"]["mmd"]
        self.DIP = default_values["default_values"]["dip"]
        self.Z = default_values["default_values"]["Z"]
        self.AZ = default_values["default_values"]["az"]
        self.CD = default_values["default_values"]["cd"]
        self.KOP = default_values["default_values"]["kop"]
        self.BU = default_values["default_values"]["bu"]

    @staticmethod
    def _get_index(a, b):
        """Helper function for _get_casing_split. 

        Args:
            a (np.array): [description]
            b (np.array): [description]

        Returns:
            (list): A list of boolean values
        """        
        return sum(a < b)

    def _get_casing_split(self):
        """Finds the well trajectory index of the casing split.

        Returns:
            split_index (int): Index denoting where to split r & z
        """

        shifted_cd = self.CD - self.Z

        if self.CD <= self.KOP: # Casing split on first leg
            split_index = self._get_index(self.z, shifted_cd)
        # The +50 is b/c the vertical segment always has a len of 50 which must be accounted for
        elif self.KOP < self.CD < self.len_buildup[-1]:  # Casing split on second leg
            split_index = self._get_index(self.len_buildup, shifted_cd) + 50
        elif self.len_buildup[-1] < self.CD:  # Casing split on third leg
            split_index = len(self.len_buildup) + \
                self._get_index(self.len_slanted, shifted_cd) + 50
        else:
            warnings.warn('Check casing block')

        return split_index

    def _vertical_leg(self):
        """First leg - a vertical well segment

        Returns:
            r_vertical (np.array): Horizontal displacement (all zeros)
            z_vertical (np.array): Vertical displacement linspace
        """

        z_vertical = np.linspace(-self.Z, self.KOP - self.Z)
        r_vertical = np.zeros_like(z_vertical)

        return r_vertical, z_vertical

    def _buildup_leg(self, end_z_vertical):
        """Second leg - gradual incline buildup.

        Args:
            end_z_vertical (float): Last z val of previous leg (r val is 0)

        Returns:
            r_buildup (np.array): Horizontal displacement, perpendicular to azimuth
            z_vertical (np.array): Vertical displacement
        """

        r_buildup = np.zeros(self.DIP - 1)
        z_buildup = np.zeros(self.DIP - 1)
        self.len_buildup = np.zeros(self.DIP - 1)

        z_buildup[0] = end_z_vertical
        self.len_buildup[0] = end_z_vertical
        for i in range(1, self.DIP - 1):
            r_buildup[i] = r_buildup[i-1] + sind(i) / self.BU
            z_buildup[i] = z_buildup[i-1] + cosd(i) / self.BU
            self.len_buildup[i] = self.len_buildup[i-1] + 1 / self.BU

        return r_buildup, z_buildup

    def _slanted_leg(self, end_r_buildup, end_z_buildup):
        """Third and last leg - straight slanted.

        Args:
            end_r_buildup (float): Last r val of previous leg
            end_z_buildup (float): Last z val of previous leg

        Returns:
            r_slanted (np.array): Horizontal displacement, perpendicular to azimuth
            z_slanted (np.array): Vertical displacement
        """

        L2 = self.MMD - self.KOP - self.DIP / self.BU
        r_slanted = np.linspace(end_r_buildup, L2 * sind(self.DIP))
        vert = end_z_buildup + np.linspace(0, L2 * cosd(self.DIP))
        p = np.polyfit(r_slanted, vert, 1)
        z_zlanted = np.polyval(p, r_slanted)
        self.len_slanted = z_zlanted / cosd(self.DIP)

        return r_slanted, z_zlanted

    def assemble(self):
        """[summary]

        Returns:
            [type]: [description]
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
    def __init__(self):
        super().__init__()
        self.r, self.z, self.casing_split_index = super().assemble()

    def _get_delta(self, r):
        """Forks horizontal displacement r into x and y components using the azimuth.

        Args:
            r (float): r component (inherited from super)

        Returns:
            delta_x (float): east/westbound increment
            delta_y (float): north/southbound increment
        """

        delta_y = r / np.sqrt(tand(self.AZ)**2 + 1)
        delta_x = delta_y * tand(self.AZ)

        delta_y /= M_TO_DEG
        # m to deg is lat dependent for lon
        delta_x *= cosd(self.LAT) / M_TO_DEG

        return delta_x, delta_y

    def fork_r(self):
        """Forks vector r into x and y components.

        Returns:
            x (np.array): east/westbound component
            y (np.array): north/southbound component
            r (np.array): sqrt(x^2 + y^2) -> For 2D plot
            z (np.array): vertical component
            casing_split_index (int): casing split index, see Trajectory2d.get_casing_split()
        """

        x = self.LON + np.zeros(len(self.r))
        y = self.LAT + np.zeros(len(self.r))

        # Special cases -> tand(az) = inf
        if self.AZ == 90 or self.AZ == 270:
            x += self.r
            return x, y

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

if __name__ == '__main__':

    # traj2d = Trajectory2d()
    # r, z, casing_split_index = traj2d.assemble()
    # TestPlots.plot_2d_trajectory(r, z, casing_split_index)
    traj3d = Trajectory3d()
    x, y, r, z, i = traj3d.fork_r()
    TestPlots.plot_3d_trajectory(x, y, z, i)
