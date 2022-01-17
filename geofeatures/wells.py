import json
import pandas as pd

with open("config.json") as f:
    settings = json.load(f)
locations = settings["locations_bbox"]


class OpenSourceWells:
    """Downloads, processes, and saves the (open-source)
    coordinates of all wellheads in Reykjanes.
    """

    def download(self):
        """Downloads dataset from LMÍ.

        Returns:
            (pd.DataFrame): All wells in Iceland
        """

        return pd.read_csv(settings["borholuskra"])

    def filter_area(self, all_wells_in_iceland: pd.DataFrame):
        """Filters the dataset of all wells in Iceland to the
        wells in desired geothermal area.

        Args:
            all_wells_in_iceland (pd.DataFrame): All wells in Iceland.

        Returns:
            (pd.DataFrame): All (currently available) wells
                            in settings["geothermal_area"]
        """

        is_well_in_area = (
            all_wells_in_iceland["SVAEDISNAFN"] == settings["geothermal_area"]
        )

        return all_wells_in_iceland[is_well_in_area]

    def process(self, wells_raw: pd.DataFrame):
        """Filters out unwanted columns and drops NaN values.

        Args:
            wells (pd.DataFrame): All (currently available) wells
                                  in settings["geothermal_area"]

        Returns:
            (pd.DataFrame): A filtered version of wells
        """

        wells = wells_raw[["Borholunofn", "x", "y", "MaxFDypi"]]
        wells = wells.dropna()

        return wells

    def save(self, wells: pd.DataFrame):
        wells.to_csv(settings["wells_filename"], index=False)