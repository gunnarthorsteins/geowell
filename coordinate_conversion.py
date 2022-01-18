import math

import json
import numpy as np
from scipy.optimize import fsolve


class Conversion:
    """Converts between WGS84 and ISN93.
    
    Provides a framework for converting coordinates between
    WGS84 and ISN93, the latter being the standard georeference
    system for industry in Iceland.

    Equations adapted from Kristjan Mikaelsson's JS-code:
    https://bit.ly/32rqbFE

    Example:
        conversion_ = Conversion()
        lon, lat = -22.69113, 63.82388
        x, y = conversion_.wgs_to_isn(lon, lat)
    """

    def __init__(self):
        with open("config.json") as f:
            settings = json.load(f)

        constants = settings["wgs_isn_conversion_constants"]
        self.A = constants["A"]
        self.B = constants["B"]
        self.C = constants["C"]
        self.E = constants["E"]
        self.F = constants["F"]
        self.G = constants["G"]
        self.H = constants["H"]
        self.J = constants["J"]
        self.K = constants["K"]

    def wgs_to_isn(self, lon: float, lat: float):
        """Converts WGS84 value pairs (the familiar lon and lat) to ISN93.

        No use in trying to prettify the equation
        it is truly an eyesore. See it here in a cleaner format:
        https://i.imgur.com/UH42pDb.png

        Args:
            lon: longitude
            lat: latitude
        
        Returns:
            x (float): horizontal ISN93 coordinate
            y (float): vertical ISN93 coordinate
        """

        k = lat * self.A
        p = self.F * np.sin(k)
        o = self.B * math.pow(
            math.tan(self.C - (k / 2)) / math.pow((1 - p) / (1 + p), self.E), self.G
        )
        q = (lon + 19) * self.H
        x = self.K + o * np.sin(q)
        y = self.J - o * np.cos(q)

        return round(x, 1), round(y, 1)

    def isn_to_wgs(self, x: float, y: float):
        """Converts ISN93 value pairs to WGS84 (the familiar lat & lon).
        
        No use in trying to prettify the equation
        it is truly an eyesore. See it here in a cleaner format:
        https://i.imgur.com/UH42pDb.png

        Args:
            x: horizontal ISN93 coordinate
            y: vertical ISN93 coordinate
        
        Returns:
            lon (float): WGS84 longitude
            lat (float): WGS84 latitude
        """

        DECIMALS = 5

        def _f(k):
            """The empirical equation for latitude.

            Is solved numerically.
            Note that it's written here as f(k)=0

            Args:
                k ([type]): The variable to optimize

            Returns:
                [type]: [description]
            """            
            return (
                (1.0 + self.F * np.sin(k))
                * (np.tan(self.C - 0.5 * k)) ** (1.0 / self.E)
                / (
                    (1.0 - self.F * np.sin(k))
                    * (p / self.B) ** (1.0 / (self.E * self.G))
                )
                - 1
            )

        q = np.arctan((x - 5 * 10 ** 5) / (self.J - y))
        p = (x - 5 * 10 ** 5) / (np.sin(q))

        r = float(fsolve(_f, 1.0))

        lon = q / self.H - 19
        lat = r / self.A

        return round(lon, DECIMALS), round(lat, DECIMALS)