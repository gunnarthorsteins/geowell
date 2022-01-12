import json
import numpy as np
import pandas as pd

from plots import UnitPlots

with open("config.json") as f:
    settings = json.load(f)


class UnitTests:
    def test_trajectory(trajectory_instance):
        x, y, _, z, i = trajectory_instance.fork_r()
        UnitPlots.plot_3d_trajectory(x, y, z, i)

    def test_elevation():
        with open(f"data/Reykjanes.json") as f:
            elevation_data = json.load(f)
        UnitPlots.plot_elevation_map(elevation_data)

    def test_wells(wells_filename):
        wells_df = pd.read_csv(wells_filename)
        UnitPlots.plot_incumbent_wells(wells_df)

    def test_distance(distance_instance):
        distance_instance.run()