class Widgets:
    def __init__(self):
        pass

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
