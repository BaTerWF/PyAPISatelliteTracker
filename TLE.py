import requests
from sgp4.api import Satrec
from astropy.coordinates import TEME, ITRS, CartesianRepresentation, EarthLocation
from astropy.time import Time as AstroPyTime
from astropy import units as u
from datetime import datetime
from numpy import rad2deg

TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

def fetch_tle_from_source():
    """Fetch TLE data from CelesTrak."""
    try:
        response = requests.get(TLE_URL)
        if response.status_code != 200:
            raise Exception("Failed to fetch TLE data.")
        tle_data = response.text.splitlines()
        return tle_data
    except Exception as e:
        raise Exception(f"Error fetching TLE: {str(e)}")

def process_tle_data(tle_data):
    """Process TLE data into satellite entries."""
    satellites = []
    for i in range(0, len(tle_data), 3):
        satellite_name = tle_data[i].strip()
        line1 = tle_data[i + 1].strip()
        line2 = tle_data[i + 2].strip()
        satellites.append({
            "satellite_name": satellite_name,
            "line1": line1,
            "line2": line2
        })
    return satellites

def get_orbital_parameters(tle_line1, tle_line2):
    """Calculate orbital parameters from TLE data."""
    sat = Satrec.twoline2rv(tle_line1, tle_line2)
    # Calculate semi-major axis in km
    mu = 398600.4418  # Earth's gravitational parameter in km^3/s^2
    n = sat.no_kozai / 60.0  # Mean motion in revs per second
    semi_major_axis = (mu / (n * 2 * 3.14159265359) ** 2) ** (1 / 3)

    params = {
        "semi_major_axis_km": semi_major_axis,
        "eccentricity": sat.ecco,
        "inclination_deg": rad2deg(sat.inclo),
        "right_ascension_deg": rad2deg(sat.nodeo),
        "argument_perigee_deg": rad2deg(sat.argpo),
        "mean_anomaly_deg": rad2deg(sat.mo),
    }
    return params

def get_satellite_position_xyz(tle_line1, tle_line2, current_time=None):
    """Get satellite position in XYZ coordinates (ITRS) for the given time."""
    sat = Satrec.twoline2rv(tle_line1, tle_line2)

    if current_time is None:
        current_time = datetime.utcnow()

    astro_time = AstroPyTime(current_time, scale="utc")
    jd, fr = astro_time.jd1, astro_time.jd2

    error_code, teme_position, teme_velocity = sat.sgp4(jd, fr)
    if error_code != 0:
        raise ValueError(f"SGP4 error code: {error_code}")

    teme_coords = TEME(CartesianRepresentation(teme_position * u.km), obstime=astro_time)
    itrs_coords = teme_coords.transform_to(ITRS(obstime=astro_time)).cartesian.xyz

    return {
        "x_km": itrs_coords[0].value,
        "y_km": itrs_coords[1].value,
        "z_km": itrs_coords[2].value,
    }

def get_lat_lon_alt(tle_line1, tle_line2, current_time=None):
    """Get satellite latitude, longitude, and altitude for the given time."""
    sat = Satrec.twoline2rv(tle_line1, tle_line2)

    if current_time is None:
        current_time = datetime.utcnow()

    astro_time = AstroPyTime(current_time, scale="utc")
    jd, fr = astro_time.jd1, astro_time.jd2

    error_code, teme_position, teme_velocity = sat.sgp4(jd, fr)
    if error_code != 0:
        raise ValueError(f"SGP4 error code: {error_code}")

    teme_coords = TEME(CartesianRepresentation(teme_position * u.km), obstime=astro_time)
    itrs_coords = teme_coords.transform_to(ITRS(obstime=astro_time)).cartesian.xyz

    earth_location = EarthLocation(x=itrs_coords[0], y=itrs_coords[1], z=itrs_coords[2])
    geodetic_location = earth_location.to_geodetic()

    return {
        "latitude_deg": geodetic_location.lat.deg,
        "longitude_deg": geodetic_location.lon.deg,
        "altitude_km": geodetic_location.height.to(u.km).value,
    }

def get_orbit_and_position(tle_line1, tle_line2, current_time=None):
    """Get both orbital parameters and current position of the satellite."""
    orbital_params = get_orbital_parameters(tle_line1, tle_line2)
    position_xyz = get_satellite_position_xyz(tle_line1, tle_line2, current_time)
    lat_lon_alt = get_lat_lon_alt(tle_line1, tle_line2, current_time)

    return {
        "orbital_parameters": orbital_params,
        "current_position_xyz": position_xyz,
        "current_lat_lon_alt": lat_lon_alt,
    }
