import os
import json
from scipy.interpolate import griddata
import requests
from osgeo import gdal
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm
from mpl_toolkits.mplot3d import Axes3D

from bokeh.models import ColumnDataSource, LayoutDOM
from bokeh.core.properties import Instance, String
from bokeh.models import ColumnDataSource, LayoutDOM
from bokeh.util.compiler import TypeScript
from bokeh.plotting import figure, show


class Preprocess:
    def __init__(self, overwrite=False):
        self.overwrite = overwrite

        with open('locations.json') as json_file:
            self.locations = json.load(json_file)

    def download(self, resolution=20):
        """Downloads a raster map of Iceland from The National Land Survey of Iceland

        Args:
            resolution (int): elevation resolution [m]. Can be either 10, 20 (default) or 50
        """

        file = 'data/iceland.tif'
        if os.path.exists(file) or not self.overwrite:
            return

        folder = 'https://ftp.lmi.is/gisdata/raster/'
        url = f'{folder}IslandsDEMv1.0_{resolution}x{resolution}m_isn2016_daylight.tif'
        request = requests.get(url, stream=True)
        if request.status_code != 200:
            return

        with open(file, 'wb') as f:
            for chunk in request.iter_content(1024):
                f.write(chunk)

    def warp(self):
        """Warps the original file from ESPG:8088 (ISN2016) to ESPG:3057 (ISN93)"""

        raster = 'data/iceland.tif'
        ds = gdal.Open(raster)
        projection = ds.GetProjection()
        if projection.find('ISN93') == -1:
            warp = gdal.Warp(raster, ds, dstSRS='EPSG:3057')
        ds = None

    def clip(self, location, coordinates):
        """Clips the entire map into smaller, more manageble maps of each area

        Args:
            location (str): The location name
            coordinates (dict): Two sets of coordinates, ulx, uly, lrx, lry
        """

        file = f'data/{location}.tif'
        if os.path.exists(file):
            return

        ds = gdal.Open('data/iceland.tif')
        ds = gdal.Translate(file,
                            ds,
                            projWin=[coordinates["ulx"],
                                     coordinates["uly"],
                                     coordinates["lrx"],
                                     coordinates["lry"]])
        ds = None

    def tif_to_csv(self, location):
        """Converts geotiff to csv for plotting 3d mesh in bokeh

        Args:
            location (str): The location name
        """
        file = f'data/{location}.csv'
        if os.path.exists(file):
            return

        ds = gdal.Open(f'data/{location}.tif')
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
        df = pd.DataFrame(dictionary)
        df = df.round()
        df.to_csv(f'data/{location}.csv', index=False)

    def run(self):
        """Runs elevation data preprocessing."""

        if not os.path.exists('data/'):
            self.download()
            self.warp()

        for location, coordinates in self.locations.items():
            self.clip(location, coordinates)
            self.tif_to_csv(location)


class Surface:
    def __init__(self):
        pass

    def mesh(self, location):

        df = pd.read_csv(f'data/{location}.csv')

        # Create a 2D mesh grid
        mesh_resol = 100  # Increase/decrease for higher/lower resolution
        xi = np.linspace(min(df.x), max(df.x), mesh_resol)
        yi = np.linspace(min(df.y), max(df.y), mesh_resol)
        self.X, self.Y = np.meshgrid(xi, yi)
        # Interpolate to fit grid
        self.Z = griddata(
            points=(df.x, df.y), values=df.value, xi=(self.X, self.Y), fill_value=0)
        self.source3D = ColumnDataSource(
            data=dict(x=self.X, y=self.Y, z=self.Z))

    def test(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(self.X, self.Y, self.Z, rstride=1, cstride=1,
                        cmap=matplotlib.cm.jet, linewidth=1, antialiased=True)
        fig.show()

    def javascript(self):
        class Surface3d(LayoutDOM):
            with open('vis.ts') as tsFile:
                TS_CODE = tsFile.read()
            __implementation__ = TypeScript(TS_CODE)
            data_source = Instance(ColumnDataSource)

            # The vis.js library that we are wrapping expects data for x, y, and z.
            # The data will actually be stored in the ColumnDataSource, but these
            # properties let us specify the *name* of the column that should be
            # used for each field.
            x = String
            y = String
            z = String

        surface = Surface3d(
            x='x', y='y', z='z', data_source=self.source3D)
        show(surface)  # saves the figure as elevation.html

    def run(self):
        location = 'Svartsengi'
        self.mesh(location)
        self.javascript()


if __name__ == '__main__':
    preprocessing = Preprocess(overwrite=False)
    preprocessing.run()
    surface = Surface()
    surface.run()
