from skyfield.api import load, EarthSatellite
from datetime import datetime, timedelta

class TLEConverter:
    def __init__(self, tle_line1, tle_line2):
        # Загружаем данные TLE и создаем объект спутника
        self.timescale = load.timescale()
        self.satellite = EarthSatellite(tle_line1, tle_line2, 'Satellite', self.timescale)

    def calculate_orbit(self, start_time, end_time, step_minutes=1):
        t0 = self.timescale.utc(start_time.year, start_time.month, start_time.day, start_time.hour, start_time.minute)
        t1 = self.timescale.utc(end_time.year, end_time.month, end_time.day, end_time.hour, end_time.minute)

        total_minutes = (end_time - start_time).total_seconds() / 60
        num_steps = int(total_minutes // step_minutes)

        time_range = [t0 + (i * (t1 - t0) / num_steps) for i in range(num_steps + 1)]
        orbit_coords = []

        for t in time_range:
            geocentric = self.satellite.at(t)  # Позиция спутника в геоцентрических координатах
            subpoint = geocentric.subpoint()  # Подспутниковая точка
            latitude = subpoint.latitude.degrees  # Широта
            longitude = subpoint.longitude.degrees  # Долгота
            elevation = subpoint.elevation.m  # Высота над поверхностью
            orbit_coords.append((latitude, longitude, elevation))

        return orbit_coords