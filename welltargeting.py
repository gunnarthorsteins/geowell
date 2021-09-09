


class WellTargeting:
    '''Interactive well targeting.

    Params:
        lon:            Well head horizontal coordinate
                            (either in WGS84 (GPS) or ISN93 (Iceland only))
        lat:            Well head vertical coordinate
                            (either in WGS84 (GPS) or ISN93 (Iceland only))
        mmd:            Measured depth (m or km)
        Z:              Well head altitude above sea level
        az:             Well trajectory (deg clockwise from north).
                            Default: 0
        kop:            Kick-off point. Default: 0
        dip:            Maximum well angle after build-up
                            (measured from vertical)
        casing_depth:   Casing depth (m or ratio of mmd)
        bu:             Build-up from kick-off (degs per 100 ft)

    '''

    def __init__(
        self,
        lon,
        lat,
        mmd,
        Z,
        az=0,
        kop=False,
        dip=20,
        cd=0,
        bu=2
    ):

        self.lon = lon
        self.lat = lat
        self.mmd = mmd
        self.Z = Z
        self.az = az
        self.kop = kop
        self.dip = dip
        self.cd = cd
        self.bu = bu / 30

    # TODO: Why did I do this?
    def __enter__(self):
        return self

    # TODO: Why did I do this?
    def __exit__(self, exc_type, exc_val, tb):
        pass


if __name__ == '__main__':
    with open('defaults.json') as json_file:
        def_val = json.load(json_file)

    run = WellTargeting(
        lon=def_val["lon"],
        lat=def_val["lat"],
        mmd=def_val["mmd"],
        Z=def_val["Z"],
        az=def_val["az"],
        cd=def_val["cd"],
        kop=def_val["kop"],
        bu=def_val["bu"],
    )

    run.trajectory_2d()
    run.plot_2d()
    run.elevation()
    run.widgets()
    # run.trajectory_3d()
    run.present()
