import os
import sys
import unittest

# To import from other parent directory in repo
pwd = os.getcwd()
sys.path.insert(0, pwd)

from coordinate_conversion import Conversion

# Hnit til prófunar í báðum hnitakerfum úr borholugrunni OS
# Þessi tilteknu eru holutoppshnit RN-27:
# https://orkustofnun.is/borholuleit/nr/18927/?iframed
x_verification = 318_331.6
y_verification = 374_188.5
lon_verification = -22.69113
lat_verification = 63.82388


class TestCoordinateConversion(unittest.TestCase):
    def test_wgs_to_isn(self):
        conversion_ = Conversion()
        x_test, y_test = conversion_.wgs_to_isn(lon_verification, lat_verification)
        self.assertAlmostEqual(x_test, x_verification, places=0)
        self.assertAlmostEqual(y_test, y_verification, places=0)

    def test_isn_to_wgs(self):
        conversion_ = Conversion()
        lon_test, lat_test = conversion_.isn_to_wgs(x_verification, y_verification)
        self.assertAlmostEqual(lon_test, lon_verification)
        self.assertAlmostEqual(lat_test, lat_verification)


if __name__ == "__main__":
    unittest.main()
