"""The geowell application.

Usage:
    > python geowell.py --parameter=value

    where 'parameter' can be any of the default_values in config.json
    and 'value' any corresponding value

Example:
    > python geowell.py --az=300
"""

import fire
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings

from geofeatures.distance import Distance
from geofeatures.trajectory import Trajectory3d
from plots import GUI

# Suppressing an obnoxious mapping plotting warning
warnings.filterwarnings("ignore", category=RuntimeWarning)

with open("config.json") as f:
    settings = json.load(f)
parameters = settings["default_values"]


def geowell(**custom_params):
    for parameter, value in custom_params.items():
        parameters[parameter] = value

    gui = GUI()

    # Trajectory
    traj_instance = Trajectory3d(parameters)
    x, y, r, z, casing_index = traj_instance.fork_r()
    gui.plot_2d_trajectory(r, z, casing_index)
    gui.plot_3d_trajectory(x, y, z, casing_index)

    # Elevation
    with open(f"data/Reykjanes.json") as f:
        elevation_data = json.load(f)
    gui.plot_elevation_map(elevation_data)

    # Wells
    wells_filename = "data/wells.csv"
    wells_df = pd.read_csv(wells_filename)
    gui.plot_incumbent_wells(wells_df)

    # Well distance
    incumbent_wells = pd.read_csv(settings["wells_filename"])
    proposed_well = np.array((x, y, z)).T
    distance_ = Distance(incumbent_wells, proposed_well)
    distances = distance_.run()
    gui.plot_distances(distances, z)

    plt.show()


if __name__ == "__main__":
    fire.Fire(geowell)
