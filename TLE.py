from skyfield.api import load, EarthSatellite
from astropy.time import Time
from astropy.coordinates import EarthLocation, GCRS, ITRS
from astropy import units as u
import numpy as np
from datetime import datetime, timedelta


class TLEConverter:
    def __init__(self, tle_line1, tle_line2):
        # Загружаем данные TLE и создаем объект спутника
        self.timescale = load.timescale()
        self.satellite = EarthSatellite(tle_line1, tle_line2, 'Satellite', self.timescale)

    def tle_to_ef(self, time):
        """Преобразует TLE в Earth-Fixed координаты на заданное время"""
        # Преобразуем время в формат Skyfield
        t = self.timescale.utc(time.year, time.month, time.day, time.hour, time.minute, time.second)
        geocentric = self.satellite.at(t)
        subpoint = geocentric.subpoint()
        return subpoint.latitude.degrees, subpoint.longitude.degrees, subpoint.elevation.m

    def ef_to_j2000(self, time):
        """Преобразует Earth-Fixed в J2000"""
        lat, lon, elevation = self.tle_to_ef(time)
        location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)
        time_astropy = Time(time.isoformat())
        itrs = ITRS(location.get_itrs(obstime=time_astropy))
        gcrs = itrs.transform_to(GCRS(obstime=time_astropy))
        return gcrs.cartesian

    def calculate_orbit(self, start_time, end_time, step_minutes=1):
        """Функция для расчета орбиты спутника за указанный временной период.
        :param start_time: время начала (datetime)
        :param end_time: время окончания (datetime)
        :param step_minutes: шаг в минутах между расчетными точками
        :return: список координат спутника на каждый временной шаг
        """
        # Преобразуем время начала и конца в формат Skyfield
        t0 = self.timescale.utc(start_time.year, start_time.month, start_time.day, start_time.hour, start_time.minute)
        t1 = self.timescale.utc(end_time.year, end_time.month, end_time.day, end_time.hour, end_time.minute)

        # Вычисляем количество временных шагов
        total_minutes = (end_time - start_time).total_seconds() / 60
        num_steps = int(total_minutes // step_minutes)

        # Создаем временной диапазон с заданным шагом
        time_range = [t0 + (i * (t1 - t0) / num_steps) for i in range(num_steps + 1)]
        orbit_coords = []

        # Для каждого временного шага рассчитываем положение спутника
        for t in time_range:
            geocentric = self.satellite.at(t)
            subpoint = geocentric.subpoint()
            latitude = subpoint.latitude.degrees
            longitude = subpoint.longitude.degrees
            elevation = subpoint.elevation.m
            orbit_coords.append((latitude, longitude, elevation))

        return orbit_coords

    def convert(self, time):
        """Основной метод для выполнения всех преобразований на указанное время"""
        lat, lon, elevation = self.tle_to_ef(time)
        print(f"EF (Lat, Lon, Elev): {lat}, {lon}, {elevation}")

        j2000_coords = self.ef_to_j2000(time)
        print(f"J2000 (X, Y, Z): {j2000_coords.x.value}, {j2000_coords.y.value}, {j2000_coords.z.value}")

        # Здесь можно добавить дальнейшие преобразования, если необходимо

        return lat, lon, elevation, j2000_coords

