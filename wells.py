import json
import pandas as pd
import matplotlib.pyplot as plt

from tests import TestPlots

class Wells:
    """Gets and processes the (open-source) coordinates of all wellheads in Reykjanes."""

    def __init__(self):
        with open('config.json') as f:
            self.settings = json.load(f)
    
    def download(self):
        """Downloads dataset from LMI.

        Returns:
            (pd.DataFrame): All wells in Iceland
        """        
        
        return pd.read_csv(self.settings["borholuskra"])
    
    def filter_area(self, all_wells_in_iceland: pd.DataFrame):
        """Filters the dataset of all wells in Iceland to the
        wells in Reykjanes geothermal area.

        Args:
            all_wells_in_iceland (pd.DataFrame): [description]

        Returns:
            (pd.DataFrame): All (currently available) wells
                            in Reykjanes geothermal area.
        """        

        return all_wells_in_iceland[all_wells_in_iceland['SVAEDISNAFN']=='Reykjanes']

    def process(self, rn_wells_raw: pd.DataFrame):
        """[summary]

        Args:
            rn_wells (pd.DataFrame): [description]

        Returns:
            [type]: [description]
        """        

        rn_wells = rn_wells_raw[['Borholunofn', 'x', 'y', 'MaxFDypi']]
        rn_wells = rn_wells.dropna()

        return rn_wells
    
    def extract_coordinates(self, rn_wells: pd.DataFrame):
        """Splits the Reykja

        Args:
            rn_wells (pd.DataFrame): [description]

        Returns:
            [type]: [description]
        """       
         
        x = rn_wells['x'].tolist()
        y = rn_wells['y'].tolist()
        z = rn_wells['MaxFDypi'].tolist()
        name = rn_wells['Borholunofn'].tolist()

        return x, y, z, name

def main():
    wells = Wells()
    all_wells_in_iceland = wells.download()
    rn_wells_raw = wells.filter_area(all_wells_in_iceland)
    rn_wells = wells.process(rn_wells_raw)
    x, y, z, name = wells.extract_coordinates(rn_wells)
    TestPlots.plot_well_heads(x, y, z, name)

if __name__ == '__main__':
    main()