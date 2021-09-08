import os
import json
import scipy
import requests
from osgeo import gdal
import pandas as pd
import numpy as np

from bokeh.models import ColumnDataSource, LayoutDOM


class Preprocess:
    def __init__(self):
        # with open('iceland.json') as json_file:
        #     self.locations = json.load(json_file)
        pass

    def is_existant(self, dest_file):
        __is_exist = os.path.exists(dest_file)
        return __is_exist

    def download(self):
        """Downloads a raster map of Iceland"""

        dest_file = 'data/iceland.tif'
        if self.is_existant(dest_file):
            return

        folder = 'https://ftp.lmi.is/gisdata/raster/'
        url = f'{folder}IslandsDEMv1.0_50x50m_isn2016_daylight.tif'
        request = requests.get(url, stream=True)
        if request.status_code != 200:
            return

        with open(dest_file, 'wb') as f:
            for chunk in request.iter_content(1024):
                f.write(chunk)

    def clip(self, location, coordinates):
        """Clips the entire map into smaller, more manageble maps of each area"""

        location_file = f'data/{location}.tif'
        if self.is_existant(location_file):
            return

        ds = gdal.Open('data/iceland.tif')
        # projWin order of coords: ulx, uly, lrx, lry
        ds = gdal.Translate(location_file,
                            ds,
                            projWin=[coordinates["xmin"],
                                     coordinates["ymax"],
                                     coordinates["xmax"],
                                     coordinates["ymin"]])
        ds = None

    def tif_to_csv(self, location):
        """Converts geotiff to csv for plotting 3d mesh in bokeh"""

        ds = gdal.Open(f'data/{location}.tif')

        array = ds.GetRasterBand(1).ReadAsArray()
        flattened = array.flatten()
        geotransform = ds.GetGeoTransform()
        res = geotransform[1]
        x_min = geotransform[0]
        y_max = geotransform[3]
        x_size = ds.RasterXSize
        y_size = ds.RasterYSize
        x_start = x_min + res / 2
        y_start = y_max - res / 2
        ds = None

        x = np.arange(x_start, x_start + x_size * res, res)
        y = np.arange(y_start, y_start - y_size * res, -res)
        x = np.tile(x, y_size)
        y = np.repeat(y, x_size)

        dictionary = {'x': x,
                      'y': y,
                      'value': flattened}
        df = pd.DataFrame(dictionary)
        df.to_csv(f'data/{location}.csv')

    def process(self):

        with open('locations.json') as json_file:
            locations = json.load(json_file)

        for location, coordinates in locations.items():
            self.clip(location, coordinates)
            self.tif_to_csv(location)


class Elevation:
    def __init__(self):
        pass

    def elevation(self):
        with open('vis.ts') as tsFile:
            TS_CODE = tsFile.read()

        # This custom extension model will have a DOM view that should layout-able in
        # Bokeh layouts, so use ``LayoutDOM`` as the base class. If you wanted to create
        # a custom tool, you could inherit from ``Tool``, or from ``Glyph`` if you
        # wanted to create a custom glyph, etc.
        class Surface3d(LayoutDOM):

            # The special class attribute ``__implementation__`` should contain a string
            # of JavaScript code that implements the browser side of the extension model.
            __implementation__ = TypeScript(TS_CODE)

            # Below are all the "properties" for this model. Bokeh properties are
            # class attributes that define the fields (and their types) that can be
            # communicated automatically between Python and the browser. Properties
            # also support type validation. More information about properties in
            # can be found here:
            #
            #    https://docs.bokeh.org/en/latest/docs/reference/core/properties.html#bokeh-core-properties

            # This is a Bokeh ColumnDataSource that can be updated in the Bokeh
            # server by Python code
            data_source = Instance(ColumnDataSource)

            # The vis.js library that we are wrapping expects data for x, y, and z.
            # The data will actually be stored in the ColumnDataSource, but these
            # properties let us specify the *name* of the column that should be
            # used for each field.
            x = String
            y = String
            z = String

        df = pd.read_csv('data/Svartsengi.csv', index_col=0)
        df.replace(to_replace=-9999.0, value=0, inplace=True)
        x = df.x
        y = df.y
        z = df.value

        # Create a 2D grid
        mesh_resol = 100  # Increase/decrease for higher/lower resolution
        xi = np.linspace(min(x), max(x), mesh_resol)
        yi = np.linspace(min(y), max(y), mesh_resol)
        X, Y = np.meshgrid(xi, yi)
        # Interpolate to fit grid
        Z = scipy.interpolate.griddata(
            points=(x, y), values=z, xi=(X, Y), fill_value=0)

        # For testing
        # fig = plt.figure()
        # ax = Axes3D(fig)
        # ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.jet,linewidth=1, antialiased=True)
        # plt.show()

        self.source3D = ColumnDataSource(data=dict(x=X, y=Y, z=Z))
        self.elevation = Surface3d(
            x='x', y='y', z='z', data_source=self.source3D)


if __name__ == '__main__':
    elev = Preprocess()
    elev.download()
    elev.process()