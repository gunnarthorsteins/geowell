import math
import json
import numpy as np
import pandas as pd
from scipy.optimize import fsolve


class Conversion:
    """Provides a framework for converting coordinates between
    ISN93 and WGS84, the former being the standard georeference
    system for industry in Iceland.

    Params:
        new_ref_system (str): The destination coordinate system,
                              either 'isn' or 'wgs'
        folder (str): File folder absolute path
        file (str): The file name, including file ending

    Usage:
        conversion = Conversion('isn',
                                'C:/Users/',
                                'Earthquakes.csv')
        conversion.read_file()
        conversion.converter()
        conversion.write_csv()

    Note:
        Equations adapted from Kristjan Mikaelsson's JS-code:
        https://bit.ly/32rqbFE
    """

    def __init__(self):
        with open("constants.json") as f:
            c = json.load(f)

        # Empirical coefficients
        self.A = c["A"]
        self.B = c["B"]
        self.C = c["C"]
        self.E = c["D"]
        self.F = c["F"]
        self.G = c["G"]
        self.H = c["H"]
        self.J = c["J"]
        self.K = c["K"]

    def read_file(self):
        # NOTE This method needs to be adapted for different
        # column structures. No use in making it too general.
        # just make sure the i and j values are converted to numpy
        self.df = pd.read_csv(f"{self.folder}/{self.file}")

    def wgs_to_isn(self):
        """Converts WGS84 value pairs (the familiar lon and lat) to ISN93.

        Note:
            No use in trying to prettify the equation
            in the code, it is truly an eyesore. See it here
            in a cleaner format: https://i.imgur.com/UH42pDb.png
        """

        lon = self.df.lon.to_numpy()
        lat = self.df.lat.to_numpy()

        x = []
        y = []
        for i, val in enumerate(lon):
            k = lat[i] * self.A
            p = self.F * np.sin(k)
            o = self.B * math.pow(
                math.tan(self.C - (k / 2)) / math.pow((1 - p) / (1 + p), self.E), self.G
            )
            q = (val + 19) * self.H
            x.append(round((self.K + o * np.sin(q)) * 1000) / 1000)
            y.append(round((self.J - o * np.cos(q)) * 1000) / 1000)

        self.df.lon = x
        self.df.lat = y
        self.df.rename(columns={"lon": "x", "lat": "y"}, inplace=True)
        print(self.df.head())

    def isn_to_wgs(self):
        """Converts ISN93 value pairs to WGS84 (the familiar lat & lon)."""

        x = self.df.x.to_numpy()
        y = self.df.y.to_numpy()
        # The empirical equation for latitude.
        # Note that it's written here as f(k)=0

        def f(k):
            return (
                (1.0 + self.F * np.sin(k))
                * (np.tan(self.C - 0.5 * k)) ** (1.0 / self.E)
                / (
                    (1.0 - self.F * np.sin(k))
                    * (p / self.B) ** (1.0 / (self.E * self.G))
                )
                - 1
            )

        lon = []
        lat = []
        for i, val in enumerate(x):
            q = np.arctan((val - 5 * 10 ** 5) / (self.J - y[i]))
            p = (val - 5 * 10 ** 5) / (np.sin(q))

            # We solve the equation numerically with an initial guess of
            # f=1.0 [is safe for the range of values encountered here]
            r = float(fsolve(f, 1.0))

            lon.append(round(q / self.H - 19, 5))
            lat.append(round(r / self.A, 5))

        self.df.x = lon
        self.df.y = lat
        self.df.rename(columns={"x": "lon", "y": "lat"}, inplace=True)

    def converter(self):
        """Performs the actual conversion."""

        if self.new_ref_system == "isn":
            self.wgs_to_isn()
        elif self.new_ref_system == "wgs":
            self.isn_to_wgs()

    def write_csv(self):
        """"Writes dataframe to csv."""

        file = self.file.split(".")[0]
        self.df.to_csv(f"{self.folder}{file}_converted.csv")

    def write_xlsx(self, x, y):
        pass


if __name__ == "__main__":
    conversion = Conversion("wgs", "C:/Users/", "Earthquakes.csv")
    conversion.read_file()
    conversion.converter()
    # conversion.write_csv()
