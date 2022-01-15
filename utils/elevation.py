import json
import os
import requests

from osgeo import gdal
import numpy as np
import pandas as pd
from scipy.interpolate import griddata


with open("config.json") as f:
    settings = json.load(f)
locations = settings["locations_bbox"]
RESOLUTION = settings["ELEVATION_RESOLUTION"]


url_prefix = "https://ftp.lmi.is/gisdata/raster/"
url = f"{url_prefix}IslandsDEMv1.0_{RESOLUTION}x{RESOLUTION}m_isn2016_zmasl.tif"


class Download:
    """Downloads and preprocesses an elevation map of Iceland."""

    def __init__(self, overwrite=False):
        self.filename = "data/iceland.tif"
        if overwrite:
            self._download()
            self._warp()

    def _download(self):
        """Downloads a raster map of Iceland.
        
        The map is from Landmælingar Íslands.
        The elevation resolution is set in config.json
        """

        request = requests.get(url, stream=True)
        if request.status_code != 200:
            return

        with open(self.filename, "wb") as f:
            for chunk in request.iter_content(1024):
                f.write(chunk)

    def _warp(self):
        """Warps the original file.
        
        Warps from ESPG:8088 (ISN2016) to ESPG:3057 (ISN93).
        """

        ds = gdal.Open(self.filename)
        projection = ds.GetProjection()
        if projection.find("ISN93") == -1:
            print("Warping...")
            warp = gdal.Warp(self.filename, ds, dstSRS="EPSG:3057")
            print("Warping finished")
        ds = None


class Process:
    """Collects and prepares elevation raster data for plotting.
    
    Attributes:
        location (str): Location name, see config.json
        coordinates (dict): Location bounding box, see config.json
        overwrite (bool, optional): Whether to overwrite existing surface
            data or not. Defaults to False.
    """

    def __init__(self, location, coordinates, overwrite=False):
        self.overwrite = overwrite
        self.location = location
        self.coordinates = coordinates

    def clip(self):
        """Clips the original map into smaller, more manageble pieces.

        Does so by zooming in to the bbox, see config.json
        """

        old_map = f"data/IslandsDEMv0_{RESOLUTION}x{RESOLUTION}m_zmasl_isn93.tif"
        new_map = f"data/{self.location}.tif"

        ds = gdal.Open(old_map)
        ds = gdal.Translate(
            new_map,
            ds,
            projWin=[
                self.coordinates["ulx"],
                self.coordinates["uly"],
                self.coordinates["lrx"],
                self.coordinates["lry"],
            ],
        )
        ds = None

    def detiffify(self):
        """Converts geotiff to df.

        Geotiffs are a little too cumbersome for this usage case.

        Returns:
            (pd.DataFrame): A dataframe of the elevation data
        """

        file_loc = f"data/{self.location}"
        ds = gdal.Open(f"{file_loc}.tif")
        xyz = gdal.Translate(f"{file_loc}.xyz", ds)
        xyz = None
        ds = None

        df = pd.read_csv(f"{file_loc}.xyz", sep=" ", names=["x", "y", "z"], header=0)
        os.remove(f"{file_loc}.xyz")
        to_replace = [-3.402823466385289e38, -9999.0]  # don't know why...
        df.replace(to_replace, 0, inplace=True)

        return df

    def mesh(self, df: pd.DataFrame):
        """Generates a 3D mesh of elevation data.
        
        Args:
            df: The elevation data in table format

        Returns:
            dict_: The elevation data as a mesh
        """

        # Create a 2D mesh grid
        xi = np.linspace(min(df.x), max(df.x), settings["MESH_RESOLUTION"])
        yi = np.linspace(min(df.y), max(df.y), settings["MESH_RESOLUTION"])
        x_mesh, y_mesh = np.meshgrid(xi, yi)
        # Interpolate to fit grid
        z_mesh = griddata(
            points=(df.x, df.y), values=df.z, xi=(x_mesh, y_mesh), fill_value=0
        )
        dict_ = dict(x=x_mesh.tolist(), y=y_mesh.tolist(), z=z_mesh.tolist())

        return dict_

    def save(self, dict_):
        with open(f"data/{self.location}.json", "w") as f:
            json.dump(dict_, f)

    def run(self):
        """High-level method for elevation data preprocessing."""

        self.clip()
        df = self.detiffify()
        dict_ = self.mesh(df)
        self.save(dict_)
