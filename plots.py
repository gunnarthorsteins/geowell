import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm
from matplotlib.font_manager import FontProperties
from matplotlib.gridspec import GridSpec


with open("config.json") as f:
    settings = json.load(f)


class GUI:
    def __init__(self):
        plt.rcParams["font.family"] = "monospace"
        self.fig = plt.figure(figsize=(12, 12))
        gs = GridSpec(nrows=3, ncols=3, figure=self.fig)

        # 2D Trajectory
        self.ax_2d = self.fig.add_subplot(gs[:2, 0])
        self.ax_2d.invert_yaxis()
        self.ax_2d.set_ylabel("Depth [m]")
        self.ax_2d.set_xlabel("Horizontal throw [m]")
        self.ax_2d.xaxis.tick_top()
        self.ax_2d.xaxis.set_label_position("top")

        # Well distance
        self.ax_distances = self.fig.add_subplot(gs[-1, 0])
        self.ax_distances.set_ylabel("Vertical Depth [m]")
        well_name = settings["well_name"]
        self.ax_distances.set_xlabel(
            f"Distance between {well_name}\nand other wells [m]"
        )
        self.ax_distances.set_xlim([0, settings["max_distance"] + 100])
        self.ax_distances.invert_yaxis()

        # 3D Map
        self.ax_3d = self.fig.add_subplot(gs[:, 1:3], projection="3d")
        self.ax_3d.view_init(
            elev=90, azim=0
        )  # elev=90 & azim=0 sets a birds-eye initial view
        self.ax_3d.invert_xaxis()
        self.ax_3d.invert_zaxis()
        self.ax_3d.dist = 8
        self.ax_3d.set_proj_type("ortho")

    def _2d_annotation(self):
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
            loc="upper right",
            edges="open",
            colLoc="right",
        )
        # Column alignment
        for (row, col), cell in table.get_celld().items():
            if (row == 0) or (col == -1):
                cell.set_text_props(fontproperties=FontProperties(weight="bold"))
            if col == 0 or col == 2:
                cell.set_text_props(ha="left")

        table.auto_set_column_width([0, 1, 2])

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
        # Reversed b/c z-axis is reversed
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
            self.ax_3d.text(
                y[j], x[j], 0, name[j], c=settings["palette"]["blue"], fontsize=8
            )

    def plot_distances(self, distances: dict, z, CASING_DEPTH_ABSOLUTE):
        legend = []
        no_of_wells_plotted = 0
        for well_name, distance_curve in distances.items():
            if min(distance_curve) < settings["max_distance"]:
                no_of_wells_plotted += 1
                legend.append(well_name)
                self.ax_distances.plot(distance_curve, z[: len(distance_curve)])
        if not no_of_wells_plotted:
            self.ax_distances.text(
                100,
                0.7,
                f'No wells at distance <{settings["max_distance"]} m',
                rotation=45,
            )
        else:
            self.ax_distances.hlines(
                CASING_DEPTH_ABSOLUTE, 0, 1000, color="k", linestyles="dashed"
            )
        self.ax_distances.legend(legend)
        self.fig.tight_layout()

