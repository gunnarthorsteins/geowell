import json
import pandas as pd
import matplotlib.pyplot as plt

from tests import UnitTests

with open("config.json") as f:
    settings = json.load(f)
locations = settings["locations_bbox"]


class OpenSourceWells:
    """Gets, processes, and saves the (open-source) coordinates of all wellheads in Reykjanes."""

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
            all_wells_in_iceland (pd.DataFrame): [description]

        Returns:
            (pd.DataFrame): All (currently available) wells
                            in Reykjanes geothermal area.
        """

        return all_wells_in_iceland[all_wells_in_iceland["SVAEDISNAFN"] == "Reykjanes"]

    def process(self, wells_raw: pd.DataFrame):
        """Filters out unwanted columns and drops NaN values.

        Args:
            wells (pd.DataFrame): [description]

        Returns:
            (pd.DataFrame): A filtered version of the 
        """

        wells = wells_raw[["Borholunofn", "x", "y", "MaxFDypi"]]
        wells = wells.dropna()

        return wells

    def save(self, wells: pd.DataFrame):
        wells.to_csv(settings["wells_filename"], index=False)


def main():
    wells_instance = OpenSourceWells()
    all_wells_in_iceland = wells_instance.download()
    wells_raw = wells_instance.filter_area(all_wells_in_iceland)
    wells_df = wells_instance.process(wells_raw)
    wells_instance.save(wells_df)


if __name__ == "__main__":
    # main()
    UnitTests.test_wells(settings["wells_filename"])
