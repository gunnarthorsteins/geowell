import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm


class TestPlots:
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

    def plot_well_heads(x, y, z, name):
        """[summary]

        Args:
            x ([type]): [description]
            y ([type]): [description]
            z ([type]): [description]
            name ([type]): [description]
        """        
        
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