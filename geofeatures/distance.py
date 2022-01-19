import json
import numpy as np


with open("config.json") as f:
    settings = json.load(f)


def interpolate(a: list, b: list):
    """General linear table interpolation.

    Args:
        a (list): Shape 1x3 
        b (list): Shape 1x2. Interpolating for the value between b[0] and b[1]
    
    Returns:
        interpolated value
    """
    return b[0] + (b[1] - b[0]) * (a[1] - a[0]) / (a[2] - a[0])


def generate_zs_for_incumbent_vertical_wells(well_depth, len_of_proposed_well):
    return np.linspace(
        settings["default_values"]["Z"], well_depth, len_of_proposed_well
    )


# TODO: Change incumbent wells from vertical (open-source) to closed-source
# TODO: Visualize casing of incumbents in distance plotting
class Distance:
    """Calculates distance of proposed well to nearest incumbent wells.

    Incumbent wells and proposed well don't usually have same z-linspaces.
    This solves that by creating new x and y values for incumbents
    at depths corresponding to the proposed well to be able to calculate
    the horizontal distance between wells.
    
    Attributes:
        incumbent_wells: A dict of 3D coordinates of all incumbent wells.
            The format is well name as key, with x, y, and z coordinates
            as nested keys
        proposed_well: An array of the 3D coordinates of the proposed well
    """

    def __init__(self, incumbent_wells, proposed_well):
        self.incumbent_wells = incumbent_wells
        self.proposed_well = proposed_well

    def _synthesize_values(self, index_proposed: int, value_to_interpolate: list):
        """Creates X & Y values at equal depths for proposed and incumbent wells.

        Args:
            i_reference (int): The proposed well depth index
            value_to_interpolate (list): 1x2

        Returns:
            interpolated_value (float): The interpolated value
        """

        interpolated_value = interpolate(
            a=self.proposed_well[index_proposed - 1 : index_proposed + 2, -1],
            b=value_to_interpolate,
        )

        return interpolated_value

    def _calculate_distance(
        self, x_interp: float, y_interp: float, index_proposed: int
    ):
        """Calculates the distance between two points on a 2D surface.

        Calculates the L2-distance between two pairs of coordinates,
        the one being of an incumbent well and the other for the proposed
        well. The depths should be equal.

        Args:
            x_interp (float): The incumbent well's (synthesized) x-coordinate
                at a depth corresponding to the prosed well's depth.
            y_interp (float): The incumbent well's (synthesized) y-coordinate
                at a depth corresponding to the prosed well's depth.
            index_proposed (int): Index at the depth of the proposed well

        Returns:
            distance (float): The L-2 distance between the two points.
        """

        distance = np.sqrt(
            (x_interp - self.proposed_well[index_proposed, 0]) ** 2
            + (y_interp - self.proposed_well[index_proposed, 1]) ** 2
        )

        return distance

    def run(self):
        """High-level method for calculating distance between wells.

        Returns:
            distances (dict): Each key-value pair contains the distance
                between an incumbent well (identified by key) and the
                proposed well at every z-step of the proposed well

        NOTE: To modify when proper well coordinates are received.                
        """

        len_of_proposed_well = len(self.proposed_well)
        distances = dict()
        for _, well in self.incumbent_wells.iterrows():
            well_distance_temp = []
            z_incumbent = generate_zs_for_incumbent_vertical_wells(
                well_depth=well["MaxFDypi"], len_of_proposed_well=len_of_proposed_well
            )
            for index_proposed in range(1, len(self.proposed_well) - 1):
                for k in range(1, len(z_incumbent) - 1):
                    if (
                        z_incumbent[k]
                        < self.proposed_well[index_proposed, 2]
                        < z_incumbent[k + 1]
                    ):
                        x_interp = self._synthesize_values(
                            index_proposed=index_proposed,
                            value_to_interpolate=np.repeat(well["x"], 2),
                        )
                        y_interp = self._synthesize_values(
                            index_proposed=index_proposed,
                            value_to_interpolate=np.repeat(well["y"], 2),
                        )
                        well_distance_temp.append(
                            self._calculate_distance(x_interp, y_interp, index_proposed)
                        )
            if well_distance_temp:
                well_name = well["Borholunofn"]
                distances[well_name] = well_distance_temp

        return distances

