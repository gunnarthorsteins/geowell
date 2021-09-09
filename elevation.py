import os
import json
from scipy.interpolate import griddata
import requests
from osgeo import gdal
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm


class Download:
    """Downloads a map of Iceland and preprocesses."""

    def __init__(self, overwrite=False):
        self.overwrite = overwrite
        if not self.overwrite:
            self._download()
            self._wrap()

    def _download(self, resolution=20):
        """Downloads a raster map of Iceland from
        The National Land Survey of Iceland.

        Args:
            resolution (int): elevation resolution [m].
                                Can be 10, 20 (default) or 50
        """

        file = 'data/iceland.tif'
        url_folder = 'https://ftp.lmi.is/gisdata/raster/'
        url = f'{url_folder}IslandsDEMv1.0_{resolution}x{resolution}m_isn2016_daylight.tif'
        request = requests.get(url, stream=True)
        if request.status_code != 200:
            return

        with open(file, 'wb') as f:
            for chunk in request.iter_content(1024):
                f.write(chunk)

    def _warp(self):
        """Warps the original file from
        ESPG:8088 (ISN2016) to ESPG:3057 (ISN93).
        """

        raster = 'data/iceland.tif'
        ds = gdal.Open(raster)
        projection = ds.GetProjection()
        if projection.find('ISN93') == -1:
            warp = gdal.Warp(raster,
                             ds,
                             dstSRS='EPSG:3057')
        ds = None


class Process:
    """Collects and prepares elevation raster data for plotting"""

    def __init__(self, location, coordinates, overwrite=False):
        """
        Args:
            overwrite (bool, optional): Whether to overwrite existing surface
                                        data or not. Defaults to False.
        """

        self.overwrite = overwrite
        self.location = location
        self.coordinates = coordinates
        print(self.location)

    def clip(self):
        """Clips the original map into smaller, more manageble pieces.

        Args:
            location (str): The location name
            coordinates (dict): Two sets of coordinates: ulx, uly,
                                                         lrx, lry
        """

        file = f'data/{self.location}.tif'
        if os.path.exists(file):
            return

        ds = gdal.Open('data/iceland.tif')
        ds = gdal.Translate(file,
                            ds,
                            projWin=[self.coordinates["ulx"],
                                     self.coordinates["uly"],
                                     self.coordinates["lrx"],
                                     self.coordinates["lry"]])
        ds = None

    def detiffify(self):
        """Converts geotiff to csv.

        Args:
            location (str): The location name
        """

        ds = gdal.Open(f'data/{self.location}.tif')

        geotransform = ds.GetGeoTransform()
        res = round(geotransform[1])
        x_min = geotransform[0]
        y_max = geotransform[3]
        x_size = ds.RasterXSize
        y_size = ds.RasterYSize
        x_start = x_min + res / 2
        y_start = y_max - res / 2

        x = np.arange(x_start, x_start + x_size * res, res)
        y = np.arange(y_start, y_start - y_size * res, -res)
        x = np.tile(x, y_size)
        y = np.repeat(y, x_size)

        array = ds.GetRasterBand(1).ReadAsArray()
        ds = None
        dictionary = {'x': x,
                      'y': y,
                      'value': array.flatten()}
        self.df = pd.DataFrame(dictionary)

    def mesh(self):
        """Generates a 3D mesh of elevation data."""

        # Create a 2D mesh grid
        mesh_resol = 100  # Increase/decrease for higher/lower resolution
        xi = np.linspace(min(self.df.x),
                         max(self.df.x),
                         mesh_resol)
        yi = np.linspace(min(self.df.y),
                         max(self.df.y),
                         mesh_resol)
        self.X, self.Y = np.meshgrid(xi, yi)
        # Interpolate to fit grid
        self.Z = griddata(points=(self.df.x, self.df.y),
                          values=self.df.value,
                          xi=(self.X, self.Y),
                          fill_value=0)

        dict_ = dict(x=self.X,
                     y=self.Y,
                     z=self.Z)
        
        with open(f'data/{self.location}.json', 'w') as f:
            json.dump(dict_, f)

    def i_dont_know_how_to_write_a_test(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(self.X,
                        self.Y,
                        self.Z,
                        rstride=1,
                        cstride=1,
                        cmap=matplotlib.cm.jet,
                        linewidth=1,
                        antialiased=True)
        fig.show()

    def test(self):
        """Runs elevation data preprocessing."""

        self.clip()
        self.detiffify()
        self.mesh()
        self.i_dont_know_how_to_write_a_test()
        # self.javascript()


if __name__ == '__main__':
    # download = Download(overwrite=False)

    with open('data/locations.json') as f:
        locations = json.load(f)

    for location, coordinates in locations.items():

        process = Process(location, coordinates)
        process.test()
