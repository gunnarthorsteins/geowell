import os
import json
from scipy.interpolate import griddata
import requests
from osgeo import gdal
import pandas as pd
import numpy as np

from tests import TestPlots

class Download:
    """Downloads a map of Iceland and preprocesses."""

    def __init__(self, overwrite=False):
        self.overwrite = overwrite
        if self.overwrite:
            self._download()
            self._warp()

    def _download(self, resolution=20):
        """Downloads a raster map of Iceland from
        The National Land Survey of Iceland.

        Args:
            resolution (int): elevation resolution [m].
                              Can be 10, 20 (default) or 50.
        """

        file = 'data/iceland.tif'
        url_folder = 'https://ftp.lmi.is/gisdata/raster/'
        url = f'{url_folder}IslandsDEMv1.0_{resolution}x{resolution}m_isn2016_zmasl.tif'
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
            print('Warping...')
            warp = gdal.Warp(raster,
                             ds,
                             dstSRS='EPSG:3057')
            print('Warping finished')
        ds = None


class Process:
    """Collects and prepares elevation raster data for plotting"""

    def __init__(self, location, coordinates, overwrite=False):
        """
        Args:
            location (str): Location name, see config
            coordinates (dict): Location bounding box, see config
            overwrite (bool, optional): Whether to overwrite existing surface
                                        data or not. Defaults to False.
        """

        self.overwrite = overwrite
        self.location = location
        self.coordinates = coordinates

    def clip(self):
        """Clips the original map into smaller, more manageble pieces.

        Args:
            location (str): The location name
            coordinates (dict): Two sets of coordinates: ulx, uly,
                                                         lrx, lry
        """

        file = f'data/{self.location}.tif'

        ds = gdal.Open('data/iceland.tif')
        ds = gdal.Translate(file,
                            ds,
                            projWin=[self.coordinates["ulx"],
                                     self.coordinates["uly"],
                                     self.coordinates["lrx"],
                                     self.coordinates["lry"]])
        ds = None

    def detiffify(self):
        """Converts geotiff to df.

        Args:
            location (str): The location name
        """

        file_loc = f'data/{self.location}'
        ds = gdal.Open(f'{file_loc}.tif')
        xyz = gdal.Translate(f'{file_loc}.xyz', ds)
        xyz = None
        ds = None

        df = pd.read_csv(f'{file_loc}.xyz',
                         sep=' ',
                         names=['x', 'y', 'z'],
                         header=0)
        os.remove(f'{file_loc}.xyz')
        to_replace = -3.402823466385289e+38  # don't know why...
        df.replace(to_replace, 0, inplace=True)
        self.df = round(df)

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
        x_mesh, y_mesh = np.meshgrid(xi, yi)
        # Interpolate to fit grid
        z_mesh = griddata(points=(self.df.x, self.df.y),
                          values=self.df.z,
                          xi=(x_mesh, y_mesh),
                          fill_value=0)
        dict_ = dict(x=x_mesh.tolist(),
                     y=y_mesh.tolist(),
                     z=z_mesh.tolist())

        with open(f'data/{self.location}.json', 'w') as f:
            json.dump(dict_, f)

    def run(self):
        """Runs elevation data preprocessing."""

        self.clip()
        self.detiffify()
        self.mesh()

def main():
    download = Download(overwrite=True)
    for location, coordinates in locations.items():
        process = Process(location, coordinates)
        process.run()
        break  # Only want Reykjanes

if __name__ == '__main__':
    with open('config.json') as f:
        settings = json.load(f)
    locations = settings["locations_bbox"]

    # main()

    # For testing
    with open(f'data/Reykjanes.json') as f:
        elevation_data = json.load(f)        
    TestPlots.plot_elevation_map(elevation_data)
