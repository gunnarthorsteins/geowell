import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils.interpolate import interpolate
import trajectory

with open("config.json") as f:
    settings = json.load(f)


class Distance:
    """Calculates distance to nearest wells."""

    def __init__(self, incumbent_wells, proposed_well):
        self.incumbent_wells = incumbent_wells
        self.proposed_well = proposed_well

    def synthesize_values(
        self, i_proposed: int, x_to_interpolate: float, y_to_interpolate: float
    ):
        """Incumbent wells and proposed well don't usually have same z-linspaces.
        This method bridges that by creating new x and y values for incumbents at depths
        corresponding to the proposed well.

        Args:
            i_reference (int): The proposed well depth index
            x_to_interpolate (list): 1x2
            y_to_interpolate (list): 1x2

        Returns:
            x_interp (float): The interpolated x-value
            y_interp (float): The interpolated y-value
        """

        # Interpolate x and y vals to match depths
        g = self.proposed_well[i_proposed - 1 : i_proposed + 1, -1]
        # print(x_to_interpolate)
        print(g)
        x_interp = interpolate(
            a=self.proposed_well[i_proposed - 1 : i_proposed + 1, -1],
            b=x_to_interpolate,
        )
        y_interp = interpolate(
            a=self.proposed_well[i_proposed - 1 : i_proposed + 1, -1],
            b=y_to_interpolate,
        )

        return x_interp, y_interp

    def calculate_distance(self, x_interp, y_interp, i_proposed):
        # Calculate distance
        distance = np.sqrt(
            (x_interp - self.proposed_well[i_proposed, 0]) ** 2
            + (y_interp - self.proposed_well[i_proposed, 1]) ** 2
        )

        return distance

    def run(self):
        distances = dict()
        for _, well in self.incumbent_wells.iterrows():
            well_distance_temp = []
            well_name = well["Borholunofn"]
            z_incumbent = np.linspace(
                settings["default_values"]["Z"],
                well["MaxFDypi"],
                len(self.proposed_well),
            )
            for i_proposed in range(1, len(self.proposed_well)):
                for k in range(1, len(z_incumbent) - 1):
                    if (
                        z_incumbent[k]
                        < self.proposed_well[i_proposed, 2]
                        < z_incumbent[k + 1]
                    ):
                        x_interp, y_interp = self.synthesize_values(
                            i_proposed=i_proposed,
                            x_to_interpolate=np.repeat(well["x"], 2),
                            y_to_interpolate=np.repeat(well["y"], 2),
                        )
                        well_distance_temp.append(
                            self.calculate_distance(x_interp, y_interp)
                        )
            distances[well_name] = well_distance_temp

        for well_name, linspace in distances.items():
            plt.plot(linspace)
            plt.show()

    def sort(self, n):
        """Sorts the well distances

        Args:


        Returns:
            (pd.DataFrame): A top n list
        """
        pass


def main():
    wells_filename = "data/wells.csv"
    incumbent_wells = pd.read_csv(wells_filename)
    traj_instance = trajectory.Trajectory3d()
    x, y, _, z, _ = traj_instance.fork_r()
    proposed_well = np.array((x, y, z)).T
    distance = Distance(incumbent_wells, proposed_well)
    distance.run()


if __name__ == "__main__":
    main()

