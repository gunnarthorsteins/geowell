from geofeatures import elevation
from geofeatures import wells

elevation.Download()
p = elevation.Process()
p.run()

wells_instance = wells.OpenSourceWells()
all_wells_in_iceland = wells_instance.download()
wells_raw = wells_instance.filter_area(all_wells_in_iceland)
wells_df = wells_instance.process(wells_raw)
wells_instance.save(wells_df)