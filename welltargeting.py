import warnings
import numpy as np
import pandas as pd

# import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from bokeh.plotting import figure, show


class WellTargeting:
    '''Interactive well targeting.

    Params:
        lon:            Well head horizontal coordinate
                            (either in WGS84 (GPS) or ISN93 (Iceland only))
        lat:            Well head vertical coordinate
                            (either in WGS84 (GPS) or ISN93 (Iceland only))
        mmd:            Measured depth (m or km)
        Z:              Well head altitude above sea level
        az:             Well trajectory (deg clockwise from north).
                            Default: 0
        kop:            Kick-off point. Default: 0
        dip:            Maximum well angle after build-up
                            (measured from vertical)
        casing_depth:   Casing depth (m or ratio of mmd)
        bu:             Build-up from kick-off (degs per 100 ft)
        mapping:        Choice of map to overlay:
                        Thermal, RGB or Faults

    '''

    def __init__(
        self,
        lon,
        lat,
        mmd,
        Z,
        az=0,
        kop=None,
        dip=20,
        cd=0,
        bu=2,
        mapping=None,
    ):

        self.lon = lon
        self.lat = lat
        self.mmd = mmd if mmd > 10 else mmd * 1000
        self.Z = Z
        self.az = az
        self.kop = kop
        self.dip = dip
        self.cd = cd if cd > 1 else cd * self.mmd
        self.bu = bu / 30
        self.mapping = mapping

        self.coord_sys = 'WGS84' if lat < 90 else 'ISN93'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, tb):
        pass

    @staticmethod
    def cosd(deg):
        return np.cos(np.deg2rad(deg))

    @staticmethod
    def sind(deg):
        return np.sin(np.deg2rad(deg))

    @staticmethod
    def tand(deg):
        return np.tan(np.deg2rad(deg))

    def trajectory_2d(self):
        '''Three legs:
        1) Down to KOP
        2) Build-up
        3) Last leg to well bottom (straight)
        '''

        def first_leg():
            """Creates a vertical well segment"""

            z = np.linspace(-self.Z, self.kop - self.Z)
            r = np.zeros_like(z)

            return r, z

        # Directional
        if self.kop != None:
            # First leg
            r1, z1 = first_leg()

            # Second leg - The curved segment
            r2 = np.zeros(self.dip - 1)
            z2 = np.zeros(self.dip - 1)
            z2[0] = z1[-1]
            len_2 = np.zeros(self.dip - 1)
            len_2[0] = z1[-1]
            for i in range(1, self.dip - 1):
                r2[i] = r2[i-1] + self.sind(i) / self.bu
                z2[i] = z2[i-1] + self.cosd(i) / self.bu
                len_2[i] = len_2[i-1] + 1 / self.bu

            # Third leg - The last one
            L2 = self.mmd - self.kop - self.dip / self.bu
            r3 = np.linspace(
                r2[-1], L2 * self.sind(self.dip)
            )
            vert = z2[-1] + np.linspace(0, L2 * self.cosd(self.dip))
            p = np.polyfit(r3, vert, 1)
            z3 = np.polyval(p, r3)
            len_3 = z3 / self.cosd(self.dip)

            self.r = np.concatenate((r1, r2, r3))
            self.z = np.concatenate((z1, z2, z3))

        # Vertical
        else:
            self.r, self.z = first_leg()

        # Determine casing TVD to split curve
        if self.cd <= self.kop:
            self.split = sum(self.z < (self.cd - self.Z))
        elif self.kop < self.cd and self.cd < len_2[-1]:
            self.split = 50 + sum(len_2 < (self.cd - self.Z))
        elif len_2[-1] < self.cd:
            self.split = 50 + len(z2) + sum(len_3 < (self.cd - self.Z))
        else:
            warnings.warn('Check casing block')

        self.plot_2d(self.r, self.z, self.split)

    def plot_2d(self, r, z, split):
        self.fig = figure(title="Simple line example", x_axis_label='x', y_axis_label='y')

        # self.fig = plt.figure(dpi=250)
        # self.gs = GridSpec(4, 4, figure=self.fig)
        # ax2D = self.fig.add_subplot(self.gs[:, 0])

        def plotter(r, z, c):
            ax2D.plot(
                r,
                z,
                c=c,
                linewidth=3,
                solid_capstyle='round',
            )

        plotter(r[:split+1], z[:split+1], 'k')
        plotter(r[split:], z[split:], 'r')
        self.fig.line(r, z, legend_label="Temp.", line_width=2)
        ax2D.set_xlabel('Horizontal Throw [m]')
        ax2D.set_ylabel('Vert. Depth [m]')
        ax2D.set(
            xlim=(-50, max(r) + 100),
            ylim=(-50 - self.Z, max(z) + 100)
        )
        ax2D.invert_yaxis()
        hor, ver = ('lon', 'lat') if self.lon < 90 else ('X', 'Y')
        anno = (
            f'{hor} = {self.lon}\n{ver} = {self.lat}\nmMD = {self.mmd}\n'
            f'Z = {self.Z}\nKOP = {self.kop}\n'
            f'az = {self.az}\nDip = {self.dip}\n'
            f'CD = {self.cd}\nBU = {self.bu}'
        )
        # ax2D.text(
        #     x=max(r) * 0.67,
        #     y=50,
        #     s=anno,
        #     backgroundcolor='w',
        #     verticalalignment='top',
        #     linespacing=1,
        #     bbox=dict(
        #         facecolor='w', edgecolor='black', boxstyle='round,pad=1'
        #     ),
        # )
        ax2D.grid(zorder=-1)
        show(self.fig)

    def trajectory_3d(self):

        def delta(r):

            delta_y = r / np.sqrt(self.tand(self.az)**2 + 1)
            delta_x = delta_y * self.tand(self.az)

            return delta_x, delta_y

        # fig = plt.figure(dpi=200)
        # ax = plt.axes(projection='3d')
        ax3D = self.fig.add_subplot(self.gs[:, 1:],projection='3d')
        ax3D.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        ax3D.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        ax3D.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        x = self.lon + np.zeros(len(self.r))
        y = self.lat + np.zeros(len(self.r))
        m_to_deg = 1.11e5  # m to deg on Earth's surface

        for i in range(len(self.z)):
            # Accounting for special cases -> tand(az) = inf
            if self.az == 90 or self.az == 270:
                delta_y = 0
                delta_x = self.r[-1]
            else:
                delta_x, delta_y = delta(self.r[i])

            delta_y /= m_to_deg
            # m to deg is lat dependent for lon
            delta_x *= self.cosd(self.lat) / m_to_deg
            if self.az <= 90 or self.az > 270:
                y[i] += delta_y
                x[i] += delta_x
            else:
                y[i] -= delta_y
                x[i] -= delta_x

        ax3D.plot3D(x[:self.split+1], y[:self.split+1], self.z[:self.split+1], 'k')
        ax3D.plot3D(x[self.split:], y[self.split:], self.z[self.split:], 'r')
        ax3D.set_box_aspect([1, 1, 1])
        ax3D.invert_zaxis()
        plt.show()


if __name__ == '__main__':
    run = WellTargeting(
        lon=-22.7,
        lat=63.4,
        mmd=2500,
        Z=20,
        az=30,
        cd=1500,
        kop=1000,
        bu=1.5,
    )

    run.trajectory_2d()
    # run.trajectory_3d()
