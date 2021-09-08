
class Trajectory2d:
    def __init__(self):
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


class Trajectory3d(Trajectory2d):


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
