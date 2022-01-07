import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import trajectory
from plots import GUI

gui = GUI()

# Trajectory
traj_instance = trajectory.Trajectory3d()
x, y, r, z, casing_index = traj_instance.fork_r()
gui.plot_2d_trajectory(r, z, casing_index)
gui.plot_3d_trajectory(x, y, z, casing_index)

# Elevation
with open(f'data/Reykjanes.json') as f:
    elevation_data = json.load(f)        
gui.plot_elevation_map(elevation_data)

# Wells
wells_filename = 'data/wells.csv'
wells_df = pd.read_csv(wells_filename)
gui.plot_incumbent_wells(wells_df)

plt.show()
