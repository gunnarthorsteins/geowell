import json
import warnings
import numpy as np
import pandas as pd
from matplotlib import cm
from scipy.interpolate import griddata

from bokeh.plotting import figure, show
from bokeh.layouts import gridplot, column
from bokeh.core.properties import Instance, String
from bokeh.models import ColumnDataSource, LayoutDOM
from bokeh.models import CustomJS, Select, Slider
from bokeh.util.compiler import TypeScript

import plotting


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

    # TODO: Are these static methods the best way to do things?
    @staticmethod
    def cosd(deg):
        return np.cos(np.deg2rad(deg))

    # TODO: Are these static methods the best way to do things?
    @staticmethod
    def sind(deg):
        return np.sin(np.deg2rad(deg))

    # TODO: Are these static methods the best way to do things?
    @staticmethod
    def tand(deg):
        return np.tan(np.deg2rad(deg))

    # TODO: Are these static methods the best way to do things?
    @staticmethod
    def split_curve(self):        # Determine casing TVD to split curve
        """Splits the curve above/below casing for plot coloring"""

        if self.cd <= self.kop:
            self.split = sum(self.z < (self.cd - self.Z))
        elif self.kop < self.cd < len_2[-1]:
            self.split = 50 + sum(len_2 < (self.cd - self.Z))
        elif len_2[-1] < self.cd:
            self.split = 50 + len(z2) + sum(len_3 < (self.cd - self.Z))
        else:
            warnings.warn('Check casing block')

    def trajectory_2d(self):
        '''Three legs:
        1) Down to KOP
        2) Build-up
        3) Last leg to well bottom (straight)
        '''

        def first_leg():
            """Creates a vertical well segment"""

            z = np.linspace(-self.Z, self.kop - self.Z)
            r = np.zeros_like(z)

            return r, z

        # Vertical
        if not self.kop:
            self.r, self.z = first_leg()

            return

        # Directional
        # First leg
        r1, z1 = first_leg()

        # Second leg - The curved segment
        r2 = np.zeros(self.dip - 1)
        z2 = r2
        len_2 = r2
        z2[0] = z1[-1]
        len_2[0] = z1[-1]
        for i in range(1, self.dip - 1):
            r2[i] = r2[i-1] + self.sind(i) / self.bu
            z2[i] = z2[i-1] + self.cosd(i) / self.bu
            len_2[i] = len_2[i-1] + 1 / self.bu

        # Third leg - The last one
        L2 = self.mmd - self.kop - self.dip / self.bu
        r3 = np.linspace(
            r2[-1], L2 * self.sind(self.dip)
        )
        vert = z2[-1] + np.linspace(0, L2 * self.cosd(self.dip))
        p = np.polyfit(r3, vert, 1)
        z3 = np.polyval(p, r3)
        len_3 = z3 / self.cosd(self.dip)

        self.r = np.concatenate((r1, r2, r3))
        self.z = np.concatenate((z1, z2, z3))

    def trajectory_3d(self):

        def delta(r):

            delta_y = self.r / np.sqrt(self.tand(self.az)**2 + 1)
            delta_x = delta_y * self.tand(self.az)

            return delta_x, delta_y

        x = self.lon + np.zeros(len(self.r))
        y = self.lat + np.zeros(len(self.r))
        m_to_deg = 1.11e5  # m to deg on Earth's surface

        for i, r in enumerate(self.r):
            # Accounting for special cases -> tand(az) = inf
            if self.az == 90 or self.az == 270:
                delta_y = 0
                delta_x = self.r[-1]
            else:
                delta_x, delta_y = delta(self.r)

            delta_y /= m_to_deg
            # m to deg is lat dependent for lon
            delta_x *= self.cosd(self.lat) / m_to_deg
            if self.az <= 90 or self.az > 270:
                y[i] += delta_y
                x[i] += delta_x
            else:
                y[i] -= delta_y
                x[i] -= delta_x

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
        Z = griddata(points=(x, y), values=z, xi=(X, Y), fill_value=0)

        # For testing
        # fig = plt.figure()
        # ax = Axes3D(fig)
        # ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.jet,linewidth=1, antialiased=True)
        # plt.show()

        self.source3D = ColumnDataSource(data=dict(x=X, y=Y, z=Z))
        self.elevation = Surface3d(
            x='x', y='y', z='z', data_source=self.source3D)


    def widgets(self):

        def select():

            areas = ['Svartsengi', 'Reykjanes', 'Hellisheidi',
                     'Nesjavellir', 'Krafla', 'Theistareykir']

            select = Select(title='Geothermal Area',
                            value='Svartsengi', options=areas)
            select.js_on_change("value", CustomJS(code="""
                console.log('select: value=' + this.value, this.toString())"""))

            return select

        # TODO: Functionality

        def slider(param, step, title, buffer=None, start=None, end=None):

            if start is None:
                start = param - buffer
                end = param + buffer

            slider = Slider(start=start,
                            end=end,
                            value=param,
                            step=step,
                            title=title)
            # fill_source = ColumnDataSource(data=dict(x=[], y=[], z=[]))
            # callback = CustomJS(args=dict(source=self.source), code="""
            #     var data = source.data;
            #     var f = cb_obj.value
            #     var x = data['x']
            #     var y = data['y']
            #     var z = data['z']
            #     for (var i = 0; i < x.length; i++) {
            #         y[i] = Math.pow(x[i], f)
            #     }
            #     source.change.emit();
            # """)
            # callback = CustomJS(args=dict(source=self.source, fill_source=fill_source),
            #                     code="""var data = source.data;
            #                             var fill_data = fill_source.data;
            #                             var f = cb_obj.value;
            #                             fill_data['x']=[];
            #                             fill_data['y']=[];
            #                             fill_data['z']=[];
            #                             for (i = 0; i < f; i++) {
            #                                 fill_data['y'][i].push(data['y'][i]);
            #                                 fill_data['x'][i].push(data['x'][i]);
            #                                 fill_data['z'][i].push(data['z'][i]);
            #                                 }
            #                             fill_source.trigger('change');
            #                             """)
            # def update(attr, old, new):
            #     pass
            #     # new_data = dict(
            #     #     r=self.r,
            #     #     z=new
            #     # )
            #     # self.source2D.data = new_data

            slider.js_on_change('value', CustomJS(code="""
               console.log('slider: value=' + this.value, this.toString())
             """))
            # print(title)

            return slider

        # def slider_input_handler(attr, old, new):

        # TODO: This is awful. Should I load a json with the values?
        
        lon = slider(param=self.lon,
                     buffer=2000,
                     step=10,
                     title='X Coordinate')
        lat = slider(param=self.lat,
                     buffer=2000,
                     step=10,
                     title='Y Coordinate')
        cd = slider(param=1500,
                    start=0,
                    end=2500,
                    step=10,
                    title='Casing Depth')
        kop = slider(param=self.kop,
                     start=0,
                     end=self.mmd,
                     step=0.5,
                     title='Kick-Off')
        mmd = slider(param=2500,
                     start=0,
                     end=2500+1000,
                     step=10,
                     title='Measured Depth')
        Z = slider(param=self.Z,
                   buffer=100,
                   step=1,
                   title='Well Head Elevation')
        az = slider(param=self.az,
                    start=0,
                    end=359,
                    step=5,
                    title='Azimuth')
        bu = slider(param=self.bu,
                    start=0,
                    end=5,
                    step=0.5,
                    title='Build-Up')

        area = select()
        self.widgets = column(area, lon, lat, mmd, Z, az, cd, kop, bu)

    def present(self):
        grid = gridplot([[self.fig2D, self.elevation], [
            self.widgets]], sizing_mode='stretch_both')
        show(grid)


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
