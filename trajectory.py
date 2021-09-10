import json
import numpy as np
import warnings

import matplotlib.pyplot as plt


M_TO_DEG = 1.11e5  # m to deg on Earth's surface


class Trajectory2d:

    '''Three legs:
    1) Down to KOP
    2) Build-up
    3) Last leg to well bottom (straight)
    '''

    def __init__(self):

        with open('data/defaults.json') as json_file:
            default_values = json.load(json_file)

        self.lon = default_values["lon"]
        self.lat = default_values["lat"]
        self.mmd = default_values["mmd"]
        self.dip = default_values["dip"]
        self.Z = default_values["Z"]
        self.az = default_values["az"]
        self.cd = default_values["cd"]
        self.kop = default_values["kop"]
        self.bu = default_values["bu"]

        self.assemble()

    def _cosd(self, deg):
        return np.cos(np.deg2rad(deg))

    def _sind(self, deg):
        return np.sin(np.deg2rad(deg))

    def _get_index(self, a, b):
        return sum(a < b)

    def _casing_split(self):
        """Splits the curve at end of casing for plot coloring

        Returns:
            split (int): Index denoting where to split r & z
        """

        shifted_cd = self.cd - self.Z

        if self.cd <= self.kop:
            split_index = self._get_index(self.z, shifted_cd)
        elif self.kop < self.cd < self.len_buildup[-1]:
            split_index = self._get_index(self.len_buildup, shifted_cd)
        elif self.len_buildup[-1] < self.cd:
            # NOTE Used to have +50 here, don't know why
            split_index = len(self.len_buildup) + \
                self._get_index(self.len_slanted, shifted_cd)
        else:
            warnings.warn('Check casing block')

        return split_index

    def vertical_leg(self):
        """First leg - a vertical well segment

        Returns:
            r_vertical (1D array): Horizontal displacement (all zeros)
            z_vertical (1D array): Vertical displacement linspace
        """

        z_vertical = np.linspace(-self.Z, self.kop - self.Z)
        r_vertical = np.zeros_like(z_vertical)

        return r_vertical, z_vertical

    def buildup_leg(self, end_z_vertical):
        """Second leg - gradual incline buildup.

        Returns:
            r_buildup (1D array): Horizontal displacement, perpendicular to azimuth
            z_vertical (1D array): Vertical displacement
        """

        r_buildup = np.zeros(self.dip - 1)
        z_buildup = np.zeros(self.dip - 1)
        self.len_buildup = np.zeros(self.dip - 1)

        z_buildup[0] = end_z_vertical
        self.len_buildup[0] = end_z_vertical
        for i in range(1, self.dip - 1):
            r_buildup[i] = r_buildup[i-1] + self._sind(i) / self.bu
            z_buildup[i] = z_buildup[i-1] + self._cosd(i) / self.bu
            self.len_buildup[i] = self.len_buildup[i-1] + 1 / self.bu

        return r_buildup, z_buildup

    def slanted_leg(self, end_r_buildup, end_z_buildup):
        """Third and last leg - straight slanted.

        Args:
            end_r_buildup (float): Last r val of previous leg
            end_z_buildup (float): Last z val of previous leg

        Returns:
            r_slanted (1D array): Horizontal displacement, perpendicular to azimuth
            z_slanted (1D array): Vertical displacement
        """

        L2 = self.mmd - self.kop - self.dip / self.bu
        r_slanted = np.linspace(end_r_buildup, L2 * self._sind(self.dip))
        vert = end_z_buildup + np.linspace(0, L2 * self._cosd(self.dip))
        p = np.polyfit(r_slanted, vert, 1)
        z_zlanted = np.polyval(p, r_slanted)
        self.len_slanted = z_zlanted / self._cosd(self.dip)

        return r_slanted, z_zlanted

    def assemble(self):
        self.r, self.z = self.vertical_leg()
        if not self.kop:
            return

        r2, z2 = self.buildup_leg(self.z[-1])
        r3, z3 = self.slanted_leg(r2[-1], z2[-1])

        self.r = np.concatenate((self.r, r2, r3))
        self.z = np.concatenate((self.z, z2, z3))
        split_index = self._casing_split()

    def test_plot(self):
        plt.plot(self.r, self.z)


class Trajectory3d(Trajectory2d):
    def __init__(self):
        super().__init__()

    def _tand(self, deg):
        return np.tan(np.deg2rad(deg))

    def _delta(self, r):
        """Forks horizontal displacement r into x and y components using the azimuth.

        Args:
            r (float): r component (inherited from super)

        Returns:
            delta_x (float): east/westbound increment
            delta_y (float): north/southbound increment
        """

        delta_y = r / np.sqrt(self._tand(self.az)**2 + 1)
        delta_x = delta_y * self._tand(self.az)

        delta_y /= M_TO_DEG
        # m to deg is lat dependent for lon
        delta_x *= self._cosd(self.lat) / M_TO_DEG

        return delta_x, delta_y

    def fork_r(self):
        """Forks vector r into x and y components.

        Returns:
            x (1D array): east/westbound component
            y (1D array): north/southbound component 
        """

        x = self.lon + np.zeros(len(self.r))
        y = self.lat + np.zeros(len(self.r))

        # Special cases -> tand(az) = inf
        if self.az == 90 or self.az == 270:
            x += self.r
            return x, y

        for i, r in enumerate(self.r):
            delta_x, delta_y = self._delta(r)
            if 90 < self.az <= 270:
                y[i] -= delta_y
                x[i] -= delta_x
            else:
                y[i] += delta_y
                x[i] += delta_x

        return x, y

    def run(self):
        self.x, self.y = self.fork_r()

    def test_plot(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(self.x, self.y, self.z)
        fig.show()


if __name__ == '__main__':

    # traj2d = Trajectory2d()
    # traj2d.assemble()
    # traj2d.test_plot()
    traj3d = Trajectory3d()
    traj3d.run()
    traj3d.test_plot()
