import time
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm
import warnings

from geofeatures.elevation import Process
from geofeatures.wells import OpenSourceWells
from geofeatures.trajectory import Trajectory3d
from geofeatures.distance import Distance

# Suppressing an obnoxious mapping plotting warning
warnings.filterwarnings("ignore", category=RuntimeWarning)


with open("config.json") as f:
    settings = json.load(f)
locations = settings["locations_bbox"]


def write_test_results(test):
    print(f"{test} OK")


class FigureTests:
    def test_trajectory():
        trajectory_ = Trajectory3d(settings["default_values"])
        x, y, r, z, i = trajectory_.fork_r()
        # UnitPlots.plot_2d_trajectory(r, z, i)
        UnitPlots.plot_3d_trajectory(x, y, z, i)
        write_test_results("trajectory")

    def test_elevation():
        for location, coordinates in locations.items():
            process = Process(location, coordinates)
            process.run()
            break  # Only want Reykjanes
        with open(f"data/Reykjanes.json") as f:
            elevation_data = json.load(f)
        UnitPlots.plot_elevation_map(elevation_data)
        write_test_results("elevation")

    def test_wells():
        wells_ = OpenSourceWells()
        all_wells_in_iceland = wells_.download()
        wells_raw = wells_.filter_area(all_wells_in_iceland)
        wells_df = wells_.process(wells_raw)
        wells_.save(wells_df)
        UnitPlots.plot_incumbent_wells(wells_df)
        write_test_results("wells")

    def test_distance():
        """Cannot make completely independent of other modules
        b/c its dependent on the well trajectory
        """

        incumbent_wells = pd.read_csv(settings["wells_filename"])
        trajectory_ = Trajectory3d(settings["default_values"])
        x, y, _, z, _ = trajectory_.fork_r()
        proposed_well = np.array((x, y, z)).T
        distance_ = Distance(incumbent_wells, proposed_well)
        distances = distance_.run()
        UnitPlots.plot_distances(distances)
        write_test_results("distance")


class UnitPlots:
    def plot_2d_trajectory(r: np.array, z: np.array, i: int):
        """[summary]

        Args:
            r (np.array): [description]
            z (np.array): [description]
            i (int): Casing split index, see
                     Trajectory2d.get_casing_split()
        """

        plt.plot(r[:i], z[:i], c="#ee2d36")
        plt.plot(r[i - 1 :], z[i - 1 :], c="#ee2d36")
        plt.gca().invert_yaxis()
        plt.axis("equal")
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
        # ax.view_init(elev=90, azim=0)  # elev=90 & azim=0 sets a birds-eye initial view
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
        ax.view_init(elev=90, azim=0)  # elev=90 & azim=0 sets a birds-eye initial view
        ax.set_proj_type("ortho")
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

    def plot_distances(distances: dict):
        for well_name, distance_curve in distances.items():
            plt.plot(distance_curve)
        plt.show()


def _between_unit_tests():
    time.sleep(1)
    plt.close("all")


def main():
    FigureTests.test_trajectory()
    _between_unit_tests()
    FigureTests.test_elevation()
    _between_unit_tests()
    FigureTests.test_wells()
    _between_unit_tests()
    FigureTests.test_distance()
    _between_unit_tests()


if __name__ == "__main__":
    main()
