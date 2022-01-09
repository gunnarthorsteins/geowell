import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import

with open("config.json") as f:
    settings = json.load(f)

# I'm basically writing the same functions twice, one for unit testing and
# the other for GUI. Should I make ABCs?


class UnitPlots:
    def plot_2d_trajectory(r: np.array, z: np.array, i: int):
        """[summary]

        Args:
            r (np.array): [description]
            z (np.array): [description]
            i (int): Casing split index, see Trajectory2d.get_casing_split()
        """

        plt.plot(r[:i], z[:i], c="#ee2d36")
        plt.plot(r[i - 1 :], z[i - 1 :], c="#ee2d36")
        plt.gca().invert_yaxis()
        plt.show()

    def plot_3d_trajectory(x: np.array, y: np.array, z: np.array, i: int):
        """[summary]

        Args:
            x (np.array): [description]
            y (np.array): [description]
            z (np.array): [description]
            i (int): [description]
        """

        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection="3d")
        ax.view_init(elev=90, azim=0)  # elev=90 & azim=0 sets a birds-eye initial view
        ax.invert_zaxis()  # We want the z-axis to be reversed
        # ax.set_proj_type('ortho')
        ax.plot(x[:i], y[:i], z[:i], c="#ee2d36")
        ax.plot(
            x[i - 1 :], y[i - 1 :], z[i - 1 :], c="#4c4c4c"
        )  # i-1 to ensure overlap w. casing
        plt.show()

    def plot_elevation_map(elevation_data):
        """[summary]

        Args:
            elevation_data ([type]): [description]
        """
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection="3d")
        x = np.array(elevation_data["x"])
        y = np.array(elevation_data["y"])
        z = np.array(elevation_data["z"])
        ax.plot_surface(
            x,
            y,
            z,
            rstride=1,
            cstride=1,
            cmap=matplotlib.cm.coolwarm,
            linewidth=1,
            antialiased=True,
        )
        plt.show()

    def plot_incumbent_wells(wells: pd.DataFrame):
        """Plots a 

        Args:
            wells (pd.DataFrame): [description]
        """

        x = wells["x"].tolist()
        y = wells["y"].tolist()
        z = wells["MaxFDypi"].tolist()
        name = wells["Borholunofn"].tolist()

        def repeat(val):
            return np.repeat(val, 50)

        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(projection="3d")
        for j in range(len(x)):
            x_linspace = repeat(x[j])
            y_linspace = repeat(y[j])
            z_linspace = np.linspace(0, z[j])
            ax.scatter(x_linspace, y_linspace, z_linspace)
            ax.text(x[j], y[j], 0, name[j])
        ax.invert_zaxis()  # We want the z-axis to be reversed
        plt.show()


class GUI:
    def __init__(self):
        plt.rcParams["font.family"] = "monospace"
        fig = plt.figure(figsize=(12, 12))
        gs = GridSpec(3, 3, figure=fig)

        self.ax_2d = fig.add_subplot(gs[:, 0])
        self.ax_2d.invert_yaxis()
        self.ax_2d.set_ylabel("Depth [m]")
        self.ax_2d.set_xlabel("Horizontal throw [m]")
        self.ax_2d.spines["right"].set_visible(False)
        self.ax_2d.spines["top"].set_visible(False)

        self.ax_3d = fig.add_subplot(gs[:, 1:], projection="3d")
        self.ax_3d.view_init(
            elev=90, azim=0
        )  # elev=90 & azim=0 sets a birds-eye initial view
        self.ax_3d.invert_xaxis()
        self.ax_3d.invert_zaxis()
        self.ax_3d.dist = 7
        self.ax_3d.set_proj_type("ortho")
        # self.ax_3d.set_ylim([373_000, 376_000])
        # self.ax_3d.set_xlim([317_500, 319_500])

    def _2d_annotation(self):
        # keys = ['X', 'Y', 'MMD', 'Dip', 'Z', 'Az', 'CD', 'KOP', 'BU']
        # units = ['ISN93', 'ISN93', 'm', 'deg', 'm', 'deg', 'm', 'm', 'deg/100ft']
        # vals = [317000, 374000, 2500, 20, 20, 30, 1500, 1000, 1.5]
        cell_text = list(
            zip(
                settings["default_values"].keys(),
                settings["default_values"].values(),
                settings["units"],
            )
        )
        col_labels = ["param", "val", "unit"]
        table = self.ax_2d.table(
            cellText=cell_text,
            colLabels=col_labels,
            colColours=[settings["palette"]["light_gray"]] * 3,
            cellLoc="right",
            loc="upper right",
            colLoc="right",
            edges="open",
        )
        table.auto_set_column_width([0, 1, 2])

        def set_align_for_column(table, col, align="left"):
            cells = [key for key in table._cells if key[1] == col]
            for cell in cells:
                table._cells[cell]._loc = align

        set_align_for_column(table, col=0, align="left")
        # set_align_for_column(table, col=1, align="left")
        for key, cell in table.get_celld().items():
            if key[0] == 0 or key[1] == -1:
                cell.weight = "extra bold"

    def plot_2d_trajectory(self, r: np.array, z: np.array, i: int):
        """[summary]

        Args:
            r (np.array): [description]
            z (np.array): [description]
            i (int): Casing split index, see Trajectory2d.get_casing_split()
        """

        self._2d_annotation()
        self.ax_2d.plot(
            r[:i],
            z[:i],
            c=settings["palette"]["blue"],
            linewidth=3,
            solid_capstyle="round",
        )
        self.ax_2d.plot(
            r[i - 1 :],
            z[i - 1 :],
            c=settings["palette"]["red"],
            linewidth=3,
            solid_capstyle="round",
        )
        # self.ax_2d.set_title('Perpendicular view')

    def plot_3d_trajectory(self, x: np.array, y: np.array, z: np.array, i: int):
        """[summary]

        Args:
            x (np.array): [description]
            y (np.array): [description]
            z (np.array): [description]
            i (int): [description]
        """

        self.ax_3d.plot(y[:i], x[:i], z[:i], c=settings["palette"]["blue"])
        self.ax_3d.plot(
            y[i - 1 :],
            x[i - 1 :],
            z[i - 1 :],
            c=settings["palette"]["red"],
            solid_capstyle="round",
        )  # i-1 to ensure overlap w. casing
        self.ax_3d.text(y[0], x[0], z[0], settings["well_name"], fontweight="bold")

    def plot_elevation_map(self, elevation_data: pd.DataFrame):
        """[summary]

        Args:
            elevation_data ([type]): [description]
        """

        x = np.array(elevation_data["x"])
        y = np.array(elevation_data["y"])
        z = np.array(elevation_data["z"])
        cmap = matplotlib.cm.get_cmap("binary_r")
        self.ax_3d.plot_surface(
            y, x, -z, rstride=1, cstride=1, cmap=cmap, linewidth=1, alpha=0.5
        )

    def plot_incumbent_wells(self, wells: pd.DataFrame):
        """Plots a 

        Args:
            wells (pd.DataFrame): [description]
        """

        x = wells["x"].tolist()
        y = wells["y"].tolist()
        z = wells["MaxFDypi"].tolist()
        name = wells["Borholunofn"].tolist()

        def repeat(val):
            return np.repeat(val, 50)

        for j in range(len(x)):
            x_linspace = repeat(x[j])
            y_linspace = repeat(y[j])
            z_linspace = np.linspace(-20, z[j])
            self.ax_3d.scatter(y[j], x[j], -20, c="k", s=3)
            self.ax_3d.plot(
                y_linspace, x_linspace, z_linspace, c="k", solid_capstyle="round"
            )
            self.ax_3d.text(y[j], x[j], 0, name[j], c=settings["palette"]["gray"])

