import ast
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
        kop=None,
        dip=20,
        cd=0,
        bu=2
    ):

        self.lon = lon
        self.lat = lat
        self.mmd = mmd if mmd > 10 else mmd * 1000
        self.Z = Z
        self.az = az
        self.kop = kop
        self.dip = dip
        self.cd = cd if cd > 1 else cd * self.mmd
        self.bu = bu / 30

        self.coord_sys = 'WGS84' if lat < 90 else 'ISN93'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, tb):
        pass

    @staticmethod
    def cosd(deg):
        return np.cos(np.deg2rad(deg))

    @staticmethod
    def sind(deg):
        return np.sin(np.deg2rad(deg))

    @staticmethod
    def tand(deg):
        return np.tan(np.deg2rad(deg))

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

        # Directional
        if self.kop != None:
            # First leg
            r1, z1 = first_leg()

            # Second leg - The curved segment
            r2 = np.zeros(self.dip - 1)
            z2 = np.zeros(self.dip - 1)
            z2[0] = z1[-1]
            len_2 = np.zeros(self.dip - 1)
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

        # Vertical
        else:
            self.r, self.z = first_leg()

        # Determine casing TVD to split curve
        if self.cd <= self.kop:
            self.split = sum(self.z < (self.cd - self.Z))
        elif self.kop < self.cd and self.cd < len_2[-1]:
            self.split = 50 + sum(len_2 < (self.cd - self.Z))
        elif len_2[-1] < self.cd:
            self.split = 50 + len(z2) + sum(len_3 < (self.cd - self.Z))
        else:
            warnings.warn('Check casing block')

        self.plot_2d(self.r, self.z, self.split)


    def plot_2d(self, r, z, split):
        # y-axis is reversed by reversing the axis range
        self.fig2D = figure(title="2D Trajectory",
                            x_axis_label='Horizontal Throw [m]',
                            y_axis_label='Vert. Depth [m]',
                            x_range=(-50, max(r) + 100),
                            y_range=(max(z) + 100, -50 - self.Z))

        # def plotter(r, z, c):
        self.source2D = ColumnDataSource(data=dict(x=r, y=z))
        self.fig2D.line(x='x', y='y', data_source=self.source2D)
        # self.fig2D.line(
        #     r,
        #     z,
        #     color=c,
        #     line_width=3,
        #     line_cap='round'
        # )

        # plotter(r[:split+1], z[:split+1], '#000000')
        # plotter(r[split:], z[split:], '#ff0000')
        # show(self.fig2D)



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

    def trajectory_3d(self):

        def delta(r):

            delta_y = r / np.sqrt(self.tand(self.az)**2 + 1)
            delta_x = delta_y * self.tand(self.az)

            return delta_x, delta_y

        self.fig3D = px.scatter_3d(title="3D Trajectory",
                                   x_axis_label='Horizontal Throw [m]',
                                   y_axis_label='Vert. Depth [m]',
                                   x_range=(-50, max(r) + 100),
                                   y_range=(max(z) + 100, -50 - self.Z))
        # fig = plt.figure(dpi=200)
        # ax = plt.axes(projection='3d')
        # ax3D = self.fig.add_subplot(self.gs[:, 1:], projection='3d')
        # ax3D.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        # ax3D.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        # ax3D.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        x = self.lon + np.zeros(len(self.r))
        y = self.lat + np.zeros(len(self.r))
        m_to_deg = 1.11e5  # m to deg on Earth's surface

        for i in range(len(self.z)):
            # Accounting for special cases -> tand(az) = inf
            if self.az == 90 or self.az == 270:
                delta_y = 0
                delta_x = self.r[-1]
            else:
                delta_x, delta_y = delta(self.r[i])

            delta_y /= m_to_deg
            # m to deg is lat dependent for lon
            delta_x *= self.cosd(self.lat) / m_to_deg
            if self.az <= 90 or self.az > 270:
                y[i] += delta_y
                x[i] += delta_x
            else:
                y[i] -= delta_y
                x[i] -= delta_x

        ax3D.plot3D(x[:self.split+1], y[:self.split+1],
                    self.z[:self.split+1], 'k')
        ax3D.plot3D(x[self.split:], y[self.split:], self.z[self.split:], 'r')
        ax3D.set_box_aspect([1, 1, 1])
        ax3D.invert_zaxis()
        # plt.show()
        # show(row(self.fig2D, self.fig3D))

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


            slider.js_on_change('value', CustomJS(code= """
               console.log('slider: value=' + this.value, this.toString())
             """))
            # print(title)

            return slider

        # def slider_input_handler(attr, old, new):

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
    run = WellTargeting(
        lon=333_000,
        lat=376_000,
        mmd=2500,
        Z=20,
        az=30,
        cd=1500,
        kop=1000,
        bu=1.5,
    )

    run.trajectory_2d()
    run.elevation()
    run.widgets()
    # run.trajectory_3d()
    run.present()
