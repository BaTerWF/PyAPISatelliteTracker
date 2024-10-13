from skyfield.api import EarthSatellite, load
from astropy.time import Time
from astropy.coordinates import EarthLocation, GCRS, ITRS, AltAz
from astropy import units as u
from astropy.coordinates import CartesianRepresentation
import numpy as np


# Пока не работает.
class TLEConverter:
    def __init__(self, tle_line1, tle_line2):
        self.tle_line1 = tle_line1
        self.tle_line2 = tle_line2
        self.timescale = load.timescale()
        self.satellite = EarthSatellite(tle_line1, tle_line2, 'Sat', self.timescale)

    def tle_to_ef(self, time_str):
        t = self.timescale.utc(Time(time_str).datetime)
        geocentric = self.satellite.at(t)
        subpoint = geocentric.subpoint()
        return subpoint.latitude.degrees, subpoint.longitude.degrees, subpoint.elevation.m

    def ef_to_j2000(self, time_str):
        lat, lon, elevation = self.tle_to_ef(time_str)
        location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg, height=elevation*u.m)
        time = Time(time_str)
        itrs = ITRS(location.get_itrs(obstime=time))
        gcrs = itrs.transform_to(GCRS(obstime=time))
        return gcrs.cartesian

    def j2000_to_gtsk(self, time_str):
        cartesian = self.ef_to_j2000(time_str)
        x, y, z = cartesian.x.value, cartesian.y.value, cartesian.z.value
        return x, y, z

    def gtsk_to_pz90(self, x, y, z):
        return x, y, z

    def convert(self, time_str):
        lat, lon, elevation = self.tle_to_ef(time_str)
        print(f"EF (Lat, Lon, Elev): {lat}, {lon}, {elevation}")

        j2000_coords = self.ef_to_j2000(time_str)
        print(f"J2000 (X, Y, Z): {j2000_coords.x.value}, {j2000_coords.y.value}, {j2000_coords.z.value}")

        x, y, z = self.j2000_to_gtsk(time_str)
        print(f"GTSK (X, Y, Z): {x}, {y}, {z}")

        pz90_x, pz90_y, pz90_z = self.gtsk_to_pz90(x, y, z)
        print(f"PZ-90 (X, Y, Z): {pz90_x}, {pz90_y}, {pz90_z}")