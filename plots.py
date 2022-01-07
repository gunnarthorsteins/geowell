import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import

with open('config.json') as f:
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

        plt.plot(r[:i], z[:i], c='#ee2d36')
        plt.plot(r[i-1:], z[i-1:], c='#ee2d36')
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
        
        fig = plt.figure(figsize=(8,8))
        ax = fig.add_subplot(111, projection='3d')
        ax.view_init(elev=90, azim=0)  # elev=90 & azim=0 sets a birds-eye initial view
        ax.invert_zaxis()  # We want the z-axis to be reversed
        # ax.set_proj_type('ortho')
        ax.plot(x[:i], y[:i], z[:i], c='#ee2d36')
        ax.plot(x[i-1:], y[i-1:], z[i-1:], c='#4c4c4c')  # i-1 to ensure overlap w. casing
        plt.show()

    def plot_elevation_map(elevation_data):
        """[summary]

        Args:
            elevation_data ([type]): [description]
        """        
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')
        x = np.array(elevation_data['x'])
        y = np.array(elevation_data['y'])
        z = np.array(elevation_data['z'])
        ax.plot_surface(x,
                        y,
                        z,
                        rstride=1,
                        cstride=1,
                        cmap=matplotlib.cm.coolwarm,
                        linewidth=1,
                        antialiased=True)
        plt.show()

    def plot_incumbent_wells(wells: pd.DataFrame):
        """Plots a 

        Args:
            wells (pd.DataFrame): [description]
        """

        x = wells['x'].tolist()
        y = wells['y'].tolist()
        z = wells['MaxFDypi'].tolist()
        name = wells['Borholunofn'].tolist()

        def repeat(val):
            return np.repeat(val, 50)
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(projection='3d')
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
        plt.rcParams['font.family'] = 'monospace'
        fig, self.ax = plt.subplots(figsize=(12,12), sharex=False, sharey=False)
        gs = GridSpec(3, 3, figure=fig)

        self.ax_2d = fig.add_subplot(gs[:, 0])
        self.ax_2d.invert_yaxis()
        self.ax_2d.set_ylabel('Depth [m]')
        self.ax_2d.set_xlabel('Horizontal throw [m]')

        self.ax_3d = fig.add_subplot(gs[1:2, :], projection='3d')
        self.ax_3d.view_init(elev=90, azim=0)  # elev=90 & azim=0 sets a birds-eye initial view
        self.ax_3d.invert_xaxis()
        self.ax_3d.invert_zaxis()
        # self.ax_3d.dist = 3
        # self.ax_3d.set_proj_type('ortho')

    def _2d_annotation(self):
        keys = ['X', 'Y', 'MMD', 'Dip', 'Z', 'Azimuth', 'CD', 'KOP', 'BU']
        units = ['ISN93', 'ISN93', 'm', 'deg', 'm', 'deg', 'm', 'm', 'deg/100ft']
        vals = [317000, 374000, 2500, 20, 20, 30, 1500, 1000, 1.5]
        cell_text = list(zip(keys, units, vals))
        col_labels = ['parameter', 'unit', 'val']
        self.ax_2d.table(cellText=cell_text,
                         colLabels=col_labels,
                         colColours=[settings['palette']['gray']] * len(keys),
                         cellLoc='right',
                         loc='upper right')
        # box_props = dict(boxstyle='round', facecolor='white', alpha=0.5)
        # text = f'lon: 317000\n'\
        #        f'lat: 374000\n'\
        #        f'mmd [m]: 2500\n'\
        #        f'dip [deg]: 20\n'\
        #        f'Z [m]: 20\n'\
        #        f'az [deg]: 30\n'\
        #        f'cd [m]: 1500\n'\
        #        f'kop [m]: 1000\n'\
        #        f'bu [deg/100ft]: {0.05*30}'
        # # place a text box in upper left in axes coords
        # self.ax_2d.text(0.6, 0.9, text,
                        # transform=self.ax_2d.transAxes,
                        # fontsize=14,
                        # va='top',
                        # ha='right',
                        # bbox=box_props)


    def plot_2d_trajectory(self, r: np.array, z: np.array, i: int):
        """[summary]

        Args:
            r (np.array): [description]
            z (np.array): [description]
            i (int): Casing split index, see Trajectory2d.get_casing_split()
        """        

        self._2d_annotation()
        self.ax_2d.plot(r[:i],
                        z[:i],
                        c=settings['palette']['blue'],
                        linewidth=3,
                        solid_capstyle='round')
        self.ax_2d.plot(r[i-1:],
                        z[i-1:],
                        c=settings['palette']['red'],
                        linewidth=3, solid_capstyle='round')

    def plot_3d_trajectory(self, x: np.array, y: np.array, z: np.array, i: int):
        """[summary]

        Args:
            x (np.array): [description]
            y (np.array): [description]
            z (np.array): [description]
            i (int): [description]
        """    
        
        self.ax_3d.plot(x[:i], y[:i], z[:i], c=settings['palette']['blue'])
        self.ax_3d.plot(x[i-1:], y[i-1:], z[i-1:], c=settings['palette']['red'])  # i-1 to ensure overlap w. casing

    def plot_elevation_map(self, elevation_data: pd.DataFrame):
        """[summary]

        Args:
            elevation_data ([type]): [description]
        """        

        x = np.array(elevation_data['x'])
        y = np.array(elevation_data['y'])
        z = np.array(elevation_data['z'])
        self.ax_3d.plot_surface(x,
                                y,
                                z,
                                rstride=1,
                                cstride=1,
                                cmap=matplotlib.cm.binary,
                                linewidth=1,
                                antialiased=True,
                                alpha=0.5)

    def plot_incumbent_wells(self, wells: pd.DataFrame):
        """Plots a 

        Args:
            wells (pd.DataFrame): [description]
        """

        x = wells['x'].tolist()
        y = wells['y'].tolist()
        z = wells['MaxFDypi'].tolist()
        name = wells['Borholunofn'].tolist()

        def repeat(val):
            return np.repeat(val, 50)
        for j in range(len(x)):
            x_linspace = repeat(x[j])
            y_linspace = repeat(y[j])
            z_linspace = np.linspace(0, z[j])
            self.ax_3d.plot(x_linspace, y_linspace, z_linspace, c='k')
            self.ax_3d.text(x[j], y[j], 0, name[j])
