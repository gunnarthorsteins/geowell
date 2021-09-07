def plot_2d(self):

    self.split_curve()

    # y-axis is reversed by reversing the axis range
    self.fig2D = figure(title="2D Trajectory",
                        x_axis_label='Horizontal Throw [m]',
                        y_axis_label='Vert. Depth [m]',
                        x_range=(-50, max(self.r) + 100),
                        y_range=(max(self.z) + 100, -50 - self.Z))

    self.source2D = ColumnDataSource(data=dict(x=self.r, y=self.z))
    self.fig2D.line(x='x', y='y', data_source=self.source2D)

def plot_3d(self):

    self.fig3D = px.scatter_3d(title="3D Trajectory",
                                x_axis_label='Horizontal Throw [m]',
                                y_axis_label='Vert. Depth [m]',
                                x_range=(-50, max(r) + 100),
                                y_range=(max(z) + 100, -50 - self.Z))
    ax3D.plot3D(x[:self.split+1], y[:self.split+1],
                self.z[:self.split+1], 'k')
    ax3D.plot3D(x[self.split:], y[self.split:], self.z[self.split:], 'r')
    ax3D.set_box_aspect([1, 1, 1])
    ax3D.invert_zaxis()
    # show(row(self.fig2D, self.fig3D))
